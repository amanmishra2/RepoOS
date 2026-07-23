# P08 preservation-first canary hygiene

Date: 2026-07-23
Mode: read-only downstream revalidation and RepoOS-local decision preparation
Decision: preserve both P08 worktrees unchanged and defer the canary

## Privacy boundary

This packet is `public_safe`. It uses only P08, P04-A, P04-B, P08-W1, and P08-W2.
Exact local paths, repository names, remotes, branch names, and private commit identifiers are
intentionally absent. The schema-valid mapping remains only in the ignored
`.repoos/local/projects.private.yaml` overlay.

## Outcome

Every stop-condition field matched the
[2026-07-23 readiness packet](../../canary-readiness/2026-07-23/README.md). P08 still has exactly
two present, readable, unlocked, non-prunable worktrees. P08-W1 remains clean, fully reachable from
live `main`, and superseded by merged work. P08-W2 still has no tracked or unique commits and
retains 18 untracked entries for an open issue.

No automatic cleanup is appropriate. P08 remains `blocked`, but it can become
`eligible_after_repository_hygiene` after the owner-directed gates in this packet are satisfied.
That prospective classification describes repository condition only. RepoOS is not engine-ready
for P08; the separate real-repository manifest-bootstrap issue remains required.

## Packet

| Document | Purpose |
|---|---|
| [00_PRESERVATION_DECISION.md](00_PRESERVATION_DECISION.md) | Current decision and eligibility boundary |
| [01_STATE_REVALIDATION.md](01_STATE_REVALIDATION.md) | Aliased local and GitHub evidence |
| [02_ALTERNATIVES_AND_APPROVALS.md](02_ALTERNATIVES_AND_APPROVALS.md) | Preservation choices and exact authority gates |
| [p08-hygiene.json](p08-hygiene.json) | Deterministic public-safe summary |

## Safety result

No downstream file, worktree, branch, upstream, remote, GitHub resource, P04-A state, P04-B state,
or user-global file was changed. No untracked P08-W2 file body was opened. No worktree metadata was
pruned, no branch was repaired, and no push or pull request was performed.
