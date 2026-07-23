# AgentOps

AgentOps turns repeated, evidenced failures into proportionate, testable improvements.

## Loop

```text
redacted evidence
→ deterministic observation record
→ candidate pattern
→ neutral fixture
→ human decision
→ bounded adoption
→ regression and rollback review
```

AI may summarize or cluster approved evidence but cannot approve, enforce, mutate, or promote.

## Choose the smallest valid fix

| Failure | Preferred fix |
|---|---|
| Behavioral defect | Product test and code fix |
| Stale instruction | Repair/delete the lower-authority document |
| Invalid contract | Schema plus valid/invalid fixtures |
| Unsafe mutation path | Deterministic core guard and negative test |
| Repeated tool misuse | Tool contract or focused skill |
| Hook/rule gap | Core guard first; hook/rule only as tested defense in depth |
| Repository-specific exception | Keep local; do not promote by similarity |

## Current authority

- Architecture and automation: `docs/implementation/`
- Machine contracts: `schemas/`
- Safety: `policies/security/COMMAND_SAFETY.md`
- Learning: `docs/architecture/LEARNING_LOOP.md`
- Verification: `docs/verification.md`

Legacy registries remain informational until entries are backed by executable tests.
