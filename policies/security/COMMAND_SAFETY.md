# Command safety policy

Status: policy source, not executable hook or rules enforcement

RepoOS separates durable safety policy from active runtime enforcement. The current hook configuration is intentionally empty until a command hook can be proven against current event fixtures without blocking legitimate work.

## Prohibited implicit behavior

RepoOS must not:

- delete, reset, clean, stash, or switch a repository to resolve user changes;
- operate outside an explicit configured root or repository;
- execute a repository hook, build, test, or validation command during discovery;
- print secret values or publish private portfolio identifiers;
- mutate a dirty, conflicted, stale, paused, locked, or ownership-ambiguous target;
- commit, push, merge, open a PR, or change GitHub settings as part of apply;
- install user-global Codex files without exact authorization;
- interpret a plan or AI recommendation as approval.

## Required mutation gates

An implemented mutation path requires explicit target, clean common-Git state, current base, deterministic plan, path containment, ownership, lock, pause check, maximum-change limits, backup, journal, validation, restoration on failure, and a human-reviewed result.

## Future executable rules

Any future `.codex/rules/*.rules` file must use current `prefix_rule(...)` syntax, pass `codex execpolicy check` positive and negative fixtures, and remain narrower than this policy. Hooks are defense in depth and cannot replace core CLI validation.
