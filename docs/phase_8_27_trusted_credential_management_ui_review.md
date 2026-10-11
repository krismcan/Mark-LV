# Phase 8.27 — Trusted first-run credential lifecycle controls

**Date:** 11 October 2026. **Protected starting branch and HEAD:** `nayeon-v1` at `21ae4ff6746d94968c60f07287bf4e10e0f5659b`. **Last full sealed regression:** 2,091/2,091.

## Human-approved bounded implementation

A new isolated first-run Tk `FirstRunCredentialManagementWindow` supports three specific, human-initiated operations: **CONNECT**, **REPLACE** and **REMOVE**. A trusted parent must inject an exact `CooperativeOnboardingCoordinator`, which itself delegates to `TrustedCredentialOperationHost`, `OnboardingReviewSession` and the permanently bound credential lifecycle.

- No operation is automatically proposed or executed at construction, import, refresh or launch.
- A user must select a named **Review** button, then separately select **Approve selected operation once**. Replays and duplicate pending proposals cannot execute.
- **CONNECT** and **REPLACE** require the user to enter a nonblank masked candidate in a disabled-by-default Tk Entry; the UI clears the Entry before invoking the existing coordinator, and never retains the candidate in pending-review state.
- **REMOVE** has no credential text input; an explicit checkbox acknowledging destructive deletion is required *in addition* to the review and approval clicks. Checkbox state is cleared on rejection and every new review.
- Rejection, close, blank/invalid input, unsupported readiness, state conflicts, expired review, busy shared mutex, marker or backend error fail closed.
- Messages are fixed and non-secret. Even a successful submission **does not** prove durable storage, provider entitlement, transactional completion, or key validation status after the fact. Conflict, uncertain effect and marker states require human reconciliation.
- The Tk panel contains no credential backend, Windows credential native, secret resolver, filesystem storage, SDK, network code, model route or generic settings object. It can *only* construct an ephemeral SecretValue and call the injected coordinator.
- Tk masking and best-effort deletion are not memory zeroisation, clipboard isolation against malicious software, credential theft resistance or definitive proof of a genuine human actor inside a hostile process.

## Security and ownership contract

The existing **permission → policy → confirmation → execution → verification** boundary remains authoritative for machine actions. Credential lifecycle operations belong only to the host-owned onboarding workflow, never to an untrusted model request. The Phase 8.26 Windows-session single-writer mutex guards execution, not review think-time. The underlying credential storage and metadata stores do not support compare-and-swap or cross-store transactions; external writers and same-presence ABA changes may evade this coordination.

The new panel is **available for trusted composition only**. The main Personal Alpha entry point is deliberately unchanged and cannot automatically instantiate a real backend. All acceptance tests inject synthetic credential storage and validators. There is no live provider call, live Windows Credential Manager access, real key handling, user credential import or full consumer first-run acceptance in Phase 8.27. Phase 8.28 will handle trustworthy metadata and recovery integration; Phase 8.29 remains conditional on separate consent and evidence.

## Verification and milestone close-out

- 20 new focused tests: 17 synthetic host/coordinator/Tk callback tests plus three genuine Windows Tk callback exercises. Key outcomes include successful fake connect/replace/delete, invalid replacement preserving the old fake credential, explicit deletion acknowledgement, replay/reject/close, masked-entry clearing, busy/conflict/recovery block and restricted imports.
- Historical test inventories must only add the exact new module. Secret consumer exceptions must allow only a transient SecretValue, a masked-entry .get/.delete, the non-secret checkbox getter and two fixed message map lookups. No generic access to SecretBackend, WindowsCredentialBackend, stored credential reads, deletion, put or reveal.
- Focused security guards, independent source review, full regression, compileall, exact staging, seal-time and post-commit tests must all pass before GitHub push/tag verification.
- A separate Codex handoff update and **same Google Drive file ID** `.xlsm` workbook update (all 16 worksheets intact) are mandatory. Formal Phase 8 remains IN PROGRESS, 5/19 phase exits, 0/12 release gates.

**No results are treated as verified until the exact commands succeed.**
