# Phase 2 implementation handoff

Date: 2026-07-23
Updated: 2026-07-25
Status: Phase 2 foundation/fixture engine and guarded manifest-bootstrap prerequisite complete
locally; no real canary executed

## Repository state

- Repository: public RepoOS control plane
- Starting branch: `main`
- Initial HEAD: `bb9d54425001afad655680235acb0326c1aab401`
- Implementation branch: `codex/ros-001-006-phase2-foundation`
- Foundation checkpoint: `79c474ddaf72f455115db23312584065c5cb56a1`
- Transaction implementation: the commit containing this handoff; resolve locally with
  `git rev-parse HEAD`
- Push/PR: none
- Downstream repository state: unchanged

## Foundation checkpoint

- Read all 16 Phase 1 documents and mapped 152 requirement IDs.
- Integrity/path/type-audited all 49 supplied ZIP entries without executing bundled content.
- Inventoried all 14 first-level portfolio directories read-only.
- Created all 11 Stage 1 baseline outputs and all 9 Stage 2 reconciliation documents.
- Established RepoOS `0.1.0`, package metadata, public registry, self-manifest, six initial JSON
  Schemas, read-only CLI, dry-run planning, repaired RepoOS Codex surfaces, hosted pinned CI,
  learning layout, recurring read-only specs, and architecture/operations/reference documents.
- Pre-checkpoint validation passed Ruff, MyPy across 13 modules, 78 tests, all six schemas, CLI
  smoke checks, offline build, and installed-wheel version/doctor checks.

## Transactional fixture engine

Version `0.2.0` adds:

- immutable update-plan schema v2 with exact target/source roots, common-Git identity, HEAD/status,
  manifest/version, ownership, source/target/mode/section hashes, intended outputs, validation
  commands, safety limits, and canonical digest;
- explicit transaction states and deterministic transition validation;
- per-common-Git filesystem locks plus short-lived global recovery lock, required owner metadata,
  active/stale/malformed classification, preserved stale-lock recovery, and interrupted-process
  handling;
- atomically finalized approved-path backups with plan/manifest/transaction/HEAD/status snapshots,
  original bytes/modes, new-file records, section boundaries, restore order, retention metadata,
  and full snapshot/payload integrity validation;
- rendered-state staging, per-file atomic replacement, mode and LF/CRLF preservation, applied-hash
  journaling, and stop-on-first-failure;
- fully managed, generated, and one uniquely marked UTF-8 managed section per file;
- explicit preservation of repository-owned, extension, local-override, and excluded files;
- limits for files/creates/deletes/bytes/lines/repository percentage/path allow/deny/section count,
  with apply-time contract recomputation and exact recorded overrides;
- bounded no-shell fixture validation, automatic rollback, drift-aware manual rollback,
  interruption recovery, idempotent rollback, and terminal `rollback_failed`;
- public-safe transaction observations with no paths, contents, credentials, environment values,
  or unbounded output;
- `rollback`, `transaction show`, and `transaction list` CLI commands plus executable
  `apply --execute`.

Three additional schemas bring the total to nine:

- `transaction.schema.json`
- `backup-manifest.schema.json`
- `transaction-observation.schema.json`

Executable deletion, force apply/rollback, multiple sections in one file, structured-file sections,
real-repository apply, release migration, commit, push, PR creation, external settings, global
installation, broad rollout, and automatic learning promotion remain unsupported.

The preceding paragraph is the historical `0.2.0` boundary. RepoOS `0.3.0` adds only the
real-repository exception documented below; all other listed limitations remain.

## Transaction validation

| Command/check | Result |
|---|---|
| `python3 -m ruff format --check .` | Pass |
| `python3 -m ruff check .` | Pass |
| `python3 -m mypy src/repoos` | Pass; 17 source files |
| `python3 -m pytest` | Pass; 138 tests |
| `repoos validate --all` | Pass; all nine schemas and operating surfaces |
| CLI help/doctor/update check | Pass |
| New apply/rollback/transaction CLI help | Pass |
| `python3 -m build --no-isolation` | Pass; sdist and wheel |
| Installed-wheel help plus fixture plan/dry-run/apply/show/list/rollback/repeat rollback | Pass |
| Standard isolated build | Environment-only limitation: sandbox DNS cannot provision build dependencies; offline no-isolation build passes |

The temporary-Git fixture suite proves managed/generated/section apply, repository-owned content
preservation, local override/exclusion, dirty/HEAD/source/target/manifest/version staleness,
active/stale/malformed locks, explicit recovery, different-repository concurrency, same-target
refusal, backup failure/integrity, one-write failure, validation failure, rollback failure,
interruption, symlink/traversal, marker ambiguity, every safety-limit class, repeat apply, repeat
rollback, and byte/mode restoration.

## Guarded manifest-bootstrap extension

RepoOS `0.3.0` preserves update-plan v2 and adds the separate
`repoos.manifest-bootstrap-plan.v1` operation for one absent `.repoos/project.yaml`.

- The plan binds canonical target/worktree/common-Git paths, branch, HEAD, target cleanliness,
  content-free sibling summaries, common-Git metadata, exact manifest bytes/schema/version,
  destination absence, parent state, fixed limits, validations, and authorization requirements.
