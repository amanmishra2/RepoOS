# Dirty and conditional repositories

Date: 2026-07-23

This public report uses aliases. Exact private paths and file names remain in local evidence outside the repository.

## Blocked by dirty state

| Alias | Confirmed state | Additional risk | Required disposition |
|---|---|---|---|
| P01 | 5 untracked entries | Multiple present worktrees | Preserve; no RepoOS writes |
| P02 | 4 tracked deletions | Ahead 18, behind 2; 26 prunable worktree records | Reconcile user changes and branch/worktree state |
| P04-A | 3 tracked and 54 untracked entries | 64 worktree records; inconsistent submodule metadata | Resolve user changes and repository structure |
| P07 | 15 tracked and 1 untracked entry | No remote or authoritative default branch | Preserve changes; decide version-control/remote policy |

## Clean but not currently eligible

| Alias | Confirmed state | Why not eligible |
|---|---|---|
| P04-B | Clean linked worktree, behind 7 | Shares P04-A’s dirty Git common directory and worktree registry |
| P08 | Clean working tree | Upstream is gone; 15 worktree records are prunable |

## Stop rule

RepoOS must refuse mutation when a target is dirty, shares a dirty common Git directory, has unresolved operation state, lacks a trustworthy base, or has ambiguous ownership. This inventory did not stash, reset, clean, prune, switch, or otherwise reconcile any target.
