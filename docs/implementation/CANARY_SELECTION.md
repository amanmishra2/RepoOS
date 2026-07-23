# Canary selection

Status: provisional candidate selected; migration blocked

## Selection

P08 is the provisional canary candidate because it is a clean, independent, active Git repository and is more isolated than the other clean downstream working tree.

It is **not approved for writes**. The private alias mapping is intentionally not committed to public RepoOS. The implementation handoff may disclose the local name directly to the user.

## Candidate comparison

| Alias | Positive evidence | Blocking evidence | Decision |
|---|---|---|---|
| P04-B | Clean; existing RepoOS experiment | Shares P04-A’s dirty common Git directory; behind 7; instruction drift | Reject as isolated canary |
| P08 | Clean; independent repository; strong local safety/ownership guide | Upstream gone; 15 prunable worktree records; commands/family/sensitivity unconfirmed | Provisional candidate |
| P02 | Active and governed | Dirty, diverged, many prunable worktrees | Block |
| P01 | Active | Untracked user files and multiple present worktrees | Block |
| P04-A | Active | Dirty, 64 worktrees, inconsistent submodule metadata | Block |
| P07 | Active and governed | Dirty; no remote/default authority | Block |
| Non-Git roots | Some useful reference content | No PR/rollback boundary or confirmed lifecycle | Exclude |

## Required confirmation

Before touching P08, the user must confirm:

- project identity and active status;
- sensitivity/risk classification;
- authoritative build, test, lint, format, type, and security commands;
- intended default/base branch and replacement for the gone upstream;
- worktree-registration disposition;
- family/overlay classification;
- manifest ownership and exclusions;
- P08 as the exact canary.

## Proposed two-step migration

1. Manifest-only adoption on an isolated issue-linked branch/worktree, with no behavior change.
2. One bounded, low-risk component after the first diff is reviewed.

Both steps require plan artifacts, clean-state recheck, repository-owned validation, user diff review, and forward rollback proof. No commit, push, or PR occurs automatically.

## Stop decision

Stage 8 stops here. RepoOS foundation and neutral fixtures may continue; downstream mutation may not.