- The reviewed manifest is strictly validated before planning and apply. It requires explicit
  sensitivity, no overlays/local overrides/managed/generated/extensions, bounded
  repository-owned/excluded identifiers, repository validation commands, and denied mutation
  permissions.
- A local mode-`0600` receipt binds the exact operation, worktree/common Git directory, branch,
  HEAD, plan, manifest, destination, authorizer hash, and expiration. One transaction reserves and
  consumes it; it cannot be replayed or used elsewhere.
- The common-Git lock serializes sibling worktrees. Dirty siblings are protected, not cleaned:
  bodies are not opened, untracked names are not persisted, and pre/post HEAD/status/index/lock/
  registration summaries must match.
- Apply renders outside the destination, records absence-aware backup evidence, installs exactly
  one file without overwrite, validates bytes/mode/schema, runs bounded repository commands, and
  proves Git/sibling preservation.
- Automatic/manual rollback removes only the created manifest and a transaction-created parent
  that remains empty. It preserves pre-existing directories/content, is idempotent, and never uses
  Git reset/clean/checkout/stash/prune.
- General real-repository update, existing-manifest replacement, overlays/components, Git
  metadata writes, commit, push, PR, GitHub, user-global files, force, and safety overrides remain
  refused.

All destructive, failure-injection, interruption, rollback, drift, and concurrency proofs use
temporary synthetic repositories. Installed-wheel smoke exercises both the unchanged fixture path
and the new bootstrap lifecycle.

| `0.3.0` validation/check | Result |
|---|---|
| `make verify` | Pass |
| Ruff format/lint | Pass; 50 Python files formatted |
| MyPy | Pass; 18 source files |
| Full Pytest | Pass; 192 tests |
| Focused manifest-bootstrap integration | Pass; 48 tests |
| `repoos validate --all` and `doctor` | Pass; all 11 schemas |
| Offline sdist/wheel build | Pass; `repoos-0.3.0` artifacts |
| Installed-wheel workflow | Pass; fixture update and manifest bootstrap |
| Dirty-sibling/body-name, dry-run, rollback, replay, race, and general-real-refusal proofs | Pass |

## Inventory and canary status

- 14 first-level directories
- 7 Git working trees backed by 6 independent common Git directories
- 4 dirty Git working trees: blocked
- 2 clean but conditional working trees: not eligible
- 7 non-Git roots: exclude/classify/version first
- 1 clean low-ambiguity implementation target: RepoOS
- P08: provisional downstream canary only; explicit confirmation and Git reconciliation required

Fixture success does not make P08 or any other real repository eligible. Before a canary, refresh
read-only Git/GitHub evidence and confirm identity, lifecycle, sensitivity, commands, family,
ownership, base/upstream, worktree disposition, and exact target authorization.

## Canary readiness refresh

The dated [readiness packet](canary-readiness/2026-07-23/README.md) completed that read-only
evidence refresh using only P08, P04-A, and P04-B aliases. Exact mappings remain in the ignored
private overlay.

- P08 identity, canonical private GitHub repository, live `main`, active lifecycle, Python
  CLI/application family, ownership proposal, and offline validation commands are confirmed.
- The historical 16-record/15-prunable P08 snapshot is stale. Current authoritative state is two
  valid records and zero prunable records.
- P08's primary checkout is clean but 29 commits behind after its branch merged. Its second
  worktree contains 18 untracked implementation files and must be preserved.
- The live default-branch tracked state passes Product CI and AgentOps local equivalents.
- Sensitivity remains a user-approved decision; evidence supports personal-data risk.
- At the time of the readiness packet, RepoOS `0.2.0` could not authorize a real repository or
  bootstrap an absent adoption manifest. The synthetic-only `0.3.0` prerequisite is now complete;
  it does not retroactively authorize P08.
- P08 remains provisional but `blocked`; P04-B is `unsuitable_as_first_canary`.

No downstream or GitHub mutation was performed by the readiness audit.

## P08 preservation decision

P08-W2 contains active or potentially active implementation work and must remain in place.
RepoOS must not inspect its untracked bodies, report its names/content, archive, delete, clean,
prune, move, reset, stash, or modify it. P08-W1 also remains unchanged. Neither is the canary
target.

A later P08 run must revalidate current GitHub `main`, create a new isolated worktree, review a
manifest-only dry run, stop for execute approval, apply and run the full P08 profile, demonstrate
rollback, stop for reapplication approval, and create at most a local manifest-only commit. Push
and pull request require separate authorization.

## Safety confirmation

- No downstream or dirty portfolio repository was modified.
- No stash, reset, clean, prune, checkout/switch, force push, default-branch push, merge, or
  downstream worktree operation occurred.
- No bundled ZIP code was executed.
- No user-global Codex file was installed or changed.
- No GitHub issue, setting, ruleset, secret, variable, runner, app, branch push, PR, release, or
  merge was created or changed.
- All destructive-path tests used temporary synthetic Git repositories.
- Public artifacts contain aliases/redaction rather than private portfolio mappings.
- No secret-bearing file was added; synthetic credential shapes exist only in redaction tests.

## Next gate

Use the date-stamped manifest-bootstrap next-canary prompt in a separate run. Do not execute it as
part of the RepoOS implementation transaction. Exact worktree creation, manifest execute,
post-rollback reapplication, local commit, push, and pull request remain separate decisions.
