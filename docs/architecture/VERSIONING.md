# Versioning

RepoOS follows SemVer. The machine-readable current version is declared in:

- `VERSION`
- `pyproject.toml` → `project.version`
- `src/repoos/__init__.py` → `__version__`

Tests require all three to agree. Human-visible changes and compatibility notes live in `CHANGELOG.md`.

Downstream desired state declares `repoos_version` in `.repoos/project.yaml`. A generated lock and immutable baseline retention are deferred until release artifact integrity and rollback recovery are implemented.

Existing static-copy template files do not acquire a RepoOS version automatically.
