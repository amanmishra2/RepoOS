"""Fail-closed per-repository file locks."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from repoos.errors import ExitCode, RepoOSError


def lock_key(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class RepositoryLock:
    """An explicit O_EXCL lock; stale recovery is intentionally manual."""

    state_directory: Path
    identity: str
    _path: Path | None = None
    _fd: int | None = None

    def acquire(self) -> None:
        lock_directory = self.state_directory / "locks"
        lock_directory.mkdir(parents=True, exist_ok=True)
        self._path = lock_directory / f"{lock_key(self.identity)}.lock"
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "identity_sha256": lock_key(self.identity),
                "acquired_at": datetime.now(UTC).isoformat(),
            },
            sort_keys=True,
        ).encode("utf-8")
        try:
            self._fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RepoOSError(
                "Another RepoOS operation holds this repository lock.",
                ExitCode.LOCKED,
                "lock_contended",
                {"lock": str(self._path)},
            ) from exc
        try:
            os.write(self._fd, payload)
            os.fsync(self._fd)
        except BaseException:
            os.close(self._fd)
            self._fd = None
            self._path.unlink(missing_ok=True)
            self._path = None
            raise

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self._path is not None:
            self._path.unlink(missing_ok=True)
            self._path = None

    def __enter__(self) -> RepositoryLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()
