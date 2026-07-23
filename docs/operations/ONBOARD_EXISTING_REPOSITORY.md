# Onboard an existing repository

Real onboarding is not enabled in `0.1.0`.

Required sequence:

1. Inventory read-only and confirm identity, lifecycle, sensitivity, commands, family, and ownership.
2. Require a clean common-Git state and trustworthy base.
3. Create a manifest-only plan with no behavior change.
4. Review the plan and repository diff.
5. Apply on an isolated issue-linked branch/worktree only after explicit approval.
6. Run repository-owned validation.
7. Record adoption and prove a post-adoption no-op.
8. Demonstrate forward rollback before another component.

See [CANARY_SELECTION.md](../implementation/CANARY_SELECTION.md).
