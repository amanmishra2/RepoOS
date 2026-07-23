# Candidate reusable patterns

Candidates are not centrally owned until eligibility, ownership, neutrality, rollback, and at least two appropriate consumers are confirmed.

| Pattern | Evidence | Candidate layer | Guardrail |
|---|---|---|---|
| Short `AGENTS.md` entry map | Multiple governed roots | Portfolio baseline | Product rules remain local |
| Explicit source-of-truth hierarchy | P02, P06, P08, P09 | Portfolio baseline | Repositories may rank contracts differently |
| Minimal context loading | P02, P04, P09 | User-global or baseline | Preserve task-specific required reads |
| Evidence-based final handoff | P02, P04, P07, P08 | Portfolio baseline | Exact format may remain local |
| Operating docs change with tools/hooks/workflows | P04, P06 | AgentOps capability | No forced edits in dirty repositories |
| Offline-by-default/live boundary | P04, P08 | Safety capability | Product-specific live policy remains local |
| Stop on authority, secrets, or live-access ambiguity | P08, P09 | Safety capability | Never weaken stricter local restrictions |
| Issue/branch/ownership discipline | P08, P09 | GitHub capability | Branch naming remains local |
| Failure taxonomy and evidence handoff | P08 | AgentOps capability | Calibrate categories per repository |
| Nested-project boundary declarations | P02, P05, P09 | Documentation capability | Honor nested `AGENTS.md` precedence |
| Issue/PR intake skeletons | Supplied ZIP and RepoOS | Bootstrap seed | Validate labels and repository fit |
| Plan/retrospective templates | Supplied ZIP and RepoOS | Optional seed | Repository owns decision history |

## Not global candidates

Do not promote product scope, database choices, live-service permissions, exact validation commands, package-manager assumptions, runner labels, branch prefixes, data-retention rules, or repository-specific safety policies.

## Promotion gate

A candidate needs two or more confirmed consumers, explicit owner, testable eligibility, version, migration/rollback, neutral fixtures, confidentiality classification, and human approval. Until then it stays repository-local or experimental.
