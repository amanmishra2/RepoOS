# Canary selection

Status: P08 remains the provisional canary; engine prerequisite complete in RepoOS `0.3.0`;
downstream execution not performed

## Evidence

The public-safe
[readiness packet](../../reports/canary-readiness/2026-07-23/README.md) and
[preservation packet](../../reports/canary-hygiene/2026-07-23/README.md) remain the evidence base.
Exact mappings remain outside committed artifacts.

| Alias | Confirmed positive evidence | Decision |
|---|---|---|
| P08 | Private active repository; live `main`; Python CLI/application; exact offline gates; two current worktrees; no prunable record; reviewed one-file ownership proposal | Provisional rank 1; later isolated canary only |
| P04-B | Identifiable clean worktree | Unsuitable: shared dirty/common-Git and stale/ambiguous registry boundary |
| P04-A | Active canonical common-Git owner | Blocked by current dirty state |
| Other historical candidates | Baseline evidence retained | Not refreshed; no eligibility |

## Authoritative P08-W2 decision

P08-W2 contains active or potentially active implementation work. Preserve it in place.

- Do not inspect its untracked file bodies.
- Do not archive, delete, clean, prune, move, reset, stash, repair, or modify it.
- Do not use it as the canary target.
- Exclude it from RepoOS writes.
- Exclude its untracked contents from reports and learning records.

P08-W1 is also not a canary target and remains unchanged. A dirty P08-W2 is not itself a target
cleanliness failure for a separate clean worktree; RepoOS `0.3.0` classifies it as a protected
sibling and requires its metadata/state summary to remain unchanged.

## Required future target

A later canary must revalidate current GitHub `main` and create a new isolated, issue-linked
worktree from that exact base. The canary must use only that clean worktree, while P08-W1 and
P08-W2 remain registered and unchanged. Locked, malformed, prunable, or drifting sibling metadata
blocks execution; RepoOS never cleans it automatically.

The first proposal remains exactly `.repoos/project.yaml`, with:

- project family `null`;
- no overlays, managed/generated/extension components, or local overrides;
- explicit personal-data sensitivity for review;
- repository-owned P08 validation commands;
- apply/commit/push/external permissions denied.

RepoOS `0.3.0` now provides the synthetic-verified planning, one-use authorization, locking,
atomic creation, validation, and rollback prerequisite. That implementation does not authorize a
P08 write. The later run must stop for explicit execute approval, demonstrate rollback, stop again
for reapplication approval, and create at most a local manifest-only commit. Push and pull request
remain separately prohibited without new authority.

## Stop decision for this run

Do not create the P08 canary worktree or inspect/modify either existing P08 worktree in this run.
Do not add a downstream manifest, execute RepoOS downstream, commit downstream, push, or open a
pull request. Use the date-stamped next-canary prompt only in a separate authorized run.
