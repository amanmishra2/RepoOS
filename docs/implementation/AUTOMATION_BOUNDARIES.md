# Automation boundaries

Status: authoritative for RepoOS `0.3.0`

## Deterministic local automation

Allowed without new external authority:

- read-only discovery, metadata inventory, validation, status, doctor, diff, audit, update check,
  and public-safe reporting;
- deterministic fixture and manifest-bootstrap plan generation;
- no-write dry runs;
- synthetic temporary-repository fixture update and manifest-bootstrap tests;
- local transaction/backup/rollback inspection.

Real-repository target mutation is allowed only when all of these are true:

```text
operation_kind == manifest_bootstrap
destination == .repoos/project.yaml
destination is absent
target worktree is clean and exact
common-Git/sibling state is unambiguous and preserved
plan and manifest are exact and current
one-use local authorization is valid
common-Git lock is held
fixed non-overridable limits pass
repository-owned validation passes
```

Any other real-repository operation is refused. The target write is exactly one file creation.

## Approval boundaries

A plan is not authorization. Bootstrap dry run does not create approval. Authorization creation
requires `--approve`, binds one exact worktree/HEAD/branch/plan/manifest/destination, expires, and is
consumed by one reserved attempt. Execute, post-rollback reapplication, local commit, push, and pull
request are distinct decisions.

## External actions

RepoOS never implicitly commits, pushes, opens PRs, merges, changes refs or worktree registrations,
changes rulesets, registers runners, edits secrets/variables, installs a GitHub App, changes
organization settings, or writes user-global Codex configuration. Each requires a separately
implemented and approved action with its own preview and recovery plan.

## Protected sibling worktrees

Target cleanliness and sibling preservation are separate controls. A dirty sibling may coexist
with a clean bootstrap target and is classified `protected_dirty`; its bodies are not opened and
its names are not persisted. Locked, malformed, prunable, duplicate, or drifting sibling state
fails closed. RepoOS never cleans, prunes, repairs, checks out, resets, stashes, or writes a sibling.

## AI boundary

AI may summarize redacted evidence, cluster observations, or draft candidate records. It may not:

- set approval fields or synthesize authorization;
- change eligibility or ownership;
- widen a transaction;
- weaken a stop condition;
- promote a component/channel;
- operate on secrets or unapproved private content.

The system remains useful with AI disabled.

## Pause and locking

Pause precedence is environment, local state-root pause file, then target-specific safety block.
Pause is checked before planning and at mutation boundaries.

Repository transactions lock the canonical common Git directory, so sibling worktrees share a
serialization boundary. Different common Git directories may proceed concurrently. Stale or
malformed lock recovery requires an explicit flag and preserves the prior record; a live owner is
never overridden.

## GitHub Actions and recurring work

CI uses GitHub-hosted ephemeral runners, read-only permissions, immutable action pins, concurrency
cancellation, timeouts, deterministic commands, and no repository secrets. Scheduled jobs remain
read-only. No long-running daemon is justified.

| Cadence | Initial home | Mutation |
|---|---|---|
| On demand/daily health | Manual CLI or read-only CI | None |
| Weekly cross-project review | Manual/Codex task using redacted reports | None |
| Biweekly update proposal | Manual CLI | Plan only |
| Monthly architecture audit | Manual or read-only CI | None |

Portfolio-wide write flags and generic force options do not exist.
