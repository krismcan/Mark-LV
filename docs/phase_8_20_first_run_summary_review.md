# Phase 8.20 - Non-secret first-run decision summary

This milestone begins the next five-phase bounded engineering tranche from
sealed Phase 8.19 at `b8a220682da54e500656c7485ab498269d1e1246`.

The new `first_run_summary.py` combines the existing read-only
reconciliation recovery and eligibility interfaces into one typed
`FirstRunSummary` for eventual first-run presentation. It reuses established
`OnboardingDisplayState`, `ConnectionRecoveryStep`, and
`OnboardingOperation` types rather than introducing a parallel authorization
contract. All seven observation states are covered deterministically.

**Conservative safety**: malformed/unknown/changed/unsupported observations
cannot suggest credential actions. Even for a suggested operation, the result
only informs a human and retains `requires_reobservation=True` and
`grants_execution_authority=False`. There are no credential values, backend
access, file reads/writes, network calls, SDK calls, mutations, automatic
retries or model/tool routes. No normal-user live status claim is made.

**Next:** explicit user-owned status refresh controller and first-run interface.
The adapter must not turn suggestions into consent or implementation authority.
Formal Phase 8 and all 12 release gates remain open pending normal-user tests.
