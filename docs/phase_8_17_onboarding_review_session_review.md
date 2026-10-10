# Phase 8.17 — Single-Pending Human Onboarding Review Lifecycle

A host-owned in-memory state machine proposes exactly one non-secret operation
advice at a time. A trusted application UI must route a real human button
event to `finish`; text, semantic model output and the assistant dispatcher
must never approve. The review has a bounded monotonic deadline, rejection,
expiry and consume-once semantics.

Its immutable `CompletedOnboardingReview` **does not grant execution
authority**. The next trusted layer independently reobserves state, obtains
operation-specific consent and validates the secret input or stored key
before any side effect. Neither candidate secrets nor approval tokens
are stored in the review or serialized/logged.

No filesystem, credential backend, provider SDK, GUI, environment variable,
permission escalation, provider activation or actual mutation is introduced.
Tests cover replay, changed state, reject, expiry, pending exclusivity,
invalid clocks and immutable outcome constraints. Real user approval and
first-run acceptance remain unverified. Backend/metadata transactions still
lack compare-and-swap and cross-store atomicity.
