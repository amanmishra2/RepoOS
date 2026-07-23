from __future__ import annotations

import pytest

from repoos.errors import RepoOSError
from repoos.ownership import (
    line_change_counts,
    locate_managed_section,
    render_managed_file,
    render_managed_section,
)
from repoos.paths import sha256_bytes

START = "# repoos:start fixture"
END = "# repoos:end fixture"


def _conflict_type(error: pytest.ExceptionInfo[RepoOSError]) -> str:
    return str(error.value.details["conflict_type"])


def test_managed_section_preserves_outside_bytes_and_crlf() -> None:
    before = (
        b"owner content\r\n"
        + START.encode()
        + b"\r\nold\r\n"
        + END.encode()
        + b"\r\nowner tail\r\n"
    )
    rendered, layout = render_managed_section(before, b"new\nvalue\n", START, END)
    assert rendered == (
        b"owner content\r\n"
        + START.encode()
        + b"\r\nnew\r\nvalue\r\n"
        + END.encode()
        + b"\r\nowner tail\r\n"
    )
    after_layout = locate_managed_section(rendered, START, END)
    assert after_layout.outside_sha256 == layout.outside_sha256
    assert after_layout.section_sha256 == sha256_bytes(b"new\r\nvalue\r\n")


def test_full_managed_file_preserves_existing_newline_convention() -> None:
    assert render_managed_file(b"one\ntwo\n", b"old\r\nvalue\r\n") == b"one\r\ntwo\r\n"


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"no markers\n", "managed_section_missing_start"),
        (START.encode() + b"\nbody\n", "managed_section_missing_end"),
        (
            START.encode() + b"\n" + START.encode() + b"\n" + END.encode() + b"\n",
            "managed_section_duplicate_start",
        ),
        (
            START.encode() + b"\n" + END.encode() + b"\n" + END.encode() + b"\n",
            "managed_section_duplicate_end",
        ),
        (
            END.encode() + b"\nbody\n" + START.encode() + b"\n",
            "managed_section_reversed_markers",
        ),
    ],
)
def test_managed_section_rejects_ambiguous_markers(content: bytes, expected: str) -> None:
    with pytest.raises(RepoOSError) as caught:
        locate_managed_section(content, START, END)
    assert _conflict_type(caught) == expected


def test_managed_section_rejects_nested_marker_in_source() -> None:
    before = START.encode() + b"\nold\n" + END.encode() + b"\n"
    with pytest.raises(RepoOSError) as caught:
        render_managed_section(before, START.encode() + b"\n", START, END)
    assert _conflict_type(caught) == "managed_section_nested_marker"


def test_managed_section_rejects_non_utf8_target() -> None:
    before = START.encode() + b"\n\xff\n" + END.encode() + b"\n"
    with pytest.raises(RepoOSError) as caught:
        locate_managed_section(before, START, END)
    assert _conflict_type(caught) == "managed_section_unsupported_encoding"


def test_line_change_counts_are_deterministic() -> None:
    assert line_change_counts(b"one\ntwo\n", b"one\nthree\nfour\n") == (2, 1)
