# Changelog

All notable RepoOS changes are recorded here. RepoOS follows Semantic Versioning.

## 0.3.0 — Unreleased

### Added

- A dedicated immutable manifest-bootstrap plan for creating exactly one absent
  `.repoos/project.yaml` in an explicitly authorized clean Git worktree.
- Expiring, local-only, one-transaction authorization receipts bound to the exact target,
  common Git directory, branch, HEAD, plan, manifest digest, destination, and local identity.
- Content-free sibling-worktree protection fingerprints that allow a dirty sibling while
  preserving its HEAD, status, index, lock state, and registration unchanged.
- Exclusive atomic manifest installation, absent-file backup records, automatic/manual
  rollback, authorization consumption, and stable bootstrap failure classifications.
- Outside-all-worktrees isolation for manifest, plan, state, and authorization artifacts plus
  durable device/inode creation evidence that prevents rollback from deleting a raced-in file.

### Compatibility and migration

- Fixture update-plan v2 and its existing apply/rollback behavior remain supported unchanged.
- Manifest bootstrap uses the separate `repoos.manifest-bootstrap-plan.v1` contract; it does not
  authorize ordinary real-repository updates, overlays, deletion, commit, push, or GitHub writes.
- Existing project manifests remain schema-valid. New manifest-bootstrap inputs must include an
  explicit sensitivity classification and the bounded first-adoption policy required by `0.3.0`.

## 0.2.0 — Unreleased

### Added

- Immutable fixture update plans with ownership, source/target, Git-state, manifest, and
  safety-limit preconditions.
- Persistent transaction lifecycle, per-common-Git locks, explicit stale-lock recovery,
  atomic approved-path backups, atomic file replacement, bounded validation, automatic
  rollback, and drift-aware manual rollback.
- Fixture-only managed-section updates with unique marker validation and byte-preserving
  repository-owned content outside the section.
- Transaction, backup-manifest, and public-safe transaction-observation schemas and CLI
  inspection commands.

### Compatibility and migration

- Update-plan schema v1 remains historical and is not executable; approved plans must be
  regenerated and reviewed under immutable update-plan schema v2.
- Exact RepoOS source-version compatibility is required while the executable engine remains
  pre-1.0 and fixture-only.
- Real repositories, deletion, force rollback, structured-file managed sections, commit, push,
  PR creation, and global installation remain unsupported.

## 0.1.0 — Unreleased

### Added

- Public-safe Phase 1 and portfolio evidence baseline.
- Validated Phase 2 architecture, migration, ownership, overlay, automation, backlog, and canary decisions.
- Installable Python package foundation and deterministic schemas.
- Public-safe project registry and RepoOS self-manifest.
- Read-only CLI, fixture-only planning, and dry-run apply revalidation.
- Current-format Codex agents, empty honest hook configuration, and command safety policy.
- Full-SHA-pinned hosted CI plus a scheduled read-only audit.
- Seventy-eight semantic unit, integration, schema, Codex, CLI, and security tests.

### Changed

- RepoOS is now defined as a deterministic control plane rather than a static copy template.

### Compatibility and migration

- This is the first control-plane version; no prior RepoOS release is compatible or automatically migrated.
- Existing copied template files remain repository-owned until explicitly adopted.
- No downstream repository or user-global configuration is changed by installing this version.
