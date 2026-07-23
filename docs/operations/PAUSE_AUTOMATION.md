# Pause automation

Initial pause precedence is strictest-wins:

1. `REPOOS_PAUSED` environment variable with a truthy value.
2. `PAUSED` file in the configured local RepoOS state directory.
3. Target-specific Git or safety block.

Read status:

```bash
repoos --format json status --project /explicit/project
```

The CLI does not create or remove the pause file automatically. Operators control it locally. A future mutation path must recheck pause before planning and before every write boundary.
