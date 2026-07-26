# P08 Git state

Date: 2026-07-23

## Current state

| Property | Evidence | Decision |
|---|---|---|
| Primary working tree | Clean | Necessary but not sufficient |
| Primary current branch | Local issue branch whose pull request is merged | Superseded base |
| Primary HEAD | Reachable from `main`; 29 commits behind | Do not use for a canary |
| Current upstream | Configured remote branch is absent | Expected after merged-branch deletion |
| Default branch | `origin/main` locally and `main` on GitHub | Authoritative base confirmed |
| Common Git directory | Primary `.git` | Lock/safety identity for both P08 worktrees |
| Registered worktrees | Two | Current authoritative count |
| Prunable records | Zero | No P08 metadata cleanup is currently indicated |
| Secondary status | No tracked change; 18 untracked entries | Active user work; blocking |
| Unique commits | None in either worktree relative to observed `main` | No unique-commit loss risk |
| Unique untracked data | Present in the secondary worktree | Unsafe to remove or reset |

Private paths, branch names, remotes, and SHAs are redacted from this public-safe record.

## Repository shape

- Full, non-bare, non-shallow repository.
- No sparse checkout or partial-clone configuration.
- File-mode tracking is enabled.
- No configured hooks path or filesystem monitor.
- No registered submodule or tracked symlink at the observed default-branch commit.
- No lock file or intentionally locked worktree was observed.
- Remote fetch configuration is conventional and covers all branches.
- The default branch has 427 tracked files.

## RepoOS adoption state

- `.repoos/project.yaml` is absent.
- `.repoos-fixture` is absent and must not be added to make a real repository look eligible.
- No RepoOS managed-section markers were found.
- No current file has an explicit RepoOS ownership transfer.
- Unknown and unadopted paths therefore remain repository-owned.

## Base selection

The primary checkout is not a trustworthy canary base even though it is clean. Its merged branch is
superseded and materially behind the default branch. The secondary checkout is based on the
default branch but contains active untracked work. A future canary requires a newly verified,
issue-linked checkout from live `main` after the active-work disposition and explicit
authorization are resolved.

No branch, upstream, ref, remote, index, or worktree metadata was changed during this audit.
