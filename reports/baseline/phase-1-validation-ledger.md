# RepoOS Phase 1 Requirements Ledger

## Phase 2 local disposition overlay

Local validation date: 2026-07-23

This file preserves all 152 individually mapped Phase 1 requirement rows below. The following local-evidence overlay is authoritative where the original provisional wording differs:

| Disposition | Locally validated scope |
|---|---|
| Confirmed | Read-only-first governance; dirty-tree refusal; repository autonomy; deterministic enforcement separated from AI; explicit ownership; no direct protected-branch push; no secret collection; local state outside managed repositories; YAML desired state and JSON generated state; neutral fixtures before real targets. |
| Confirmed with modification | Four layers remain useful, but family overlays require two confirmed consumers and are not yet implemented. The CLI starts smaller than the candidate tree. The public registry uses aliases/redaction. GitHub-hosted CI replaces the self-hosted default. The current Codex schema contains a mode-specific `agents.max_depth` surface, so the Phase 1 blanket statement is narrowed; RepoOS does not emit it initially. |
| Rejected based on local evidence | Static ZIP/rsync as an ongoing updater; the current RepoOS identity as a copy template; false hook enforcement; Markdown custom agents as active definitions; prose `.rules` as enforcement; self-hosted PR execution as the default. |
| Deferred | Managed sections, real overlays, user-global installer, release signing/service, GitHub App, organization governance, AI semantic review, database/service/dashboard/event bus, broad rollout, and learning automation. |
| Requires authorization | User-global writes; downstream manifest/component writes; canary selection and migration; GitHub issues/settings/rulesets/runners/secrets/variables; release publication; push/PR/merge; any external mutation. |
| Not applicable in this run | Organization-wide enforcement, runner registration, bulk PR creation, and real target rollback exercises. |

Completed local evidence:

- All 16 Phase 1 Markdown files were read and mapped before implementation.
- The ZIP passed integrity/traversal checks and was audited without executing bundled content.
- Every first-level portfolio directory received a read-only Git/filesystem safety classification.
- All 71 tracked RepoOS files and required repository instructions were read.
- RepoOS was the only clean, low-ambiguity implementation candidate; no downstream canary was eligible or approved.
- RepoOS is public, so private portfolio identifiers are not committed.

The dependency corrections in this ledger control the validated backlog: remove the ROS-001/ROS-003 cycle, move inventory behind a minimal redaction contract, make ROS-015 depend on apply/rollback, and do not gate safe rollout on scheduled learning.

Audit date: 2026-07-23
Scope: all 16 Markdown files in the supplied `repoos-phase-1` packet, read in full.
Evidence boundary: Phase 1 documents and the current attachment status only. No project repository, GitHub account, Codex installation, user-global configuration, or extracted template content was inspected for this ledger.

## Status vocabulary

- `Accepted-design`: internally selected in Phase 1, but still subject to current-state validation.
- `Provisional`: explicitly depends on local, account, runtime, or template evidence.
- `Blocked`: cannot be decided safely until named evidence exists.
- `Deferred`: intentionally postponed until a trigger or measured need.
- `Rejected`: excluded as the primary design; a narrow valid use may remain.
- `Superseded-fact`: the Phase 1 statement is stale because the ZIP is now supplied; the audit result is still pending.

Original Phase 1 dispositions below retain their provisional wording for traceability. The Phase 2 overlay above controls implementation. `GAP` means the Phase 1 backlog lacked a clearly owning implementation issue.

## Source aliases

Rows use short numeric aliases where several documents control the same requirement:

| Alias | Exact source file |
|---|---|
| `README` | `README.md` |
| `00` | `00_EXECUTIVE_SUMMARY.md` |
| `01` | `01_RESEARCH_AND_SOURCES.md` |
| `02` | `02_EXISTING_TEMPLATE_AUDIT.md` |
| `03` | `03_TARGET_ARCHITECTURE.md` |
| `04` | `04_GLOBAL_FAMILY_LOCAL_CLASSIFICATION.md` |
| `05` | `05_DISTRIBUTION_AND_SYNC_DECISION.md` |
| `06` | `06_CONTINUOUS_LEARNING_SYSTEM.md` |
| `07` | `07_AUTOMATION_AND_RUNNER_DESIGN.md` |
| `08` | `08_REPOOS_CLI_SPECIFICATION.md` |
| `09` | `09_REPOSITORY_INVENTORY_SPECIFICATION.md` |
| `10` | `10_MIGRATION_AND_ROLLOUT_PLAN.md` |
| `11` | `11_GITHUB_ISSUE_BACKLOG.md` |
| `12` | `12_PHASE_2_CODEX_HANDOFF.md` |
| `13` | `13_DECISION_LOG.md` |
| `14` | `14_RISKS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md` |

## Governance, authority, and safety

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| GOV-001 | Preserve repository autonomy as the default; similarity never transfers ownership. | `03_TARGET_ARCHITECTURE.md` / Design principles; Layer 4 | Accepted-design | Yes | Supplied brief says repositories evolved independently and differ materially; no repository evidence. | Preserve | ROS-002, ROS-007 | Inventory every candidate path; human ownership map; conflict fixtures. |
| GOV-002 | Require explicit eligibility, ownership, version, preview, review, and rollback for shared behavior. | `03_TARGET_ARCHITECTURE.md` / Design principles | Accepted-design | Yes | Architecture rationale only. | Implement | ROS-005, ROS-007, ROS-009, ROS-011 | Schema tests; ownership conflict tests; dry-run and rollback fixtures. |
| GOV-003 | Keep discovery and analysis read-only by default. | `03_TARGET_ARCHITECTURE.md`; `09_REPOSITORY_INVENTORY_SPECIFICATION.md` | Accepted-design | Yes | Phase 1 intentionally made no repository inspection. | Implement | ROS-004, ROS-009 | Filesystem snapshots; Git status before/after; process tracing for hook/script non-execution. |
| GOV-004 | Keep deterministic enforcement separate from AI recommendations. | `03_TARGET_ARCHITECTURE.md`; `06_CONTINUOUS_LEARNING_SYSTEM.md`; D-013 | Accepted-design | Yes | Research/design argument only. | Preserve | ROS-006–ROS-012, ROS-017–ROS-018 | Architecture tests; schemas prohibit AI-written approval fields; mutation-path dependency audit. |
| GOV-005 | Do not silently normalize conflicts among research, runtime, or repository behavior. | `README.md` / Authority; `12_PHASE_2_CODEX_HANDOFF.md` / Conflict resolution | Accepted-design | Yes | Supplied docs define precedence but contain no runtime evidence. | Preserve | All issues | Record conflict; isolate reproduction; require human disposition before migration. |
| GOV-006 | Unknown ownership defaults to repository-owned. | `03_TARGET_ARCHITECTURE.md`; `09_REPOSITORY_INVENTORY_SPECIFICATION.md` / Ambiguity | Accepted-design | Yes | Design-only safety rule. | Preserve | ROS-007 | Property test that unknown paths never enter mutation plan. |
| GOV-007 | Refuse dirty, conflicted, operation-in-progress, stale-base, missing-baseline, secret-bearing, protected, or out-of-root mutation targets. | `03`, `07`, `08`, `09`, `10`, `12` safety sections | Accepted-design | Yes | Repeated normative rule; no local fixtures yet. | Implement | ROS-004, ROS-009–ROS-012 | Dedicated negative fixtures for every stop condition and stable exit code. |
| GOV-008 | Never directly push protected branches, force-push, or auto-merge during initial rollout. | `03`, `05`, `07`, `10`, `12`; D-006, D-014 | Accepted-design | Yes | Supplied brief requires controlled changes. | Preserve | ROS-015, ROS-016, ROS-019 | Fake transport tests; branch policy checks; audit Git command allowlist. |
| GOV-009 | Never collect secret values or cross-project business logic. | `03` / Data flow; `07` / Safety; `09` / Confidential exclusions | Accepted-design | Yes | Policy only; no local content inspected. | Preserve | ROS-012, ROS-017 | Secret fixtures; output/log scanning; allowlist and redaction tests. |
| GOV-010 | Use issue-linked branches/worktrees and preserve unrelated changes. | `10_MIGRATION_AND_ROLLOUT_PLAN.md` / Global gates; backlog common constraints | Accepted-design | Yes | No actual issue taxonomy or RepoOS worktree inspected. | Conditional | All implementation issues | Inspect `AGENTS.md`, issue taxonomy, Git state, and active user changes first. |
| GOV-011 | Treat current official schemas as authoritative for new output, while preserving verified installed behavior until migration is decided. | `01_RESEARCH_AND_SOURCES.md`; `12` / Conflict resolution | Accepted-design | Yes | Phase 1 official citations only; installed Codex version unknown. | Preserve | ROS-006 | Record installed version; validate current schema; reproduce discrepancies in isolated fixtures. |
| GOV-012 | Stop and request human direction when identity, ownership, sensitivity, commands, permissions, or rollback are ambiguous. | `10` stop conditions; `12` handoff | Accepted-design | Yes | Phase 1 lists all as unknown. | Preserve | All issues | Approval ledger and explicit stop-state tests. |
| GOV-013 | Keep external GitHub settings mutations separate from repository content changes. | `04` matrix; `10`; ROS-020 | Accepted-design | Yes | GitHub plan/org state unknown. | Preserve | ROS-020 plus separate per-mutation issue | Read-only comparison first; distinct approval, plan, rollback, and audit record. |
| GOV-014 | Require exact authorization before user-global Codex changes. | `03` / Layer 1; `04` / Global files; `06` / Human approvals | Provisional | Yes | No user-global audit or authority exists in Phase 1. | Defer | GAP—proposed ROS-021 | Explicit target list, backup, checksum/adoption plan, and user approval. |

