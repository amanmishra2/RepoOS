# Folder structure map

```text
.
├── .agents/skills/           # Candidate repository skills
├── .codex/                   # Minimal project config, agents, empty hook registry
├── .github/                  # Issue/PR forms and pinned hosted CI
├── .repoos/project.yaml      # RepoOS self-manifest
├── docs/
│   ├── architecture/         # Stable architecture explanations
│   ├── implementation/       # Validated Phase 2 decisions and backlog
│   ├── operations/           # Operator runbooks
│   └── reference/            # CLI/schema/manifest/registry contracts
├── learning/                 # Git-tracked redacted learning records
├── policies/security/        # Durable safety policy
├── registry/                 # Public-safe project registry
├── reports/baseline/         # Public-safe Phase 2 evidence
├── schemas/                  # JSON Schema Draft 2020-12 contracts
├── src/repoos/               # Deterministic CLI and safety primitives
├── tests/                    # Unit, integration, schema, Codex, CLI, security
└── tools/agentops/           # Legacy informational helpers pending retirement
```

The map is validated against actual structure during review. No `docs/decisions/` or `docs/specs/` directory is claimed.
