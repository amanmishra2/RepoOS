"""Deterministic human and JSON output."""

from __future__ import annotations

import json
from typing import Any

from repoos.redaction import redact_data


def json_text(value: Any) -> str:
    return json.dumps(redact_data(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def human_text(value: Any) -> str:
    """Render compact deterministic human-readable output."""

    safe = redact_data(value)
    if isinstance(safe, dict):
        lines: list[str] = []
        for key in sorted(safe):
            item = safe[key]
            if isinstance(item, (dict, list)):
                lines.append(f"{key}:")
                rendered = json.dumps(item, indent=2, sort_keys=True, ensure_ascii=False)
                lines.extend(f"  {line}" for line in rendered.splitlines())
            else:
                lines.append(f"{key}: {item}")
        return "\n".join(lines) + "\n"
    return f"{safe}\n"


def render(value: Any, output_format: str) -> str:
    return json_text(value) if output_format == "json" else human_text(value)
