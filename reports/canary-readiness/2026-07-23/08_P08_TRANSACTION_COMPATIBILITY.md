# P08 transaction-engine compatibility

Date: 2026-07-23
RepoOS version assessed: `0.2.0`

## Classification

**Ready after a small, bounded RepoOS enhancement.**

The transactional core is suitable for a one-file bootstrap, but the eligibility and bootstrap
surface is not. The enhancement is security-critical and must be proved on synthetic repositories
before P08 is reconsidered.

## Current product gates

RepoOS planning currently:

1. requires a regular `.repoos-fixture` marker;
2. rejects an unmarked real repository with an authorization-required error;
3. requires `.repoos/project.yaml` to exist before it can build a plan; and
4. requires the existing manifest to set `automation_permissions.apply: true`.

P08 has neither marker nor manifest. Adding a fixture marker would not authorize a real target and
is explicitly prohibited. The current engine therefore cannot create the manifest-only adoption
proposal described by ROS-011.

## Proposed minimal operation

The first canary needs one full-file creation:

```text
.repoos/project.yaml
```

It does not require deletion, force behavior, a managed section, multiple sections, a
structured-file patch, a whole-tree copy, or a business-logic edit. The resulting manifest should
initially keep apply, commit, push, and external settings denied.

## Existing controls that can be reused

- exact target root and common-Git identity;
- HEAD and target-status fingerprint;
- immutable plan digest and RepoOS version binding;
- approved-path-only backup with an explicit “file did not exist” record;
- rendered-state validation and atomic file creation;
- conservative one-file safety limits;
- process-visible common-Git lock;
- bounded no-shell validation commands;
- automatic rollback that removes a transaction-created file;
- manual, integrity-checked, idempotent rollback;
- public-safe observation records.

For this one-file scope, existing backup and byte-for-byte rollback semantics are sufficient after
the authorization/bootstrap gap is closed.

## Worktree effect

Both P08 worktrees share one common-Git lock identity. RepoOS can serialize its own operations, but
the current target-status check does not turn active untracked work in a sibling worktree into an
approved risk. A real-canary gate must bind the complete assessed worktree set or require an
explicit, fresh acknowledgement of every sibling state. P08's current secondary worktree would
fail that gate.

Validation itself can run without secrets: both documented gate families passed on the live
default-branch tracked snapshot.

## Smallest separate RepoOS issue

Proposed title: **Add an approved real-repository manifest-bootstrap gate**

Bounded scope:

- add a dedicated adoption-bootstrap plan type for exactly one absent `.repoos/project.yaml`;
- require an ignored local authorization receipt binding alias, canonical target/common-Git
  fingerprints, live base/HEAD, assessed worktree set, allowed path, expiry, and plan digest;
- bind a trusted RepoOS source commit or wheel digest in addition to version `0.2.0`;
- validate the proposed manifest while allowing its initial `apply` permission to remain false;
- refuse `.repoos-fixture` as real-repository authority;
- revalidate all target and sibling-worktree fingerprints before lock, backup, and write;
- reuse existing one-file backup, limit, validation, observation, and rollback machinery;
- add only synthetic non-fixture Git tests for absent-manifest creation, stale authorization,
  sibling drift, dirty sibling, rollback, repeat apply, and path/symlink refusal;
- expose plan and dry-run before execute, with execute still requiring a second explicit approval.

Out of scope:

- executing against P08 or any real repository;
- ordinary component apply;
- Git commit, branch, push, pull request, or GitHub mutation;
- deletion, force, structured section patching, broad rollout, or global installation.

Acceptance requires the full RepoOS suite, installed-wheel smoke, no-write dry-run proof, automatic
and manual rollback proof, and a staged public-safety scan. The issue must be completed separately
before ROS-011 can perform a real manifest bootstrap.
