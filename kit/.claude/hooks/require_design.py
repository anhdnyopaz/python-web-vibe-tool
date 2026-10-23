#!/usr/bin/env python3
"""PreToolUse(Write/Edit): bắt buộc nạp skill frontend-design trước khi sửa giao diện."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import edited_file, pre_tool_decision, project_dir, read_input, relative_to_project  # noqa: E402

UI_FILE = re.compile(r"^frontend/src/.+\.(tsx|jsx|css)$")
NOT_UI = re.compile(r"(\.test\.|\.spec\.|/__tests__/)")
SKILL_MARKER = "/skills/frontend-design"


def transcript_for(data: dict) -> Path | None:
    transcript = data.get("transcript_path")
    if not transcript:
        return None
    path = Path(transcript)
    agent_id = data.get("agent_id")
    if agent_id:
        # Sub agent có transcript riêng: <session>.jsonl -> <session>/subagents/agent-<id>.jsonl
        return path.with_suffix("") / "subagents" / f"agent-{agent_id}.jsonl"
    return path


def skill_loaded(transcript: Path, cache_dir: Path, cache_key: str) -> bool:
    marker = cache_dir / f"design-ok-{cache_key}"
    if marker.exists():
        return True
    try:
        with transcript.open(encoding="utf-8", errors="ignore") as handle:
            found = any(SKILL_MARKER in line for line in handle)
    except OSError:
        return True  # không đọc được transcript thì không chặn nhầm
    if found:
        cache_dir.mkdir(parents=True, exist_ok=True)
        marker.touch()
    return found


def main() -> int:
    data = read_input()
    path = edited_file(data)
    relative = relative_to_project(data, path) if path else None
    if not relative or not UI_FILE.match(relative) or NOT_UI.search(relative):
        return 0
    transcript = transcript_for(data)
    if transcript is None:
        return 0
    key = re.sub(r"[^\w-]", "", f"{data.get('session_id', '')}-{data.get('agent_id') or 'main'}")
    if not skill_loaded(transcript, project_dir(data) / ".pm" / "logs", key):
        pre_tool_decision("deny", "Bắt buộc dùng skill frontend-design trước khi sửa giao diện. "
                                  "Gọi Skill tool với skill 'frontend-design:frontend-design', lập design plan "
                                  "theo hướng dẫn của skill, rồi mới sửa file này.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
