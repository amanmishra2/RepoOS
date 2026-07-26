# P08 project-family assessment

Date: 2026-07-23

## Evidence-backed profile

| Dimension | P08 |
|---|---|
| Primary language | Python |
| Supported runtime | Python 3.11+ |
| Application type | Local-first CLI and evidence-oriented application |
| Packaging | Setuptools with `pyproject.toml`; editable pip development flow |
| Runtime dependency shape | Small; YAML support is the declared runtime dependency |
| Test framework | Pytest, offline by default |
| Format / lint / type | Ruff format, Ruff lint, MyPy |
| Command orchestration | Make |
| Deployment | Local CLI; no hosted deployment model is documented |
| CI | GitHub-hosted Product CI and AgentOps workflows |
| Agent infrastructure | Mature repository-local instructions, agents, issue packets, policies, and contract validators |
| Documentation model | Documentation-heavy, versioned issue/contract/ADR system |
| Data behavior | Public/reference datasets plus future local personal evidence; live sources disabled |

## Classification

Primary classification: **Python CLI/application**.

Secondary capabilities: **documentation-heavy repository**, **offline evidence/data processing**,
and **mature repository-local AgentOps**. Those capabilities do not make P08 an AI-agent
infrastructure project or a live data-ingestion service.

P08 is explicitly standalone: its instructions identify the repository as its sole authority and
reject active sibling-repository dependencies or a shared runtime package during the current
product phase.

## Overlay decision

RepoOS has no validated real project-family overlay. One repository is not a family, and no
two-consumer evidence has been approved. The first P08 manifest should therefore use:

```yaml
project_family: null
additional_overlays: []
```

This is not a permanent rejection of a `python-cli` family. It is a fail-closed decision until at
least two consumers, deterministic predicates, ownership, neutral fixtures, and human membership
approval exist.

## Repository-local exceptions

The following remain P08-owned even if a future generic Python overlay is created:

- product and trust invariants;
- issue/packet lifecycle and one-issue-per-worktree rules;
- separate Product CI and AgentOps conclusions;
- source/provider access and retention policy;
- append-only evidence contracts;
- project-specific architecture checks and reason registries;
- all business logic, data contracts, workflows, and validation commands not explicitly adopted.

Web deployment, shared runtime, live-provider, organization-governance, and broad workflow overlays
are inapplicable to the first canary.