## Architecture, scope, ownership, and state

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| ARC-001 | Use four layers: user-global Codex, RepoOS control plane, family/capability overlays, and repository-local. | `00`; `03` / Four layers; D-001 | Accepted-design | Yes | Brief establishes multiple divergent projects; sharing shape is unverified. | Conditional | ROS-002, ROS-007, ROS-013 | Current-state matrix; confirm at least one reusable component and explicit local exceptions. |
| ARC-002 | Keep RepoOS independent rather than a monorepo, submodule parent, or source host. | `03` / Layer 2; D-002 | Accepted-design | Yes | Brief calls projects siblings and RepoOS likely control plane. | Preserve unless existing structure conflicts | ROS-003 | Inspect actual RepoOS and repository relationships without mutation. |
| ARC-003 | Keep user-global content limited to universal preferences, safety, environment-backed MCP, and genuinely reusable agents/skills/hooks. | `03` / Layer 1; `04` matrix | Accepted-design | Yes | No global files inspected. | Conditional | GAP—ROS-021 | Separate user-global audit; test an unrelated-repository applicability criterion. |
| ARC-004 | Keep business rules, architecture, validation commands, local triggers, and unadopted files repository-owned. | `03` / Layer 4; `04` matrix | Accepted-design | Yes | Brief says repositories differ. | Preserve | ROS-002, ROS-007 | Inventory and human confirmation per repository. |
| ARC-005 | Permit one primary family and ordered additive capability overlays. | `03` / Layer 3; D-009 | Accepted-design | Yes | No real repository shapes inspected; at least two shared members is assumed. | Conditional | ROS-002, ROS-007 | Evidence-backed classification; test multi-runtime counterexamples and exception rate. |
| ARC-006 | Do not create a family when only one repository fits; keep it local or experimental. | `09` / Ambiguity; `12` / Decision rules | Accepted-design | Yes | Portfolio expected to contain only three or four projects. | Preserve | ROS-002, ROS-013 | Family membership count and human confirmation. |
| ARC-007 | Prefer whole managed files; use managed sections only in stable text formats. | `03` / File ownership; `05`; D-007 | Accepted-design | Yes | No unavoidable section use case identified. | Preserve | ROS-007, ROS-008 | Marker parser fixtures and inventory of actual mixed-ownership files. |
| ARC-008 | Prohibit managed sections in TOML, JSON, and workflow YAML initially. | `03` / Managed section | Accepted-design | Yes | Design-only safety choice. | Preserve | ROS-008 | Negative fixtures; require separate decision to expand formats. |
| ARC-009 | Require stable nonnested unique section markers and preserve surrounding bytes. | `03`; `05`; ROS-008 | Accepted-design | Yes | Markdown marker example only; plain-text syntax unspecified. | Revise/specify | ROS-008 | Define marker grammar for each supported text format; property tests. |
| ARC-010 | Generated files carry generator version/input digest and reject local edits. | `03` / Generated file | Accepted-design | Yes | No generated-file candidates exist locally. | Conditional | ROS-005, ROS-008 | Determinism and unauthorized-edit fixtures; document recovery/adoption path. |
| ARC-011 | Represent local overrides with reason, owner, review date, and optional expiry. | `03` / Local override; project schema | Accepted-design | Yes | No current exception inventory. | Implement | ROS-005, ROS-007, ROS-019 | Schema and expiry reporting tests; human owner validation. |
| ARC-012 | Maintain `.repoos/project.yaml` as repository-owned desired state. | `03` / Repository metadata | Accepted-design | Yes | No target currently inspected or adopted. | Implement after canary approval | ROS-005, ROS-013, ROS-016 | Schema fixtures; no-behavior adoption diff; human review. |
| ARC-013 | Commit generated `.repoos/lock.json` with exact release, SHA, components, digests, and baseline references. | `03` / Generated lock; `05` / Baseline | Accepted-design | Yes | Baseline store/release retention not implemented. | Implement after artifact design | ROS-005, ROS-008, ROS-011, ROS-013 | Clone/offline explanation test; tamper detection; release resolution and rollback fixtures. |
| ARC-014 | Keep immutable baseline bodies in a RepoOS release or content-addressed artifact, not every repository. | `03`; `05` / Baseline | Accepted-design | Yes | No release mechanism, integrity format, retention, or recovery policy exists. | Revise/specify | ROS-003, ROS-008, ROS-011 | Signed/hash-verified artifact fixture; offline recovery and unavailable-baseline tests. |
| ARC-015 | Use YAML for reviewed desired state, JSON for generated state, JSONL optionally for ingestion, and defer SQLite. | `03` / Storage; `08`; D-005 | Accepted-design | Yes | Small expected portfolio supports low-complexity choice. | Preserve | ROS-005, ROS-017 | Data-volume baseline; deterministic serialization; revisit threshold. |
| ARC-016 | Keep cache/state outside managed repositories and configurable. | `03` / Storage; `08` / State | Accepted-design | Yes | No actual state root or permissions inspected. | Implement | ROS-003, ROS-004, ROS-009, ROS-012 | Platform path tests; repository snapshot proves no internal cache writes. |
| ARC-017 | Keep operational timestamps out of project desired state. | `03` / Repository metadata; D-020 | Accepted-design | No for initial implementation | Rationale supplied; no competing compliance need known. | Preserve | ROS-005, ROS-012 | Schema rejects volatile audit fields; normalized output tests. |
| ARC-018 | Defer dashboard, service/API, event bus, vector DB, relational server, generic policy language, real-time watchers, autonomous promotion, and runner fleet. | `03` / Premature abstractions | Deferred | Conditional | Portfolio is only three or four projects. | Defer | None until trigger | Revisit only with measured burden/volume or an unmet requirement. |
| ARC-019 | Use explicit component target paths; never unresolved mutation globs. | `03` / Component model | Accepted-design | Yes | Design-only safety rule. | Preserve | ROS-005, ROS-007, ROS-009 | Schema rejection and path-containment tests. |
| ARC-020 | Formalize overlay compatibility, component migrations, and release SemVer. | `03` / Precedence and versioning | Provisional | Yes | Only high-level rules exist; migration graph semantics are incomplete. | Revise/specify | ROS-005, ROS-007, ROS-011 | Version compatibility matrix; every supported edge and reverse/forward rollback fixture. |
| ARC-021 | Make project IDs stable across folder moves and lowercase/unique. | `03` / Schema rules | Accepted-design | Yes | Actual identities, collisions, and moves unknown. | Implement | ROS-002, ROS-005 | Duplicate/move/rename fixtures and human mapping review. |

