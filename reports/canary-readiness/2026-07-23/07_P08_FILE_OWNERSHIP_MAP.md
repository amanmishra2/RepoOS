# P08 file-ownership map

Date: 2026-07-23
Status: proposal only; no ownership transfer approved

RepoOS's authoritative default applies: unknown and unadopted paths are repository-owned.

## Operating-layer boundary

| Path | Current state and purpose | Proposed ownership | First canary? | Reason |
|---|---|---|---|---|
| `AGENTS.md` | Present; authoritative repository instructions | `repository_owned` | No | Project trust, issue, and stop rules are local authority |
| Nested `AGENTS.md` files | None observed | `repository_owned` if later created | No | No adoption evidence |
| `.codex/config.toml` | Present; repository-specific Codex configuration | `repository_owned` | No | No explicit extension or transfer |
| `.codex/hooks.json` | Absent | `repository_owned` if later created | No | Adding hooks expands executable surface |
| `.codex/agents/**` | Present; repository roles | `repository_owned` | No | Coupled to local issue and product contracts |
| `.agents/skills/**` | Absent | `repository_owned` if later created | No | No validated shared consumer |
| `.github/workflows/**` | Present; Product CI, AgentOps, and repository automation | `repository_owned` | No | Structured workflow governance is high-impact and actively changing |
| `.github/ISSUE_TEMPLATE/**` | Present | `repository_owned` | No | Coupled to local issue taxonomy |
| `.github/pull_request_template.md` | Present | `repository_owned` | No | Coupled to local review contract |
| `README.md` | Present; product and contributor entry point | `repository_owned` | No | Product status and scope |
| `Makefile` | Present; authoritative local gates | `repository_owned` | No | Validation commands remain target authority |
| `pyproject.toml` | Present; package and tool configuration | `repository_owned` | No | Product packaging and tool policy |
| `docs/verification.md` | Present; validation authority | `repository_owned` | No | Must not be normalized centrally |
| `docs/issue-map.md` and `docs/issues/**` | Present; versioned issue state and contracts | `repository_owned` | No | High-churn repository governance |
| `docs/orchestration/**` | Present; execution plans and context packets | `repository_owned` | No | Repository-specific orchestration |
| `MEMORY.md` | Present; durable project facts | `repository_owned` | No | Private repository knowledge |
| Workflow-audit scripts and tests | Present under repository scripts/tests | `repository_owned` | No | Product-specific contract enforcement |
| `src/**`, `schemas/**`, `data/**`, product tests | Present | `repository_owned` | No | Business logic, contracts, reference data, and product proof |
| `.repoos/project.yaml` | Absent; proposed reviewed adoption manifest | `requires_manual_migration`, then `repository_owned` | Yes, alone | Desired state belongs to the target; current engine cannot bootstrap it |
| `.repoos/local/**` | Absent from Git by policy | `excluded` | Never | Private mappings, authorizations, and state must not be committed |
| `.repoos-fixture` | Absent | `excluded` / prohibited | Never | A real repository must not gain fixture authority through a marker |
| `.env*`, keys, credentials, personal config, databases, local data, output, digests | Ignored path classes | `excluded` | Never | Secret, personal, runtime, or generated local state |

No managed section is proposed. No RepoOS markers exist, and structured YAML/TOML section editing is
unsupported.

## Candidate RepoOS components

| Candidate | Current format/divergence | Proposed source and mode | Local content to preserve | Conflict risk | Adoption value | First transaction |
|---|---|---|---|---|---|---|
| Adoption manifest at `.repoos/project.yaml` | File is absent | Dedicated `real-canary-manifest-bootstrap` operation, not yet implemented; resulting file remains repository-owned desired state | P08's exact validation commands, `project_family: null`, empty overlays/components, and all mutation permissions denied initially | Low file conflict; high authority significance | High: establishes explicit identity, ownership, and permission boundary | Yes; it must be the only target file |
| Generated ownership-boundary note | No approved file or source exists | Possible future generated Markdown component | All repository-specific exceptions | Low product risk but unnecessary for bootstrap | Medium | No |
| RepoOS drift workflow | No approved file; existing workflows are active and repository-owned | Possible future generated full file only | Current CI split, permissions, pins, and repository automation | High workflow-policy conflict | Unproven | No |

No ordinary managed or generated component qualifies for the first canary. After a successful
manifest-only step and no-op proof, one separate low-risk component may be proposed; it is not
selected or authorized by this audit.
