# Update a fixture repository

The authoritative mutation boundary is
[Validated architecture](../implementation/VALIDATED_ARCHITECTURE.md); ownership is defined by
[File ownership](../implementation/FILE_OWNERSHIP_MODEL.md). Version `0.2.0` is fixture-only.

## Plan

The target must be a disposable Git repository with a regular `.repoos-fixture` marker and a
schema-valid manifest whose `automation_permissions.apply` is `true`.

```bash
repoos --format json plan-update \
  --repo /fixture/repository \
  --source-root /fixture/components \
  --file component.txt=managed/component.txt \
  --generated generated.txt=generated/result.txt \
  --section 'body.txt=managed/section.txt::# repoos:start fixture::# repoos:end fixture' \
  --preserve local.txt=local_override \
  --output /tmp/plan.json
```

`--file` is fully managed, `--generated` is generated, and `--section` supplies only a UTF-8
section body. Optional `COMPONENT|` prefixes bind a component ID. Preserve entries accept
`repository_owned`, `repository_extension`, `local_override`, or `excluded`.

Plan v2 binds its canonical digest, RepoOS source version, exact target/source roots, common-Git
identity, HEAD and status fingerprint, manifest version/hash, source and target hashes, modes,
ownership, section/outside hashes, intended output hashes, validation commands, and safety
measurements. Editing any bound field without a new reviewed plan makes it stale.

## Dry-run

```bash
repoos --format json --state-dir /tmp/repoos-state \
  apply --plan /tmp/plan.json --dry-run
```

Dry-run performs every non-locking precondition check and inspects existing lock state. It writes
neither the target nor the state directory. Output lists each exact target, action, component, and
ownership mode.

## Execute

```bash
repoos --format json --state-dir /tmp/repoos-state \
  apply --plan /tmp/plan.json --execute
```

Execution requires the explicit `--execute` switch. The paths bound into the plan are used unless
the same exact paths are supplied again with `--repo` and `--source-root`.
The configured state directory must remain outside both the target fixture and component source
root, so transaction records cannot change the planned Git or source state.

Before target writes RepoOS:

1. creates a failed-attempt-capable transaction record;
2. revalidates target/source paths, plan digest, fixture marker, source version, manifest, HEAD,
   clean status fingerprint, source/target hashes, pause state, ownership, recomputed operation
   measurements/limits, and lock state;
3. acquires the common-Git write lock and repeats freshness checks;
4. creates and integrity-validates the atomic approved-path backup;
5. renders every output beneath the transaction state directory.

It then checks pause before each target write, atomically replaces one file at a time, records the
applied hash, revalidates ownership boundaries, runs manifest validation commands without a shell,
and completes only after all required checks pass.

## Safety limits

Conservative defaults cover files changed/created/deleted, bytes, lines added/removed, percentage
of repository files, allowed prefixes, forbidden path patterns, and managed-section count. Plan
options configure them. An exceeded limit blocks before backup and target writes.

An exception requires the exact named override:

```bash
repoos --state-dir /tmp/repoos-state apply \
  --plan /tmp/plan.json --execute \
  --override-limit max_total_bytes_changed
```

The override is stored in the transaction and public-safe outcome record. Unknown or unnecessary
authority is not inferred from an override.

## Unsupported

Real repositories, dirty targets, deletion, force apply, structured-file sections, multiple
sections per file, whole-tree copy, commit, push, PR creation, external settings, and user-global
installation are unsupported. A successful fixture transaction is not canary evidence and does not
promote a learning candidate.