## Distribution, synchronization, and rollback

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| SYN-001 | Build a small deterministic `repoos` CLI as the primary synchronization interface. | `00`; `05` / Decision; D-003 | Accepted-design | Yes | Static-copy deficiency is confirmed by brief; existing RepoOS/tooling unknown. | Conditional | ROS-003–ROS-011 | Inspect existing RepoOS; prototype safety primitives; compare maintenance burden with Copier. |
| SYN-002 | Use versioned component overlays rather than one monolithic template. | `05`; `03` / Component model | Accepted-design | Yes | Independent divergence is confirmed; reusable component boundaries are not. | Implement after inventory | ROS-005, ROS-007, ROS-013 | Classify actual candidates and prove neutral fixtures. |
| SYN-003 | Use static ZIP, GitHub templates, Cookiecutter, or Copier only for bootstrap/narrow rendering, not ongoing portfolio sync. | `05` / Rejected options; D-003 | Accepted-design or Rejected-primary | Yes | ZIP contents and lineage were not yet audited in Phase 1. | Conditional | ROS-001, ROS-003 | Template audit; compare actual update lineage and ownership needs. |
| SYN-004 | Use Cruft only for a real existing Cookiecutter lineage. | `05` / Cruft | Provisional | Yes | Template lineage unknown in Phase 1. | Defer | ROS-001 | Inspect template markers/history and any downstream lineage evidence. |
| SYN-005 | Use submodules only for a true independently versioned shared dependency. | `05`; D-002 | Rejected-primary | Yes | No shared dependency candidate identified. | Reject for root policy files | ROS-002 | Inventory actual submodules and ownership needs. |
| SYN-006 | Reject symlinks for project synchronization; allow opt-in global skill symlinks only. | `05`; D-015 | Rejected-primary | Yes | Codex skill symlink support cited; machine topology unknown. | Conditional for global only | GAP—ROS-021 | Symlink escape, portability, and multi-machine tests. |
| SYN-007 | Use installed-base, local-ours, target-theirs three-way update semantics. | `03`; `05`; D-008 | Accepted-design | Yes | No baseline or local-edit fixtures yet. | Implement | ROS-008 | Clean/local-edit/delete/conflict/binary/encoding/line-ending fixtures. |
| SYN-008 | Treat a missing locally deleted managed file as a stop unless explicit recreation policy exists. | `05` / Whole managed file | Accepted-design | Yes | No deletion policy schema specified. | Revise/specify | ROS-005, ROS-008 | Add explicit recreation policy and positive/negative fixtures. |
| SYN-009 | Stop on merge conflict, binary content, unknown baseline, malformed markers, or unauthorized generated-file edit. | `05` / Algorithm and conflict policy | Accepted-design | Yes | No implementation evidence. | Preserve | ROS-008, ROS-009 | Conflict bundle and no-write snapshot tests. |
| SYN-010 | Emit plan JSON, Markdown, patch, and conflict artifacts before any target write. | `03` / Update flow; `08` / Plan | Accepted-design | Yes | Output contracts are drafted only. | Implement | ROS-009, ROS-012 | Schema snapshots and deterministic normalized plan ID tests. |
| SYN-011 | Bind plans to project identity, base commit, releases, selected components, and render inputs. | `08` / Plan ID | Accepted-design | Yes | Canonical input serialization and path independence are unspecified. | Revise/specify | ROS-009 | Canonical serialization test; stale base/input invalidation tests. |
| SYN-012 | Apply only a verified explicit plan in a dedicated branch/worktree; do not push automatically. | `03`; `08` / Apply | Accepted-design | Yes | Worktree setup requirements and dirty-main policy unverified. | Implement | ROS-010 | Worktree lifecycle, stale-plan, dirty-state, and partial failure fixtures. |
| SYN-013 | Treat multi-file apply plus lock update as recoverable and effectively atomic. | `08`; ROS-010 | Provisional | Yes | “Atomic” is asserted but no transaction/journal algorithm is specified. | Revise/specify | ROS-010 | Fault injection after every write; journal/backup restoration; fsync/rename behavior where supported. |
| SYN-014 | Use one repository per proposal and split by limits or unrelated risk. | `05`; `07` / Limits | Accepted-design | Yes | Review capacity and natural component grouping unknown. | Preserve initially | ROS-009, ROS-015, ROS-019 | Limit tests and canary review-burden measurement. |
| SYN-015 | Roll back merged updates through a forward PR from the previous immutable release; never rewrite history. | `03`; `05`; `06`; `08`; ROS-011 | Accepted-design | Yes | File rollback model exists; external-state rollback is excluded. | Implement | ROS-011 | Migration graph and idempotent forward rollback fixtures. |
| SYN-016 | Keep external-setting rollback separate and report manual recovery exactly. | `03` / Rollback; risk R-23 | Accepted-design | Yes | No external desired-state or rollback implementations. | Preserve | ROS-020 plus per-mutation issue | Evaluate-mode canary; export before/after state; approved recovery exercise. |
| SYN-017 | Retain immutable old releases and recovery documentation after deprecation/removal. | `06` / Deprecation; `05` / Baseline | Accepted-design | Yes | No retention duration, artifact store, signature, or GC policy exists. | Revise/specify | ROS-003, ROS-011 | Release retention policy and old-pin offline rollback test. |
| SYN-018 | Pin actions and reusable workflows to full commit SHAs with readable release comments and update PRs. | `01` GitHub findings; `05`; D-010 | Accepted-design | Yes | Official docs support immutability; actual workflows/access unknown. | Preserve | ROS-006, ROS-014 | Validator fixtures; verify SHA origin; Dependabot/RepoOS update test. |
| SYN-019 | Use reusable workflows for complete policy-bearing jobs and composite actions for repeated steps. | `01`; `04`; `07` | Accepted-design | Yes | No common jobs identified locally. | Conditional | ROS-002, ROS-014 | Normalize existing workflows; caller fixtures; permission and check-name equivalence. |
| SYN-020 | Keep caller triggers, permissions, commands, runners, environments, secrets, and deployments repository-local. | `04`; `07` / Keep local | Accepted-design | Yes | Actual workflows and required checks unknown. | Preserve | ROS-002, ROS-014, ROS-016 | Inventory and before/after check behavior; least-privilege review. |

