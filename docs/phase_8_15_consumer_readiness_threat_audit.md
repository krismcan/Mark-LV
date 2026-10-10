# Phase 8.15 - Phase 8 Consumer Onboarding Closure and Concurrency Threat Audit

**Baseline**: `nayeon-v1` at `1b042aadcb678c5849e08031376c9756396d700f`; 1,985/1,985 tests. 10 October 2026.
**Nature**: bounded formal architecture/threat audit, no runtime code or credential access.

## Confirmed implemented boundaries
1. Versioned metadata in `ProviderConnectionDocumentV1`, strict canonical provider and
   identifier validation, explicitly managed `ProviderConnectionService`.
2. Key storage through `SecretBackend`, `WindowsCredentialBackend`, fixed
   `SecretIdentifier("openai.api_key")`, and `BoundCredentialLifecycle`.
3. Explicit candidate/stored validation plus explicit connect/replace/remove via
   `OpenAICredentialOnboarding`, not callable by model or GUI.
4. Read-only reconciliation, onboarding status, canonical proposal, metadata preview,
   review and change preview (8.9–8.14), not authority to mutate anything.
5. The Personal Alpha action GUI is a **Notepad-only action testbed**, not a
   credential form or full first-run onboarding product.

## Actual consumer readiness gaps
- No trusted first-run GUI for secret entry, explicit test, save, replace,
  delete, consent review, or safe error reporting.
- No complete trusted UI-to-credential-operation lifecycle/ownership.
- No explicit human-mediated and revalidated metadata mutation flow.
- No model entitlement or secure provider startup guaranteed by key existence.
- No user acceptance evidence for release gates #2, #3, #4; their statuses
  stay NOT VERIFIED. No new formal Build Plan Phase 8 closure evidence.
- No read-modify-write compare-and-swap on connection metadata and no CAS on
  `SecretBackend`. A two-read reconciliation is not a lock, nor an ABA detector.
- Metadata and credential store operations are **not** a joint transaction;
  an interrupted two-store workflow can leave a mismatched pair. Never
  claim automatic rollback, atomic setup or unconditional success.

## Decisions for the next four engineering increments
**8.16 - Trusted operation admission rules**: a pure, exact-typed, immutable
plan for human-facing onboarding operations (inspect, explicit test, connect,
replace, remove, metadata proposal/preview), including no implied consent and
a fail-closed operations matrix. No side effects.

**8.17 - Fail-closed onboarding interaction lifecycle**: an in-memory
host-only single-pending-operation state machine; explicit human confirmation
and single use of a pending decision, rejection/expiry and no accidental
approval from conversational text. Do not accept credential values into
this state machine, persist them, or issue binding authority directly.

**8.18 - Trusted operation dispatcher testbed**: a *host-only*, injected
explicit-operation adapter using existing credential onboarding and a
separate out-of-band candidate. No model-callable routes, no ambient
credential reads, no cross-store transactions, no automatic mutations.
Revalidate pending identity and cancel on staleness; receipt is a
non-secret operation status, not proof of durable success.

**8.19 - Integrated fake-backend lifecycle / closure reassessment**:
exercise the preceding layers end-to-end using fake backends and simulated
human events, failure containment and no secret output. Check which
formal Phase 8/release criteria remain unmet; do **not** mark Phase 8
complete without actual normal-user and live-safety acceptance evidence.

## Mandatory invariants
- `Permission -> Policy -> Confirmation -> Execution -> Verification` for
  any model or machine capability; first-run management is separate
  trusted-user operation, not a model-selected action.
- Validation may call OpenAI only if a trusted real human explicitly requests it;
  test fixtures must use fakes. No credentials read, printed or committed.
- Credential objects must remain redacted; a plaintext `SecretValue` may
  be passed only to a single explicit operation, not copied into an
  approval message/plan/log or reused after cancel.
- Existing frozen production remains byte-for-byte unchanged except through a
  separately audited approved scope. Preserve all milestone tags.
- The absence of transactional CAS is a high-severity *residual risk*
  requiring a later explicit design before broad deployment.

## Acceptance
Read-only source-backed gap/threat audit with baseline frozen; exact
scope, full regression, annotated commit/tag, GitHub remote verification,
Codex handoff and same-ID workbook update. No release gate closure claimed.
