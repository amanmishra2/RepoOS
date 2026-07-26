# Authorization-required work

Status: no downstream or external action is authorized by RepoOS `0.3.0`

| Action | Required evidence and explicit authority | Recovery boundary |
|---|---|---|
| Create a fresh P08 canary worktree | Revalidate live `main`, exact issue/base/branch, current two protected worktrees, and creation-only scope | Remove only the new worktree/branch after separate approval |
| Execute P08 manifest bootstrap | Review exact manifest, immutable plan/digest, no-write dry run, target/sibling summaries, local backup/state path, and one-use approval | Automatic/manual one-file rollback |
| Reapply after rollback | Fresh plan and authorization after proof review | Same one-file rollback |
| Create a local P08 commit | Successful reapplication, exact manifest-only diff, full P08 validation | Local forward/revert decision |
| Inspect or change P08-W2 | Current owner decision prohibits body inspection and all mutation; no present approval path is inferred | Preserve original bytes/metadata; no Git cleanup |
| Change P08-W1 | Not part of the canary; exact separate branch/worktree decision required | Action-specific branch/ref recovery |
| Modify any other downstream repository | Clean-state proof, identity, commands, ownership, explicit target and operation | Repository-specific |
| Write user-global Codex files | Exact targets, current digests, rendered diff, installation plan | File restore/uninstall |
| Create/modify GitHub resources or push/open PR | Exact resource, branch/commit scope, permissions and validation | Resource-specific close/revert/revoke |
| Publish a release | Artifact manifest, hashes, retention, compatibility/migration proof | Preserve old release; forward rollback |
| Change rulesets, workflows, secrets, variables, apps, runners, or organization governance | Permission-by-permission preview and affected-repository allowlist | Export/restore or revoke |
| Prune/repair worktree metadata | Exact records and owner-approved disposition | Recovery plan where possible |

## Bootstrap authorization lifecycle

The local manifest-bootstrap receipt is generated only with `--approve` after a reviewed dry run.
It binds operation, canonical repository/worktree/common-Git paths, branch, HEAD, plan ID/digest,
manifest digest, destination, creation/expiration, and hashed local identity. It is mode `0600`,
contains no credentials, and lives beneath the configured local state directory.

An approved receipt is atomically reserved by one transaction and then consumed with completed,
rolled-back, or failed outcome. Expired, malformed, changed-plan, changed-HEAD, other-worktree,
reserved, and consumed receipts fail. It does not authorize commit, push, PR, overlay, subsequent
update, another target, or another apply.

## P08 preservation decision

P08-W2 is active or potentially active work. Preserve it in place; do not inspect untracked bodies,
report their names/content, clean, archive, move, prune, reset, stash, or modify it. P08-W1 is also
left unchanged. The only eligible future target is a new isolated worktree from revalidated
current `main`.

## Approval format

Approval must name the exact action, target, scope, and mutation class. Approval for repository
content never implies worktree creation, commit, GitHub, user-global, release, or other-repository
authority. A rollback demonstration consumes its authorization; reapplication requires another
explicit approval.