## Automation, credentials, concurrency, and operations

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| AUT-001 | Use GitHub-hosted Actions for remote CI/events, local deterministic scans for siblings, Codex worktrees for bounded semantics, and humans for decisions. | `07` / Recommendation; D-011 | Accepted-design | Yes | Mac and GitHub usage are assumed; capabilities/auth unknown. | Conditional | ROS-002, ROS-014, ROS-018 | Capability matrix and one end-to-end dry run per execution surface. |
| AUT-002 | Do not run a daemon or permanent AI process. | `07` / Recommendation | Accepted-design | No unless requirements change | Small portfolio supports event/schedule model. | Preserve | ROS-018 | Architecture review; no long-lived process in deployment artifacts. |
| AUT-003 | Defer self-hosted runners, especially the general-purpose Mac. | `07`; D-012 | Deferred | Yes if revisited | Official security warning cited; no demonstrated need. | Defer | ROS-020 only on new need | Require private repo, isolation, allowlists, ephemeral cleanup, incident ownership, and cost proof. |
| AUT-004 | Use `launchd` only for weekly deterministic read-only scanning with explicit root and no write token. | `07` / Local Mac design | Provisional | Yes | User platform appears macOS; availability and preference unverified. | Conditional | ROS-018 | Local capability check; no-diff/no-network-write integration run; missed-run recovery. |
| AUT-005 | Use Codex scheduled worktrees only on redacted RepoOS evidence, with structured output and no project writes. | `07` / Scheduled-worktree design | Provisional | Yes | Codex scheduled-task capability cited; local auth/budget/config unknown. | Conditional | ROS-018 | Schema-constrained run against synthetic evidence; filesystem/write-scope audit. |
| AUT-006 | Use `codex exec` only for explicit isolated AI batches, read-only by default. | `01`; `07` | Provisional | Yes | Current docs cited; installed binary/version/auth unknown. | Conditional | ROS-018 | Version/capability check; sandbox and credential isolation test. |
| AUT-007 | Keep deterministic jobs independent of AI failure. | `07`; ROS-018 | Accepted-design | Yes | Design-only. | Preserve | ROS-018 | Inject AI timeout/invalid output; deterministic report remains complete. |
| AUT-008 | Use weekly audit, biweekly semantic review, monthly proposals, quarterly review, with catch-up IDs and backoff. | `00`; `07` / Scheduled jobs | Provisional | Yes | Cadence and budget are assumptions. | Revise after baseline | ROS-018 | Measure change frequency, noise, cost, missed runs, and action latency for two cycles. |
| AUT-009 | Record merged PR/CI metadata into an ingestion queue without copying code. | `07` / Event jobs | Provisional | Yes | “RepoOS ingestion queue” transport/storage/auth is undefined and no service is planned. | Revise/specify | ROS-017, ROS-018 | Define artifact/dispatch/pull transport; idempotency, retention, auth, offline catch-up tests. |
| AUT-010 | Use `workflow_dispatch`, `repository_dispatch`, and `schedule` only for their documented roles; keep CLI as common execution path. | `01` / GitHub findings | Accepted-design | Yes | Official docs cited; repository workflow presence/visibility unknown. | Conditional | ROS-014, ROS-018 | Default-branch trigger fixtures and external-dispatch authentication test. |
| AUT-011 | Separate read-only jobs from PR-creation/write jobs and minimize permissions. | `07` / Permissions; `12` | Accepted-design | Yes | GitHub auth model unknown. | Preserve | ROS-014, ROS-015 | Workflow permissions linter and fake authorization matrix. |
| AUT-012 | Use `GITHUB_TOKEN` for same-repository work; prefer least-privilege GitHub App for recurring cross-repository writes; PAT only as fallback. | `01`; `07`; D-011 context | Provisional | Yes | Official behavior cited; org/app ownership unknown. | Conditional | ROS-015, ROS-020 | Auth capability inventory; permissions review; fake and one approved canary write. |
| AUT-013 | Never give an AI job both broad credentials and untrusted repository execution. | `07` / Permissions | Accepted-design | Yes | Policy only. | Preserve | ROS-014, ROS-015, ROS-018 | Workflow graph/secret exposure audit and negative credential-injection tests. |
| AUT-014 | Scope secrets to declared needs, prefer OIDC where applicable, and inventory names/access only when authorized. | `07` / Secrets; `09` / GitHub enrichment | Accepted-design | Yes | Cloud providers and org secret policy unknown. | Conditional | ROS-002, ROS-014, ROS-020 | Read-only metadata inspection with explicit scope; workflow secret mapping tests. |
| AUT-015 | Use local global and per-repository locks plus GitHub concurrency groups. | `07` / Locks; `08` / Locks | Accepted-design | Yes | Lock algorithm, filesystem semantics, host identity, and concurrent tooling unknown. | Implement with revision | ROS-010, ROS-018 | Atomic acquisition, PID reuse, host mismatch, TTL, crash, and concurrency fixtures. |
| AUT-016 | Permit two concurrent reads and one portfolio mutation initially. | `07` / Locks | Provisional | Yes | Thresholds are arbitrary for a three/four-repo portfolio. | Calibrate | ROS-010, ROS-018 | Load/latency and interference tests; keep configuration explicit. |
| AUT-017 | Require proof the process is gone plus explicit flag before breaking stale locks. | `07`; `08` | Accepted-design | Yes | Cross-host proof mechanism is unspecified. | Revise/specify | ROS-010 | Process-start identity and cross-host stale-lock fixtures. |
| AUT-018 | Provide tracked pause, local `PAUSED`, environment kill switch, and external workflow variable. | `07` / Pause and kill switch | Accepted-design | Yes | Multiple control planes create propagation/precedence questions. | Implement after precedence spec | ROS-018 | Test each layer, precedence, already-running job behavior, stale checkout, and reporting. |
| AUT-019 | Start with 20 files, 1,000 lines, 250 KiB, five components, zero protected paths/conflicts. | `07` / Maximum-change defaults | Provisional | Yes | No real change-size distribution exists. | Calibrate after inventory/canary | ROS-009, ROS-016 | Boundary tests and observed canary patch statistics. |
| AUT-020 | Notify only on action-required conditions and suppress unchanged-health noise. | `07` / Notifications | Accepted-design | Yes | User notification preference and action volume unknown. | Conditional | ROS-018 | Two-cycle noise/action review. |
| AUT-021 | Use organization `.github`, custom properties, rulesets, or required workflows only after org/plan validation and separate approval. | `07`; D-017; ROS-020 | Provisional | Yes | Ownership, visibility, plan, and admin authority unknown. | Defer | ROS-020 | Read-only API inventory; evaluate-mode canary; rollback/bypass plan. |

