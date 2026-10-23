#!/usr/bin/env python3
"""PostToolUse(Write/Edit): nhắc Claude viết unit test cho file code vừa sửa (unit test là bắt buộc)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import edited_file, project_dir, read_input, relative_to_project  # noqa: E402

BACKEND_RULES = [
    (re.compile(r"^backend/app/modules/(\w+)/service\.py$"),
     lambda m: [f"backend/tests/unit/modules/{m[1]}/test_{m[1]}_service.py"]),
    (re.compile(r"^backend/app/modules/(\w+)/repository\.py$"),
     lambda m: [f"backend/tests/integration/test_{m[1]}_repository.py"]),
    (re.compile(r"^backend/app/usecases/(\w+)/(?!interfaces|mappers|__init__)(\w+)\.py$"),
     lambda m: [f"backend/tests/unit/usecases/{m[1]}/test_{m[2]}.py"]),
    (re.compile(r"^backend/app/controllers/(\w+_controller)\.py$"),
     lambda m: [f"backend/tests/unit/controllers/test_{m[1]}.py"]),
]
FRONTEND_SOURCE = re.compile(r"^frontend/src/(?!app/)(.+/)?([\w.-]+)\.(tsx?|jsx?)$")
FRONTEND_SKIP = re.compile(r"(\.test\.|\.spec\.|\.d\.ts$|/interfaces\.ts$|/types\.ts$|/index\.ts$)")


def expected_tests(relative: str) -> list[str]:
    for pattern, build in BACKEND_RULES:
        match = pattern.match(relative)
        if match:
            return build(match)
    match = FRONTEND_SOURCE.match(relative)
    if match and not FRONTEND_SKIP.search(relative):
        folder = f"frontend/src/{match[1] or ''}"
        name, ext = match[2], match[3]
        test_ext = "tsx" if ext in ("tsx", "jsx") else "ts"
        return [f"{folder}{name}.test.{test_ext}", f"{folder}__tests__/{name}.test.{test_ext}"]
    return []


def main() -> int:
    data = read_input()
    path = edited_file(data)
    if path is None:
        return 0
    relative = relative_to_project(data, path)
    if relative is None:
        return 0
    candidates = expected_tests(relative)
    root = project_dir(data)
    if candidates and not any((root / candidate).exists() for candidate in candidates):
        print(f"[Bắt buộc unit test] {relative} chưa có test. Viết test tại {candidates[0]} "
              "(dùng fake/in-memory cho các interface phụ thuộc) trước khi verify.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
