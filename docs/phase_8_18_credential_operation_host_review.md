# Phase 8.18 - Explicit Trusted Credential Operation Host

Add exactly one isolated, injected `TrustedCredentialOperationHost` adapter,
not a public agent capability or auto-start service. It binds the sealed exact
`OpenAICredentialOnboarding`, an explicitly trusted fresh
`ConnectionObservation` callback, and the host-only Phase 8.17 pending review.

Only a trusted host UI's explicit button may trigger `approve`. The adapter
checks that an operation was proposed, a candidate `SecretValue` is supplied
only for operations that need it, and the freshly observed status matches the
original (with a new eligibility check). Then the review is consumed once
and one fixed lifecycle method executes: TEST_CANDIDATE, TEST_STORED,
CONNECT, REPLACE, REMOVE. Rejection, expiry, input mismatch, changed/unknown
observations and backend errors fail closed with fixed, non-secret statuses.
A candidate is a transient method argument, not retained in the pending review.

The frozen result uses SUBMITTED/INVALID/INDETERMINATE/NOT_APPLIED/BLOCKED.
SUBMITTED acknowledges a bounded method return **not** durable storage, a
provider session, model entitlement, fresh correctness or an atomic update.
The existing lifecycle has no compare-and-swap; source-state equality does
not resolve races or ABA and never constitutes a transaction with metadata.

Validation uses fake backends and fake credential validators only. No real
secret, Windows Credential Manager operation, OpenAI API call or GUI
activation. No model-callable route is added. This host adapter is a
preparatory architecture step; real consent provenance and normal-user
first-run acceptance are still unverified.

## Phase 8.18 failure analysis and corrected security scopes

Initial validation stopped with two historical guards failing. The host's
`approve(candidate: SecretValue | None)` annotation referenced an undefined
`SecretValue` import, making module import fail in isolation. The correction
imports **only** `SecretValue` from `nayeon.secrets.contracts` and passes the
value through an existing `OpenAICredentialOnboarding` operation. It does
not perform a raw backend `get`, `put`, `delete` or secret `reveal`.

The original secret contract consumer inventory has been updated to enumerate
this exact new module. The Windows credential guard permits only the exact
`SecretValue` import in the new module, and rejects direct backend/native
storage imports, `SecretBackend`, `SecretIdentifier`, `SecretStorageError`,
`SecretStore`, `get`, `put`, `delete` and `reveal`. The lifecycle consumer
guard makes an exception for this module's exact single
`CredentialValidationStatus` enum import; it still rejects imports of
`BoundCredentialLifecycle` and expanded lifecycle symbols in this module.
Earlier production files are unchanged.

Reproduced prior errors; after the fixes, **103/103 targeted trust-path tests
passed**. The full pre-seal regression passed **2,009/2,009**. The host is
not a real human-provenance mechanism: an actual trusted first-run UI and
formal acceptance evidence are still required. Credentials are never
persisted by the host directly. The underlying credential/backend has no
compare-and-swap or cross-store transaction, and status SUBMITTED is never
a durability or entitlement guarantee.
