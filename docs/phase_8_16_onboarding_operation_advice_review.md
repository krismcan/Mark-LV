# Phase 8.16 - Pure Credential Operation Advice Matrix

**Scope**: one new pure `onboarding_operation_advice` production module and
exhaustive deterministic tests. No storage/validator/network or GUI wiring.

The matrix maps the seven sealed `ConnectionObservationStatus` states against
six human-facing operations: REVIEW, TEST_CANDIDATE, TEST_STORED, CONNECT,
REPLACE, REMOVE. All UNKNOWN, CHANGED_DURING_OBSERVATION or UNSUPPORTED
snapshots conservatively block mutation and testing suggestions; REVIEW
offers informational text only. A missing key suggests CONNECT, whereas
a present key suggests REPLACE/REMOVE/TEST_STORED. TEST_CANDIDATE never
persists any secret.

Outputs are fresh frozen, slotted, repr-redacted objects. Exact inputs and
matrix invariants enforce `requires_fresh_state` and
`requires_real_human_intent`. SUGGESTED is NOT permission; before executing
a future host must obtain real independent user intent, independently
reobserve current state, enforce operation-specific checks and handle races.
No credential values or approval tokens are represented.

**Residual risk**: the backend has no compare-and-swap; even a fresh
reobservation is not transactional. There is no UI/normal-user acceptance,
no Phase 8 closure, no verified release gates beyond the existing baseline.
