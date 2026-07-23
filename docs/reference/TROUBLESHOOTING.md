# Troubleshooting

| Symptom | Meaning | Next step |
|---|---|---|
| Exit 3 | Schema or operating-surface validation failed | Read structured findings; fix the source, not the validator output |
| Exit 4 | Dirty, stale, path, or other unsafe state | Preserve target; resolve only with owner direction |
| Exit 6 | Repository lock exists | Verify the active operation; do not delete blindly |
| Exit 7 | Environment or state-file pause | Confirm operator intent before resuming |
| Exit 8 | Git, path, schema directory, or runtime unavailable | Classify as environment/dependency |
| Exit 9 | New authority or execute path required | Request exact approval; do not bypass |
| Build cannot resolve packages | Isolated build lacks network/cache | Use `python3 -m build --no-isolation` with verified local dependencies |
| `validate --all` finds floating action | Workflow action is not a full 40-character SHA | Verify upstream tag/commit and pin it |
| Installed Codex accepts unknown config | Runtime acceptance is not strict validation | Use RepoOS validator and current official schema |
