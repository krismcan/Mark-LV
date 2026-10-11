# Phase 8.25 — Human-triggered candidate validation entry (scope and review)

**Protected starting baseline:** branch `nayeon-v1`, HEAD `7bfb831167d88079bc48d647e063ac98de442e90`, 2,054/2,054 full regression passing at the prior sealed checkpoint. Date: 11 October 2026.

## Bounded outcome

Add one isolated trusted Tk candidate-entry panel, `nayeon/desktop_alpha/first_run_credential_validation_window.py`, wired only to `TrustedCredentialOperationHost.request(TEST_CANDIDATE)`, `approve(candidate=SecretValue(...))` and `reject()`. The key is accepted only after an explicit review request; the user must then deliberately click Approve one validation. Validation may contact a provider *in an eventual trusted live composition* only on the human approval action. This milestone uses deterministic fakes exclusively.

The entry is masked, ordinary copy/cut Tk bindings are intercepted, the panel does not use a tkinter StringVar, and text is removed before the validation operation. Clearing is a best effort and does not ensure Python memory erasure or hostile local-process isolation. The result displays only fixed, non-secret messages and expressly states that validation does not save the key. No actual Windows credential backend, real secret, network, SDK or provider account was used during tests.

**Existing authority reused:** `TrustedCredentialOperationHost`, `OnboardingReviewSession`, `OpenAICredentialOnboarding`, `BoundCredentialLifecycle`. No new backend, model tool, path/shell command, permission override or generic credential manager. Existing Phase 8.23 review-only window remains unchanged.

## Security review

- Constructor causes no observation or validation; credential entry disabled until the user requests an eligible review.
- Two distinct button actions required: request review then approve. Rejection, close, invalid/blank entry, incompatible state and backend failure are fail-closed.
- Approval is single use, eligibility is reobserved by the host, expired reviews are blocked by the host; only `TEST_CANDIDATE` operation is hard-coded in the UI.
- No writes/deletion: the only credential lifecycle path accessible through this UI is validation of an ephemeral candidate; no persisted key, model entitlement, or durable result is claimed.
- No key in pending review, public messages or exception output. The Tk widget and Python values are not cryptographically isolated. Direct method invocation from a hostile same-process actor remains outside the trusted host model.
- Prior historical freeze/secret-consumer guards were updated for exactly the one new Python module. The guard allows `SecretValue` construction only and allows `get/delete` only when the receiver is `self._entry`, not a credential store.
- No live Windows acceptance, no end-user launch/composition, no secure credential save/replace/delete, no concurrent CAS or cross-store transaction. Formal Phase 8 remains IN PROGRESS; phase closure 5/19 and release gates 0/12.

## Acceptance conditions before seal

1. All new synthetic Tk callbacks test using the actual host with fake storage/validator; assertion that no credential writes or deletes occur.
2. Historical frozen-production and secret import boundary guards pass, with no relaxed production authority.
3. Independent source/diff review; `compileall`, `git diff --check`, focused security tests and full host-Python `unittest` regression pass.
4. Exact staged scope, seal-time rerun, product commit, immutable annotated tag, approved GitHub push and remote peeled-tag verification.
5. Codex handoff refresh, same-ID 16-worksheet master `.xlsm` update, exact file identity/readback verification.

**Next:** Phase 8.26 trusted coordination/concurrency threats. Explicit user approval still required for any genuine live validation, credential input, change of approved scope, or production readiness claim.

## Phase 8.25 post-product maintenance: real Tk acceptance

The first product seal verified 2,067/2,067 deterministic tests before and after the commit, but that suite drove the Tk API through synthetic widgets. The additional actual-Windows-Tk acceptance now creates a genuine withdrawn `tk.Tk()`, binds the real `tk.Entry` and `tk.Button` widgets, and uses `Button.invoke()` for explicit review, approval, rejection and invalid-entry paths with fake backend/validator only. All three real-Tk cases passed in the initial focused run, along with the original 13 synthetic cases (16/16 combined).

This is genuine Tk widget callback evidence, **not** actual human consent, native Credential Manager I/O, connected provider validation, packaging, or formal release gate evidence. No existing tag moves; record the new persistent real-Tk suite in a distinct post-product maintenance commit and annotated tag only after full regression.
