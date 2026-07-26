"""Global pause controls."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_FALSE_VALUES = {"", "0", "false", "no", "off"}


@dataclass(frozen=True, slots=True)
class PauseStatus:
    paused: bool
    source: str | None

    def as_dict(self) -> dict[str, str | bool | None]:
        return {"paused": self.paused, "source": self.source}


def get_pause_status(state_directory: Path) -> PauseStatus:
    env_value = os.environ.get("REPOOS_PAUSED", "")
    if env_value.strip().lower() not in _FALSE_VALUES:
        return PauseStatus(True, "environment:REPOOS_PAUSED")
    pause_file = state_directory / "PAUSED"
    if pause_file.is_file():
        return PauseStatus(True, "state_file")
    return PauseStatus(False, None)
