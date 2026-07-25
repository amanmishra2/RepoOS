# Hook registry

RepoOS `0.3.0` has no active Codex hooks:

```json
{"hooks": {}}
```

The previous router ignored event input and always exited successfully, so it could not enforce its blocking claim. It was removed rather than preserved as false safety.

A future hook requires current-schema structure, stable execution path, bounded timeout, project trust review, event payload parsing, positive/negative/bypass/subdirectory fixtures, actionable output, and a matching registry claim.

Hooks are defense in depth. Dirty-state, path, ownership, pause, lock, plan, and authorization checks belong in deterministic RepoOS code.

Validation:

```bash
make hooks-smoke
```
