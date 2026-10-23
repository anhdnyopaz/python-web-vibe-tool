#!/usr/bin/env python3
"""PreToolUse(Bash): hỏi lại trước lệnh nguy hiểm, chặn commit khi code chưa được kiểm tra."""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import pre_tool_decision, project_dir, read_input  # noqa: E402

DANGEROUS = [
    (r"\bdocker(-compose|\s+compose)\b[^;&|]*\bdown\b[^;&|]*(\s-v\b|--volumes)",
     "Lệnh này XOÁ dữ liệu database và Redis (docker volume)."),
    (r"\bdocker\s+(volume\s+(rm|prune)|system\s+prune)", "Lệnh này xoá dữ liệu/volume Docker."),
    (r"\bgit\s+push\b[^;&|]*(\s-f\b|--force)", "Force push ghi đè lịch sử trên GitHub."),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard xoá các thay đổi chưa commit."),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean xoá file chưa được git theo dõi."),
    (r"\bgit\s+checkout\s+--\s+\.", "Lệnh này huỷ toàn bộ thay đổi chưa commit."),
    (r"\bgit\s+branch\s+-D\b", "Xoá branch chưa merge."),
    (r"(?i)\b(drop\s+(table|database|schema)|truncate\s+table)\b", "Lệnh SQL xoá dữ liệu."),
    (r"\balembic\s+downgrade\b", "Downgrade migration có thể làm mất dữ liệu."),
    (r"\bchmod\s+-R\s+777\b", "Mở toàn quyền file là lỗ hổng bảo mật."),
    (r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba)?sh\b", "Chạy script tải từ Internet."),
]
RM_RF = re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|-r\s+-f|-f\s+-r)\s+(.+)")
SAFE_RM_TARGETS = {"node_modules", ".next", "__pycache__", ".pytest_cache", ".ruff_cache", "test-results",
                   "playwright-report", "coverage", "htmlcov", "dist", "build", ".turbo"}
COMMIT = re.compile(r"\bgit\s+(-C\s+\S+\s+)?commit\b")

# Ghi file code bằng shell sẽ lách hook require_tests/require_design (chỉ bắt Write/Edit).
SOURCE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
TARGET = r"""('[^']*'|"[^"]*"|[^\s;&|<>()]+)"""
REDIRECT = re.compile(r"(?:^|[^<>&\d])\d?>{1,2}\|?\s*" + TARGET)
TEE = re.compile(r"\btee\s+(?:-\w+\s+)*" + TARGET)
IN_PLACE = re.compile(r"\b(?:sed|perl)\b[^;&|]*?\s(?:-[a-zA-Z]*i\b|--in-place)([^;&|]*)")
COPY = re.compile(r"\bcp\s+([^;&|]+)")


def strip_heredoc_bodies(command: str) -> str:
    """Bỏ nội dung heredoc để không nhầm dấu '>' trong code là lệnh ghi file."""
    lines, kept, delimiter = command.split("\n"), [], None
    for line in lines:
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        kept.append(line)
        match = HEREDOC.search(line)
        if match:
            delimiter = match.group(2)
    return "\n".join(kept)


def shell_write_targets(command: str) -> list[str]:
    command = strip_heredoc_bodies(command)
    targets = [m.group(1) for m in REDIRECT.finditer(command)]
    targets += [m.group(1) for m in TEE.finditer(command)]
    for match in IN_PLACE.finditer(command):
        targets += match.group(1).split()
    for match in COPY.finditer(command):
        words = match.group(1).split()
        if len(words) >= 2:
            targets.append(words[-1])
    return [t.strip("'\"") for t in targets]


def protected_source(target: str, root: Path) -> bool:
    if Path(target).suffix not in SOURCE_EXTENSIONS or target.startswith("~"):
        return False
    path = Path(target)
    if not path.is_absolute():
        return True
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False  # file tạm ngoài dự án, ví dụ /tmp/shot.ts


def rm_is_safe(arguments: str) -> bool:
    try:
        targets = shlex.split(arguments.split("&&")[0].split(";")[0].split("|")[0])
    except ValueError:
        return False
    return bool(targets) and all(Path(t.rstrip("/")).name in SAFE_RM_TARGETS for t in targets)


def check_commit(command: str, root: Path) -> str | None:
    if "--no-verify" in command:
        return "Không được bỏ qua kiểm tra khi commit (--no-verify)."
    pm = root / ".claude" / "tools" / "pm.py"
    if not pm.exists():
        return None
    env = {**os.environ, "PM_ROOT": str(root)}
    result = subprocess.run([sys.executable, str(pm), "check-fresh"], capture_output=True, text=True,
                            env=env, cwd=root)
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        return message[len("Lỗi: "):] if message.startswith("Lỗi: ") else message
    return None


def main() -> int:
    data = read_input()
    command = (data.get("tool_input") or {}).get("command") or ""
    if not command:
        return 0
    if COMMIT.search(command):
        reason = check_commit(command, project_dir(data))
        if reason:
            pre_tool_decision("deny", f"Chặn commit: {reason}")
            return 0
    written = [t for t in shell_write_targets(command) if protected_source(t, project_dir(data))]
    if written:
        pre_tool_decision("deny", f"Không ghi file code bằng shell ({', '.join(written)}). "
                                  "Dùng công cụ Write/Edit để hook kiểm tra unit test và thiết kế chạy được.")
        return 0
    for pattern, reason in DANGEROUS:
        if re.search(pattern, command):
            pre_tool_decision("ask", f"⚠️ {reason} Chỉ đồng ý nếu bạn chắc chắn.")
            return 0
    match = RM_RF.search(command)
    if match and not rm_is_safe(match.group(2)):
        pre_tool_decision("ask", "⚠️ Lệnh xoá thư mục/file vĩnh viễn (rm -rf). Chỉ đồng ý nếu bạn chắc chắn.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
