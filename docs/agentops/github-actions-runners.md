# GitHub Actions runners

RepoOS initial CI uses GitHub-hosted `ubuntu-latest` ephemeral runners.

## Trust policy

- Public pull-request code does not run on a persistent personal machine.
- Token permissions are explicitly read-only.
- Third-party actions are pinned to verified full commit SHAs.
- Jobs have concurrency cancellation and timeouts.
- CI receives no RepoOS secrets.

The current workflow tests Python 3.11 and 3.13. It does not register, label, or manage runners.

## Self-hosting

Self-hosted runners are deferred. Enabling one requires explicit authorization and an isolation, ephemeral lifecycle, repository allowlist, labels/groups, secret boundary, patching, monitoring, and incident/revocation plan. A runner should not be added merely to mirror a developer laptop.

## Validation

```bash
python3 -m pytest tests/codex/test_codex_validation.py
PYTHONPATH=src python3 -m repoos --format json validate --all
```
