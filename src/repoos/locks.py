"""Process-visible global and per-common-Git operation locks."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from repoos.errors import ExitCode, RepoOSError

DEFAULT_STALE_AFTER_SECONDS = 3600


def lock_key(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class LockInspection:
    path: Path
    state: str
    metadata: dict[str, Any] | None
    reason: str | None

    @property
    def available(self) -> bool:
        return self.state == "missing"


def inspect_lock_file(
    path: Path,
    *,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
    now: datetime | None = None,
) -> LockInspection:
    """Classify a lock without changing it."""

    if not path.exists():
        return LockInspection(path, "missing", None, None)
    if path.is_symlink() or not path.is_file():
        return LockInspection(path, "malformed", None, "lock_not_regular_file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return LockInspection(path, "malformed", None, "lock_json_invalid")
    required = {
        "pid": int,
        "hostname": str,
        "start_time": str,
        "target": str,
        "transaction_id": str,
        "kind": str,
        "owner_token": str,
    }
    if not isinstance(value, dict):
        return LockInspection(path, "malformed", None, "lock_root_invalid")
    if any(not isinstance(value.get(key), expected) for key, expected in required.items()):
        return LockInspection(path, "malformed", value, "lock_metadata_invalid")
    try:
        started = datetime.fromisoformat(value["start_time"].replace("Z", "+00:00"))
    except ValueError:
        return LockInspection(path, "malformed", value, "lock_start_time_invalid")
    if started.tzinfo is None:
        return LockInspection(path, "malformed", value, "lock_start_time_missing_timezone")

    current = now or _now()
    hostname = socket.gethostname()
    if value["hostname"] == hostname:
        if _pid_is_alive(value["pid"]):
            return LockInspection(path, "active", value, "local_process_alive")
        return LockInspection(path, "stale", value, "local_process_missing")

    age = max(0.0, (current - started.astimezone(UTC)).total_seconds())
    if age > stale_after_seconds:
        return LockInspection(path, "stale", value, "remote_lock_expired")
    return LockInspection(path, "active", value, "remote_owner_within_stale_window")


def repository_lock_path(state_directory: Path, identity: str) -> Path:
    return state_directory / "locks" / "repositories" / f"{lock_key(identity)}.lock"


def global_lock_path(state_directory: Path) -> Path:
    return state_directory / "locks" / "global.lock"


def _lock_error(inspection: LockInspection) -> RepoOSError:
    details: dict[str, Any] = {
        "lock": str(inspection.path),
        "lock_state": inspection.state,
        "reason": inspection.reason,
    }
    if inspection.metadata is not None:
        for key in ("pid", "hostname", "start_time", "target", "transaction_id", "kind"):
            details[key] = inspection.metadata.get(key)
    if inspection.state in {"stale", "malformed"}:
        details["recovery_required"] = True
        return RepoOSError(
            "A stale or malformed RepoOS lock requires explicit recovery.",
            ExitCode.LOCKED,
            f"{inspection.state}_lock",
            details,
        )
    return RepoOSError(
        "Another active RepoOS operation owns this lock.",
        ExitCode.LOCKED,
        "lock_conflict",
        details,
    )


def require_lock_available(
    path: Path,
    *,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> None:
    inspection = inspect_lock_file(path, stale_after_seconds=stale_after_seconds)
    if not inspection.available:
        raise _lock_error(inspection)


@dataclass(slots=True)
class OperationLock:
    """An O_EXCL lock with owner-checked release and explicit stale recovery."""

    path: Path
    kind: str
    target: str
    transaction_id: str
    recover_stale: bool = False
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS
    _fd: int | None = None
    _owner_token: str | None = None

    def _payload(self) -> dict[str, object]:
        started = _now()
        seed = (
            f"{os.getpid()}:{socket.gethostname()}:{started.timestamp()}:{time.time_ns()}:"
            f"{self.target}:{self.transaction_id}:{self.kind}"
        )
        self._owner_token = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return {
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "start_time": _timestamp(started),
            "target": self.target,
            "transaction_id": self.transaction_id,
            "kind": self.kind,
            "owner_token": self._owner_token,
        }

    def _recover(self, inspection: LockInspection) -> None:
        if inspection.state not in {"stale", "malformed"}:
            raise _lock_error(inspection)
        recovered = self.path.with_name(
            f"{self.path.name}.recovered.{int(time.time())}.{os.getpid()}"
        )
        try:
            os.replace(self.path, recovered)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise RepoOSError(
                "RepoOS could not preserve the stale lock during explicit recovery.",
                ExitCode.LOCKED,
                "lock_recovery_failed",
                {"lock": str(self.path), "exception_type": type(exc).__name__},
            ) from exc

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(self._payload(), sort_keys=True) + "\n").encode("utf-8")
        for attempt in range(2):
            try:
                self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                inspection = inspect_lock_file(
                    self.path,
                    stale_after_seconds=self.stale_after_seconds,
                )
                if self.recover_stale and inspection.state in {"stale", "malformed"}:
                    self._recover(inspection)
                    if attempt == 0:
                        continue
                raise _lock_error(inspection) from exc
            try:
                os.write(self._fd, payload)
                os.fsync(self._fd)
            except BaseException:
                os.close(self._fd)
                self._fd = None
                self.path.unlink(missing_ok=True)
                raise
            return
        raise RepoOSError(
            "RepoOS lock acquisition lost a recovery race.",
            ExitCode.LOCKED,
            "lock_recovery_race",
            {"lock": str(self.path)},
        )

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self._owner_token is None:
            return
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
            return
        if isinstance(value, dict) and value.get("owner_token") == self._owner_token:
            self.path.unlink(missing_ok=True)
        self._owner_token = None

    def __enter__(self) -> OperationLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


class RepositoryLock(OperationLock):
    def __init__(
        self,
        state_directory: Path,
        identity: str,
        *,
        target: str | None = None,
        transaction_id: str = "unassigned",
        recover_stale: bool = False,
        stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
    ) -> None:
        super().__init__(
            path=repository_lock_path(state_directory, identity),
            kind="repository",
            target=target or identity,
            transaction_id=transaction_id,
            recover_stale=recover_stale,
            stale_after_seconds=stale_after_seconds,
        )


class GlobalLock(OperationLock):
    def __init__(
        self,
        state_directory: Path,
        *,
        transaction_id: str,
        recover_stale: bool = False,
        stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
    ) -> None:
        super().__init__(
            path=global_lock_path(state_directory),
            kind="global_metadata",
            target="repoos-state",
            transaction_id=transaction_id,
            recover_stale=recover_stale,
            stale_after_seconds=stale_after_seconds,
        )
