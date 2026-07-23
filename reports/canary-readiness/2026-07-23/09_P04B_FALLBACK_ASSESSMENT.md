# P04-B fallback assessment

Date: 2026-07-23
Scope: bounded read-only comparison with P08

## Identity and relationship

P04-B's local path is resolved by the ignored private overlay. Its `origin` was independently
inspected rather than inferred: it points to the same canonical GitHub repository as P04-A.
P04-A and P04-B share one common Git directory. P04-B is a linked worktree, not an independent
repository or rollback boundary.

Exact paths, remote, repository name, branch names, and SHAs are redacted.

## Current evidence

| Property | P04-B result | Readiness effect |
|---|---|---|
| Target worktree | Clean | Positive only in isolation |
| Own remote branch | Exists; P04-B is seven commits behind it | Stale |
| Live default branch | Confirmed; P04-B is 67 commits behind | Not authoritative |
| Branch lifecycle | Its prior operating-layer pull request was merged | Superseded implementation base |
| Manifest | `.repoos/project.yaml` absent | Not adopted |
| Instruction drift | Material changes in scope, multi-writer policy, README, verification, Makefile, and packaging | Current branch cannot define present authority |
| Shared common Git worktrees | 64 records; 10 prunable; none locked | High ambiguity and coordination burden |
| P04-A status | Three tracked changes and 54 untracked entries | Shared state is not clean |
| GitHub lifecycle | Public, active, 18 open pull requests, 55 open issues, two workflows | High active-change interference |
| Branch protection / rulesets | Default branch unprotected; no rulesets observed | No enforced merge gate |
| Independent rollback | No | Common-Git and branch history are shared |

P04-B's own validation document lists `make agentops-pr`, hook and MCP smoke checks, and Pytest.
Those commands were not run: the branch is materially behind current authority, the shared
repository is dirty, and executing a stale validation surface would not prove current readiness.
The branch also documents environment-dependent future commands and an external runner assumption;
those claims require current default-branch reconciliation.

## Precise RepoOS block

RepoOS defines the canonical common Git directory as the lock and safety identity and states that
linked worktrees are not independent repositories. Real onboarding requires a clean common-Git
state and a trustworthy base. P04-B fails both:

1. P04-A shares its common Git directory and contains user changes.
2. The worktree registry contains prunable ambiguity.
3. P04-B's branch is stale relative to both its own remote and live `main`.

A transaction backup limited to P04-B files would not create an independent recovery boundary for
the shared branch/worktree ecosystem. Modifying P04-B could also conflict with P04-A's active
integration work and its many open branches.

## Decision

Classification: **`unsuitable_as_first_canary`**

P04-B is less safe than P08. Do not repair, update, validate by execution, prune, or adopt either
P04 worktree in this run.
