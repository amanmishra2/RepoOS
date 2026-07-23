# Validated implementation backlog

Validated: 2026-07-23
Authority: local backlog only; no GitHub issues were created

## Dependency graph

```mermaid
flowchart LR
  R1["ROS-001"] --> R3["ROS-003"]
  R2["ROS-002"] --> R3
  R3 --> R4["ROS-004"]
  R3 --> R5["ROS-005"]
  R4 --> R5
  R5 --> R6["ROS-006"]
  R3 --> R7["ROS-007"]
  R6 --> R9["ROS-009"]
  R7 --> R9
  R9 --> R8["ROS-008"]
  R4 --> R10["ROS-010"]
  R9 --> R10
  R6 --> R11["ROS-011"]
  R8 --> R11
  R9 --> R11
  R11 --> R12["ROS-012"]
```

This graph removes the Phase 1 ROS-001/ROS-003 cycle, makes real delivery depend on apply/rollback proof, and does not make scheduled learning a prerequisite for safe rollout.

## Common constraints

Every issue preserves unrelated work, keeps private evidence out of public artifacts, uses explicit targets, rejects dirty/unsafe mutation, and makes no external write without separate authorization. Neutral disposable fixtures are allowed; real portfolio writes are not.

## ROS-001 — Validate Phase 1 and audit the supplied ZIP

- **Objective:** establish a complete traceable requirements baseline and safe template disposition before implementation.
- **Detailed scope:** read all 16 Phase 1 files; map every recommendation; hash, integrity-test, safely extract, inventory, and statically audit all 49 ZIP files; compare with RepoOS.
- **Out of scope:** executing bundled code, modifying the template, or using the future CLI to validate its own prerequisite.
- **Dependencies:** none.
- **Acceptance criteria:** 152 unique requirement IDs; ZIP hash/counts; traversal/type/duplicate checks; preserve/fix/replace/move decisions; contradictions recorded.
- **Files expected to change:** `reports/baseline/phase-1-validation-ledger.md`, `reports/baseline/template-divergence-report.md`.
- **Validation commands:** `rg ... | sort -u | wc -l`; `unzip -t`; archive metadata parser; `git diff --check`.
- **Risks:** executing untrusted archive content; losing source traceability.
- **Rollback:** delete only the generated reports on the isolated branch.
- **Parallelization group:** A0, read-only.
- **Execution wave:** 0.
- **Status:** completed locally.
- **Local evidence:** ZIP SHA-256 `7dc977d8663abe7209ba00f6ca784ecf6c773dbad1ee8191e527b2c8c5e4b486`; 49 safe regular entries; 152 ledger IDs.

## ROS-002 — Produce the public-safe portfolio baseline

- **Objective:** classify every first-level portfolio directory without leaking private project metadata.
- **Detailed scope:** read-only Git/filesystem safety inventory; public aliases; dirty/conditional/non-Git classification; bounded instruction-pattern audit; required Stage 1 reports.
- **Out of scope:** project scripts, builds, tests, hooks, fetches, lifecycle changes, or downstream writes.
- **Dependencies:** a minimal redaction rule established within the audit harness.
- **Acceptance criteria:** 14 roots accounted for; Git common-directory identity preserved; all 11 required baseline outputs; JSON parses; facts/inferences/unknowns distinguished.
- **Files expected to change:** `reports/baseline/*`.
- **Validation commands:** `jq empty reports/baseline/portfolio-inventory.json`; exact file-list check; `git diff --check`.
- **Risks:** confidentiality leakage; treating linked worktrees as separate repositories; invented commands.
- **Rollback:** remove generated public reports; local evidence remains outside RepoOS.
- **Parallelization group:** A0, read-only.
- **Execution wave:** 0.
- **Status:** completed locally.
- **Local evidence:** 14 directories, 7 working trees, 6 common Git directories, 4 dirty, 2 conditional, 1 safe candidate.

## ROS-003 — Establish the versioned Python foundation

