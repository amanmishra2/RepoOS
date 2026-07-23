# Validated migration plan

Status: active
Validated: 2026-07-23

## Preconditions

- Preserve all dirty or ambiguous repositories.
- Work only in the clean RepoOS branch until fixture safety is proven.
- Keep private project mappings out of the public repository.
- Do not execute bundled ZIP content.
- Do not change GitHub settings, runners, user-global Codex files, or downstream repositories.

## Dependency-ordered waves

### Wave 0 — Evidence and truthfulness

1. Complete the 152-row Phase 1 requirements ledger.
2. Audit the ZIP safely with existing tools; do not depend on the future CLI.
3. Inventory every first-level portfolio directory read-only.
4. Deep-audit RepoOS and record preserve/fix/replace/move/generate/remove dispositions.
5. Publish only redacted, public-safe baseline reports.

Exit gate: all required Stage 1 outputs exist and RepoOS is still the only approved write target.

### Wave 1 — Minimal foundation

1. Add version/package metadata and deterministic schemas.
2. Add a public-safe registry with RepoOS as the only unredacted project.
3. Implement containment, redaction, Git safety, pause, locking, structured errors, and report primitives.
4. Implement read-only CLI commands and strict validation.

Exit gate: clean build, schema valid/invalid fixtures, deterministic JSON, no-write snapshots, and stable exit codes.

### Wave 2 — Controlled update fixtures

1. Define exact ownership and plan formats.
2. Generate plans only for explicit fixture repositories.
3. Implement dry-run-first apply, backup, operation journal, atomic replacement, and rollback against disposable fixtures.
4. Inject failures after each write boundary and prove restoration.

Exit gate: dirty/stale/conflict/lock/path-escape refusals pass; repeat execution is idempotent; no real project changed.

### Wave 3 — RepoOS active-surface repair

1. Replace unsupported Codex config.
2. Replace obsolete agents with a minimal TOML set.
3. Replace or remove false hook/rule enforcement and add fixtures.
4. Replace the self-hosted workflow with pinned GitHub-hosted read-only CI.
5. Update README, memory, maps, runner, hook, and verification claims to shipped behavior.

Exit gate: Codex/workflow validators and negative fixtures pass; docs match behavior.

### Wave 4 — Canary proposal

1. Refresh candidate Git and GitHub state read-only.
2. Obtain explicit human confirmation of identity, lifecycle, sensitivity, commands, ownership, family, and P08 as canary.
3. Create an isolated issue-linked branch/worktree only in the selected repository.
4. First PR: manifest/lock adoption with no behavior change.
5. Second PR: one bounded component only after the first is reviewed.
6. Demonstrate forward rollback.

Exit gate: user reviews the diff; repository CI-equivalent checks pass; post-merge plan is a no-op.

### Wave 5 — Learning and broader rollout

Learning records may begin from redacted evidence, but scheduled/AI review is not a prerequisite for safe synchronization. Broad rollout remains one explicit proposal per repository after the canary proves update and rollback.

## Stop conditions

Stop before writes on dirty/conflicted state, operation in progress, stale base, unknown baseline, path escape, symlink escape, ownership ambiguity, missing commands, sensitivity ambiguity, secret-like output, missing rollback, lock contention, pause activation, excessive change count/bytes, or any request for new authority.

Stop portfolio rollout on shared regression, repeated conflict, permission expansion, review overload, or an exception rate that makes centralization uneconomic.

## Rollback

- Uncommitted fixture apply: restore from the operation journal and backups.
- Merged repository update: generate a new forward proposal targeting the previous immutable version; never rewrite history.
- GitHub setting: out of scope; record the exact manual rollback separately before any approved mutation.
- User-global install: out of scope until backup, checksum, adoption, and restore contracts exist.

## Migration notes

Static ZIP/rsync update lineage is not imported. Existing files remain repository-owned until explicit adoption. No file becomes managed based on similarity alone.
