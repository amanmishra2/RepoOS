# P08 identity and GitHub

Date: 2026-07-23
Publishability: `public_safe`

## Identity resolution

| Field | Confirmed evidence |
|---|---|
| RepoOS project ID | P08 |
| Local directory and absolute path | Resolved from the ignored private overlay; redacted here |
| Git repository root | Matches the mapped P08 root |
| Git common directory | The primary checkout's own `.git`; independent of other portfolio repositories |
| Current primary worktree | Resolved and readable; path redacted |
| Canonical GitHub identity and URL | Matches the ignored overlay and `origin`; redacted here |
| Owner/name agreement | Local remote, overlay, and GitHub canonical identity agree |
| Visibility | Private |
| Fork | No |
| Archived / disabled | No / no |
| Description / topics / release | No description, no topics, no release |
| Default branch | `main` |
| Default-branch HEAD | Live GitHub and the local remote-tracking ref agree; SHA redacted |
| Repository access | Read, push, maintain, and admin permissions observed |

The repository was created in July 2026 and had repository and workflow activity on the audit date.
There is no rename, transfer, stale remote URL, default-branch change, access loss, or malformed
remote configuration in the observed evidence.

## Meaning of “upstream is gone”

The GitHub repository still exists and is canonical. The primary local branch has a well-formed
configuration pointing to `origin`, but that specific remote branch no longer exists. Its pull
request was merged, the local commit is reachable from `main`, and the branch's remote ref was
deleted afterward. The primary checkout is 29 commits behind `main`.

This is a deleted branch upstream, not a deleted or inaccessible repository. It should not be
“repaired” by changing the old branch's upstream. A future canary requires a fresh branch from a
freshly verified `main`.

The secondary worktree's local branch also does not exist remotely and has no pull request. Its
issue remains open and its HEAD equals the observed default-branch HEAD; the worktree's change is
currently untracked local content rather than commits.

## Live GitHub state

| Signal | Result | Readiness effect |
|---|---|---|
| Open pull requests | One automation review changing four generated current-state documents | No file overlap with a future manifest, but confirms active automation |
| Recently merged pull requests | Ten recent merges observed over the prior eight days | High development velocity |
| Open issues | 48, excluding pull requests | Active roadmap |
| Workflows | Five active workflows | Product and operating-layer checks exist |
| Latest default-branch Product CI | Success | Positive validation evidence |
| Latest default-branch AgentOps | Success | Positive repository-contract evidence |
| Default branch protection flag | `false` | Checks are not shown as enforced |
| Legacy protection endpoint | Unavailable for this private-plan repository | No stronger protection evidence |
| Rulesets endpoint | Unavailable for this private-plan repository | Ruleset state cannot be independently enumerated |
| Releases | None | Pre-release development |

The open automation pull request's two pull-request workflows reported `action_required`, while its
scheduled source workflow succeeded. That is a workflow-policy signal, not evidence of a product
test failure.

## GitHub conclusion

GitHub identity and access are sufficient for a later reviewed pull request. The default branch is
authoritative. The repository is active, private, and unprotected by any visible required-check
rule. A future canary branch is technically reviewable, but it is not currently safe or authorized
because the local worktree and RepoOS product gates remain unresolved.
