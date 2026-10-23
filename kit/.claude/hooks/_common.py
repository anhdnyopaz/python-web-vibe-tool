"""Tiện ích dùng chung cho các hook (chỉ thư viện chuẩn, chạy được với Python 3.9)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

FILE_KEYS = ("file_path", "path", "target_file", "target_filepath", "filepath")


def read_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def project_dir(data: dict[str, Any]) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()).resolve()


def edited_file(data: dict[str, Any]) -> Path | None:
    tool_input = data.get("tool_input") or {}
    for key in FILE_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            path = Path(value)
            return (path if path.is_absolute() else project_dir(data) / path).resolve()
    return None


def relative_to_project(data: dict[str, Any], path: Path) -> str | None:
    try:
        return path.relative_to(project_dir(data)).as_posix()
    except ValueError:
        return None


def pre_tool_decision(decision: str, reason: str) -> None:
    """In quyết định cho PreToolUse: 'allow' | 'deny' | 'ask'."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": decision,
                                             "permissionDecisionReason": reason}},
                     ensure_ascii=False))
