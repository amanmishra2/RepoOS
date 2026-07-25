# Update a fixture repository

This command remains the update-plan v2 proof surface for disposable Git fixtures. The only
real-repository mutation is the separate manifest-bootstrap workflow documented in
[Onboard an existing repository](ONBOARD_EXISTING_REPOSITORY.md).

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

Update-plan v2 binds its canonical digest, RepoOS source version, exact target/source roots,
common-Git identity, HEAD and status fingerprint, manifest version/hash, source and target hashes,
modes, ownership, section/outside hashes, intended output hashes, validation commands, and safety
measurements. Editing any bound field without a new reviewed plan makes it stale.

## Dry run and execute

```bash
repoos --format json --state-dir /tmp/repoos-state \
  apply --plan /tmp/plan.json --dry-run

repoos --format json --state-dir /tmp/repoos-state \
  apply --plan /tmp/plan.json --execute
```

Dry run performs every non-locking precondition check and inspects existing lock state. It writes
neither the target nor the state directory. Execute requires `--execute`; the state directory must
remain outside the fixture and component source.

Before writes RepoOS records the attempt, revalidates the marker, exact paths, plan, source version,
manifest, Git state, hashes, pause, ownership, limits, and lock state; acquires the common-Git lock;
repeats freshness checks; creates an integrity-checked approved-path backup; and renders outputs in
transaction state. It checks pause before each atomic write, validates ownership, runs bounded
no-shell commands, and completes only after every required check passes.

## Configurable fixture limits

Fixture plans have conservative file, byte, line, percentage, prefix, pattern, and section limits.
An exceptional fixture plan may name an exact limit override at execute; that authority is recorded
in transaction evidence. This override mechanism does not apply to manifest bootstrap.

## Refusal boundary

`plan-update` and its apply path require `.repoos-fixture` at planning, precondition, execute, and
rollback boundaries. Adding a marker to a real repository is not an onboarding mechanism.

Deletion, force apply, structured-file sections, multiple sections per file, whole-tree copy,
commit, push, pull-request creation, external settings, and user-global installation remain
unsupported. An unmarked real repository is refused even when it has a valid project manifest or
manifest-bootstrap authorization.
