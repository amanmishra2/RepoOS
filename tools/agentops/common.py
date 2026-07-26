from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def require_file(path: str) -> bool:
    p = ROOT / path
    if not p.exists():
        print(f"FAIL missing {path}")
        return False
    print(f"OK {path}")
    return True


def warn_if_large(path: str, max_lines: int) -> bool:
    p = ROOT / path
    if not p.exists():
        print(f"WARN missing {path}")
        return True
    lines = p.read_text(encoding="utf-8").splitlines()
    if len(lines) > max_lines:
        print(f"WARN {path} has {len(lines)} lines; target <= {max_lines}")
    else:
        print(f"OK {path} size {len(lines)} lines")
    return True


def load_json(path: str) -> bool:
    p = ROOT / path
    try:
        json.loads(p.read_text(encoding="utf-8"))
        print(f"OK valid JSON {path}")
        return True
    except Exception as exc:
        print(f"FAIL invalid JSON {path}: {exc}")
        return False


def require_any(paths: Iterable[str], label: str) -> bool:
    if any((ROOT / p).exists() for p in paths):
        print(f"OK {label}")
        return True
    print(f"WARN no {label}")
    return True


def main_check(name: str, checks: Iterable[bool]) -> int:
    ok = all(checks)
    print(f"{name}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1
