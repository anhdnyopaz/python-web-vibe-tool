#!/usr/bin/env python3
"""pm — công cụ quản lý dự án nhỏ cho quy trình TechLead.

Chỉ dùng thư viện chuẩn của Python. Dữ liệu nằm ở `.pm/board.json` (commit vào git),
bảng xem nhanh được sinh ra ở `docs/BOARD.md`, dashboard web chạy bằng `pm serve`.

Ví dụ:
    python3 .claude/tools/pm.py init --name "Shop hoa"
    python3 .claude/tools/pm.py add "Đăng ký tài khoản" --priority P1 --api --ui \
        --ac "Given khách chưa có tài khoản When nhập email hợp lệ Then tài khoản được tạo"
    python3 .claude/tools/pm.py start T-001
    python3 .claude/tools/pm.py verify
    python3 .claude/tools/pm.py submit T-001
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

UTC = timezone.utc  # Python 3.9 trên macOS chưa có datetime.UTC
PM_DIR = ".pm"
BOARD_FILE = "board.json"
CONFIG_FILE = "config.json"
BOARD_MD = Path("docs") / "BOARD.md"
DECISIONS_DIR = Path("docs") / "decisions"
CHANGELOG = Path("CHANGELOG.md")
DASHBOARD_HTML = Path(__file__).with_name("dashboard.html")

STATUSES = ("todo", "doing", "review", "blocked", "done")
STATUS_LABELS = {
    "todo": "Cần làm",
    "doing": "Đang làm",
    "review": "Chờ nghiệm thu",
    "blocked": "Bị chặn",
    "done": "Đã xong",
}
TYPES = ("feature", "bug", "chore")
TYPE_LABELS = {"feature": "Tính năng", "bug": "Lỗi", "chore": "Kỹ thuật"}
BRANCH_PREFIX = {"feature": "feat", "bug": "fix", "chore": "chore"}
PRIORITIES = ("P0", "P1", "P2", "P3")
REQUEST_KINDS = ("feature", "bug")
DEPLOY_RESULTS = ("success", "failed", "rolled_back")

DEFAULT_CONFIG: dict[str, Any] = {
    "wip_limit": 1,
    "require_acceptance": False,
    "gates": {
        "lint": "make lint",
        "unit": "make test-unit",
        "api": "make test-api",
        "e2e": "make test-e2e",
    },
    "always_gates": ["lint", "unit"],
    "source_paths": ["backend", "frontend", "tests", "docker-compose.yml", "Makefile"],
    "ignore_dirs": [
        ".git", "node_modules", ".next", "__pycache__", ".pytest_cache", ".ruff_cache",
        ".import_linter_cache", ".venv", "coverage", "htmlcov", "test-results",
        "playwright-report", "blob-report",
    ],
    "links": {
        "app": "http://localhost:8080",
        "api_docs": "http://localhost:8080/api/docs",
    },
}


class PMError(Exception):
    """Lỗi nghiệp vụ hiển thị cho người dùng (không in traceback)."""


# --------------------------------------------------------------------------- tiện ích


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def slugify(text: str, max_length: int = 40) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_length].rstrip("-") or "item"


def find_root(start: Path | None = None) -> Path:
    if os.environ.get("PM_ROOT"):
        return Path(os.environ["PM_ROOT"]).resolve()
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / PM_DIR).is_dir():
            return candidate
    return current


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(tmp, path)


# --------------------------------------------------------------------------- lưu trữ


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.pm_dir = root / PM_DIR

    @property
    def initialized(self) -> bool:
        return (self.pm_dir / BOARD_FILE).exists()

    def require(self) -> None:
        if not self.initialized:
            raise PMError("Dự án chưa khởi tạo. Chạy: python3 .claude/tools/pm.py init --name \"Tên\"")

    def load_board(self) -> dict[str, Any]:
        self.require()
        board = json.loads((self.pm_dir / BOARD_FILE).read_text(encoding="utf-8"))
        for key in ("tasks", "requests", "questions", "deploys", "releases"):
            board.setdefault(key, [])
        board.setdefault("seq", {})
        return board

    def save_board(self, board: dict[str, Any]) -> None:
        write_atomic(self.pm_dir / BOARD_FILE,
                     json.dumps(board, ensure_ascii=False, indent=2) + "\n")
        write_atomic(self.root / BOARD_MD, render_board_md(board))

    def load_config(self) -> dict[str, Any]:
        path = self.pm_dir / CONFIG_FILE
        config = json.loads(json.dumps(DEFAULT_CONFIG))
        if path.exists():
            config.update(json.loads(path.read_text(encoding="utf-8")))
        return config

    def save_config(self, config: dict[str, Any]) -> None:
        write_atomic(self.pm_dir / CONFIG_FILE,
                     json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def next_id(board: dict[str, Any], prefix: str, width: int = 3) -> str:
    board["seq"][prefix] = board["seq"].get(prefix, 0) + 1
    return f"{prefix}-{board['seq'][prefix]:0{width}d}"


def find_task(board: dict[str, Any], task_id: str) -> dict[str, Any]:
    wanted = task_id.upper()
    for task in board["tasks"]:
        if task["id"] == wanted:
            return task
    raise PMError(f"Không tìm thấy task {task_id}")


def find_item(items: list[dict[str, Any]], item_id: str, label: str) -> dict[str, Any]:
    wanted = item_id.upper()
    for item in items:
        if item["id"] == wanted:
            return item
    raise PMError(f"Không tìm thấy {label} {item_id}")


def set_status(task: dict[str, Any], status: str, note: str | None = None) -> None:
    previous = task["status"]
    task["status"] = status
    task["updated_at"] = now_iso()
    task.setdefault("history", []).append(
        {"at": task["updated_at"], "from": previous, "to": status, **({"note": note} if note else {})})
    if status == "done":
        task["done_at"] = task["updated_at"]


def priority_key(task: dict[str, Any]) -> tuple:
    return (PRIORITIES.index(task.get("priority", "P2")), task.get("milestone") or "~",
            int(task["id"].split("-")[1]))


def deps_done(board: dict[str, Any], task: dict[str, Any]) -> bool:
    done = {t["id"] for t in board["tasks"] if t["status"] == "done"}
    return all(dep in done for dep in task.get("after", []))


# --------------------------------------------------------------------------- dấu vân tay mã nguồn


def source_files(root: Path, config: dict[str, Any]) -> list[Path]:
    """Danh sách file nguồn (ưu tiên hỏi git để tôn trọng .gitignore)."""
    paths = [p for p in config["source_paths"] if (root / p).exists()]
    if not paths:
        return []
    try:
        result = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z", "--", *paths],
            cwd=root, capture_output=True, check=True)
        names = [name for name in result.stdout.decode().split("\0") if name]
        return sorted(root / name for name in names if (root / name).is_file())
    except (OSError, subprocess.CalledProcessError):
        ignore = set(config["ignore_dirs"])
        found: list[Path] = []
        for entry in paths:
            target = root / entry
            if target.is_file():
                found.append(target)
                continue
            for dirpath, dirnames, filenames in os.walk(target):
                dirnames[:] = [d for d in dirnames if d not in ignore]
                found.extend(Path(dirpath) / name for name in filenames)
        return sorted(found)


def source_fingerprint(root: Path, config: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    for path in source_files(root, config):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


# --------------------------------------------------------------------------- kiểm tra chất lượng


def gates_for(task: dict[str, Any] | None, config: dict[str, Any]) -> list[str]:
    if task is None:
        return list(config["gates"])
    gates = list(config["always_gates"])
    if task.get("needs_api"):
        gates.append("api")
    if task.get("needs_ui"):
        gates.append("e2e")
    return [gate for gate in gates if gate in config["gates"]]


def run_gates(store: Store, gates: list[str], config: dict[str, Any]) -> dict[str, Any]:
    logs_dir = store.pm_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    fingerprint = source_fingerprint(store.root, config)
    started = now_iso()
    results: dict[str, Any] = {}
    for gate in gates:
        command = config["gates"][gate]
        log_path = logs_dir / f"{gate}.log"
        print(f"▶ {gate}: {command}", flush=True)
        begin = time.monotonic()
        with log_path.open("w", encoding="utf-8") as log:
            code = subprocess.run(command, shell=True, cwd=store.root, stdout=log,
                                  stderr=subprocess.STDOUT).returncode
        duration = round(time.monotonic() - begin, 1)
        passed = code == 0
        results[gate] = {"passed": passed, "seconds": duration, "exit_code": code}
        if passed:
            print(f"  ✔ {gate} đạt ({duration}s)", flush=True)
        else:
            tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
            print(f"  ✘ {gate} KHÔNG đạt ({duration}s) — log đầy đủ: {log_path.relative_to(store.root)}")
            print("  " + "\n  ".join(tail), flush=True)
    return {"at": started, "passed": all(r["passed"] for r in results.values()),
            "gates": results, "fingerprint": fingerprint}


def is_fresh(verify: dict[str, Any] | None, store: Store, config: dict[str, Any]) -> bool:
    return bool(verify and verify.get("passed")
                and verify.get("fingerprint") == source_fingerprint(store.root, config))


# --------------------------------------------------------------------------- render


def progress_bar(done: int, total: int, width: int = 20) -> str:
    filled = round(width * done / total) if total else 0
    percent = round(100 * done / total) if total else 0
    return f"{'█' * filled}{'░' * (width - filled)} {percent}% ({done}/{total})"


def ac_summary(task: dict[str, Any]) -> str:
    criteria = task.get("acceptance", [])
    return f"{sum(c['done'] for c in criteria)}/{len(criteria)}" if criteria else "—"


def render_board_md(board: dict[str, Any]) -> str:
    tasks = board["tasks"]
    done = sum(t["status"] == "done" for t in tasks)
    lines = [
        f"# Bảng dự án: {board['project']['name']}",
        "",
        "> File này được sinh tự động bởi `pm`. Đừng sửa tay — xem trực quan hơn bằng lệnh `/board`.",
        "",
        f"**Tiến độ:** `{progress_bar(done, len(tasks))}`",
        "",
    ]
    open_questions = [q for q in board["questions"] if q["status"] == "open"]
    new_requests = [r for r in board["requests"] if r["status"] == "new"]
    if open_questions or new_requests:
        lines += ["## Việc cần Product Owner", ""]
        lines += [f"- ❓ **{q['id']}** {q['text']}" + (f" _(task {q['task']})_" if q.get("task") else "")
                  for q in open_questions]
        lines += [f"- 📥 **{r['id']}** ({'Tính năng' if r['kind'] == 'feature' else 'Lỗi'}) {r['text']}"
                  for r in new_requests]
        lines.append("")
    for status in ("doing", "review", "blocked", "todo", "done"):
        group = sorted((t for t in tasks if t["status"] == status), key=priority_key)
        if status == "done":
            group = sorted(group, key=lambda t: t.get("done_at", ""), reverse=True)[:20]
        if not group:
            continue
        lines += [f"## {STATUS_LABELS[status]} ({len(group)})", "",
                  "| ID | Việc | Loại | Ưu tiên | Milestone | Tiêu chí đạt |",
                  "|---|---|---|---|---|---|"]
        for task in group:
            title = task["title"].replace("|", "\\|")
            if status == "blocked" and task.get("blocked_reason"):
                title += f" — _{task['blocked_reason']}_"
            lines.append(f"| {task['id']} | {title} | {TYPE_LABELS[task['type']]} | "
                         f"{task['priority']} | {task.get('milestone') or ''} | {ac_summary(task)} |")
        lines.append("")
    if board["deploys"]:
        lines += ["## Lịch sử deploy (5 lần gần nhất)", "", "| Thời gian | Phiên bản | Nơi | Kết quả |",
                  "|---|---|---|---|"]
        for deploy in board["deploys"][-5:][::-1]:
            lines.append(f"| {deploy['at']} | {deploy['version']} | {deploy['target']} | {deploy['result']} |")
        lines.append("")
    return "\n".join(lines)


def describe_task(task: dict[str, Any]) -> str:
    lines = [f"{task['id']} · {task['title']}",
             f"  Loại: {TYPE_LABELS[task['type']]} | Ưu tiên: {task['priority']} | "
             f"Trạng thái: {STATUS_LABELS[task['status']]}"
             + (f" | Milestone: {task['milestone']}" if task.get("milestone") else "")]
    needs = [name for flag, name in (("needs_api", "Hurl (API)"), ("needs_ui", "Playwright (UI)"))
             if task.get(flag)]
    lines.append(f"  Test bắt buộc: lint, unit{', ' + ', '.join(needs) if needs else ''}")
    if task.get("after"):
        lines.append(f"  Làm sau: {', '.join(task['after'])}")
    if task.get("branch"):
        lines.append(f"  Branch: {task['branch']}")
    if task.get("description"):
        lines.append(f"  Mô tả: {task['description']}")
    if task.get("blocked_reason"):
        lines.append(f"  Bị chặn vì: {task['blocked_reason']}")
    lines.append("  Tiêu chí chấp nhận:")
    for index, criterion in enumerate(task.get("acceptance", []), start=1):
        lines.append(f"    [{'x' if criterion['done'] else ' '}] {index}. {criterion['text']}")
    if not task.get("acceptance"):
        lines.append("    (chưa có — thêm bằng: pm edit ID --ac \"Given ... When ... Then ...\")")
    verify = task.get("verify")
    if verify:
        gates = ", ".join(f"{name} {'✔' if r['passed'] else '✘'}" for name, r in verify["gates"].items())
        lines.append(f"  Kiểm tra gần nhất: {verify['at']} — {gates}")
    for note in task.get("notes", [])[-5:]:
        lines.append(f"  📝 {note['at']}: {note['text']}")
    return "\n".join(lines)


def summarize(board: dict[str, Any]) -> dict[str, Any]:
    counts = {status: 0 for status in STATUSES}
    for task in board["tasks"]:
        counts[task["status"]] += 1
    todo = sorted((t for t in board["tasks"] if t["status"] == "todo" and deps_done(board, t)),
                  key=priority_key)
    milestones: dict[str, dict[str, int]] = {}
    for task in board["tasks"]:
        name = task.get("milestone") or "Chưa xếp"
        bucket = milestones.setdefault(name, {"done": 0, "total": 0})
        bucket["total"] += 1
        bucket["done"] += task["status"] == "done"
    return {
        "counts": counts,
        "total": len(board["tasks"]),
        "next": todo[0]["id"] if todo else None,
        "milestones": milestones,
        "open_questions": sum(q["status"] == "open" for q in board["questions"]),
        "new_requests": sum(r["status"] == "new" for r in board["requests"]),
    }


# --------------------------------------------------------------------------- lệnh


def cmd_init(store: Store, args: argparse.Namespace) -> str:
    if store.initialized and not args.force:
        raise PMError("Dự án đã được khởi tạo (.pm/board.json đã có). Dùng --force để tạo lại.")
    board = {"project": {"name": args.name, "created_at": now_iso()}, "seq": {}, "tasks": [],
             "requests": [], "questions": [], "deploys": [], "releases": []}
    store.pm_dir.mkdir(parents=True, exist_ok=True)
    if not (store.pm_dir / CONFIG_FILE).exists():
        store.save_config(DEFAULT_CONFIG)
    write_atomic(store.pm_dir / ".gitignore", "logs/\n")
    (store.root / DECISIONS_DIR).mkdir(parents=True, exist_ok=True)
    store.save_board(board)
    return f"Đã khởi tạo dự án \"{args.name}\". Bảng: {BOARD_MD}"


def _apply_task_fields(board: dict[str, Any], task: dict[str, Any], args: argparse.Namespace) -> None:
    for field in ("title", "milestone"):
        value = getattr(args, field, None)
        if value is not None:
            task[field] = value
    if getattr(args, "desc", None) is not None:
        task["description"] = args.desc
    if getattr(args, "type", None):
        task["type"] = args.type
    if getattr(args, "priority", None):
        task["priority"] = args.priority.upper()
    if getattr(args, "api", None) is not None:
        task["needs_api"] = args.api
    if getattr(args, "ui", None) is not None:
        task["needs_ui"] = args.ui
    if getattr(args, "after", None):
        deps = [dep.strip().upper() for dep in args.after.split(",") if dep.strip()]
        for dep in deps:
            find_task(board, dep)
            if dep == task["id"]:
                raise PMError("Task không thể phụ thuộc chính nó")
        task["after"] = deps
    for text in getattr(args, "ac", None) or []:
        task.setdefault("acceptance", []).append({"text": text, "done": False})
    task["updated_at"] = now_iso()


def cmd_add(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    if args.priority and args.priority.upper() not in PRIORITIES:
        raise PMError(f"Ưu tiên phải là một trong {', '.join(PRIORITIES)}")
    task = {"id": next_id(board, "T"), "title": args.title, "type": args.type or "feature",
            "priority": (args.priority or "P2").upper(), "milestone": args.milestone,
            "status": "todo", "description": args.desc or "", "acceptance": [], "after": [],
            "needs_api": bool(args.api), "needs_ui": bool(args.ui), "notes": [], "history": [],
            "created_at": now_iso()}
    args.api = args.ui = args.desc = args.priority = args.type = None
    _apply_task_fields(board, task, args)
    if args.source:
        request = find_item(board["requests"], args.source, "yêu cầu")
        task["source"] = request["id"]
        request.setdefault("tasks", []).append(task["id"])
        request["status"] = "triaged"
    board["tasks"].append(task)
    store.save_board(board)
    return f"Đã thêm {task['id']}: {task['title']}"


def cmd_edit(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    if args.priority and args.priority.upper() not in PRIORITIES:
        raise PMError(f"Ưu tiên phải là một trong {', '.join(PRIORITIES)}")
    _apply_task_fields(board, task, args)
    store.save_board(board)
    return describe_task(task)


def cmd_list(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    tasks = sorted(board["tasks"], key=priority_key)
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]
    elif not args.all:
        tasks = [t for t in tasks if t["status"] != "done"]
    if args.milestone:
        tasks = [t for t in tasks if t.get("milestone") == args.milestone]
    if not tasks:
        return "Không có task nào khớp."
    return "\n".join(f"{t['id']}  [{STATUS_LABELS[t['status']]}]  {t['priority']}  "
                     f"{t['title']}  (AC {ac_summary(t)})" for t in tasks)


def cmd_show(store: Store, args: argparse.Namespace) -> str:
    return describe_task(find_task(store.load_board(), args.id))


def cmd_start(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    config = store.load_config()
    task = find_task(board, args.id)
    if task["status"] not in ("todo", "blocked"):
        raise PMError(f"{task['id']} đang ở trạng thái '{STATUS_LABELS[task['status']]}', không thể bắt đầu")
    doing = [t["id"] for t in board["tasks"] if t["status"] == "doing"]
    if len(doing) >= config["wip_limit"]:
        raise PMError(f"Giới hạn {config['wip_limit']} task cùng lúc. Đang làm: {', '.join(doing)}. "
                      "Hoàn thành hoặc block task đó trước.")
    if not deps_done(board, task):
        raise PMError(f"{task['id']} phải làm sau {', '.join(task['after'])} (chưa xong)")
    if not task.get("acceptance"):
        raise PMError(f"{task['id']} chưa có tiêu chí chấp nhận. Thêm bằng: pm edit {task['id']} --ac \"...\"")
    task["branch"] = task.get("branch") or f"{BRANCH_PREFIX[task['type']]}/{task['id'].lower()}-{slugify(task['title'], 30)}"
    task.pop("blocked_reason", None)
    set_status(task, "doing")
    store.save_board(board)
    return (f"Bắt đầu {task['id']}: {task['title']}\n"
            f"Tạo branch: git switch -c {task['branch']}  (hoặc git switch {task['branch']} nếu đã có)")


def cmd_ac(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    criteria = task.get("acceptance", [])
    if not 1 <= args.index <= len(criteria):
        raise PMError(f"{task['id']} chỉ có {len(criteria)} tiêu chí")
    criteria[args.index - 1]["done"] = not args.undo
    if args.evidence:
        criteria[args.index - 1]["evidence"] = args.evidence
    task["updated_at"] = now_iso()
    store.save_board(board)
    return f"{task['id']}: tiêu chí {args.index} {'chưa đạt' if args.undo else 'đã đạt'} (AC {ac_summary(task)})"


def cmd_note(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    task.setdefault("notes", []).append({"at": now_iso(), "text": args.text})
    store.save_board(board)
    return f"Đã ghi chú vào {task['id']}"


def cmd_block(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    if task["status"] == "done":
        raise PMError("Task đã xong, không thể block")
    task["blocked_reason"] = args.reason
    set_status(task, "blocked", args.reason)
    store.save_board(board)
    return f"{task['id']} bị chặn: {args.reason}"


def cmd_unblock(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    if task["status"] != "blocked":
        raise PMError(f"{task['id']} không bị chặn")
    task.pop("blocked_reason", None)
    set_status(task, "todo")
    store.save_board(board)
    return f"{task['id']} đã gỡ chặn, quay về 'Cần làm'"


def cmd_verify(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    config = store.load_config()
    task = None
    if args.id:
        task = find_task(board, args.id)
    elif not args.all:
        doing = [t for t in board["tasks"] if t["status"] == "doing"]
        task = doing[0] if len(doing) == 1 else None
    gates = gates_for(task, config)
    print(f"Kiểm tra {'cho ' + task['id'] if task else 'toàn dự án'}: {', '.join(gates)}", flush=True)
    result = run_gates(store, gates, config)
    board = store.load_board()  # gate có thể chạy lâu — đọc lại để không ghi đè thay đổi khác
    if task:
        find_task(board, task["id"])["verify"] = result
    board["last_verify"] = result
    store.save_board(board)
    if not result["passed"]:
        raise PMError("Kiểm tra KHÔNG đạt. Sửa lỗi rồi chạy lại verify. Không được tắt/skip test.")
    return "✅ Tất cả kiểm tra đều đạt."


def cmd_submit(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    config = store.load_config()
    task = find_task(board, args.id)
    if task["status"] != "doing":
        raise PMError(f"{task['id']} phải đang ở trạng thái 'Đang làm' mới nộp được")
    pending = [str(i) for i, c in enumerate(task.get("acceptance", []), start=1) if not c["done"]]
    if pending:
        raise PMError(f"Còn tiêu chí chưa đạt: {', '.join(pending)}. Đánh dấu bằng: pm ac {task['id']} <số>")
    if not is_fresh(task.get("verify"), store, config):
        raise PMError("Chưa có lần verify đạt nào sau lần sửa code gần nhất. "
                      f"Chạy: python3 .claude/tools/pm.py verify {task['id']}")
    required = set(gates_for(task, config))
    missing = required - set(task["verify"]["gates"])
    if missing:
        raise PMError(f"Lần verify gần nhất thiếu: {', '.join(sorted(missing))}. Chạy lại verify.")
    if config.get("require_acceptance"):
        set_status(task, "review")
        message = f"{task['id']} chuyển sang 'Chờ nghiệm thu'. Mời Product Owner thử và chấp nhận."
    else:
        set_status(task, "done")
        message = f"🎉 {task['id']} hoàn thành."
    store.save_board(board)
    return message


def cmd_accept(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    if task["status"] != "review":
        raise PMError(f"{task['id']} không ở trạng thái 'Chờ nghiệm thu'")
    set_status(task, "done", "Product Owner chấp nhận")
    store.save_board(board)
    return f"🎉 {task['id']} được chấp nhận và hoàn thành."


def cmd_reject(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    task = find_task(board, args.id)
    if task["status"] != "review":
        raise PMError(f"{task['id']} không ở trạng thái 'Chờ nghiệm thu'")
    task.setdefault("notes", []).append({"at": now_iso(), "text": f"PO từ chối: {args.reason}"})
    task.pop("verify", None)
    set_status(task, "doing", args.reason)
    store.save_board(board)
    return f"{task['id']} quay lại 'Đang làm'. Lý do: {args.reason}"


def cmd_next(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    doing = [t for t in board["tasks"] if t["status"] == "doing"]
    if doing:
        return "Đang làm dở — tiếp tục task này trước:\n" + describe_task(doing[0])
    task_id = summarize(board)["next"]
    if not task_id:
        return "Không còn task nào sẵn sàng. Thêm việc bằng /feature hoặc kiểm tra task bị chặn."
    return "Task tiếp theo nên làm:\n" + describe_task(find_task(board, task_id))


def cmd_status(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    config = store.load_config()
    info = summarize(board)
    counts = info["counts"]
    lines = [f"Dự án: {board['project']['name']}",
             f"Tiến độ: {progress_bar(counts['done'], info['total'])}",
             "Trạng thái: " + " | ".join(f"{STATUS_LABELS[s]} {counts[s]}" for s in STATUSES if counts[s])]
    doing = [t for t in board["tasks"] if t["status"] == "doing"]
    if doing:
        lines.append(f"Đang làm: {doing[0]['id']} {doing[0]['title']} (AC {ac_summary(doing[0])})")
    if info["next"]:
        lines.append(f"Tiếp theo: {info['next']} {find_task(board, info['next'])['title']}")
    for task in board["tasks"]:
        if task["status"] == "blocked":
            lines.append(f"Bị chặn: {task['id']} {task['title']} — {task.get('blocked_reason', '')}")
    if info["new_requests"]:
        lines.append(f"📥 {info['new_requests']} yêu cầu mới từ Product Owner chưa phân tích (pm inbox)")
    if info["open_questions"]:
        lines.append(f"❓ {info['open_questions']} câu hỏi đang chờ Product Owner trả lời (pm questions)")
    review = [t["id"] for t in board["tasks"] if t["status"] == "review"]
    if review:
        lines.append(f"🔎 Chờ nghiệm thu: {', '.join(review)}")
    last = board.get("last_verify")
    if last:
        state = "đạt" if last["passed"] else "KHÔNG đạt"
        fresh = "" if is_fresh(last, store, config) else " (code đã đổi sau đó)"
        lines.append(f"Kiểm tra gần nhất: {last['at']} — {state}{fresh}")
    if board["deploys"]:
        deploy = board["deploys"][-1]
        lines.append(f"Deploy gần nhất: {deploy['version']} → {deploy['target']} ({deploy['result']}, {deploy['at']})")
    if args.brief:
        return "[pm] " + "\n[pm] ".join(lines)
    if info["milestones"]:
        lines.append("Milestone:")
        for name, bucket in sorted(info["milestones"].items()):
            lines.append(f"  {name}: {progress_bar(bucket['done'], bucket['total'], 10)}")
    return "\n".join(lines)


def cmd_board(store: Store, args: argparse.Namespace) -> str:
    store.save_board(store.load_board())
    return f"Đã cập nhật {BOARD_MD}"


def add_request(board: dict[str, Any], kind: str, text: str, task: str | None = None) -> dict[str, Any]:
    if kind not in REQUEST_KINDS:
        raise PMError("Loại yêu cầu phải là 'feature' hoặc 'bug'")
    text = text.strip()
    if not text:
        raise PMError("Nội dung yêu cầu không được để trống")
    request = {"id": next_id(board, "R"), "kind": kind, "text": text, "status": "new",
               "at": now_iso(), "tasks": [], **({"related_task": task} if task else {})}
    board["requests"].append(request)
    return request


def cmd_request(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    request = add_request(board, args.kind, args.text, args.task)
    store.save_board(board)
    return f"Đã ghi nhận {request['id']}"


def cmd_inbox(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    items = [r for r in board["requests"] if args.all or r["status"] == "new"]
    if not items:
        return "Hộp thư trống — không có yêu cầu mới."
    return "\n".join(f"{r['id']} [{'Tính năng' if r['kind'] == 'feature' else 'Lỗi'}] [{r['status']}] "
                     f"{r['text']}" + (f" → {', '.join(r['tasks'])}" if r.get("tasks") else "")
                     for r in items)


def cmd_triage(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    request = find_item(board["requests"], args.id, "yêu cầu")
    if args.tasks:
        for task_id in args.tasks.split(","):
            task = find_task(board, task_id.strip())
            task["source"] = request["id"]
            if task["id"] not in request["tasks"]:
                request["tasks"].append(task["id"])
    request["status"] = "triaged"
    if args.note:
        request["note"] = args.note
    store.save_board(board)
    return f"{request['id']} đã phân tích" + (f" → {', '.join(request['tasks'])}" if request["tasks"] else "")


def cmd_ask(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    if args.task:
        find_task(board, args.task)
    question = {"id": next_id(board, "Q"), "text": args.text, "status": "open", "at": now_iso(),
                **({"task": args.task.upper()} if args.task else {})}
    board["questions"].append(question)
    store.save_board(board)
    return f"Đã ghi câu hỏi {question['id']} cho Product Owner"


def answer_question(board: dict[str, Any], question_id: str, text: str) -> dict[str, Any]:
    question = find_item(board["questions"], question_id, "câu hỏi")
    if not text.strip():
        raise PMError("Câu trả lời không được để trống")
    question.update({"status": "answered", "answer": text.strip(), "answered_at": now_iso()})
    return question


def cmd_answer(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    question = answer_question(board, args.id, args.text)
    store.save_board(board)
    return f"Đã lưu câu trả lời cho {question['id']}"


def cmd_questions(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    items = [q for q in board["questions"] if args.all or q["status"] == "open"]
    if not items:
        return "Không có câu hỏi nào đang chờ."
    return "\n".join(f"{q['id']} [{q['status']}] {q['text']}"
                     + (f"\n    → {q['answer']}" if q.get("answer") else "") for q in items)


def cmd_adr(store: Store, args: argparse.Namespace) -> str:
    store.require()
    directory = store.root / DECISIONS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.name[:4]) for p in directory.glob("[0-9][0-9][0-9][0-9]-*.md")]
    number = max(numbers, default=0) + 1
    path = directory / f"{number:04d}-{slugify(args.title)}.md"
    write_atomic(path, "\n".join([
        f"# {number:04d}. {args.title}", "",
        f"- Ngày: {datetime.now(UTC).date().isoformat()}",
        f"- Trạng thái: {args.status}", "",
        "## Bối cảnh", "", args.context or "_Vấn đề cần quyết định là gì? Vì sao bây giờ?_", "",
        "## Quyết định", "", args.decision or "_Chúng ta chọn làm gì?_", "",
        "## Hệ quả", "", args.consequences or "_Được gì, mất gì, cần lưu ý gì về sau?_", ""]))
    return f"Đã tạo {path.relative_to(store.root)}"


def cmd_link(store: Store, args: argparse.Namespace) -> str:
    store.require()
    config = store.load_config()
    if args.remove:
        config["links"].pop(args.name, None)
        message = f"Đã xoá link {args.name}"
    else:
        if not args.url:
            raise PMError("Thiếu URL")
        config["links"][args.name] = args.url
        message = f"Đã lưu link {args.name}: {args.url}"
    store.save_config(config)
    return message


def cmd_deploy_log(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    entry = {"at": now_iso(), "version": args.version, "target": args.target,
             "result": args.result, **({"note": args.note} if args.note else {})}
    board["deploys"].append(entry)
    store.save_board(board)
    return f"Đã ghi lịch sử deploy {args.version} → {args.target}: {args.result}"


def cmd_release(store: Store, args: argparse.Namespace) -> str:
    board = store.load_board()
    if any(r["version"] == args.version for r in board["releases"]):
        raise PMError(f"Phiên bản {args.version} đã tồn tại")
    tasks = [t for t in board["tasks"] if t["status"] == "done" and not t.get("released_in")]
    if not tasks:
        raise PMError("Không có task nào mới hoàn thành kể từ lần phát hành trước")
    for task in tasks:
        task["released_in"] = args.version
    board["releases"].append({"version": args.version, "at": now_iso(),
                              "tasks": [t["id"] for t in tasks]})
    section = [f"## {args.version} — {datetime.now(UTC).date().isoformat()}", ""]
    for kind, heading in (("feature", "Tính năng mới"), ("bug", "Sửa lỗi"), ("chore", "Kỹ thuật")):
        group = [t for t in tasks if t["type"] == kind]
        if group:
            section += [f"### {heading}", ""] + [f"- {t['title']} ({t['id']})" for t in group] + [""]
    changelog = store.root / CHANGELOG
    existing = changelog.read_text(encoding="utf-8") if changelog.exists() else "# Nhật ký thay đổi\n"
    header, _, rest = existing.partition("\n")
    write_atomic(changelog, f"{header}\n\n" + "\n".join(section) + rest.lstrip("\n"))
    store.save_board(board)
    return "\n".join(section) + f"\nĐã cập nhật {CHANGELOG}. Gắn tag: git tag -a {args.version} -m \"{args.version}\""


def cmd_check_fresh(store: Store, args: argparse.Namespace) -> str:
    """Dùng cho hook chặn commit: đạt khi code nguồn không đổi kể từ lần verify đạt gần nhất."""
    if not store.initialized:
        return "pm chưa khởi tạo — bỏ qua kiểm tra"
    config = store.load_config()
    if not source_files(store.root, config):
        return "Chưa có mã nguồn — bỏ qua kiểm tra"
    board = store.load_board()
    if is_fresh(board.get("last_verify"), store, config):
        return "Code đã được kiểm tra — được phép commit"
    raise PMError("Code đã thay đổi sau lần kiểm tra đạt gần nhất (hoặc chưa từng kiểm tra). "
                  "Chạy `python3 .claude/tools/pm.py verify` cho đến khi đạt rồi mới commit.")


# --------------------------------------------------------------------------- dashboard


class DashboardHandler(BaseHTTPRequestHandler):
    store: Store
    token: str
    allowed_hosts: set[str]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - chữ ký của thư viện chuẩn
        pass

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _host_ok(self) -> bool:
        return (self.headers.get("Host") or "").split(":")[0] in self.allowed_hosts

    def do_GET(self) -> None:  # noqa: N802 - tên do http.server quy định
        if not self._host_ok():
            return self._json(HTTPStatus.FORBIDDEN, {"error": "host không hợp lệ"})
        if self.path in ("/", "/index.html"):
            html = DASHBOARD_HTML.read_text(encoding="utf-8").replace("__PM_TOKEN__", self.token)
            return self._send(HTTPStatus.OK, html.encode(), "text/html; charset=utf-8")
        if self.path == "/api/state":
            return self._json(HTTPStatus.OK, dashboard_state(self.store))
        return self._json(HTTPStatus.NOT_FOUND, {"error": "không tìm thấy"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._host_ok() or self.headers.get("X-PM-Token") != self.token:
            return self._json(HTTPStatus.FORBIDDEN, {"error": "không được phép"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}") if length else {}
            message = handle_dashboard_action(self.store, self.path, payload)
            return self._json(HTTPStatus.OK, {"message": message})
        except PMError as error:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except (ValueError, json.JSONDecodeError):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "dữ liệu gửi lên không hợp lệ"})


def dashboard_state(store: Store) -> dict[str, Any]:
    board = store.load_board()
    config = store.load_config()
    return {"project": board["project"], "links": config.get("links", {}),
            "require_acceptance": config.get("require_acceptance", False),
            "tasks": board["tasks"], "requests": board["requests"], "questions": board["questions"],
            "deploys": board["deploys"][-10:], "releases": board["releases"][-5:],
            "last_verify": board.get("last_verify"), "summary": summarize(board),
            "labels": {"status": STATUS_LABELS, "type": TYPE_LABELS}}


def handle_dashboard_action(store: Store, path: str, payload: dict[str, Any]) -> str:
    board = store.load_board()
    parts = [part for part in path.split("/") if part]
    if parts == ["api", "requests"]:
        request = add_request(board, str(payload.get("kind", "")), str(payload.get("text", "")),
                              payload.get("task"))
        message = f"Đã gửi {request['id']}. TechLead sẽ phân tích ở lần /next hoặc /feature tiếp theo."
    elif len(parts) == 4 and parts[:2] == ["api", "questions"] and parts[3] == "answer":
        question = answer_question(board, parts[2], str(payload.get("text", "")))
        message = f"Đã lưu câu trả lời cho {question['id']}"
    elif len(parts) == 4 and parts[:2] == ["api", "tasks"] and parts[3] in ("accept", "reject"):
        task = find_task(board, parts[2])
        if task["status"] != "review":
            raise PMError(f"{task['id']} không ở trạng thái 'Chờ nghiệm thu'")
        if parts[3] == "accept":
            set_status(task, "done", "Product Owner chấp nhận (dashboard)")
            message = f"{task['id']} đã được chấp nhận"
        else:
            reason = str(payload.get("reason", "")).strip()
            if not reason:
                raise PMError("Hãy ghi lý do từ chối để TechLead biết cần sửa gì")
            task.setdefault("notes", []).append({"at": now_iso(), "text": f"PO từ chối: {reason}"})
            task.pop("verify", None)
            set_status(task, "doing", reason)
            message = f"{task['id']} quay lại 'Đang làm'"
    else:
        raise PMError("Hành động không hợp lệ")
    store.save_board(board)
    return message


def cmd_serve(store: Store, args: argparse.Namespace) -> str:
    store.require()
    handler = type("Handler", (DashboardHandler,), {
        "store": store, "token": secrets.token_urlsafe(24),
        "allowed_hosts": {"localhost", "127.0.0.1", args.host}})
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://localhost:{args.port}"
    print(f"Dashboard đang chạy tại {url}  (Ctrl+C để dừng)", flush=True)
    if args.open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, url], check=False)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return "Đã dừng dashboard"


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pm", description="Quản lý dự án cho quy trình TechLead")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Khởi tạo dự án")
    p.add_argument("--name", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    def task_fields(p: argparse.ArgumentParser, creating: bool) -> None:
        if not creating:
            p.add_argument("--title")
        p.add_argument("--type", choices=TYPES)
        p.add_argument("--priority", help="P0 (gấp nhất) … P3")
        p.add_argument("--milestone")
        p.add_argument("--desc")
        p.add_argument("--ac", action="append", help="Tiêu chí chấp nhận (lặp lại được)")
        p.add_argument("--api", action=argparse.BooleanOptionalAction, default=None,
                       help="Task có API → bắt buộc Hurl test")
        p.add_argument("--ui", action=argparse.BooleanOptionalAction, default=None,
                       help="Task có giao diện → bắt buộc Playwright test")
        p.add_argument("--after", help="Làm sau các task, ví dụ T-001,T-002")

    p = sub.add_parser("add", help="Thêm task")
    p.add_argument("title")
    task_fields(p, creating=True)
    p.add_argument("--from", dest="source", help="Tạo từ yêu cầu R-xxx của PO")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("edit", help="Sửa task (--ac sẽ THÊM tiêu chí)")
    p.add_argument("id")
    task_fields(p, creating=False)
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("list", help="Liệt kê task")
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--milestone")
    p.add_argument("--all", action="store_true", help="Gồm cả task đã xong")
    p.set_defaults(func=cmd_list)

    for name, func, help_text in (("show", cmd_show, "Xem chi tiết task"),
                                  ("start", cmd_start, "Bắt đầu làm task"),
                                  ("submit", cmd_submit, "Nộp task (cần AC + verify đạt)"),
                                  ("accept", cmd_accept, "PO chấp nhận task"),
                                  ("unblock", cmd_unblock, "Gỡ chặn task")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("id")
        p.set_defaults(func=func)

    p = sub.add_parser("ac", help="Đánh dấu tiêu chí chấp nhận đã đạt")
    p.add_argument("id")
    p.add_argument("index", type=int)
    p.add_argument("--undo", action="store_true")
    p.add_argument("--evidence", help="Test nào chứng minh, ví dụ tests/e2e/specs/signup.spec.ts")
    p.set_defaults(func=cmd_ac)

    p = sub.add_parser("note", help="Ghi chú vào task")
    p.add_argument("id")
    p.add_argument("text")
    p.set_defaults(func=cmd_note)

    for name, func, field in (("block", cmd_block, "reason"), ("reject", cmd_reject, "reason")):
        p = sub.add_parser(name, help="Chặn task" if name == "block" else "PO từ chối task")
        p.add_argument("id")
        p.add_argument(field)
        p.set_defaults(func=func)

    p = sub.add_parser("verify", help="Chạy các bước kiểm tra chất lượng")
    p.add_argument("id", nargs="?")
    p.add_argument("--all", action="store_true", help="Chạy mọi gate cho toàn dự án")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("next", help="Gợi ý task tiếp theo")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("status", help="Báo cáo tiến độ")
    p.add_argument("--brief", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("board", help="Sinh lại docs/BOARD.md")
    p.set_defaults(func=cmd_board)

    p = sub.add_parser("request", help="Ghi nhận yêu cầu của PO")
    p.add_argument("kind", choices=REQUEST_KINDS)
    p.add_argument("text")
    p.add_argument("--task", help="Task liên quan (khi báo lỗi)")
    p.set_defaults(func=cmd_request)

    p = sub.add_parser("inbox", help="Yêu cầu mới của PO")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_inbox)

    p = sub.add_parser("triage", help="Đánh dấu yêu cầu đã phân tích")
    p.add_argument("id")
    p.add_argument("--tasks", help="Các task được tạo, ví dụ T-004,T-005")
    p.add_argument("--note")
    p.set_defaults(func=cmd_triage)

    p = sub.add_parser("ask", help="Ghi câu hỏi cần PO trả lời")
    p.add_argument("text")
    p.add_argument("--task")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("answer", help="Lưu câu trả lời của PO")
    p.add_argument("id")
    p.add_argument("text")
    p.set_defaults(func=cmd_answer)

    p = sub.add_parser("questions", help="Câu hỏi đang chờ PO")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_questions)

    p = sub.add_parser("adr", help="Ghi một quyết định kỹ thuật")
    p.add_argument("title")
    p.add_argument("--status", default="accepted")
    p.add_argument("--context")
    p.add_argument("--decision")
    p.add_argument("--consequences")
    p.set_defaults(func=cmd_adr)

    p = sub.add_parser("link", help="Lưu link hiển thị trên dashboard (app, share, prod…)")
    p.add_argument("name")
    p.add_argument("url", nargs="?")
    p.add_argument("--remove", action="store_true")
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("deploy-log", help="Ghi lịch sử deploy")
    p.add_argument("--version", required=True)
    p.add_argument("--target", required=True, help="vps | tunnel | ...")
    p.add_argument("--result", required=True, choices=DEPLOY_RESULTS)
    p.add_argument("--note")
    p.set_defaults(func=cmd_deploy_log)

    p = sub.add_parser("release", help="Chốt phiên bản, cập nhật CHANGELOG.md")
    p.add_argument("version")
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("check-fresh", help="(hook) Code đã verify sau lần sửa cuối chưa?")
    p.set_defaults(func=cmd_check_fresh)

    p = sub.add_parser("serve", help="Mở dashboard web")
    p.add_argument("--port", type=int, default=4000)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--open", action="store_true", help="Tự mở trình duyệt")
    p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store(Path.cwd().resolve() if args.command == "init" and not os.environ.get("PM_ROOT")
                  else find_root())
    try:
        print(args.func(store, args))
        return 0
    except PMError as error:
        print(f"Lỗi: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