## CLI, schemas, packaging, and developer interface

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| CLI-001 | Implement in Python 3.11+ unless existing RepoOS or environment makes another language preferable. | `08` / Implementation choice; D-004 | Provisional | Yes | Python rationale only; current RepoOS and developer runtime unknown. | Conditional | ROS-003 | Inspect existing code; clean-environment build/install; compare migration cost. |
| CLI-002 | Keep initial dependencies small and choose CLI/YAML/merge libraries only after inspection. | `08` / Dependencies | Provisional | Yes | Candidate libraries only. | Conditional | ROS-003, ROS-008 | Dependency security/maintenance review; round-trip and merge fixtures. |
| CLI-003 | Use Git executable with argument arrays and machine-readable output; avoid shell interpolation. | `08`; `09` / Git detection | Accepted-design | Yes | Design and official Git behavior only. | Preserve | ROS-004, ROS-010 | Shell-injection/path fixtures and command-spy assertions. |
| CLI-004 | Keep target repositories independent of RepoOS Python packages. | `08` / Packaging | Accepted-design | Yes | Target stacks unknown. | Preserve | ROS-003, ROS-014 | Consumer fixture uses released CLI/action without project dependency change. |
| CLI-005 | Require explicit absolute portfolio roots and containment checks after expansion/canonicalization. | `08` / Config; `09` / Root validation | Accepted-design | Yes | `~/Coding` is the intended root but not inspected by this audit. | Preserve | ROS-004 | Root refusal, symlink escape, unresolved variable, mount-boundary fixtures. |
| CLI-006 | Define stable JSON envelopes, Markdown headers, symbolic errors, and exit codes. | `08` / Output and exit codes | Accepted-design | Yes | Draft contract only. | Implement | ROS-005, ROS-009, ROS-012 | JSON Schema snapshots; stdout/stderr separation; every error-path fixture. |
| CLI-007 | Add the documented command suite incrementally rather than scaffolding all modules immediately. | `08` / Commands and package tree | Provisional | Yes | Full package tree is far larger than Wave 1 needs. | Simplify/sequence | ROS-003–ROS-018 | Implement only issue-owned commands; docs-to-command conformance tests. |
| CLI-008 | `discover` lists bounded siblings and Git roots without descending into content. | `08` / `discover`; `09` | Accepted-design | Yes | No actual root evidence. | Implement | ROS-004 | Synthetic directory/tree fixtures and no-content-read tracing. |
| CLI-009 | `inventory` defaults to metadata-only, no scripts/hooks, and optionally authorized GitHub enrichment. | `08`; `09` | Accepted-design | Yes | Inventory schema only. | Implement | ROS-002, ROS-004, ROS-006, ROS-012 | Repeat-run stability; process tracing; redaction and auth-state tests. |
| CLI-010 | `status`, `doctor`, `validate`, `diff`, and `check-update` remain read-only. | `08` / Command contract | Accepted-design | Yes | No implementation. | Implement incrementally | ROS-003, ROS-006, ROS-008, ROS-009 | Repository snapshots and fake network/release stores. |
| CLI-011 | Define `--fail-on` explicitly because `status` references it but the option contract omits it. | `08` / `status`; Global options | Provisional | No local evidence needed | Internal specification gap. | Fix spec | ROS-003, ROS-005 | CLI help/golden tests for accepted values and exit 4 behavior. |
| CLI-012 | Block migration/apply when version-sensitive schemas cannot be verified within policy. | `08` / `validate`; `07` / Failure handling | Accepted-design | Yes | Cache-age policy has no default or provenance format. | Revise/specify | ROS-006 | Fresh/stale/offline/tampered cache fixtures and installed-runtime exception path. |
| CLI-013 | Make `apply --dry-run` an exact no-mutation alias for planning. | `08` / Dry run | Accepted-design | Yes | Contract only. | Preserve | ROS-009 | Snapshot repository, Git refs/index/worktrees/remotes and fake external state. |
| CLI-014 | Permit dry-run verification commands only when explicitly selected and classified safe. | `08` / Dry-run guarantees | Provisional | Yes | No safe-command classification model exists. | Defer or specify narrowly | ROS-009, ROS-010 | Explicit allowlist schema; sandbox/side-effect fixtures; default remains off. |
| CLI-015 | Require explicit project and plan ID for apply and revalidate all digests/base immediately. | `08` / Apply | Accepted-design | Yes | Plan/apply option syntax is incomplete. | Fix spec and implement | ROS-009, ROS-010 | CLI help tests; stale base/input/plan tamper fixtures. |
| CLI-016 | Keep `open-pr` explicit, idempotent, non-merging, and restricted to validated applied plans. | `08`; ROS-015 | Accepted-design | Yes | Remote/auth behavior unknown. | Implement | ROS-015 | Fake transport partial failure/retry/duplicate tests; approved canary. |
| CLI-017 | Split rollback planning from applying or require an equally explicit apply mode. | `08` / `rollback` | Provisional | No local evidence needed | Current command says “plan or apply” but approval boundary is ambiguous. | Revise spec | ROS-011 | CLI golden tests require `--dry-run` default or explicit `--apply --plan`. |
| CLI-018 | Keep global commands separate from repository commands because blast radius differs. | `08` / User-global commands | Accepted-design | Yes | No global manifest, adoption semantics, or issue exists. | Defer | GAP—ROS-021 | Separate schemas, backups, ownership, conflict, authorization, and rollback tests. |
| CLI-019 | Never log file bodies, prompts, environment values, tokens, or detector matches; debug stays redacted. | `08` / Logging | Accepted-design | Yes | Policy only. | Preserve | ROS-012 | Canary-secret fixtures through stdout, stderr, log, JSON, and Markdown. |
| CLI-020 | Make lock acquisition atomic and verify PID plus process-start identity. | `08` / Locks | Accepted-design | Yes | Cross-platform process identity API unknown. | Implement with platform review | ROS-010 | Linux/macOS fixtures; crash/PID reuse/TTL tests. |
| CLI-021 | Prove unit, integration, migration, rollback, security, and property contracts before real updates. | `08` / Tests; `12` completion boundary | Accepted-design | Yes | Test lists only; no current harness. | Preserve | ROS-003–ROS-013 | CI matrix and traceability from each requirement to fixture. |

## Inventory, template audit, and current-state validation

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| INV-001 | Safely hash and extract the supplied ZIP into a temporary directory and complete every file-level finding. | `02_EXISTING_TEMPLATE_AUDIT.md`; ROS-001 | Superseded-fact: ZIP now supplied; audit pending | Yes | Phase 1 said ZIP missing; the current task supplies `<user-downloads>/generic_project_operating_layer_template.zip`. | Execute read-only audit | ROS-001 | Archive SHA/size/path audit; reject traversal/symlink/device/duplicate normalized entries; full inventory. |
| INV-002 | Do not treat any Phase 1 template-specific assertion as final before the ZIP audit. | `00`; `02`; `12`; D-019 | Accepted-design | Yes | All template findings were explicitly blocked. | Preserve | ROS-001 | Map every template path/finding to evidence and disposition record. |
| INV-003 | Test advertised template behavior, negative cases, idempotence, migrations, and rollback in disposable fixtures rather than checking file presence. | `02` / Audit protocol | Accepted-design | Yes | Protocol only. | Preserve | ROS-001 | Trace commands; inject semantic defects; lifecycle fixture matrix. |
| INV-004 | Inventory one or more explicitly approved roots, default depth one, with no symlink following or mount crossing. | `09` / Discovery and traversal | Accepted-design | Yes | `~/Coding` is named by brief but this delegated audit did not treat that as implementation authorization. | Conditional | ROS-002, ROS-004 | Confirm scope; path traversal fixtures; per-sibling record/skip reason. |
| INV-005 | Refuse `/`, home, unresolved variables, and unsafe roots; permit resolved `~/Coding` only explicitly. | `09` / Root validation | Accepted-design | Yes | Intended root known from brief. | Preserve | ROS-004 | Root validation fixtures and user-authorized resolved path record. |
| INV-006 | Never execute repository files, package managers, hooks, setup scripts, tests, submodule updates, fetches, or checkouts during inventory. | `09` / Traversal and Git | Accepted-design | Yes | Policy only. | Preserve | ROS-002, ROS-004 | Process/command spy; before/after Git/filesystem state. |
| INV-007 | Allowlist structural text needed for classification and cap reads at 256 KiB/file and 10 MiB/repository. | `09` / Content scanning | Provisional | Yes | Limits are arbitrary; deterministic truncation selection/order is unspecified. | Revise/specify | ROS-002, ROS-012 | Define stable traversal/order; boundary/truncation fixtures; calibrate on authorized inventory. |
| INV-008 | Define the separate “metadata limit” referenced for special/large files. | `09` / Traversal | Provisional | No local evidence needed | Specification references a configured metadata limit but supplies no value/schema. | Fix spec | ROS-004, ROS-005 | Config/schema and boundary tests. |
| INV-009 | Detect Git roots, worktrees, branches, dirty categories, remotes, shallow/submodule/sparse/operation state using machine-readable read-only commands. | `09` / Git and dirty-tree detection | Accepted-design | Yes | No repositories inspected. | Implement | ROS-004 | Synthetic repositories for every state; command allowlist and no-lock verification. |
| INV-010 | Treat nested candidates whose Git root is a parent as one project unless explicitly registered. | `09` / Git detection and ambiguity | Accepted-design | Yes | Actual nested structures unknown. | Conditional | ROS-002, ROS-004 | Nested repo/worktree fixtures and human exception record. |
| INV-011 | Redact credentials from remotes and do not choose among multiple remotes automatically. | `09` / Remote detection | Accepted-design | Yes | Actual remotes unknown. | Preserve | ROS-004, ROS-012 | SSH/HTTPS/embedded-token fixtures; ambiguity report. |
| INV-012 | Perform GitHub enrichment only when authorized; use `not_observed` rather than false when unavailable. | `09` / GitHub detection | Accepted-design | Yes | No auth/account evidence. | Conditional | ROS-002 | Auth capability matrix and schema distinction tests. |
| INV-013 | Gate organization-level metadata, runners, apps, secrets, variables, rulesets, and protections behind explicit read scopes/admin authorization. | `09` / GitHub enrichment; `06` approvals | Accepted-design | Yes | These calls can require broad scopes; availability unknown. | Conditional | ROS-002, ROS-020 | Permission-by-field plan; read-only API errors map to `not_observed`. |
| INV-014 | Detect languages/frameworks from manifests/extensions/declarations without importing or executing; retain uncertainty. | `09` / Language and framework detection | Accepted-design | Yes | No stack evidence. | Implement | ROS-002 | Neutral polyglot/conflicting/declared-unused fixtures and confidence rules. |
| INV-015 | Define deterministic scoring before assigning a primary language or family. | `09` / Language detection | Provisional | Yes | Scoring thresholds are absent. | Revise/specify | ROS-002, ROS-007 | Publish rule; compare with human classification; leave null on ambiguity. |
| INV-016 | Treat `AGENTS.md`, active CI, task config, and docs as ordered command evidence, but require approved execution before verification. | `09` / Validation command detection | Accepted-design | Yes | Actual commands unknown. | Preserve | ROS-002, ROS-016 | Record sources/conflicts; user confirms; run only approved command in bounded validation. |
| INV-017 | Inspect Codex instructions/config/hooks/agents/skills structurally without publishing cross-project bodies or executing anything. | `09` / Codex inspections | Accepted-design | Yes | Current artifacts/runtime unknown. | Implement | ROS-002, ROS-006, ROS-012 | Parser/schema fixtures; path/reference checks; redacted reports. |
| INV-018 | Treat unsupported-but-working Codex configuration as preserve-and-reproduce, not auto-remove. | `09` / Ambiguity; `12` | Accepted-design | Yes | Installed version and working behavior unknown. | Preserve | ROS-006 | Capture version; isolated runtime fixture; human migration decision. |
| INV-019 | Parse GitHub workflow YAML compatibly, inventory permissions/triggers/runners/pins/check risks, and do not rewrite before check identity is mapped. | `09` / Workflow inspection | Accepted-design | Yes | Parser library and actual workflows unknown. | Implement | ROS-002, ROS-006, ROS-014, ROS-016 | YAML `on` fixtures; normalized workflow model; before/after check-name/event matrix. |
| INV-020 | Treat documentation drift as a hypothesis unless broken references or version mismatches are deterministic. | `09` / Documentation inspection | Accepted-design | Yes | No documentation inspected. | Preserve | ROS-002, ROS-006 | Link/target/version checks; human semantic review. |
| INV-021 | Establish template lineage only from hashes, markers, history, or human confirmation; divergence never authorizes overwrite. | `09` / Template divergence | Accepted-design | Yes | ZIP now exists, repositories not inspected. | Preserve | ROS-001, ROS-002 | Template hash map; later repository exact/near-match plus history confirmation. |
| INV-022 | Exclude secret-like, binary, customer, log, DB, and large generated content; report only redacted detector fingerprints. | `09` / Confidential exclusions | Accepted-design | Yes | Deny patterns may create false positives and omit legitimate structural DB files. | Calibrate conservatively | ROS-012 | Positive/negative redaction fixtures; local-only false-positive review. |
| INV-023 | Distinguish null, unknown, not-observed, false, absent, and unadopted. | `09` / Schema and ambiguity | Accepted-design | Yes | Explicit schema requirement. | Preserve | ROS-005 | JSON Schema examples and serialization round-trips. |
| INV-024 | Run inventory twice, normalize volatile fields, and resolve nondeterminism before baseline acceptance. | `09` / Baseline | Accepted-design | Yes | No runner exists. | Implement | ROS-002, ROS-004, ROS-012 | Byte/semantic comparison of repeated runs on unchanged fixtures and authorized root. |
| INV-025 | Require human confirmation of identity, active state, sensitivity, family, commands, and canary before adoption. | `09`; `12` | Accepted-design | Yes | All are explicitly unknown. | Preserve | ROS-002, ROS-016 | Signed/recorded confirmation fields and pre-write checklist. |

