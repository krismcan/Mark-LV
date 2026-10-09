# Phase 8.10 — Pure trusted first-run status presentation

**Protected parent:** 5beeb7f625e0c7b5487f38547e5913b4cd7a08f5
**Scope:** one new pure presentation projection in `onboarding_status_view.py`,
one deterministic test suite and narrowly updated source inventories.

`present_onboarding_status` accepts only exact immutable Phase 8.9
`ConnectionObservation` and matching `ConnectionRecoveryAdvice`.
It produces immutable non-secret status and step enums, always marked
`must_reobserve=True`. An inconsistent pair fails closed. No UI,
filesystem/secret read, network, validator, action, or auth token is created.

This is **not** confirmation, readiness for execution, authorization,
live authentication or an end-to-end acceptance gate. Even after rendering,
status can become stale and must be observed again before a later operation.

**Validation:** focused, full regression, compileall, product/tag integrity;
stop if any fail. No new privilege or provider authority.
