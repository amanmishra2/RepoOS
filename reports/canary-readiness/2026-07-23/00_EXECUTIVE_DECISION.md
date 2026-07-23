# Executive decision

Date: 2026-07-23
Status: audit complete; adoption blocked

## Decision

P08's identity is deterministically confirmed by the ignored private overlay, local Git metadata,
and read-only GitHub evidence. Its exact name and mapping remain local-only. P08 is the stronger
provisional candidate, but it is currently `blocked`; no real canary is authorized.

P04-B is not preferable. It is `unsuitable_as_first_canary`.

## P08 blockers

1. The primary checkout is clean but its issue branch was merged, its remote branch was deleted,
   and its HEAD is 29 commits behind the authoritative default branch.
2. A second valid worktree contains 18 untracked implementation files for an open issue. It has no
   unique commits, remote branch, or pull request, but its untracked work is unique local state and
   must be preserved.
3. Development is active and high-churn. A canary would currently overlap active repository work.
4. Repository evidence supports a provisional `personal-data risk` classification, but the owner
   must approve the final risk and learning-evidence treatment.
5. Existing operating-layer files are repository-owned. The proposed adoption manifest is absent
   and its ownership has not been approved.
6. RepoOS `0.2.0` refuses unmarked real repositories and requires an existing apply-enabled
   manifest before planning. It therefore cannot execute the intended manifest-only bootstrap.

The prior finding that P08 had 16 worktree records, 15 prunable, is stale historical evidence.
Current authoritative Git metadata has two valid records and zero prunable records.

## P04-B blockers

- P04-B is 67 commits behind live `main` and seven behind its own remote branch.
- It shares P04-A's common Git directory. P04-A has three tracked changes and 54 untracked entries.
- The shared common Git directory has 64 worktree records, including 10 currently prunable.
- The branch's earlier operating-layer work was merged and is not the authoritative current base.
- Its validation and instruction surface has materially drifted.

## Required remediation

- Preserve and resolve the status of P08's active secondary worktree in a separately authorized
  repository-hygiene run.
- Use a fresh issue-linked branch/worktree from verified live `main`; do not reuse the superseded
  primary branch.
- Implement and test a bounded RepoOS real-canary manifest-bootstrap gate using only synthetic
  repositories.
- Approve P08's sensitivity, manifest ownership, and exact manifest-only scope.
- Refresh all local and GitHub evidence immediately before any downstream plan.

## Recommended next stage

Run the read-only-first hygiene prompt in
[13_NEXT_CANARY_ADOPTION_PROMPT.md](13_NEXT_CANARY_ADOPTION_PROMPT.md). It proposes disposition
choices but performs no cleanup or repair.

Real canary authorized: **no**.
