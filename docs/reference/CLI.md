# CLI reference

Global options precede the subcommand:

```text
--root PATH
--state-dir PATH
--format human|json
--privacy public|local
```

Human and JSON output are deterministic. JSON is selected with `--format json`.

| Command | Current behavior | Target writes |
|---|---|---|
| `discover` | Direct-child proposal inventory | No |
| `inventory` | Root or explicit-project metadata | No |
| `status` | Git and pause state | No |
| `doctor` | Runtime and all 11 schema checks | No |
| `validate` | One schema or all RepoOS surfaces | No |
| `diff` | Explicit text-file unified diff | No |
| `audit [--all]` | Implemented deterministic validators | No |
| `check-update` | Manifest/current-version comparison | No |
| `plan-update` | Immutable marked-fixture update-plan v2 | No |
| `plan-manifest-bootstrap` | Immutable one-file real-worktree bootstrap plan v1 | No |
| `authorize-manifest-bootstrap` | Expiring one-use local approval receipt | Local state only |
| `apply --dry-run` | Full precondition and lock-state preview; default | No |
| `apply --execute` | Fixture update or authorized manifest bootstrap | Approved paths only |
| `rollback --transaction ID` | Drift-aware operation-specific restoration | Transaction paths only |
| `transaction show ID` | Schema-valid local transaction detail | No |
| `transaction list` | Deterministic local transaction summaries | No |
| `report` | Normalize explicit JSON/YAML | No |

## Fixture planning

```text
repoos plan-update --repo PATH --source-root PATH
  [--file [COMPONENT|]SOURCE=TARGET]...
  [--generated [COMPONENT|]SOURCE=TARGET]...
  [--section [COMPONENT|]SOURCE=TARGET::START::END]...
  [--preserve [COMPONENT|]TARGET=OWNERSHIP]...
  [FIXTURE SAFETY LIMIT OPTIONS]
  [--output PLAN.json]
```

Deletion is schema-reserved but not executable. Fixture-only named limit overrides do not grant
real-repository authority.

## Manifest-bootstrap planning and approval

```text
repoos plan-manifest-bootstrap
  --repo CLEAN_WORKTREE
  --manifest-input REVIEWED_MANIFEST.yaml
  --output BOOTSTRAP_PLAN.json

repoos [--state-dir LOCAL_STATE] apply
  --plan BOOTSTRAP_PLAN.json
  [--authorization AUTHORIZATION.json]
  --dry-run

repoos [--state-dir LOCAL_STATE] authorize-manifest-bootstrap
  --plan BOOTSTRAP_PLAN.json
  [--expires-in 60..86400]
  --approve

repoos [--state-dir LOCAL_STATE] apply
  --plan BOOTSTRAP_PLAN.json
  --authorization AUTHORIZATION.json
  --execute
```

Plan output, manifest input, local state, and authorization must remain outside every registered
worktree and the common Git directory. The default authorization lifetime is 1,800 seconds.
`--approve` is mandatory and creates only the receipt; it does not execute. Bootstrap rejects
`--source-root` and all `--override-limit` values.

Dry run with no authorization can pass all repository preconditions and report
`ready_for_authorization: true`; it always reports zero target/state writes. Supplying an existing
receipt lets dry run report its lifecycle but never reserves or consumes it.

## Apply, rollback, and inspection

```text
repoos [--state-dir PATH] apply --plan PLAN.json [--dry-run]
repoos [--state-dir PATH] apply --plan PLAN.json --execute
  [--authorization AUTHORIZATION.json]
  [--override-limit FIXTURE_LIMIT]...
  [--recover-stale-lock]
repoos [--state-dir PATH] rollback --transaction ID [--recover-stale-lock]
repoos [--state-dir PATH] transaction show ID
repoos [--state-dir PATH] transaction list
```

The plan binds the target, and any restated target must match. `--execute` is mandatory for target
mutation. `--recover-stale-lock` preserves prior lock evidence and never overrides a live owner.
Transaction inspection is local and content-free; public-safe output does not disclose sibling
paths, untracked names or bodies, credentials, or authorization identity text.

## Stable exits

| Exit | Classification |
|---:|---|
| `0` | Success |
| `2` | Invalid input |
| `3` | Schema/contract validation; includes `invalid_manifest` |
| `4` | Unsafe state or unsupported operation; includes `sibling_ambiguity` |
| `5` | Conflict; includes `existing_manifest` |
| `6` | Active, stale, or malformed lock |
| `7` | Pause |
| `8` | Environment |
| `9` | Missing, invalid, expired, reserved, or consumed authorization |
| `10` | Dirty target |
| `11` | Stale target/plan/manifest binding |
| `12` | Backup creation/integrity failure |
| `13` | Apply or manifest-install failure with successful automatic rollback |
| `14` | Validation failure with successful automatic rollback |
| `15` | Rollback failure |
| `16` | Fixture safety-limit refusal |
| `70` | Redacted internal error |

Machine-readable error types further distinguish `invalid_manifest`, `existing_manifest`,
`dirty_target`, `stale_target`, `sibling_ambiguity`, `missing_authorization`,
`invalid_authorization`, `expired_authorization`, `consumed_authorization`,
`manifest_install_failure`, `validation_failed_rolled_back`, `rollback_failure`, and the lock
classification.

No command commits, pushes, opens a pull request, mutates GitHub settings, changes Git refs or
worktree registrations, registers a runner, or installs user-global files.
