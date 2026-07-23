# CLI reference

Global options must precede the subcommand:

```text
--root PATH
--state-dir PATH
--format human|json
--privacy public|local
```

| Command | Current behavior | Writes target repository |
|---|---|---|
| `discover` | Direct-child proposal inventory | No |
| `inventory` | Root or explicit-project metadata | No |
| `status` | Git and pause state | No |
| `doctor` | Runtime/schema checks | No |
| `validate` | One schema or all RepoOS surfaces | No |
| `diff` | Explicit text-file unified diff | No |
| `audit [--all]` | Implemented deterministic validators | No |
| `check-update` | Manifest/current version comparison | No |
| `plan-update` | Fixture-only explicit file plan; optional plan output | No |
| `apply --dry-run` | Freshness, safety, and digest preview | No |
| `apply --execute` | Refused in `0.1.0` with exit 9 | No |
| `report` | Normalize explicit JSON/YAML | No |

Stable exits: `0` success, `2` input, `3` validation, `4` unsafe, `5` conflict, `6` lock, `7` pause, `8` environment, `9` authorization, `70` internal.