- **Objective:** make RepoOS installable, versioned, deterministic, and truthful.
- **Detailed scope:** `0.1.0` version, `pyproject.toml`, package entry point, changelog, errors, canonical paths, redaction, reporting, state-root conventions.
- **Out of scope:** real overlays, external writes, release publication, database/service, or full candidate package tree.
- **Dependencies:** ROS-001 and ROS-002.
- **Acceptance criteria:** machine/human version agree; wheel/sdist build; `repoos --help`; stable error codes; state remains outside managed repositories; README reflects shipped behavior.
- **Files expected to change:** `VERSION`, `pyproject.toml`, `CHANGELOG.md`, `src/repoos/**`, `README.md`, `MEMORY.md`.
- **Validation commands:** `python -m build`; `python -m repoos --help`; version equality test; `pytest`.
- **Risks:** premature scaffolding and dependency burden.
- **Rollback:** remove the package files and restore documentation from Git.
- **Parallelization group:** A1, single writer for package metadata.
- **Execution wave:** 1.
- **Status:** completed locally for the `0.1.0` foundation.
- **Local evidence:** Python 3.13 is installed; existing RepoOS tooling is Python; no package metadata currently exists.

## ROS-004 — Add registry, manifest, learning, and plan schemas

- **Objective:** create deterministic contracts before behavioral implementation.
- **Detailed scope:** schemas for public-safe registry, repository manifest, observation, candidate, adoption, and update plan; valid/invalid examples; RepoOS registry entry; local-private overlay convention.
- **Out of scope:** downstream manifests, generated lock, real release artifacts, or confirmed family overlays.
- **Dependencies:** ROS-003.
- **Acceptance criteria:** unknown fields rejected; null/unknown/not-observed represented; cross-field constraints tested; public registry contains no private identifiers; RepoOS is the only unredacted entry.
- **Files expected to change:** `schemas/*.schema.json`, `registry/projects.yaml`, `examples/**`, `tests/schema/**`.
- **Validation commands:** `repoos validate --all`; `pytest tests/schema`; secret/path scan.
- **Risks:** schema overdesign; sensitive registry data.
- **Rollback:** remove schema/registry additions; no target state changes.
- **Parallelization group:** A2, schema owner.
- **Execution wave:** 1.
- **Status:** completed locally.
- **Local evidence:** public/private split is required; YAML/JSON file contracts are sufficient for the observed scale.

## ROS-005 — Implement read-only CLI and safety primitives

- **Objective:** provide deterministic discovery, inventory, status, doctor, validation, diff, audit, check, and report behavior.
- **Detailed scope:** explicit roots/targets; bounded traversal; Git common-dir identity; containment/symlink checks; redaction; pause; locks; structured JSON/human output; stable exits.
- **Out of scope:** real target apply, GitHub writes, recursive content mining, or command invention.
- **Dependencies:** ROS-003 and ROS-004.
- **Acceptance criteria:** all minimum read-only commands have useful help; JSON is deterministic; dirty state is classified; no-write snapshots pass; concurrent lock refusal and pause behavior pass.
- **Files expected to change:** `src/repoos/cli.py`, `discovery.py`, `git.py`, `locks.py`, `pause.py`, `validation.py`, `reporting.py`, related tests.
- **Validation commands:** CLI help/smoke matrix; `pytest tests/unit tests/integration tests/security`; repeat-output comparison.
- **Risks:** unbounded traversal, Git side effects, path escape, secret output.
- **Rollback:** revert package changes; no external state exists.
- **Parallelization group:** A2 after shared interfaces stabilize.
- **Execution wave:** 1.
- **Status:** completed locally for read-only and dry-run behavior.
- **Local evidence:** portfolio contains non-Git roots, linked worktrees, missing remotes, dirty trees, and complex worktree registries.

## ROS-006 — Implement fixture-only planning, apply, backup, and rollback

- **Objective:** prove update safety against disposable repositories before any canary.
- **Detailed scope:** ownership resolution; canonical plan ID; dry-run default; explicit execute; common-Git lock; dirty/stale refusal; limits; operation journal; backups; atomic replace; configured validation; restoration; rollback metadata.
- **Out of scope:** real portfolio writes, commit, push, PR, managed sections, or multi-repository mutation.
- **Dependencies:** ROS-005.
- **Acceptance criteria:** clean/local-edit/delete/conflict/binary/symlink/stale/dirty/lock fixtures; failure injection after each write; successful restore; idempotent reapply; no implicit commit/push.
- **Files expected to change:** `src/repoos/ownership.py`, `planning.py`, `apply.py`, `backup.py`, `journal.py`, fixture tests.
- **Validation commands:** `pytest tests/integration/test_plan_apply.py tests/security`; process-level Git-command allowlist test.
- **Risks:** partial writes and false atomicity.
- **Rollback:** journal-driven fixture restore; revert implementation files from Git.
- **Parallelization group:** A3, single mutation-path owner.
- **Execution wave:** 2.
- **Status:** planned.
- **Local evidence:** Phase 1 promised atomicity without an algorithm; local dirty states require fail-closed behavior.

