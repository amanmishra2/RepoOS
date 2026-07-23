"""Path containment, hashing, and state-root helpers."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

from repoos.errors import environment_error, invalid_input, unsafe_state


def canonical_path(path: str | Path, *, must_exist: bool = False) -> Path:
    """Return an expanded canonical path without silently accepting missing paths."""

    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve(strict=must_exist)
    except (OSError, RuntimeError) as exc:
        raise environment_error(
            "Unable to resolve path.", path=str(candidate), reason=str(exc)
        ) from exc
    if must_exist and not resolved.exists():
        raise environment_error("Required path does not exist.", path=str(resolved))
    return resolved


def require_directory(path: str | Path) -> Path:
    resolved = canonical_path(path, must_exist=True)
    if not resolved.is_dir():
        raise invalid_input("Expected a directory.", path=str(resolved))
    return resolved


def contained_path(root: str | Path, relative: str | Path, *, must_exist: bool = False) -> Path:
    """Resolve a relative path and reject traversal or symlink escapes."""

    root_path = require_directory(root)
    relative_path = Path(relative)
    if relative_path.is_absolute() or "\\" in str(relative):
        raise unsafe_state("Target path must be a portable relative path.", target=str(relative))
    if not relative_path.parts or any(part in {"", ".", ".."} for part in relative_path.parts):
        raise unsafe_state("Target path contains an unsafe segment.", target=str(relative))

    raw_target = root_path / relative_path
    cursor = root_path
    for part in relative_path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise unsafe_state("Target path traverses a symlink.", target=str(relative))

    target = canonical_path(raw_target, must_exist=must_exist)
    try:
        common = Path(os.path.commonpath([root_path, target]))
    except ValueError as exc:
        raise unsafe_state("Target path is outside the repository.", target=str(relative)) from exc
    if common != root_path:
        raise unsafe_state("Target path escapes the repository.", target=str(relative))
    return target


def state_root(override: str | Path | None = None) -> Path:
    """Return the configurable platform state root without creating it."""

    if override is not None:
        return canonical_path(override)
    configured = os.environ.get("REPOOS_STATE_DIR")
    if configured:
        return canonical_path(configured)
    if sys.platform == "darwin":
        return canonical_path(Path.home() / "Library" / "Application Support" / "repoos")
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return canonical_path(base / "repoos")
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return canonical_path(base / "repoos")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    file_path = canonical_path(path, must_exist=True)
    if not file_path.is_file() or file_path.is_symlink():
        raise invalid_input("Expected a regular non-symlink file.", path=str(file_path))
    digest = hashlib.sha256()
    with file_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
