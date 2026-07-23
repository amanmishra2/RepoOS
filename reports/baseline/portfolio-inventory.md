# Portfolio baseline

Date: 2026-07-23
Mode: read-only
Scope: every first-level directory under the configured `~/Coding` root

## Outcome

Fourteen first-level directories were found: seven Git working trees backed by six independent Git common directories, plus seven non-Git directories. P06 (RepoOS) is the only clean, low-ambiguity implementation target. There is no approved downstream canary.

| State | Count | Decision |
|---|---:|---|
| Clean implementation candidate | 1 | P06 only |
| Dirty Git working tree | 4 | No writes |
| Clean but conditional Git working tree | 2 | Reconcile Git state and obtain confirmation |
| Non-Git directory | 7 | Exclude, classify, or version before adoption |

The machine-readable [portfolio inventory](portfolio-inventory.json) records Git state using public-safe aliases. Exact private mappings and porcelain evidence were intentionally retained outside this public repository.

## Evidence labels

- **Confirmed local fact:** directly observed through read-only filesystem or Git metadata.
- **Inference:** a lifecycle, role, or risk conclusion derived from local evidence.
- **Unresolved ambiguity:** a fact that cannot be established safely from the available evidence.
- **Repository-specific decision:** behavior that must remain under the target repository’s authority.
- **Reusable candidate:** a pattern worth validating across more than one repository.
- **Obsolete implementation:** an existing mechanism that cannot satisfy the selected safety contract.

## Safety findings

- P01, P02, P04-A, and P07 are dirty. They are excluded from mutation.
- P04-B is a clean linked worktree, but it shares P04-A’s dirty common Git directory and is seven commits behind.
- P08 is clean, but its upstream is gone and 15 worktree registrations are prunable.
- P04-A reports inconsistent gitlink/`.gitmodules` metadata.
- P03 is a non-Git template asset containing the supplied ZIP, not an extracted project.
- P05 is an archive; P12 is shared tooling that belongs behind a separate user-global authorization boundary.
- RepoOS was clean on `main` at `bb9d54425001afad655680235acb0326c1aab401` when the implementation branch was created.

## Controls used

- Read-only Git commands with optional locks disabled.
- Repository hooks and filesystem monitors disabled for inventory commands.
- No fetch, pull, checkout, stash, reset, clean, build, test, hook, workflow, or project script execution.
- No secret-bearing, database, log, or generated-data files opened.
- No downstream file was modified.

## Human confirmation still required

Before any downstream plan or canary write, confirm project identity, lifecycle, sensitivity, family, authoritative commands, ownership, and the exact canary. Remote and divergence state must be refreshed immediately before a PR-based rollout.
