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
