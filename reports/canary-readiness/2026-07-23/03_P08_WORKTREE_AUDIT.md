# P08 worktree audit

Date: 2026-07-23
Authority: current `git worktree list --porcelain` plus read-only Git/GitHub evidence

## Every current record

| ID | Registered path | Exists / readable | Main | HEAD and branch | Detached | Locked / reason | Prunable / reason | Reachability and remote evidence | Worktree status | Classification | Cleanup decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P08-W1 | `<private:P08-primary-worktree>` | Yes / yes | Yes | Local branch exists; SHA redacted | No | No / none | No / none | Commit is reachable from `main`; branch pull request merged; remote branch deleted; 29 commits behind `main` | Clean | Superseded by merged work | Not prunable. Branch/checkout disposition requires explicit manual approval. |
| P08-W2 | `<private:P08-secondary-worktree>` | Yes / yes | No | Local branch exists at observed `main`; SHA redacted | No | No / none | No / none | No unique commit; no remote branch or pull request; owning issue remains open | 18 untracked entries; no tracked changes | Active and valid | Unsafe to remove, reset, prune, or reuse. Preserve the untracked work. |

P08-W1's last commit was on 2026-07-14. P08-W2's HEAD commit was on 2026-07-21, and its current
worktree metadata was created on 2026-07-23. Commit subjects are omitted as private project
content.

## Counts

| Measure | Current result |
|---|---:|
| Total registered records | 2 |
| Present and readable | 2 |
| Active implementation records | 1 |
| Present but superseded records | 1 |
| Locked | 0 |
| Prunable | 0 |
| Ambiguous | 0 |
| Unique-commit risk | 0 |
| Unique untracked-work risk | 1 |
| Clearly safe to prune now | 0 |

## Historical discrepancy

The older portfolio inventory recorded 16 P08 worktree records, 15 of them prunable. That snapshot
is retained as stale historical evidence; it is not the current state.

Current Git reports two valid records, and `git worktree prune --dry-run --verbose` reports nothing.
At least 14 records disappeared on a net basis between the historical snapshot and this audit.
The earlier packet did not retain the private per-record list or a precise capture timestamp, and
Git does not journal worktree-prune actions. Read-only evidence therefore cannot establish whether
the old records were pruned, manually removed, replaced, or when and by whom the change occurred.

No current P08 worktree record is stale or prunable. The cleanup question has changed from
“remove 15 stale records” to “preserve one active worktree and decide separately how to retire or
realign one superseded checkout.” Neither action is authorized here.
