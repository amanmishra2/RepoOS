"""Ownership rules and byte-preserving managed-section rendering."""

from __future__ import annotations

import difflib
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from repoos.errors import conflict
from repoos.paths import sha256_bytes


class OwnershipMode(StrEnum):
    ADOPTION_MANIFEST = "adoption_manifest"
    MANAGED_FILE = "managed_file"
    MANAGED_SECTION = "managed_section"
    GENERATED_FILE = "generated_file"
    REPOSITORY_OWNED = "repository_owned"
    REPOSITORY_EXTENSION = "repository_extension"
    LOCAL_OVERRIDE = "local_override"
    EXCLUDED = "excluded"


WRITABLE_OWNERSHIP = {
    OwnershipMode.ADOPTION_MANIFEST,
    OwnershipMode.MANAGED_FILE,
    OwnershipMode.MANAGED_SECTION,
    OwnershipMode.GENERATED_FILE,
}

PRESERVED_OWNERSHIP = {
    OwnershipMode.REPOSITORY_OWNED,
    OwnershipMode.REPOSITORY_EXTENSION,
    OwnershipMode.LOCAL_OVERRIDE,
    OwnershipMode.EXCLUDED,
}


@dataclass(frozen=True, slots=True)
class SectionLayout:
    """Offsets and hashes for one unique, nonnested managed section."""

    body_start: int
    body_end: int
    section_sha256: str
    outside_sha256: str
    newline: bytes


def _without_line_ending(line: bytes) -> bytes:
    if line.endswith(b"\r\n"):
        return line[:-2]
    if line.endswith((b"\n", b"\r")):
        return line[:-1]
    return line


def _marker_offsets(content: bytes, marker: bytes) -> list[tuple[int, int]]:
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for line in content.splitlines(keepends=True):
        next_cursor = cursor + len(line)
        if _without_line_ending(line) == marker:
            offsets.append((cursor, next_cursor))
        cursor = next_cursor
    if not content:
        return offsets
    if cursor < len(content):  # defensive: splitlines(keepends=True) normally consumes all bytes
        tail = content[cursor:]
        if _without_line_ending(tail) == marker:
            offsets.append((cursor, len(content)))
    return offsets


def _validate_marker(marker: str, *, field: str) -> bytes:
    if not marker or "\n" in marker or "\r" in marker:
        raise conflict(
            "Managed-section markers must be non-empty single lines.",
            conflict_type="invalid_managed_section_marker",
            field=field,
        )
    try:
        return marker.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise conflict(
            "Managed-section marker is not valid UTF-8.",
            conflict_type="invalid_managed_section_marker",
            field=field,
        ) from exc


def locate_managed_section(content: bytes, start_marker: str, end_marker: str) -> SectionLayout:
    """Locate one section and classify every ambiguous marker shape."""

    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise conflict(
            "Managed sections require UTF-8 text.",
            conflict_type="managed_section_unsupported_encoding",
        ) from exc

    start = _validate_marker(start_marker, field="start_marker")
    end = _validate_marker(end_marker, field="end_marker")
    if start == end:
        raise conflict(
            "Managed-section start and end markers must differ.",
            conflict_type="managed_section_identical_markers",
        )

    starts = _marker_offsets(content, start)
    ends = _marker_offsets(content, end)
    if not starts:
        raise conflict(
            "Managed-section start marker is missing.",
            conflict_type="managed_section_missing_start",
        )
    if not ends:
        raise conflict(
            "Managed-section end marker is missing.",
            conflict_type="managed_section_missing_end",
        )
    if len(starts) > 1:
        raise conflict(
            "Managed-section start marker is duplicated or nested.",
            conflict_type="managed_section_duplicate_start",
            count=len(starts),
        )
    if len(ends) > 1:
        raise conflict(
            "Managed-section end marker is duplicated or overlapping.",
            conflict_type="managed_section_duplicate_end",
            count=len(ends),
        )

    start_offset, body_start = starts[0]
    body_end, _end_after = ends[0]
    if start_offset >= body_end:
        raise conflict(
            "Managed-section markers are reversed.",
            conflict_type="managed_section_reversed_markers",
        )

    start_line = content[start_offset:body_start]
    newline = b"\r\n" if start_line.endswith(b"\r\n") else b"\n"
    section = content[body_start:body_end]
    outside = content[:body_start] + content[body_end:]
    return SectionLayout(
        body_start=body_start,
        body_end=body_end,
        section_sha256=sha256_bytes(section),
        outside_sha256=sha256_bytes(outside),
        newline=newline,
    )


def _normalized_text_bytes(value: bytes, newline: bytes, *, ensure_final_newline: bool) -> bytes:
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise conflict(
            "Rendered managed text must be UTF-8.",
            conflict_type="managed_text_unsupported_encoding",
        ) from exc
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if ensure_final_newline and normalized and not normalized.endswith("\n"):
        normalized += "\n"
    return normalized.replace("\n", newline.decode("ascii")).encode("utf-8")


def render_managed_section(
    target_content: bytes,
    source_body: bytes,
    start_marker: str,
    end_marker: str,
) -> tuple[bytes, SectionLayout]:
    """Replace only section bytes while preserving both markers and all outside bytes."""

    layout = locate_managed_section(target_content, start_marker, end_marker)
    start = _validate_marker(start_marker, field="start_marker")
    end = _validate_marker(end_marker, field="end_marker")
    for line in source_body.splitlines():
        if line in {start, end}:
            raise conflict(
                "Managed-section source contains a nested boundary marker.",
                conflict_type="managed_section_nested_marker",
            )
    normalized = _normalized_text_bytes(
        source_body,
        layout.newline,
        ensure_final_newline=True,
    )
    rendered = target_content[: layout.body_start] + normalized + target_content[layout.body_end :]
    return rendered, layout


def render_managed_file(source_content: bytes, target_content: bytes | None) -> bytes:
    """Use source bytes, preserving a consistent existing LF/CRLF convention when textual."""

    if target_content is None:
        return source_content
    without_crlf = target_content.replace(b"\r\n", b"")
    if b"\r\n" in target_content and b"\n" not in without_crlf:
        return _normalized_text_bytes(source_content, b"\r\n", ensure_final_newline=False)
    if b"\n" in target_content:
        return _normalized_text_bytes(source_content, b"\n", ensure_final_newline=False)
    return source_content


def line_change_counts(before: bytes, after: bytes) -> tuple[int, int]:
    """Return deterministic added/removed line counts for safety accounting."""

    before_lines = before.decode("utf-8", errors="replace").splitlines()
    after_lines = after.decode("utf-8", errors="replace").splitlines()
    matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines, autojunk=False)
    added = 0
    removed = 0
    for tag, first_start, first_end, second_start, second_end in matcher.get_opcodes():
        if tag in {"replace", "delete"}:
            removed += first_end - first_start
        if tag in {"replace", "insert"}:
            added += second_end - second_start
    return added, removed


def file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
