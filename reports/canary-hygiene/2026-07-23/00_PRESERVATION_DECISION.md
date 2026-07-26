# P08 preservation decision

Date: 2026-07-23

## Decision

Leave P08-W1 and P08-W2 untouched and defer the canary.

This is the only preservation-first outcome that requires no downstream mutation and cannot
overwrite or strand P08-W2's untracked work. There is no current prune candidate, no broken
worktree record to repair, and no unique commit to recover. P08-W1 is not an acceptable canary
base even though it is clean because its merged work is 29 commits behind live `main`.

No branch, upstream, worktree, or remote repair is recommended.

## Classification

| Dimension | Current result | Conditional future result |
|---|---|---|
| Repository hygiene | `blocked` | `eligible_after_repository_hygiene` |
| Canary authorization | Not authorized | Requires a new readiness decision and explicit authority |
| RepoOS engine | Not engine-ready for P08 | Requires the separate real-repository manifest-bootstrap issue |
| Automatic cleanup | Refused | Remains refused |

P08 can become `eligible_after_repository_hygiene` only when all of these facts are established:

1. The owner of P08-W2 chooses and completes a preservation or completion path without loss.
2. P08-W2 is either complete and clean or explicitly isolated as non-conflicting active work.
3. P08-W1 remains excluded as the canary base; any checkout realignment is separately approved.
4. A fresh issue-linked candidate can be created from then-live `main` without touching either
   preserved worktree.
5. The common Git directory, every registered worktree, open pull-request overlap, validation
   conclusions, and access are rechecked immediately before planning.

Meeting these repository-hygiene conditions would not authorize a manifest, RepoOS execution,
commit, push, or pull request. It would not prove the engine prerequisite.

## Independent engine gate

RepoOS `0.2.0` remains fixture-only. The first proposed P08 change is a repository-owned adoption
manifest that does not yet exist, and the current engine cannot bootstrap that file in a real
repository. The bounded manifest-bootstrap enhancement must be implemented and proved against
synthetic repositories before another P08 readiness decision.

## Current authority

The user authorized this read-only hygiene packet and one RepoOS-local documentation commit.
No downstream or GitHub mutation authority was granted.