## Continuous learning and evidence

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| LRN-001 | Treat observations as evidence, not standards, and merged PRs as events rather than proof. | `06` / Goal | Accepted-design | No local evidence needed | Brief confirms unsystematic transfer risk. | Preserve | ROS-017 | Schema/state machine prevents direct observation-to-approval transition. |
| LRN-002 | Collect redacted metadata and references, not secrets, full private source, transcripts, customer data, or cross-repo excerpts. | `06` / Sources | Accepted-design | Yes | Policy only. | Preserve | ROS-012, ROS-017 | Source-specific collectors with denylist/allowlist and leakage tests. |
| LRN-003 | Use deterministic IDs, deduplication, metrics, eligibility, schemas, and dossiers. | `06` / Responsibilities | Accepted-design | Yes | Draft schemas only. | Implement | ROS-017 | Duplicate/reorder/retry fixtures and stable ID tests. |
| LRN-004 | Limit AI to clustering, abstraction, counterexample search, and prose; schema-validate output and deny decision authority. | `06` / Responsibilities and candidate creation | Accepted-design | Yes | No AI execution design, model, budget, or sanitized bundle format exists. | Implement narrowly | ROS-018 | Synthetic/redacted input; invalid output; prompt-injection; approval-field rejection tests. |
| LRN-005 | Require two related observations, explicit nomination, or current authoritative security/schema evidence to create a candidate. | `06` / Candidate creation | Accepted-design | Yes | Threshold is policy, not locally calibrated. | Preserve initially | ROS-017 | Candidate creation rule fixtures and audit trail. |
| LRN-006 | Grade evidence as anecdotal, single-use, replicated, controlled, authoritative-control, or counterevidenced. | `06` / Evidence grades | Accepted-design | Yes | No portfolio evidence exists. | Implement after schema review | ROS-017 | Schema and independent-evidence dedup tests. |
| LRN-007 | Require neutral fixtures, counterevidence, baseline, expected effect, observation window, maintenance/security review, and smallest safe canary. | `06` / Evaluation | Accepted-design | Yes | No candidate or metric baseline exists. | Preserve | ROS-017, ROS-016 | Candidate dossier completeness validation. |
| LRN-008 | Use at least two eligible repositories for normal stable promotion, with the documented one-repo-plus-fixture exception. | `06` / Promotion criteria | Provisional | Yes | Portfolio may not have two eligible repositories per component. | Calibrate/retain exception | ROS-017, ROS-018 | Inventory eligibility counts and controlled fixture quality review. |
| LRN-009 | Observe a canary for at least 10 relevant runs or 28 days, whichever is later, absent approved security urgency. | `06` / Canary | Provisional | Yes | Practicality is an explicit assumption. | Calibrate | ROS-016 | Baseline run frequency and canary cost/latency review. |
| LRN-010 | Keep adoption channels and state transitions explicit and human-approved. | `06` / Channels and ledger | Accepted-design | Yes | Draft schema only. | Implement | ROS-005, ROS-017 | State-machine tests and approval provenance. |
| LRN-011 | Reject or demote patterns with weak portability, excessive exceptions, unsafe ownership, no rollback, or no measurable benefit. | `06` / Rejection and deprecation | Accepted-design | Yes | No actual patterns. | Preserve | ROS-017–ROS-019 | Rule fixtures and quarterly decision review. |
| LRN-012 | Use practical CI/drift/exception/conflict metrics; never auto-promote from speed, tokens, commits, lines, or one PR. | `06` / Measurement | Accepted-design | Yes | Metric access, retention, and usefulness unknown. | Conditional | ROS-017, ROS-018 | Baseline availability and two-period noise/usefulness review. |
| LRN-013 | Keep accepted/rejected decisions and redacted adoption ledger in Git; keep raw logs/traces local or artifact-retained. | `03` / Storage; `06` | Provisional | Yes | Repository/PR identifiers may themselves be confidential; retention undefined. | Revise/specify | ROS-012, ROS-017 | Sensitivity classification, retention, publishability, and redaction tests. |
| LRN-014 | Freeze rollout and generate a forward rollback proposal on canary regression. | `06` / Rollback | Accepted-design | Yes | No canary or causal analysis method exists. | Preserve | ROS-011, ROS-016, ROS-018 | Simulated stop condition and rollback workflow exercise. |

## Migration, rollout, backlog, and completion

