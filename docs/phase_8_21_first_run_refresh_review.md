# Phase 8.21 - Explicit read-only first-run refresh controller

Scope: one injected read-only controller and deterministic headless tests.
The constructor has no effects. Each explicit `refresh()` invokes exactly one
caller-injected typed observation; each response is an immutable receipt, not a
cached credential, permission, validation or durable connection result.

Errors, bad input types and reentrant observation return a fixed UNAVAILABLE
status without retaining stale data or leaking backend messages. The controller
does not itself import any secret contract, SDK, provider, filesystem writer or
credential operation. Every successful summary requires later reobservation.

This is a trusted host data-display component. No normal-user first-run UI,
actual human consent, credential operation or release gate is implied.
Next: a bounded user-driven desktop first-run status panel built around the
controller. Preserve the protected sealed historical production baseline.
