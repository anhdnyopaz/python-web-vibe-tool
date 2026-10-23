#!/usr/bin/env python3
"""SessionStart: nạp tình trạng dự án vào ngữ cảnh để Claude biết đang ở đâu."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import project_dir, read_input  # noqa: E402


def main() -> int:
    root = project_dir(read_input())
    pm = root / ".claude" / "tools" / "pm.py"
    if not (root / ".pm" / "board.json").exists():
        print("[pm] Dự án chưa được khởi tạo. Nếu người dùng muốn bắt đầu, gợi ý chạy /kickoff.")
        return 0
    result = subprocess.run([sys.executable, str(pm), "status", "--brief"], capture_output=True, text=True,
                            env={**os.environ, "PM_ROOT": str(root)}, cwd=root)
    print(result.stdout.strip() or "[pm] Không đọc được trạng thái dự án.")
    print("[pm] Nhắc: mọi việc kỹ thuật giao cho sub agent `techlead`. Người dùng xem bảng trực quan bằng /board.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
