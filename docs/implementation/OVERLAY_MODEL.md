# Overlay model

Status: validated design; no real overlay implemented

## Precedence

1. RepoOS baseline components
2. One primary family overlay
3. Ordered additive capability overlays
4. Repository-local ownership and explicit overrides

Repository-local exclusions and stricter safety rules win. An overlay cannot claim an unadopted path.

## Eligibility

An overlay requires:

- at least two confirmed consumers;
- deterministic predicates over manifest facts;
- a named owner and version;
- explicit owned paths and inputs;
- neutral valid/invalid fixtures;
- conflict behavior and rollback;
- no secret, business-rule, or repository-identity coupling;
- human confirmation of membership.

One repository is not a family. A useful single-repository pattern remains local or experimental.

## Composition rules

- One primary family maximum.
- Capability overlays are ordered explicitly in the manifest.
- Two components cannot own the same full file.
- Section overlap is unsupported while managed sections are deferred.
- Eligibility is revalidated before planning and applying.
- A local override must name reason, owner, and review date.
- Incompatibility stops planning; precedence never silently resolves an ownership collision.

## Current evidence

The portfolio contains reusable instruction and planning candidates, but no confirmed two-member overlay with validated commands and ownership. Python CI, documentation audit, and safety policy are candidates only. Creating framework overlays now would encode assumptions from incomplete and dirty repositories.

## Join and leave

Joining is a versioned adoption proposal with a no-behavior manifest step followed by one bounded component. Leaving is a forward ownership-transfer proposal that preserves repository behavior and records the prior release/baseline.

## Deferred capabilities

Managed sections, generated workflow matrices, organization-level reusable workflows, automatic family inference, and AI-driven eligibility remain deferred.
