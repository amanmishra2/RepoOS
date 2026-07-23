# Troubleshooting

| Symptom | Meaning | Next step |
|---|---|---|
| Exit `2` | Input/path/transaction ID is invalid | Correct the explicit input; do not infer a target |
| Exit `3` | Schema or RepoOS contract failed | Fix the source contract, not validator output |
| Exit `4` | Unsafe or unsupported operation | Preserve target; inspect ownership/path/unsupported deletion |
| Exit `5` | Ownership or section-marker conflict | Resolve markers/ownership explicitly and make a new plan |
| Exit `6` active lock | Another process owns the target | Inspect PID/host/transaction and wait |
| Exit `6` stale/malformed lock | Recovery is required | Verify owner is gone, then use `--recover-stale-lock` once |
| Exit `7` | Environment/state-file pause | Confirm operator intent; do not bypass |
| Exit `8` | Git/path/runtime unavailable | Classify environment/dependency failure |
| Exit `9` | New authority is required | Request exact target/action authorization |
| Exit `10` | Repository is dirty | Preserve user work; do not stash/reset/clean |
| Exit `11` | Approved plan is stale | Inspect exact failed preconditions; create and review a new plan |
| Exit `12` | Backup incomplete or corrupt | No target write should begin; preserve incomplete/final backup evidence |
| Exit `13` | Apply failed, rollback succeeded | Inspect transaction failure and restored-state proof |
| Exit `14` | Required validation failed, rollback succeeded | Fix fixture/source/command, then create a new plan |
| Exit `15` | Rollback failed | Stop; preserve backup; follow bounded manual recovery instructions |
| Exit `16` | Safety limit exceeded | Reduce plan or explicitly record the exact justified override |
| Build cannot resolve packages | Isolated build lacks network/cache | Use verified `python3 -m build --no-isolation` locally |

## Stale-lock evidence

Recovery renames the prior lock to a `.recovered.<time>.<pid>` record before acquiring a new lock.
It does not delete evidence and cannot recover a live local process. A remote-host lock is treated
as active until the conservative stale window expires.

## `rollback_failed`

There is no automatic retry and no force mode. Validate the retained backup, inspect only its
`restore_order`, and restore original bytes/modes manually. Do not use `git reset`, `clean`,
`checkout`, or `stash`.

## Installed behavior

Runtime acceptance is not strict schema validation. Use `repoos validate --all`, the transactional
schema fixtures, and the installed-wheel fixture smoke test.
