# Phase 8.8 — Trusted OpenAI Credential Onboarding Composition & Explicit Operations

## Protected baseline and user approval

Date: 9 October 2026. Repository `C:\AI\mark-lii`, branch `nayeon-v1`.
Protected HEAD: `5ff70f673b185e004e518052c859c8d1c796b9d3`.
Latest sealed PRODUCT milestone: Phase 8.7,
`nayeon-v1-provider-connection-readiness-explicit-startup-01`,
annotated tag peeled to `cadb399970a6c6bf9e1f937d033b5a7d60010c4d`.
Initial authoritative regression baseline: **1,880/1,880**.
Pre-implementation worktree was clean; no staged files.

User approved a narrowly bounded implementation with deterministic fake-backend
and fake-validator tests; no live credentials, network smoke, automatic activation,
UI or metadata-persistence coupling. **Stop before human seal approval: do not
stage, commit, tag, push, update the workbook, or refresh Codex context.**

## Approved new production modules — precisely two

1. `nayeon/brain/credential_onboarding_composition.py` (NEW)
   - `compose_openai_credential_onboarding(backend: SecretBackend)`
     accepts an explicitly trusted injected backend, constructs the sealed
     `OpenAICredentialValidator`, and uses `BoundCredentialLifecycle`
     bound to the fixed `SecretIdentifier("openai.api_key")`.
   - Returns `OpenAICredentialOnboarding` without reading from storage, making
     an SDK/client/network call, validating, saving, deleting, or connecting.
   - No provider string, model, arbitrary identifier, ambient backend, default
     path, environment setting, global registry or automatic bootstrap.

2. `nayeon/brain/credential_onboarding.py` (NEW)
   - Exact typed wrapper around one `BoundCredentialLifecycle`, rejecting
     another credential identifier and exposing no plaintext getter.
   - Explicit operations `is_connected`, `test_candidate(SecretValue)`,
     `test_stored`, `connect(SecretValue)`, `replace(SecretValue)`, and
     `remove`. A trusted caller must invoke each operation explicitly.
   - Reuses the sealed lifecycle's availability checks, validator tri-state,
     state-change rechecks, and VALID-only storage rules. Invalid and
     indeterminate candidates are **not saved**; failed replacement leaves
     the previous credential in place under the lifecycle's own assumptions.
   - Returns `CredentialValidationStatus` (VALID/INVALID/INDETERMINATE) for
     validation/mutation attempts or a typed bool for availability/deletion.
     These statuses are operation outcomes, **not proof of AI model
     entitlement, permanent key validity, or live service health**.
   - Fixed non-secret state/storage/missing-key error messages; suppressed
     backend error chaining for ordinary traceback display. Exact
     `SecretValue` input checks and redacted non-serializable wrapper.
   - No direct Windows/native backend import, SDK, frontend, capability route,
     provider configuration write, or UI/runtime auto-wiring.

## Test evidence and historical guard reconciliation

NEW deterministic suites:

- `tests/test_credential_onboarding.py`
- `tests/test_credential_onboarding_composition.py`

Tests cover no startup/composition side effects, exact constant credential
binding, missing and malformed dependencies, valid/invalid/indeterminate
candidate outcomes, stored validation, connect and replace preconditions,
rechecks against state changes, non-mutation on invalid/indeterminate status,
explicit delete and absence, storage-error sanitization, exact input and
identity types, fake validator exception containment, non-disclosure,
non-serialization, and import boundaries.

A new freeze guard checks the **102 sealed Phase 8.7 Python production files
and `requirements.txt`** byte-for-byte (with CRLF normalization) against
the annotated Phase 8.7 product tag. It permits **only the two explicit new
production paths**, as no previously sealed production code is edited.

Exactly **12 existing historical test files** were reconciled to include the
two new files in exact addition/scope inventories and to whitelist only their
required imports:
- `tests/test_bound_credential_lifecycle.py`
- `tests/test_openai_canonical_client.py`
- `tests/test_openai_provider_secure_secret.py`
- `tests/test_presentation_configuration_bootstrap.py`
- `tests/test_presentation_configuration_persistence.py`
- `tests/test_presentation_configuration_service.py`
- `tests/test_presentation_configuration_view.py`
- `tests/test_presentation_identity_contracts.py`
- `tests/test_provider_connection_composition.py`
- `tests/test_provider_connection_service.py`
- `tests/test_provider_connection_startup.py`
- `tests/test_windows_credential_backend.py`

Earlier import ownership freezes, product tags, requirements, legacy MARK,
`AGENTS.md`, `.codex/CURRENT_STATE.md`, and existing production remain
protected.

## Validation performed on the authorized Windows host

Interpreter:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

- New focused tests (including exact prior product freeze): **36/36 PASS**.
- Combined relevant affected trust-path tests: **274/274 PASS**.
- Full repository unittest discovery: **1,916/1,916 PASS** (including final run after guard refinement).
- Python compilation: **PASS**.
- `git diff --check` and independent exact unsealed 17-path audit: **PASS**.

No real secret was inspected, no Windows Credential Manager call was made,
and no OpenAI client/network probe occurred during deterministic tests.

## Residual risks, honest non-scope, and next integration seam

The sealed OpenAI validator returns `VALID` only after its bounded successful
model-list probe; any provider failure normally becomes `INDETERMINATE`
(not evidence of an invalid key). The new modules deliberately inherit
this behavior. Any explicit future production invocation could make a
provider request with the user-supplied key and needs separately approved
UI/permission and operational integration.

The sealed lifecycle is **not transactional or cross-process locked**:
availability can change between its last recheck and `put`; it has no
compare-and-swap. Provider connection metadata is stored separately and
is neither created nor changed by this onboarding module. A credential
operation success does not imply metadata was updated.

No model-selectable or public agent command, first-run UI, OS startup, default
file path, API client activation, API key test using real credentials,
credential logging, direct native secrets call, generic credential registry,
cross-store rollback, real user acceptance gate, or packaging was added.

The next approved phase should explicitly design metadata selection/storage
coupling, recovery after partial failure, safe freshness/status presentation,
and a human-invoked BYOK onboarding screen before calling this production-ready.

## Human seal gate

The implementation must remain **unsealed and unstaged** until the next
explicit user approval. Seal-time tests, one product commit, an annotated
tag, remote push, master workbook changes and Codex context refresh are
separate gates, not implied by Phase 8.8 implementation approval.
