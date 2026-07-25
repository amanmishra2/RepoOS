# Next P08 canary prompt

Use this prompt only in a new, separately authorized run. Do not execute it during the RepoOS
manifest-bootstrap implementation run.

````text
# P08 Isolated Manifest-Bootstrap Canary

Act as the RepoOS canary operator and transaction-safety reviewer.

Authority:

- the committed RepoOS `0.3.0` implementation and its authoritative operations/reference docs;
- reports/canary-readiness/2026-07-23/;
- reports/canary-hygiene/2026-07-23/;
- reports/manifest-bootstrap/2026-07-25/NEXT_P08_CANARY_PROMPT.md;
- the ignored, schema-valid RepoOS private overlay for resolving P08 locally;
- the target repository's current instructions from revalidated GitHub `main`.

Objective:

Bootstrap exactly `.repoos/project.yaml` in a newly created isolated P08 worktree from current
GitHub `main`; validate it; demonstrate transaction rollback; stop for approval; reapply; validate;
and create one local manifest-only commit. Do not push or open a pull request.

Authoritative preservation decision:

- P08-W2 contains active or potentially active implementation work.
- Preserve P08-W2 in place.
- Do not inspect its untracked file bodies.
- Do not archive, delete, clean, prune, move, reset, stash, repair, or modify it.
- Do not use P08-W2 as the canary target.
- Exclude P08-W2 from RepoOS writes.
- Exclude its untracked names/content from committed reports and learning records.
- Leave P08-W1 unchanged and do not use it as the canary target.
- Do not run target validation commands in P08-W1 or P08-W2.

Use only public aliases in RepoOS artifacts. Do not print private paths, repository names, remotes,
private SHAs, credentials, authorization contents, or protected untracked names/bodies.

Required sequence:

## 1. Verify RepoOS and the installed artifact

1. Verify the RepoOS repository, clean status, committed `0.3.0` version surfaces, and the guarded
   manifest-bootstrap commit.
2. Build with `python3 -m build --no-isolation`.
3. Install the exact wheel into a temporary isolated environment or otherwise prove the command is
   running from that wheel, not an uncommitted source tree.
4. Run installed-wheel `repoos --version`, `repoos --format json doctor`, and
   `repoos --format json validate --all`.
5. Keep manifest input, plan, authorization, transaction state, backup, and logs in a new
   local-only directory outside every P08 worktree and outside P08's common Git directory.

Stop if RepoOS is dirty, the artifact/version/commit is not exact, or the local state boundary
cannot be proven.

## 2. Revalidate P08 read-only

1. Resolve P08 only through the ignored private overlay; confirm the overlay remains ignored and
   untracked.
2. With read-only GitHub access, mutate no remote resource. Revalidate the canonical private
   repository, access, current GitHub default branch `main`, exact current `main` commit, open pull
   requests that could overlap `.repoos/project.yaml`, and current required workflow definitions.
3. Revalidate P08-W1 and P08-W2 as the two pre-existing registered worktrees using Git metadata
   only. Record public-safe hashes/counts/classifications, never raw private paths, branch names,
   untracked names, or file bodies.
4. Confirm neither pre-existing record is locked, malformed, prunable, missing, duplicated, or
   otherwise ambiguous. Do not run prune, including automatic cleanup.
5. Record a local-only before snapshot of each pre-existing worktree's HEAD, branch fingerprint,
   tracked-change count, untracked-entry count, status fingerprint, index fingerprint, lock state,
   and registration fingerprint.
6. Read the target repository instructions from the exact tracked GitHub `main` tree before
   creating the canary. Do not read P08-W2 untracked content.
7. Confirm the exact live `main` object already exists locally. If it does not, fetch only the
   advertised `refs/heads/main` object with no destination ref, no `FETCH_HEAD`, no tags, no prune,
   no submodules, and no automatic maintenance. Prove no local/remote-tracking ref changed. Stop
   if an object-only fetch cannot be performed without broadening this setup authority.

