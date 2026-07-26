# Pause automation

Initial pause precedence is strictest-wins:

1. `REPOOS_PAUSED` environment variable with a truthy value.
2. `PAUSED` file in the configured local RepoOS state directory.
3. Target-specific Git or safety block.

Read status:

```bash
repoos --format json status --project /explicit/project
```

The CLI does not create or remove the pause file automatically. Operators control it locally.

The `0.3.0` transaction engine checks pause during application preconditions, again while holding
the common-Git lock, and immediately before every target write. A pause before a write produces a
failed attempt without backup-dependent restoration. A pause after a fixture write or before
bootstrap completion triggers operation-specific automatic rollback.

Dry-run reports the pause but creates no state. Pause does not delete or bypass a lock, and removing
the pause does not recover an interrupted transaction automatically.
