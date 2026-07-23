"""Stable RepoOS errors and exit codes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class ExitCode(IntEnum):
    """Stable process exit codes."""

    OK = 0
    INVALID_INPUT = 2
    VALIDATION_FAILED = 3
    UNSAFE_STATE = 4
    CONFLICT = 5
    LOCKED = 6
    PAUSED = 7
    ENVIRONMENT = 8
    AUTHORIZATION_REQUIRED = 9
    INTERNAL_ERROR = 70


@dataclass(slots=True)
class RepoOSError(Exception):
    """An expected, machine-readable RepoOS failure."""

    message: str
    code: ExitCode
    error_type: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "type": self.error_type,
                "message": self.message,
                "exit_code": int(self.code),
                "details": self.details,
            },
        }


def invalid_input(message: str, **details: Any) -> RepoOSError:
    return RepoOSError(message, ExitCode.INVALID_INPUT, "invalid_input", details)


def validation_error(message: str, **details: Any) -> RepoOSError:
    return RepoOSError(message, ExitCode.VALIDATION_FAILED, "validation_failed", details)


def unsafe_state(message: str, **details: Any) -> RepoOSError:
    return RepoOSError(message, ExitCode.UNSAFE_STATE, "unsafe_state", details)


def environment_error(message: str, **details: Any) -> RepoOSError:
    return RepoOSError(message, ExitCode.ENVIRONMENT, "environment_error", details)


def authorization_required(message: str, **details: Any) -> RepoOSError:
    return RepoOSError(
        message,
        ExitCode.AUTHORIZATION_REQUIRED,
        "authorization_required",
        details,
    )
