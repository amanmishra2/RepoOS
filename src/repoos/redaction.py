"""Conservative output redaction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

REDACTED = "<redacted>"

_SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)\b(password|passwd|token|api[_-]?key|client[_-]?secret)"
        r"(\s*[:=]\s*)([^\s,;]+)"
    ),
    re.compile(r"(?i)(https?://[^:/\s]+:)[^@\s]+@"),
)


def redact_text(value: str, *, redact_home: bool = True) -> str:
    """Redact common credential shapes and the current home prefix."""

    redacted = value
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 3:
            redacted = pattern.sub(
                lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}", redacted
            )
        elif pattern.groups >= 1:
            redacted = pattern.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
        else:
            redacted = pattern.sub(REDACTED, redacted)
    if redact_home:
        home = str(Path.home())
        redacted = redacted.replace(home, "~")
    return redacted


def contains_secret_like(value: str) -> bool:
    """Return true when a known secret pattern is present."""

    return any(pattern.search(value) is not None for pattern in _SECRET_PATTERNS)


def redact_data(value: Any) -> Any:
    """Recursively redact strings in JSON-compatible data."""

    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_data(item) for item in value]
    if isinstance(value, tuple):
        return [redact_data(item) for item in value]
    if isinstance(value, dict):
        return {str(key): redact_data(item) for key, item in value.items()}
    return value