## ROS-007 — Repair RepoOS Codex surfaces

- **Objective:** replace unsupported or false active Codex infrastructure with current, tested contracts.
- **Detailed scope:** minimal config; selected TOML agents; current hook structure; tested guard behavior; valid executable rules or policy-only docs; skill boundary improvements; strict validators.
- **Out of scope:** propagation, user-global installation, speculative agents/skills, or broad blocking claims.
- **Dependencies:** ROS-003 and current official-schema evidence.
- **Acceptance criteria:** config allowlist passes; obsolete agent files gone/replaced; hook positive/negative fixtures; rule parser checks; skills retain required front matter; registry claims match behavior.
- **Files expected to change:** `.codex/**`, `.agents/skills/**`, `tools/agentops/**`, `docs/agentops/**`, tests.
- **Validation commands:** `repoos validate codex`; `codex execpolicy check`; hook process fixtures; `pytest tests/codex`.
- **Risks:** blocking legitimate commands or relying on undocumented behavior.
- **Rollback:** restore prior files from Git; remove active hook/rule references first if validation fails.
- **Parallelization group:** A2, Codex surface owner.
- **Execution wave:** 3.
- **Status:** completed locally.
- **Local evidence:** config custom tables, 10 Markdown agents, obsolete hook shape/no-op router, and prose rules are confirmed.

## ROS-008 — Establish safe GitHub workflow foundations

- **Objective:** make RepoOS CI portable, read-only, pinned, and representative of real validation.
- **Detailed scope:** GitHub-hosted CI; full-SHA action pins; least privilege; concurrency; timeout; package/test/lint/type/build/CLI commands; read-only scheduled audit specification.
- **Out of scope:** organization settings, required workflows, runner registration, secrets, downstream workflows, or PR automation.
- **Dependencies:** ROS-009 and ROS-007.
- **Acceptance criteria:** workflow syntax valid; pins verified against upstream commits; no self-hosted PR execution; no secrets/write permissions; CI-equivalent commands pass locally.
- **Files expected to change:** `.github/workflows/**`, workflow fixtures, runner/verification docs.
- **Validation commands:** YAML parse; workflow policy validator; exact local CI command; pin-origin verification.
- **Risks:** supply-chain pin mistakes and divergence between local/CI commands.
- **Rollback:** restore previous workflow only if safe; otherwise disable the new workflow through a follow-up commit.
- **Parallelization group:** A4 after test contract stabilizes.
- **Execution wave:** 3.
- **Status:** completed locally.
- **Local evidence:** RepoOS is public, no self-hosted runner is registered, and the current workflow uses mutable tags and a persistent Mac label set.

## ROS-009 — Build comprehensive neutral-fixture verification

- **Objective:** prove every shipped claim semantically, including negative behavior.
- **Detailed scope:** unit, integration, schema, security, CLI, migration/rollback, hook, rule, workflow, idempotency, interrupted-operation, symlink, worktree, non-Git, missing/multiple-remote fixtures.
- **Out of scope:** destructive tests in live repositories or canary CI.
- **Dependencies:** ROS-004, ROS-005, ROS-006, and ROS-007.
- **Acceptance criteria:** all requested fixture classes exist; tests fail on representative defects; build/lint/format/type/check/help/dry-run pass; coverage gaps are stated.
- **Files expected to change:** `tests/**`, `Makefile`, test config and fixtures.
- **Validation commands:** `make verify`; targeted negative-test invocations; build and installation smoke test.
- **Risks:** presence-only tests and unrepresentative fixtures.
- **Rollback:** remove defective tests only with a recorded test-defect explanation; product failures are not suppressed.
- **Parallelization group:** A3 with nonoverlapping fixture ownership.
- **Execution wave:** 2–3.
- **Status:** partial—78 tests cover shipped behavior; executable apply/rollback cases depend on ROS-006.
- **Local evidence:** current Make/test path performs shallow file-presence checks and has no `tests/` directory.

