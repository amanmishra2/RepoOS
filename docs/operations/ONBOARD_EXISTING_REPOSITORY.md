# Onboard an existing repository

RepoOS `0.3.0` enables one real-repository operation: creation of an absent
`.repoos/project.yaml` through `manifest_bootstrap`. It does not enable ordinary updates in real
repositories. The rules in this document are the normative bootstrap contract.

## Eligibility

The explicit target must be the root of a clean, non-bare, non-detached Git worktree with a
committed HEAD and branch. It must not be a submodule. The manifest and plan inputs, RepoOS state,
and authorization receipt must remain outside every target worktree and its common Git directory.

The destination must be exactly `.repoos/project.yaml` and must be absent, unignored, and reached
without symlinks or traversal. An existing `.repoos` directory is permitted when it is a real
directory; its unrelated entries are preserved. An existing manifest is never replaced.

RepoOS refuses locked, prunable, malformed, duplicate, or otherwise ambiguous worktree
registrations. A dirty sibling does not make the clean target dirty. It is instead classified as
protected, summarized by hashes/counts without opening file bodies, and required to remain
unchanged.

## Materialize and review the manifest

The proposed manifest must be a complete UTF-8 YAML file no larger than 64 KiB. It must pass the
current project-manifest schema and bootstrap semantic policy before planning and again before
apply. Bootstrap requires:

- manifest schema version `1` and the exact running RepoOS version;
- a valid project identifier and explicit sensitivity classification;
- `experimental` or `canary` adoption;
- no overlays, local overrides, managed files, generated files, or extensions;
- bounded repository-owned and excluded component identifiers;
- one or more bounded, no-shell repository verification commands;
- `read_only` and `plan` enabled, with `apply`, `commit`, `push`, and `external_settings` denied.

Unknown fields, YAML aliases/tags, credential-like values, unsafe commands or paths, unsupported
schema versions, and broad ownership claims are rejected. Execute never infers missing governance
fields.

## Plan and dry run

```bash
repoos --format json plan-manifest-bootstrap \
  --repo /path/to/clean-canary-worktree \
  --manifest-input /path/outside/worktrees/project.yaml \
  --output /path/outside/worktrees/bootstrap-plan.json

repoos --format json --state-dir /path/to/local/repoos-state \
  apply --plan /path/outside/worktrees/bootstrap-plan.json --dry-run
```

The separate `repoos.manifest-bootstrap-plan.v1` contract preserves fixture update-plan v2
compatibility. It binds the operation, canonical target and common Git paths, target worktree,
branch, HEAD, clean-status fingerprint, sibling summaries, common-Git metadata, exact manifest
bytes, parent state, destination absence, RepoOS/manifest versions, fixed limits, validation
requirements, and authorization fields. Its canonical plan ID and explicit digest cover the full
plan.

Dry run revalidates the plan and reports whether it is ready for authorization. It creates no
target, transaction, lock, backup, or authorization state. Missing approval is reported as an
authorization requirement, not generated automatically.

## Authorize and execute

Only after reviewing the manifest, plan, dry-run output, target identity, and protected-sibling
summary:

```bash
repoos --format json --state-dir /path/to/local/repoos-state \
  authorize-manifest-bootstrap \
  --plan /path/outside/worktrees/bootstrap-plan.json \
  --expires-in 1800 \
  --approve

repoos --format json --state-dir /path/to/local/repoos-state \
  apply \
  --plan /path/outside/worktrees/bootstrap-plan.json \
  --authorization /path/from-authorization-output.json \
  --execute
```

The authorization receipt is a mode-`0600`, local-only state artifact containing no credentials.
It binds the exact operation, target repository and worktree, common Git directory, branch, HEAD,
plan ID/digest, manifest digest, destination, creation/expiration times, and a hashed local identity.
It is reserved by one transaction and consumed after any authorized attempt that reaches
reservation, including a rolled-back attempt. It cannot authorize another worktree, changed HEAD,
changed plan, changed manifest, overlay, later update, or second transaction.

Execute revalidates approval, acquires the existing lock keyed by the common Git directory, repeats
all target/sibling/common-Git checks, records an absence-aware backup, renders outside the
destination, validates bytes, and installs the one file without overwrite. It then validates the
installed manifest, runs the bounded repository commands, and proves target, sibling, registration,
ref, index, config, and lock-state preservation before completion.

The transaction durably records parent creation and the installed file's device/inode before
validation. Rollback therefore cannot infer deletion authority merely from plan-time absence.

## Fixed mutation boundary

Manifest bootstrap creates one file, edits zero files, and deletes zero files. The only optional
directory creation is `.repoos`. There is no force or safety-limit override. RepoOS performs no Git
write command and does not change refs, branches, indexes, configuration, remotes, worktree
registrations, commits, GitHub resources, user-global files, or sibling paths.

General real-repository update remains refused:

```text
real repository
AND operation is manifest_bootstrap
AND exact authorization is valid
AND every bootstrap precondition passes
→ execute may proceed

any other real-repository operation
→ refuse
```

Rollback is defined in [Transaction rollback](ROLLBACK.md). Fixture updates retain their existing
contract in [Update a fixture repository](UPDATE_REPOSITORY.md).