| ID | Recommendation | Source file/section | Status provisional | Local validation required | Local evidence if available only from supplied docs | Final disposition provisional | Implementation issue ID | Validation method |
|---|---|---|---|---|---|---|---|---|
| ROL-001 | Execute Phase 0 inventory/template audit before target writes; then RepoOS fundamentals, control-plane fixtures, canary, portfolio rollout, and learning. | `10`; `12` / Sequence | Accepted-design | Yes | Sequence is conceptual; backlog dependency cycles exist. | Revise dependency graph | ROS-001–ROS-020 | Resolve contradictions listed below and publish an executable DAG. |
| ROL-002 | Audit the ZIP without modifying RepoOS or projects. | `10` Phase 0; ROS-001 | Superseded-fact: input present | Yes | ZIP path supplied now; contents unaudited. | Execute | ROS-001 | Safe extraction, full inventory, schema/behavior fixtures. |
| ROL-003 | Inspect current RepoOS and applicable instructions before choosing package language/layout or modifying it. | `10` Phase 1; `12` handoff | Blocked until authorized inspection | Yes | Existing RepoOS state wholly unknown. | Preserve | ROS-003 | Read-only repository and `AGENTS.md` audit; report overlaps and preserve/migrate choices. |
| ROL-004 | Build only minimal RepoOS fundamentals before overlays. | `10` Phase 1 | Accepted-design | Yes | Full package tree risks premature scaffolding. | Preserve | ROS-003–ROS-006, ROS-012 | Install/help/test/schema/redaction primitives; no real overlays or project writes. |
| ROL-005 | Implement control-plane behavior only against neutral fixtures before real projects. | `10` Phase 2; `12` completion boundary | Accepted-design | Yes | No fixture suite exists. | Preserve | ROS-007–ROS-013 | Full unit/integration/migration/rollback/security suite. |
| ROL-006 | Choose one explicitly approved clean low-risk representative canary with verified commands. | `10` Phase 3; `06` | Blocked | Yes | No repository inventory or approval. | Defer until confirmed | ROS-016 | Ranked current-state matrix; human approval; no-behavior adoption PR first. |
| ROL-007 | Use two canary PRs where possible: manifest/lock adoption without behavior change, then one bounded component. | `10` Phase 3; ROS-016 | Accepted-design | Yes | Actual repository behavior and component unknown. | Conditional | ROS-016 | Diff/CI/check-name equivalence; post-merge no-op; rollback exercise. |
| ROL-008 | Roll out one explicit PR per repository; every project becomes adopted, deferred, or excluded. | `10` Phase 4; ROS-019 | Accepted-design | Yes | Active project list unknown. | Conditional | ROS-019 | Portfolio state report, per-repo verification, no-op after merge. |
| ROL-009 | Run only one mutation at a time and at most two read-only plans during rollout. | `10` Phase 4 | Provisional | Yes | Operational capacity is assumed. | Calibrate | ROS-010, ROS-019 | Review/load measurement and conflict avoidance. |
| ROL-010 | Pause on shared regression, repeated conflict, exception rate over 50%, permission expansion, or review overload. | `10` Phase 4; `14` thresholds | Accepted-design with provisional thresholds | Yes | No baseline. | Preserve stop behavior; calibrate numeric threshold | ROS-018, ROS-019 | Simulated triggers and recorded resume decision. |
| ROL-011 | Operate learning only if maintenance saves time; fall back to read-only audit/manual PRs if burden exceeds benefit. | `10` Phase 5; risk R-01 | Accepted-design | Yes | Maintenance budget unknown. | Preserve | ROS-018, ROS-019 | Coarse time accounting for two review periods. |
| ROL-012 | Do not create GitHub issues until actual RepoOS repository and taxonomy are inspected. | `11` status | Blocked | Yes | Issue taxonomy unknown. | Preserve | Pre-backlog action | Read-only issue/label/milestone inspection and mapping table. |
| ROL-013 | Require implementation issues to link controlling decision records and validation evidence. | `11` / Maintenance | Accepted-design | Yes | No actual taxonomy. | Preserve | All issues | PR/issue template and closure audit. |
| ROL-014 | Add a dedicated user-global installer/audit issue before implementing `repoos global *`. | Gap across `03`, `04`, `08`, `11` | Provisional | Yes | Global commands exist in spec but no backlog owner. | Add issue if in scope | GAP—proposed ROS-021 | Define authority, manifests, backup, conflict, install, rollback, and global audit. |
| ROL-015 | Add a dedicated release artifact integrity/retention issue or expand ROS-003/ROS-011 explicitly. | Gap across `03`, `05`, `10`, `11` | Provisional | Yes | Immutable baseline is required but artifact signing/retention/recovery is underspecified. | Add/expand issue | GAP—proposed ROS-022 | Artifact manifest, hashes/signature, publication, cache, retention, offline restore tests. |
| ROL-016 | Keep real portfolio rollout separate from Phase 2 control-plane completion. | `12` / Completion boundary | Accepted-design | Yes | No real implementation yet. | Preserve | ROS-016, ROS-019 | Neutral fixture completion before canary authorization. |

## Internal contradictions and dependency defects

| Finding | Evidence | Impact | Provisional correction |
|---|---|---|---|
| DEP-001: ROS-001 depends on a CLI that ROS-003 has not built, while ROS-003 depends on ROS-001. | ROS-001 validation invokes `repoos validate`; ROS-003 dependency is “ROS-001 findings reviewed.” | Circular dependency blocks an executable Wave 0. | Run template audit with isolated existing parsers/scripts first, or split a ROS-000 audit harness from ROS-003. Do not pretend the future CLI exists. |
| DEP-002: ROS-002 is Wave 0 but depends on ROS-004, which is Wave 1 and depends on ROS-003. | Backlog waves and ROS-002/ROS-004 dependencies; graph has ROS-004 → ROS-002. | The published wave order is not topologically valid. | Either move baseline inventory after the minimal foundation or use a separately reviewed read-only inventory harness and later re-run with the CLI. |
| DEP-003: Phase 0 requires a shared redaction/schema contract, but ROS-002 does not depend on ROS-012 and ROS-012 depends on ROS-003. | `10` Phase 0 parallel rule; ROS-002 and ROS-012 dependencies. | Early inventory could run before the mechanism meant to prevent leakage. | Add a minimal redaction contract/harness before any real inventory; make full ROS-012 follow later. |
| DEP-004: ROS-015 can open a PR only for an applied plan but does not depend on ROS-010 apply/worktrees. | ROS-015 dependencies are ROS-009 and ROS-012; CLI says `open-pr` commits an applied plan. | Backlog permits implementing delivery before the required applied-plan state exists. | Add ROS-010 as a hard dependency, and likely ROS-011 for rollback text if required in every PR. |
| DEP-005: “No project repository writes before ROS-016” can be read as conflicting with ROS-010 apply tests. | Backlog common constraints versus ROS-010 apply scope. | Ambiguous language could block fixture repositories or accidentally permit real targets. | Rewrite as “no real portfolio repository writes before ROS-016; disposable fixtures are allowed.” |
| DEP-006: The handoff allowed unrelated work when ZIP was missing, while ROS-003 formally depends on the audit. | `12` lines 49–52; ROS-003 dependency. | The formal DAG and operational instruction disagree. | Now that the ZIP is supplied, finish ROS-001 first; otherwise define which ROS-003 bootstrap work is audit-independent. |
| DEP-007: Portfolio rollout depends on ROS-018 scheduled learning review even though core adoption safety does not. | ROS-019 dependency is successful ROS-016 and ROS-018 review. | Can unnecessarily delay safe portfolio adoption and couples core sync to optional AI/scheduling. | Make ROS-018 optional for ROS-019 unless continuous-learning automation is an explicit rollout objective. |
| SPEC-001: `status` references `--fail-on`, but the option is not specified. | `08` `status` versus global options. | Machine contract is incomplete. | Specify accepted conditions, combinations, and exit-code behavior. |
| SPEC-002: Rollback command combines planning and applying without a crisp approval switch. | `08` `repoos rollback`. | A safety-critical command can be misread or implemented with an unsafe default. | Make planning default and require an explicit verified plan plus apply flag/action. |
| SPEC-003: Multi-file “atomic apply” is promised without a transaction/journal algorithm. | `08` apply; ROS-010 acceptance. | False atomicity could leave partial state. | Define journal/backup/rename ordering and fault-injection guarantees. |
| SPEC-004: Baseline artifacts are “immutable” but integrity, signing, retention, garbage collection, and disaster recovery are unspecified. | `03` lock; `05` baseline/version; `10` release criteria. | Updates and rollback fail if artifacts disappear or are replaced. | Add an artifact contract and issue before first prerelease consumer. |
| SPEC-005: Plain-text managed sections are allowed, but only an HTML/Markdown marker grammar is shown. | `03` managed sections; ROS-008. | Ambiguous parsers can corrupt files. | Limit v1 to Markdown or specify per-format comment grammar. |
| SPEC-006: Inventory uses a “configured metadata limit” that is not defined. | `09` safe traversal. | Implementations may diverge or read unexpectedly large entries. | Add a config/schema field and default. |
| SPEC-007: Candidate family and language classification require evidence but deterministic scoring/eligibility grammar is not specified. | `09` language; ROS-007 small grammar. | Different implementations can make different classifications. | Publish minimal predicate grammar and confidence/scoring rules; human confirmation remains mandatory. |
| SPEC-008: Pause controls exist in tracked config, local state, environment, and GitHub variables without a full precedence/running-job contract. | `07` pause and kill switch. | Conflicting state or stale checkouts can give false assurance. | Specify strict precedence, propagation, already-running behavior, and status reporting. |
| SPEC-009: GitHub-to-RepoOS “ingestion queue” is named but no transport exists and a service is explicitly deferred. | `07` event table; `03` deferred service. | Observation collection cannot be implemented as written. | Select a minimal artifact/pull/dispatch mechanism with idempotency and authentication. |
| SPEC-010: Global installer commands are specified without a corresponding schema, ownership/migration design, or backlog issue. | `03` Layer 1; `08` global commands; `11` backlog. | High-blast-radius functionality can slip in without adequate review. | Defer and create ROS-021 if the user explicitly scopes it in. |

