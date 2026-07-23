# Rollback

Executable apply and rollback are not shipped in `0.1.0`.

The required future contract is:

- create an operation journal and backups before the first write;
- replace files atomically where supported;
- inject failures after every write boundary;
- restore applied paths in reverse on failure;
- retain evidence and never hide partial state;
- roll back merged changes through a new forward proposal to the previous immutable release;
- never rewrite Git history.

External GitHub settings and user-global files have separate rollback plans and are not covered by repository file rollback.
