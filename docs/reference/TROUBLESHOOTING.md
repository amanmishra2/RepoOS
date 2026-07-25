# Troubleshooting

| Symptom | Meaning | Next step |
|---|---|---|
| `invalid_manifest` / exit `3` | Schema, semantic, size, YAML, command, or sensitive-value policy failed | Fully materialize and review a corrected manifest; create a new plan |
| `existing_manifest` / exit `5` | Destination is no longer absent | Stop; bootstrap never replaces a manifest |
| `dirty_target` / exit `10` | Explicit target has tracked or untracked changes | Preserve the work; select or create a clean isolated target |
| `stale_target` / exit `11` | HEAD, branch, manifest, plan, parent, target, sibling, or common-Git binding changed | Inspect the named precondition and make a new plan/authorization |
| `sibling_ambiguity` / exit `4` | Registration is locked, prunable, malformed, duplicate, or unreadable | Stop; do not prune, repair, or inspect file bodies automatically |
| exit `6` active lock | Another process owns the common-Git transaction boundary | Inspect PID/host/transaction and wait |
| exit `6` stale/malformed lock | Explicit lock recovery may be needed | Verify the owner is gone, then use `--recover-stale-lock` once |
| `missing_authorization` / exit `9` | Execute has no exact local approval | Review plan/dry run, then explicitly authorize |
| `invalid_authorization` / exit `9` | Receipt malformed, moved outside state, tampered, or bound elsewhere | Do not edit it; create a new approval for a fresh reviewed plan |
| `expired_authorization` / exit `9` | Approval lifetime ended | Revalidate current state and explicitly approve again |
| `consumed_authorization` / exit `9` | Receipt is reserved or already used | Never reuse; create a new plan/approval if another attempt is authorized |
| `manifest_install_failure` / exit `13` | Exclusive install failed and automatic rollback succeeded | Inspect transaction/backup and restored-state proof |
| `validation_failed_rolled_back` / exit `14` | Repository validation failed; manifest was removed | Fix only through a new reviewed manifest/plan |
| `rollback_failure` / exit `15` | Exact restoration or preservation proof failed | Stop and preserve all transaction evidence |
| `authorization_required` on `plan-update` | Unmarked real-repository update remains unsupported | Use only the bounded onboarding workflow; never add a fixture marker |
| Build cannot resolve packages | Isolated build lacks network/cache | Use verified `python3 -m build --no-isolation` locally |

## Dirty sibling versus dirty target

A dirty sibling is content-free classified as `protected_dirty` and does not block a different
clean target. Any sibling ambiguity or any drift between pre/post summaries does block. Never make
the sibling clean to satisfy RepoOS; preserve it in place.

## Stale-lock evidence

Recovery renames the prior lock to a `.recovered.<time>.<pid>` record before acquiring a new lock.
It does not delete evidence and cannot recover a live local process. A remote-host lock remains
active until the conservative stale window expires.

## `rollback_failed`

There is no automatic retry or force mode. Validate the retained transaction and backup, inspect
only the approved restore path, and restore nothing broader. Do not use `git reset`, `clean`,
`checkout`, `stash`, worktree prune, or sibling mutation.

## Installed behavior

Runtime acceptance is not strict schema validation. Run `repoos validate --all`, the complete
synthetic transaction suite, and the installed-wheel smoke workflow. No destructive test should
name a downstream repository.
