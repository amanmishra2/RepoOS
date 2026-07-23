# GitHub workflow audit

Date: 2026-07-23

## RepoOS local workflow

The existing `.github/workflows/agentops.yml`:

- runs pull-request code on `[self-hosted, macOS, ARM64]`;
- uses mutable `actions/checkout@v4` and `actions/setup-python@v5` references;
- has no explicit least-privilege `permissions`;
- has no concurrency group or job timeout;
- combines pull-request, manual, and scheduled behavior;
- runs shallow presence/syntax checks rather than semantic tests;
- does not run the documented weekly target on its schedule.

This conflicts with the Phase 1 boundary, which defers self-hosted runners and requires immutable action pins, explicit permissions, bounded concurrency, and separate read/write trust boundaries.

## RepoOS GitHub evidence

Read-only GitHub inspection on 2026-07-23 confirmed:

- the repository is public and active with `main` as default;
- no self-hosted runner is currently registered;
- the active workflow is the AgentOps workflow;
- recent workflow history includes failures/cancellations, including a failure during `actions/setup-python@v5`;
- repository Actions allow all actions and do not require SHA pinning;
- no repository ruleset is configured and `main` is not branch-protected;
- no GitHub issues currently exist.

These are observations, not authorization to change settings. No runner, ruleset, protection, secret, variable, issue, or organization setting was changed.

## Validated initial disposition

- Replace the RepoOS workflow with GitHub-hosted, read-only CI.
- Pin every third-party action to a verified full commit SHA with a readable version comment.
- Declare read-only permissions, concurrency, timeout, and explicit commands.
- Keep project-specific CI as repository-local or a future eligibility-gated overlay.
- Do not create organization reusable workflows, rulesets, required workflows, runner registrations, or downstream workflow changes without explicit authorization.

## Portfolio limitation

Other repositories’ workflow YAML was not deeply inspected in this bounded pass. No portfolio-wide claim about pinning, permissions, runner labels, concurrency, Dependabot, CODEOWNERS, or reusable workflow adoption is made.