## ROS-010 — Establish the learning ledger and recurring read-only specs

- **Objective:** make evidence and decisions durable without adding a service or autonomous promotion.
- **Detailed scope:** observation/candidate/accepted/rejected/adoption directories; schemas/examples; deduplication key; publishability labels; daily/weekly/biweekly/monthly read-only workflow specs and pause behavior.
- **Out of scope:** AI service, database, automatic promotion, external event ingestion, long-running daemon, or schedule installation.
- **Dependencies:** ROS-004 and ROS-009.
- **Acceptance criteria:** valid/invalid records; state transitions require human fields; private evidence cannot enter public records; recurring jobs are read-only and idempotent.
- **Files expected to change:** `learning/**`, `docs/architecture/LEARNING_LOOP.md`, recurring workflow specs/tests.
- **Validation commands:** schema tests; duplicate fixture; redaction/publishability tests; repeated dry-run comparison.
- **Risks:** confidentiality leakage and process overhead.
- **Rollback:** remove unpublished records/specs; accepted/rejected history remains append-only once used.
- **Parallelization group:** A4.
- **Execution wave:** 4.
- **Status:** completed locally for the Git-tracked foundation and specifications.
- **Local evidence:** no measured evidence volume justifies AI or a database; Git-tracked decisions are sufficient.

## ROS-011 — Adopt the approved canary in two bounded proposals

- **Objective:** prove adoption, update, validation, review, and forward rollback in one real repository.
- **Detailed scope:** refresh P08 state; obtain confirmation; isolated branch/worktree; manifest-only proposal; one bounded component proposal; repository-owned checks; rollback rehearsal.
- **Out of scope:** other repositories, broad rollout, organization settings, automatic push/merge, or multiple components.
- **Dependencies:** ROS-006, ROS-008, ROS-009, explicit user authorization, and a clean/trustworthy P08 base.
- **Acceptance criteria:** approved identity/risk/commands/family/ownership; clean state; reviewed diffs; checks pass; post-adoption plan no-op; forward rollback demonstrated.
- **Files expected to change:** P08 `.repoos/project.yaml` and one explicitly approved component, plus RepoOS adoption record.
- **Validation commands:** exact P08 commands only after user confirmation; RepoOS plan/apply/rollback checks.
- **Risks:** stale upstream, worktree ambiguity, behavior regression, private metadata leakage.
- **Rollback:** forward PR to the previous version plus local backup for uncommitted failure.
- **Parallelization group:** A5, single downstream writer.
- **Execution wave:** 4.
- **Status:** blocked—authorization and Git reconciliation required.
- **Local evidence:** P08 is clean but its upstream is gone and 15 worktree records are prunable.

## ROS-012 — Govern broad rollout and high-authority extensions

- **Objective:** expand only after the canary proves value, safety, update, and rollback.
- **Detailed scope:** one explicit proposal per repository; adoption/defer/exclude state; release artifact integrity/retention; optional global installer; optional GitHub governance; optional scheduled learning after measured need.
- **Out of scope:** bulk autonomous migration, force push, auto-merge, silent settings mutation, or one-size-fits-all overlays.
- **Dependencies:** successful ROS-011 and separate authorization for each mutation class. ROS-010 scheduling is optional, not a hard dependency.
- **Acceptance criteria:** every target classified; clean state; accepted ownership; limits; review/rollback; maintenance benefit measured; high-authority actions have separate plans.
- **Files expected to change:** future repository-specific issues and explicitly approved RepoOS release/governance files.
- **Validation commands:** per-repository commands, release integrity/offline restore, settings before/after comparison where authorized.
- **Risks:** centralization overriding autonomy, review overload, artifact loss, privilege expansion.
- **Rollback:** pause rollout; forward rollback proposals; restore settings from exported prior state.
- **Parallelization group:** A6, one mutation at a time.
- **Execution wave:** 5+.
- **Status:** deferred.
- **Local evidence:** four dirty trees, two conditional trees, seven non-Git roots, and no approved canary make broad rollout unsafe.