Stop if live `main`, identity, access, instructions, worktree count/state, workflow contract, or
overlap differs materially from the approved evidence. Report only a redacted delta.

## 3. Create only the new isolated target

1. Create one new issue-linked local branch and isolated worktree at the exact revalidated current
   GitHub `main` commit. Do not switch, reset, or update P08-W1/P08-W2.
2. Confirm the new worktree is the explicit Git root, non-bare, non-detached, non-submodule, clean,
   and has a committed HEAD on the new branch.
3. Recompare the local-only P08-W1/P08-W2 snapshots. Their registrations remain present and their
   HEAD/status/index/lock summaries must be unchanged; only the authorized addition of the new
   worktree/branch may change common Git metadata.
4. Confirm `.repoos/project.yaml` is absent and unignored in the new target. Do not create `.repoos`
   manually.

Stop on any unexpected existing-worktree change. Do not repair or clean it.

## 4. Materialize the exact proposed manifest outside all worktrees

Create and review exactly these bytes, ending with one newline:

```yaml
manifest_version: 1
project_id: p08
repoos_version: 0.3.0
project_family: null
sensitivity_classification: personal_data
additional_overlays: []
components:
  managed: []
  generated: []
  repository_owned: []
  extensions: []
  excluded: []
adoption_channel: canary
local_overrides: []
verification:
  - name: agentops-check
    argv: [make, agentops-check]
  - name: product-check
    argv: [make, product-check]
automation_permissions:
  read_only: true
  plan: true
  apply: false
  commit: false
  push: false
  external_settings: false
last_successful_audit: null
```

Do not infer or add fields. In particular, add no overlay, managed/generated/extension component,
local mapping, local path, secret, remote, private SHA, apply authority, commit authority, push
authority, or external-setting authority.

## 5. Plan and dry run without state writes

1. Run installed-wheel `repoos --format json plan-manifest-bootstrap` against only the new worktree,
   the exact external manifest input, and an external plan output.
2. Inspect the complete immutable plan. Confirm:
   - operation `manifest_bootstrap`;
   - exact new target/worktree/common-Git/branch/HEAD;
   - destination `.repoos/project.yaml`, expected absent;
   - one create, zero edits, zero deletes;
   - exact manifest/plan digests;
   - P08-W1/P08-W2 represented only by protected content-free summaries;
   - P08-W2 classified protected dirty when still dirty;
   - fixed limits and both `make` validation commands;
   - no private sibling path, untracked filename, or file body in public-safe output.
3. Snapshot the external local state path as absent or unchanged.
4. Run installed-wheel `repoos --format json --state-dir <external-state> apply --plan <plan>
   --dry-run` without authorization.
5. Prove `ready_for_authorization: true`, `authorization_status: missing`, zero target/state writes,
   no transaction/lock/backup/authorization creation, unchanged manifest absence, and unchanged
   P08-W1/P08-W2 summaries.

STOP FOR EXPLICIT USER APPROVAL.

Present the exact manifest, plan ID/digest, manifest digest, target branch/HEAD aliases, protected
sibling counts/classifications, fixed mutation limits, validation commands, dry-run no-write proof,
rollback contract, and all stop conditions. Ask for approval to create one expiring authorization
and execute this exact one-file transaction. Do not generate authorization and do not execute
until approval is explicit.

## 6. First authorized apply

After approval only:

1. Revalidate live GitHub `main`, new target HEAD/branch/cleanliness, destination absence, manifest
   digest, plan digest, P08-W1/P08-W2 summaries, common-Git state, and lock availability.
2. Generate one short-lived receipt with installed-wheel
   `authorize-manifest-bootstrap --plan <plan> --expires-in 1800 --approve`.
3. Do not print receipt contents. Confirm it is local state, mode `0600`, credential-free, and
   bound to the exact target/HEAD/branch/plan/manifest/destination.
