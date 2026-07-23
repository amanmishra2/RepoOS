# Inventory

Run bounded public-safe discovery:

```bash
repoos --format json discover
```

Inspect one explicit project with local identities:

```bash
repoos --privacy local --format json inventory --project /explicit/project
```

Discovery scans direct child directories under the configured root, skips common dependency/build/cache names, executes only allowlisted read-only Git metadata commands, and never updates the registry.

Do not run project code, hooks, builds, tests, or fetches during inventory. Lifecycle, family, sensitivity, commands, and ownership remain human-confirmed decisions.
