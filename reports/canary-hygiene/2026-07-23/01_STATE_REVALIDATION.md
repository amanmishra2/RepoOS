# P08 state revalidation

Date: 2026-07-23
Comparison source:
[canary-readiness/2026-07-23](../../canary-readiness/2026-07-23/README.md)

## RepoOS and mapping gate

| Check | Result |
|---|---|
| Expected RepoOS checkout and branch | Matched |
| Expected readiness-audit commit at start | Matched |
| RepoOS version | `0.2.0` |
| RepoOS working tree at start | Clean |
| Private overlay schema | Valid |
| Private overlay ignored | Yes |
| Private overlay tracked | No |
| P08 local and GitHub identity | Agreed |

The overlay was validated using RepoOS's existing project-registry validation. No private mapping
was copied into this packet.

## Authoritative worktrees

The status fingerprint comparison used the readiness packet's exact method: Git porcelain v2,
NUL-delimited, with all untracked entries and no branch header.

| Check | P08-W1 | P08-W2 |
|---|---:|---:|
| Present and readable | Yes | Yes |
| HEAD matches preserved fingerprint | Yes | Yes |
| Status fingerprint matches | Yes | Yes |
| Tracked changes | 0 | 0 |
| Untracked entries | 0 | 18 |
| Conflicts | 0 | 0 |
| Unique local commits relative to observed `main` | 0 | 0 |
| Intentionally locked | No | No |
| Prunable record | No | No |

`git worktree prune --dry-run --verbose` reported no candidate. It was a dry run only.

P08-W1 remains 29 commits behind the observed `main`, and its HEAD remains an ancestor of that
base. P08-W2 remains at the observed `main`. No untracked file body was opened; only Git status and
filesystem metadata needed to resolve the fingerprint method were inspected.

## GitHub revalidation

| Check | Result |
|---|---|
| Repository identity, visibility, lifecycle flags, and default branch | Unchanged |
| Live `main` | Matches the preserved default and local remote-tracking state |
| P08-W1 pull request | Still merged |
| P08-W1 remote branch | Absent |
| P08-W2 owning issue | Open |
| P08-W2 remote branch | Absent |
| P08-W2 pull request | None |
| Open pull requests | One |
| Open pull-request files | Four documentation files: three Markdown and one JSON |
| Overlap with proposed manifest-only scope | None |
| Active workflows | Five |
| Product CI on the observed default branch | Success |
| AgentOps on the observed default branch | Success |
| Access for a later reviewed pull-request flow | Sufficient |

The GitHub connector was used first for repository, branch, issue, and pull-request evidence.
Read-only GitHub CLI metadata filled the exact issue, workflow, access, and overlap fields. No
GitHub mutation endpoint was called.

## Historical discrepancy

The older inventory's 16-record/15-prunable P08 snapshot remains stale historical evidence. The
current authoritative count remains two records and zero prune candidates. Git has no retained
audit trail capable of establishing how, when, or by whom the older records disappeared, so this
run does not speculate or attempt repair.

## Final downstream no-change check

| Alias | Final read-only result |
|---|---|
| P08 | Both HEADs and exact status fingerprints matched; two records, zero locked, zero prunable |
| P04-A | HEAD matched; three tracked changes, 54 untracked entries, and zero conflicts remained |
| P04-B | HEAD matched; clean with zero tracked changes, untracked entries, or conflicts |
| P04-A / P04-B common Git | Still shared; 64 records and 10 prunable records remained |

These values match the readiness packet. They are evidence of non-mutation, not approval to clean
or reconcile either project.

## Stop-condition result

No count, HEAD, exact status fingerprint, path-existence, lock, remote-branch, pull-request,
default-base, issue, workflow, overlap, or access delta was found. The preservation prompt's stop
condition did not fire.

## Evidence limits

- No P08-W2 untracked content was read.
- No secret-bearing or likely personal-data file was opened.
- Private paths, remotes, branches, issue details, and commit identifiers remain redacted.
- The prior full tracked-snapshot test evidence was not rerun because the observed default commit
  and workflow conclusions are unchanged; this was a hygiene audit, not product validation.
- No result is evidence that RepoOS can mutate a real repository safely.