4. Execute installed-wheel `repoos apply --plan <plan> --authorization <receipt> --execute`.
5. Confirm exactly `.repoos/project.yaml` was created with approved bytes/mode, validation passed,
   receipt was consumed, no Git ref/index/config/worktree registration changed, and P08-W1/P08-W2
   summaries remain unchanged.
6. In the new target run the full P08 profile in this order:
   - `make agentops-check`
   - `make product-check`
   - `git diff --check`
   - `git status --short`
7. Confirm the diff contains only the exact manifest and no commit exists.

On any install/validation/preservation failure, require RepoOS automatic rollback, preserve local
evidence, verify restoration, and stop. Do not retry with the same authorization.

## 7. Demonstrate manual rollback

1. Use the completed transaction ID with installed-wheel
   `repoos rollback --transaction <transaction-id>`.
2. Confirm the manifest is absent, `.repoos` was removed only if transaction-created and empty,
   the new target is byte/mode/Git-state equivalent to pre-bootstrap, and P08-W1/P08-W2 summaries
   are unchanged.
3. Run the identical rollback once more and require `already_rolled_back` with zero writes.
4. Prove the first receipt is consumed and cannot execute again.
5. Preserve transaction/backup/observation evidence locally; publish no private paths or contents.

## 8. Prepare reapplication and stop

1. Revalidate GitHub `main`, new target branch/HEAD/cleanliness, manifest input bytes, destination
   absence, protected siblings, common Git state, and lock.
2. Generate a fresh immutable plan and run another no-authorization dry run. Compare its exact
   binding with the reviewed proposal and explain any difference.
3. Present rollback proof, consumed-authorization refusal, fresh plan/digests, exact diff expected,
   and the proposed local commit message.

STOP FOR EXPLICIT USER APPROVAL BEFORE REAPPLICATION.

Do not create the second authorization, reapply, stage, or commit until approval explicitly covers
reapplication and the later local manifest-only commit after validation.

## 9. Reapply, validate, and commit locally

After the second approval only:

1. Create a new short-lived authorization for the fresh plan and execute exactly once.
2. Repeat:
   - `make agentops-check`
   - `make product-check`
   - `git diff --check`
   - `git status --short`
3. Verify installed bytes/digest/mode, manifest-only diff, unchanged base HEAD before commit, and
   unchanged P08-W1/P08-W2 summaries.
4. Stage only `.repoos/project.yaml`.
5. Review the staged diff and create one local commit:
   `chore: adopt RepoOS manifest`
6. Confirm the new canary worktree is clean, the commit contains only the manifest, both existing
   worktrees remain unchanged, and no authorization is reusable.

## Prohibited throughout

- any P08-W1 or P08-W2 content write or untracked-body read;
- raw protected untracked names/content in reports or learning;
- clean, reset, checkout/switch, stash, prune, repair, move, remove, or archive of existing P08
  worktrees;
- applying to an existing P08 worktree;
- editing/replacing an existing manifest;
- any file other than `.repoos/project.yaml`;
- overlays, components, AGENTS, skills, agents, hooks, Codex config, workflows, Git config, refs,
  index, remotes, or worktree registrations beyond creation of the one approved new worktree/
  branch;
- dependency installation unless separately approved as setup;
- live provider/network tests beyond read-only GitHub state;
- GitHub issue/branch/PR/settings/workflow mutation;
- fetch that updates a ref, `FETCH_HEAD`, tags, submodules, prunable metadata, or maintenance state;
- push, pull request, merge, release, or user-global change.

Final handoff:

- exact revalidated public-safe base and target aliases;
- plan/manifest/authorization lifecycle digests;
- dry-run zero-write evidence;
- first apply and full P08 validation results;
- manual and repeated rollback results;
- authorization-reuse refusal;
- second approval and reapplication results;
- local commit ID and manifest-only scope;
- before/after P08-W1/P08-W2 preservation proof;
- explicit confirmation that nothing was pushed and no PR/GitHub/global resource changed.

Do not push or open a pull request without a new, separate authorization.
````
