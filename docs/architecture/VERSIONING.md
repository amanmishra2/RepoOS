# Versioning

RepoOS follows SemVer. The machine-readable current version is declared in:

- `VERSION`
- `pyproject.toml` → `project.version`
- `src/repoos/__init__.py` → `__version__`

Tests require all three to agree. Human-visible changes and compatibility notes live in `CHANGELOG.md`.

Version `0.2.0` introduces update-plan schema v2. A plan records the exact
`repoos_source_version`; while the executable engine is pre-1.0, apply requires an exact match and
never silently upgrades or regenerates an approved plan. Plan schema v1 is historical and
non-executable.

Transaction, backup-manifest, and transaction-observation records have their own schema versions.
They are local operation evidence, not release or adoption locks.

Downstream desired state declares `repoos_version` in `.repoos/project.yaml`. An immutable
artifact/adoption lock and long-term baseline retention remain deferred until release artifact
integrity, compatibility migration, and offline recovery are authorized and implemented.

Existing static-copy template files do not acquire a RepoOS version automatically.
