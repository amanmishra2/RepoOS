# Update a repository

`plan-update` is fixture-bounded in `0.1.0`:

```bash
repoos --format json plan-update \
  --repository /fixture/repository \
  --source-root /fixture/components \
  --file source.txt=managed/target.txt \
  --output /tmp/plan.json
```

Dry-run revalidation:

```bash
repoos --format json apply \
  --plan /tmp/plan.json \
  --repository /fixture/repository \
  --source-root /fixture/components \
  --dry-run
```

Execution is refused. The plan binds project identity, base commit, versions, source/target digests, operations, conflicts, and limits. Dirty, stale, paused, non-Git, symlink, changed-source, and changed-target states prevent a positive preview.
