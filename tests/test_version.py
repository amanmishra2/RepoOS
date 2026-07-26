from __future__ import annotations

import tomllib

from repoos import __version__
from repoos.validation import repo_root


def test_version_sources_agree() -> None:
    root = repo_root()
    version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert version_file == __version__ == pyproject["project"]["version"]
