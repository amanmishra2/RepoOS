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

The `0.2.0` fixture engine checks pause during plan application preconditions, again while holding
the repository lock, and immediately before every target-file write. A pause before any target
write produces a failed transaction attempt without a backup-dependent restore. A pause after an
earlier file write stops later writes and triggers automatic rollback.

Dry-run reports the pause but creates no state. Pause does not delete or bypass a lock, and removing
the pause does not recover an interrupted transaction automatically.
