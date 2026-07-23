# File ownership

The authoritative ownership policy is
[docs/implementation/FILE_OWNERSHIP_MODEL.md](../implementation/FILE_OWNERSHIP_MODEL.md).

`0.2.0` executes fully managed, generated, and uniquely marked UTF-8 section updates only in
explicitly marked neutral fixtures. Repository-owned, extension, local-override, and excluded paths
are reviewable preservation entries and are never written. Unknown ownership is repository-owned;
deletion and structured-file sections remain unsupported.
