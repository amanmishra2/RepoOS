# RepoOS

RepoOS is a deterministic control plane for safely inspecting, validating, and planning operating-layer changes across independently owned repositories.

It is not a static template copier, monorepo parent, runtime dependency, autonomous mutation service, or organization-governance controller.

## Current status

Version `0.1.0` is an initial foundation:

- bounded, first-level discovery and metadata inventory;
- public-safe output redaction;
- Git dirty-state and common-worktree inspection;
- strict schemas for registry, manifest, learning, adoption, and update plans;
- deterministic validation, diff, audit, status, doctor, update-check, planning, and reporting commands;
- pause and per-repository lock primitives;
- fixture-only explicit file planning;
- dry-run apply revalidation.

Apply execution is intentionally disabled in `0.1.0`. RepoOS does not commit, push, open PRs, merge, change GitHub settings, register runners, or install user-global Codex files.

## Quick start

Use the source tree without installing:

```bash
PYTHONPATH=src python3 -m repoos --help
PYTHONPATH=src python3 -m repoos --format json doctor
PYTHONPATH=src python3 -m repoos --format json validate --all
python3 -m pytest
```

Install for development when dependencies are available:

```bash
python3 -m pip install -e ".[dev]"
repoos --help
```

Discovery defaults to `~/Coding`, scans direct child directories only, aliases private identities by default, and never updates the registry implicitly:

```bash
repoos --format json discover
repoos --privacy local --format json inventory --project /explicit/project
```

## Safety contract

- Unknown ownership is repository-owned.
- Similarity never transfers ownership.
- Discovery and analysis are read-only.
- A plan is not authorization.
- Mutation requires an explicit target, clean common-Git state, current base, ownership, pause check, lock, limits, backup, journal, validation, and rollback.
- No portfolio-wide write command exists.
- Private mappings, raw Git evidence, secrets, databases, logs, and project content do not belong in this public repository.
- AI may propose or summarize; deterministic code and humans enforce and approve.

The authoritative policy is [Command safety](policies/security/COMMAND_SAFETY.md).

## Architecture and operations

- [Validated architecture](docs/implementation/VALIDATED_ARCHITECTURE.md)
- [Validated migration plan](docs/implementation/VALIDATED_MIGRATION_PLAN.md)
- [File ownership](docs/implementation/FILE_OWNERSHIP_MODEL.md)
- [Automation boundaries](docs/implementation/AUTOMATION_BOUNDARIES.md)
- [CLI reference](docs/reference/CLI.md)
- [Verification](docs/verification.md)

## Portfolio state

The Phase 2 baseline found 14 first-level directories, including four dirty Git working trees, two conditional clean working trees, and seven non-Git roots. RepoOS was the only low-ambiguity implementation target. A downstream canary is only provisionally nominated and remains blocked pending explicit confirmation.

Committed reports use aliases because RepoOS is public. See [portfolio baseline](reports/baseline/portfolio-inventory.md).

## GitHub Actions

RepoOS CI uses GitHub-hosted ephemeral runners, read-only token permissions, concurrency cancellation, timeouts, and full-SHA-pinned third-party actions. Self-hosted runners and organization settings are separate authorization-dependent decisions.

## Core principles

1. Repository autonomy is the default.
2. Every behavioral claim needs a semantic test.
3. Every mutation needs preview, ownership, limits, backup, and rollback.
4. Every repeated failure should become a proportionate guardrail.
5. Every external write needs exact authority.
6. Every completion claim includes evidence and remaining limitations.