## Unsupported or version-sensitive assumptions

| Assumption | Evidence status | Required validation |
|---|---|---|
| Python 3.11+ is available and preferable. | Explicitly provisional in D-004. | Inspect current RepoOS and runtime; clean install smoke test. |
| At least two repositories share a meaningful component. | Assumption in `14`; no local evidence. | Bounded inventory and human family confirmation. |
| All relevant projects use Git and can accept PRs. | Assumption in `14`. | Detect Git/local-only/remote/permissions per project. |
| A clean, low-risk, representative canary exists. | Assumption in `14`. | Inventory, command verification, sensitivity review, explicit approval. |
| GitHub-hosted runners cover initial needs. | Assumption in `14`. | Inspect workflows, runtimes, private resources, and runner limits. |
| Current OpenAI/GitHub docs match installed/account behavior. | Phase 1 research only. | Capture installed Codex version; schema/runtime fixtures; GitHub plan/API capability checks. |
| Full-SHA private reusable workflows are accessible to all intended consumers. | Official model cited; account/org visibility unknown. | Caller fixtures under actual ownership/visibility. |
| Dependabot can update the intended action/reusable-workflow pins in current setup. | Official capability cited; configuration absent. | Fixture/repository test after access model is known. |
| 28 days/10 runs and proposed cadence/limits are practical. | Explicit initial defaults. | Baseline run frequency, patch sizes, cost, and review capacity. |
| Manual review for three or four repositories remains manageable. | Assumption in `14`. | Canary and two-cycle burden measurement. |
| Codex scheduled tasks/worktrees and `codex exec` are available, authenticated, and affordable. | Official docs cited only. | Local version/auth/sandbox/budget validation. |
| Organization `.github`, custom properties, rulesets, required workflows, GitHub Apps, variables, and runner groups are available. | Explicitly unknown. | Read-only owner/plan/permission inventory. |
| Immutable RepoOS release artifacts will remain available offline. | Design assertion only. | Artifact integrity/retention/recovery implementation and tests. |

## Missing migration or rollback detail

| Gap | Affected requirement | Needed before |
|---|---|---|
| No global-file adoption/migration/rollback contract. | User-global checksum installer and `repoos global *`. | Any write under `$CODEX_HOME` or `$HOME/.agents`. |
| No release artifact integrity, signing, retention, or restore protocol. | Locks and three-way baselines. | First consumable release. |
| No explicit project-ID/folder-move migration. | Stable IDs and registry. | Adoption of repositories likely to move/rename. |
| No formal schema compatibility/support window for alpha releases. | Manifest/lock/component versions. | More than one released schema version. |
| No exact migration ordering/transaction semantics across multiple components. | Apply/migration graph. | First multi-component migration. |
| No repair path for locally edited generated files beyond stopping. | Generated ownership. | First generated component adoption. |
| No explicit transfer procedure for managed file → repository-owned and reverse adoption beyond high-level leave steps. | Overlay join/leave. | First demotion, exclusion, or ownership transfer. |
| No external GitHub setting rollback implementation; only manual reporting principle. | Rulesets, variables, apps, runners. | Any ROS-020 mutation. |
| No already-running-job behavior for pause/kill controls. | Automation rollback/stop. | Scheduled jobs. |
| No ingestion queue replay/retention/poison-record procedure. | Learning automation. | GitHub event collection. |

## Complexity candidates to defer or simplify

| Candidate | Why it may be unnecessary initially | Provisional action |
|---|---|---|
| Full 29-module package tree. | Wave 1 needs only CLI, errors, safe paths/Git, schemas, redaction, and reporting. | Create modules only when issue-owned behavior exists. |
| Three separate pause mechanisms plus an external variable. | Valuable eventually, but precedence and propagation add failure modes. | Start with environment/local pause for local CLI and one explicit GitHub variable; expand only with tests. |
| AI semantic review before a real evidence volume exists. | Three/four repositories may not generate enough observations. | Implement record schemas first; enable scheduling after canary data. |
| ROS-018 as a hard prerequisite for portfolio rollout. | Safe sync does not require automated learning. | Make optional unless requested. |
| Managed sections in v1. | No proven unavoidable case; parser/ownership risk is material. | Defer until inventory identifies a concrete text-only need. |
| Copier as an internal renderer. | Adds a second model before component needs are known. | Audit ZIP and implement literal rendering first. |
| User-global installer. | High blast radius and outside core project synchronization. | Separate scope and issue; do not include in initial control plane. |
| GitHub App. | Three/four repositories may work with explicit local auth and same-repo tokens. | Add only after recurring cross-repo writes justify it. |
| Organization governance features. | Account/plan may not support them and repository PRs provide the initial boundary. | Defer to ROS-020. |
| SQLite, service, dashboard, event bus, vector DB, self-hosted runner. | Explicitly no measured need. | Keep deferred. |

## Authorization-dependent actions

| Action | Required authority |
|---|---|
| Inspect `~/Coding` repositories or the current RepoOS repository. | Explicitly approved root/scope plus applicable repository instructions. |
| Read user-global Codex files. | Separate explicit user-global audit approval. |
| Execute repository validation commands. | Human confirmation that each exact command is authoritative and safe. |
| Read GitHub repository/org governance metadata. | Authorized read scopes; admin-only fields require explicit approval. |
| Create issues, branches, commits, pushes, or pull requests. | Confirm repository/taxonomy; issue-linked scope; explicit external-write action. |
| Select a canary or change a repository classification/risk/sensitivity. | Human confirmation. |
| Write `.repoos` files or adopt a component. | Accepted inventory/ownership map, clean state, verified plan, rollback, and exact approval. |
| Publish a RepoOS release with migrations. | Human release approval and passing migration/rollback/artifact checks. |
| Bulk-open update PRs or promote stable/required patterns. | Explicit portfolio approval. |
| Change rulesets, required checks, variables, secrets, runner access, GitHub App permissions, or organization defaults. | Separate admin issue and explicit approval per mutation class. |
| Install or change global Codex files/plugins/skills/hooks/agents. | Exact target approval, backup/adoption/rollback plan. |
| Enable AI semantic processing on repository evidence. | Approved allowlist, redaction policy, model/budget, and confidentiality boundary. |

## Coverage statement

This ledger covers the Phase 1 packet’s normative architecture, classification, distribution, learning, automation, CLI, inventory, migration, backlog, decision, risk, and handoff requirements. Repeated statements were consolidated into one controlling row with all relevant issue mappings. No row is evidence that a repository currently conforms, violates, or needs migration; those dispositions require the authorized Stage 0 inventory and template audit.
