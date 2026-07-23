# Validated decision log

Date: 2026-07-23

| ID | Decision | Local evidence | Status |
|---|---|---|---|
| D2-001 | RepoOS becomes a deterministic control plane, not a static copy template. | ZIP and current RepoOS both lack versioned ownership/update/rollback. | Accepted |
| D2-002 | Keep the four-layer model, but create no overlay without two confirmed consumers. | Portfolio similarities exist, but identity/family classification is not human-confirmed. | Accepted with modification |
| D2-003 | Keep private portfolio mappings outside the public repository. | RepoOS is public; project identity and repository metadata may be confidential. | Accepted |
| D2-004 | Use Python 3.11+ package semantics and stdlib-first CLI design. | RepoOS already contains Python tools; Python 3.13 is installed. | Accepted |
| D2-005 | Start at version `0.1.0`; use YAML desired state and JSON generated state. | Small portfolio and reviewability favor file contracts over a database. | Accepted |
| D2-006 | Defer managed sections. | No unavoidable inventory case; parser/ownership risk is material. | Deferred |
| D2-007 | Unknown ownership is repository-owned; similarity never transfers ownership. | Independent repositories have legitimate divergent safety and validation rules. | Accepted |
| D2-008 | Discovery and inventory are bounded, metadata-first, and read-only. | Four dirty trees and complex linked worktree state make implicit writes unsafe. | Accepted |
| D2-009 | Use GitHub-hosted runners for initial RepoOS CI. | RepoOS is public and no self-hosted runner is registered; current PR workflow targets a persistent Mac. | Accepted |
| D2-010 | Full-SHA pin all third-party actions and declare least privilege. | Current mutable tags and missing permissions violate the Phase 1 security boundary. | Accepted |
| D2-011 | Strict RepoOS validation must not equate runtime acceptance with schema validity. | Installed `codex doctor` did not reject unsupported project tables. | Accepted |
| D2-012 | Replace false hook/rule enforcement with tested behavior or no claim. | Current hook router ignores payloads and prose rules are not executable policy. | Accepted |
| D2-013 | AI remains advisory and cannot approve, enforce, mutate, or promote. | Deterministic safety is required; portfolio evidence volume is not established. | Accepted |
| D2-014 | Use an environment pause plus local state-file pause initially. | More pause channels add unproven propagation and precedence complexity. | Accepted with modification |
| D2-015 | P08 is the provisional canary candidate, not an approved target. | It is the strongest clean independent candidate, but its upstream is gone and worktree metadata needs reconciliation. | Requires authorization |
| D2-016 | P04-B is not an isolated canary. | It shares P04-A’s dirty common Git directory and is behind its upstream. | Rejected |
| D2-017 | Scheduled learning does not gate core rollout. | Safe update/rollback does not depend on AI or scheduled review. | Accepted with modification |
| D2-018 | No GitHub issues are created in this run. | RepoOS has no existing taxonomy; the brief requires explicit authorization for issue creation. | Accepted |
| D2-019 | User-global installation, GitHub governance, and release publication are separate authorization domains. | Their blast radius and rollback differ from repository content changes. | Accepted |
| D2-020 | Do not mechanically import the supplied ZIP. | RepoOS is richer; the ZIP contains obsolete config, agents, hooks, and whole-tree copy behavior. | Accepted |

## Supersession

These decisions supersede local-evidence-dependent Phase 1 assumptions. Phase 1 rationale remains historical context and is not edited.
