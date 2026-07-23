# Authorization-required work

Status: no listed action is authorized by the current implementation run

| Action | Why separate authority is required | Evidence/preview required | Rollback required |
|---|---|---|---|
| Confirm and migrate P08 canary | Changes an independently owned repository | Fresh Git/GitHub state, identity/risk/commands/family/ownership confirmation, exact plan and diff | Backup plus forward repository proposal |
| Modify any other downstream repository | Dirty, ambiguous, or non-Git state | Clean-state proof, classification, commands, ownership, explicit target | Repository-specific |
| Write user-global Codex files | Home-wide blast radius | Exact target list, current digest, rendered diff, adoption/backup plan | File restore and uninstall |
| Create GitHub issues | No existing RepoOS issue taxonomy | Proposed issue bodies, labels/milestones, duplicate check | Close/edit procedure |
| Push branch or open PR | External state and review impact | Branch/commit scope and validation evidence | Close PR/delete branch if approved |
| Publish RepoOS release | Creates immutable consumer dependency | Artifact manifest, hashes/signature decision, retention, compatibility and migration tests | Retain old release; forward rollback |
| Change branch protection/rulesets/required workflows | Repository governance | Read-only before/after plan, permissions and affected repos | Export/restore prior settings |
| Register or grant self-hosted runner access | Host confidentiality and execution trust | Isolation, ephemeral lifecycle, labels/groups, secret boundary, patching and incident plan | Revoke/remove runner |
| Change Actions secrets/variables/environments | Credential and automation impact | Exact names/consumers, least privilege, rotation and audit plan | Restore/remove/rotate |
| Install GitHub App or expand token permissions | Cross-repository privilege | Permission-by-permission justification and repository allowlist | Revoke installation/token |
| Enable scheduled AI review | Private evidence and cost | Redaction allowlist, model/budget, retention, evaluation and disable switch | Disable schedule and purge retained artifacts |
| Create organization `.github` or shared governance | Organization-wide behavior | Plan/account capability and consumer impact | Repository-by-repository rollback |
| Prune worktree metadata or reconcile dirty trees | Can destroy user recovery context | Exact records and user disposition | Recovery plan where possible |

## Approval format

Approval must name the exact action, target, scope, and mutation class. Approval for repository content does not authorize GitHub settings, user-global files, runner changes, releases, or other repositories.

## Current boundary

RepoOS-local implementation, documentation, schemas, neutral fixtures, and read-only GitHub inspection are in scope. No external mutation has been performed.
