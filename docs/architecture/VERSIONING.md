# Versioning

RepoOS follows SemVer. The machine-readable current version is declared in:

- `VERSION`;
- `pyproject.toml` → `project.version`;
- `src/repoos/__init__.py` → `__version__`.

Tests require exact agreement. Human-visible changes and compatibility notes live in
`CHANGELOG.md`.

Version `0.3.0` is a backward-compatible material capability release. Fixture update-plan v2 and
its apply/rollback behavior remain executable without regeneration. The new
`repoos.manifest-bootstrap-plan.v1` and
`repoos.manifest-bootstrap-authorization.v1` contracts are separate so the narrower real-repository
exception does not weaken or reinterpret update-plan v2.

Both plan types record the exact `repoos_source_version`. While the transaction engine is pre-1.0,
apply requires an exact running version and never silently upgrades or regenerates an approved
plan. Update-plan v1 remains historical and non-executable. Bootstrap-plan/authorization v1 are
executable only for the fixed one-file operation.

Transaction, backup-manifest, and transaction-observation schema versions accept the compatible
fixture and bootstrap evidence shapes. They are local operation records, not release or adoption
locks.

A downstream `.repoos/project.yaml` declares `repoos_version`. Manifest bootstrap requires the
exact running `0.3.0`; a later release requires a new reviewed plan rather than implicit
migration. Artifact/adoption locks and long-term baseline retention remain deferred pending
separate release-integrity and offline-recovery work.

Existing static-copy template files do not acquire a RepoOS version automatically.
