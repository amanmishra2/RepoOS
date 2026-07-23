# CLI reference

Global options precede the subcommand:

```text
--root PATH
--state-dir PATH
--format human|json
--privacy public|local
```

Human and JSON output are deterministic. JSON is selected with `--format json`.

| Command | Current behavior | Writes target |
|---|---|---|
| `discover` | Direct-child proposal inventory | No |
| `inventory` | Root or explicit-project metadata | No |
| `status` | Git and pause state | No |
| `doctor` | Runtime and all nine schema checks | No |
| `validate` | One schema or all RepoOS surfaces | No |
| `diff` | Explicit text-file unified diff | No |
| `audit [--all]` | Implemented deterministic validators | No |
| `check-update` | Manifest/current version comparison | No |
| `plan-update` | Immutable fixture plan v2; optional plan output | No |
| `apply --dry-run` | Full precondition/lock-state preview; default mode | No |
| `apply --execute` | Locked, backed-up, validated fixture transaction | Approved files only |
| `rollback --transaction ID` | Drift-aware approved-path restore | Transaction files only |
| `transaction show ID` | Schema-valid local transaction detail | No |
| `transaction list` | Deterministic local transaction summaries | No |
| `report` | Normalize explicit JSON/YAML | No |

## Planning

```text
repoos plan-update --repo PATH --source-root PATH
  [--file [COMPONENT|]SOURCE=TARGET]...
  [--generated [COMPONENT|]SOURCE=TARGET]...
  [--section [COMPONENT|]SOURCE=TARGET::START::END]...
  [--preserve [COMPONENT|]TARGET=OWNERSHIP]...
  [SAFETY LIMIT OPTIONS]
  [--output PLAN.json]
```

Safety options configure maximum files, creates, deletes, bytes, added/removed lines, repository
percentage, managed sections, allowed prefixes, and forbidden patterns. Deletion is schema-reserved
but executable deletion remains unsupported.

## Apply and rollback

```text
repoos [--state-dir PATH] apply --plan PLAN.json [--dry-run]
repoos [--state-dir PATH] apply --plan PLAN.json --execute
  [--override-limit NAME]... [--recover-stale-lock]
repoos [--state-dir PATH] rollback --transaction ID [--recover-stale-lock]
```

The approved plan binds target and source roots, so restating them is optional; any restated value
must resolve to the exact bound path. `--execute` is mandatory for mutation. `--recover-stale-lock`
is explicit, preserves the prior lock record, and never overrides an active owner.

## Stable exits

| Exit | Classification |
|---:|---|
| `0` | Success |
| `2` | Invalid input |
| `3` | Schema/contract validation |
| `4` | Unsafe state or unsupported operation |
| `5` | Ownership/managed-section conflict |
| `6` | Active, stale, or malformed lock |
| `7` | Pause |
| `8` | Environment |
| `9` | New authorization required |
| `10` | Dirty repository |
| `11` | Stale approved plan |
| `12` | Backup creation/integrity failure |
| `13` | Apply failure with successful automatic rollback |
| `14` | Validation failure with successful automatic rollback |
| `15` | Rollback failure |
| `16` | Safety-limit refusal |
| `70` | Redacted internal error |

No command commits, pushes, opens a PR, mutates GitHub settings, registers a runner, or installs
user-global files.
