# Phase 6.13 bounded pointer verification integration review

## Candidate and authorization

Protected starting checkpoint verified: branch `nayeon-v1`, exact HEAD `1da0870fb3c665acb2f1a45c68ee7c183403cb35`, tag `nayeon-v1-bounded-post-effect-observation-01` at that HEAD, clean working tree. Phase 6.12 remains sealed. This is a dirty, unstaged candidate only. No stage, commit, tag, push, history rewrite, or spreadsheet update.

**NO LIVE NATIVE SMOKE AUTHORIZED.** No tests, Python, compileall, environment diagnostics, live native queries, or effects were run in Codex. Runtime validation and every passing-test claim remain pending. Static inspection does not establish runtime behavior or a verified milestone.

## Exact claim and separation

The only VERIFIED wording is:

> The complete approved three-record input batch was inserted, and the bounded post-effect sample matched original-target identity/context and foreground within the original-binding age window; UI/task result unverified.

This combines two independently captured categories: Phase 6.11 API input insertion and Phase 6.12 original-target bounded observation. It establishes neither delivery nor causal attribution, cursor placement, button state, application acknowledgement, button/control activation, or semantic UI/task success. The three-record batch is the existing absolute move, left-down, left-up batch. No semantic success flag is introduced. A changed foreground or target does not indicate semantic success or failure.

The claim depends only on an exact, revalidated `_PointerEffectReceipt` and an exact, revalidated `_PointerPostObservationResult` accepted in the same private approved invocation. It does not reinterpret the human request, inspect the UI, ask a model, or promote eligibility into effect evidence.

## Standard architecture integration

MODEL decides WHAT; AGENT decides HOW; POLICY decides WHETHER; SERVICE performs; VERIFICATION proves only the supported claim. Preparation, Permission -> Policy -> Confirmation -> Execution, fresh eligibility, coordinate mapping, and one-use approval remain on their existing private path. No public click capability is registered merely to use verification.

`ActionExecutor` already owns `VerificationService`. The private invocation now uses that exact coordinator with a narrow `_PointerVerificationProvider` implementing the existing `verify_result` protocol and returning the existing `VerificationResult`/`VerificationStatus`. No verification framework, status enum, native adapter, public executor API, or registry route is added. Existing registered capability providers and the generic executor flow are unchanged.

The protocol normally runs after a capability returns successfully. Here the private bridge runs after the bounded effect seam has completed or raised and Phase 6.12 has captured its independent observation. An attempted/partial/unknown insertion is never converted to execution success to enter the coordinator. It is conservatively classified by the provider. An invocation without valid paired evidence returns a standard INDETERMINATE locally and need not invoke the provider.

Private evidence is noncopyable. The coordinator receives only the existing fixed private request string and `output=None`; it deep-copies those ordinary values as usual. The ephemeral, frozen, slotted, redacted, noncopyable provider holds the two exact evidence objects locally. It validates and snapshots their types, scalar fields, and object identities, and is usable once. Raw evidence does not enter public JSON, service output, requests, or audit details. The standard result has an empty evidence dictionary and a fixed safe reason.

The insertion snapshot is captured immediately after receipt acceptance (or conservative fallback following an effect exception), before eligibility auditing. The observation snapshot is captured immediately after Phase 6.12 acceptance, before observation auditing. Provider construction checks against both snapshots, so valid-looking field changes and same-value object replacements across audit seams remain inconclusive. Binding, service identity, and registration checks occur before the bridge and again after the coordinator returns; evidence is also rechecked after return. These are local checks only. No Phase 6.13 sampling occurs, and no Phase 6.13 evidence evaluation or audit enters the final pre-insertion gap.

## Mapping

Invalid/missing/subclass/uninitialized evidence, validation exception, snapshot mismatch, changed operation/services/registration, invalid coordinator result, or bridge exception takes precedence and returns INDETERMINATE.

For valid unchanged paired evidence:

| Insertion receipt | Post-observation | Standard result | Evidence-supported meaning |
| --- | --- | --- | --- |
| INSERTED, attempted true, exact count 3 | VERIFIED | VERIFIED | Complete approved batch insertion AND sampled original-target equality within the unchanged age rule. |
| INSERTED, attempted true, exact count 3 | NOT_VERIFIED | NOT_VERIFIED | Positive bounded observation contradicts original-target equality. |
| INSERTED, attempted true, exact count 3 | INDETERMINATE | INDETERMINATE | Bounded target evidence is insufficient. |
| PARTIAL, attempted true, exact count 1 or 2 | Any valid status | NOT_VERIFIED | Positive insertion count proves the complete batch was not inserted, regardless of target uncertainty. |
| INDETERMINATE, attempted true, exact count 0 or None | Any valid status | INDETERMINATE | Preserve Phase 6.11 uncertainty; no complete insertion claim. |
| NOT_ATTEMPTED | Missing observation (normal), or any valid status | INDETERMINATE | No verified effect claim; no new read. |
| Read-only approval, abandonment, already closed | No new evidence | No new claim | Default or previously captured result remains; no provider reuse. |

Malformed target evidence remains insufficient even when insertion is partial: the invalid paired evidence gate takes precedence. Valid INDETERMINATE target evidence is distinct from a malformed object. Neither NOT_VERIFIED nor INDETERMINATE asserts semantic task failure.

## Ordering, lifecycle, and privacy

Phase 6.11 `_execute_effect()` still returns the original receipt, including the exact valid receipt object; standard verification never rewrites it. Phase 6.12 still performs at most its existing single original-target verification after an attempted effect, using its original-binding age window and no replacement baseline. `_post_observation` retains its separate status semantics. Both evidence contracts and native services are unchanged.

After existing observation auditing, standard verification is computed before existing effect audit and cleanup. A distinct fixed-message `VERIFICATION_OUTCOME` event has the standard status and empty details. Existing eligibility, effect, and post-observation events remain separate. Verification auditing failure cannot erase any result. Cleanup failure does not retroactively disprove already captured evidence; it clears existing authority state and retains the safe conclusion, consistent with Phase 6.12's partial-outcome rules.

The invocation retains only a standard `_verification` conclusion alongside the existing private post-observation status. The provider and receipt/observation snapshots are local temporaries, never invocation authority or executor state. Closing clears target, point, action, binding snapshot, token, registration, and service references as before. Repeated consume calls neither recompute nor overwrite the retained verification, gather new evidence, nor reinsert input. The result is historical evidence, not reusable approval. No persistence, memory, semantic flag, or undo registration is introduced.

No HWND, PID, TID, coordinates, titles, tokens, process identity, timestamps, exception text, object identity snapshots, or raw private evidence appear in public results or new audit details. Exact types and frozen snapshots are trusted in-process conventions; they do not sandbox hostile Python code that can replace internal methods or rewrite all seals.

## Limits and residual TOCTOU

Phase 6.12 samples are sequential, bounded in cardinality, and neither atomic nor continuous. Target/context/foreground may change between samples, after sampling, or while the OS processes input; change-away-and-back can be invisible. Phase 6.13 introduces no new sampling, polling, delay, model judgment, or native API. Its local integrity checks cannot strengthen the original observation or prove delivery/activation.

The original target age rule remains `acquired_from <= acquired_to <= t0 <= t1 <= acquired_to + MAX_AGE_NS` (currently one second). No timestamp refresh or target replacement repairs expiry. Existing audit delay can reduce Phase 6.12 availability; standard verification runs after that observation and cannot repair it. Partial insertion, UIPI, user interference, coordinate/monitor limitations, and uncertain button state remain unresolved. Safe retained results describe captured evidence, not current desktop state.

## Non-scope

No new desktop read, execute, retry, refocus, move, click, native API, compensating input, arbitrary click route, autonomous GUI sequence, OCR/CV/UIA/screenshot/DOM interpretation, semantic success, reusable authorization, persistence, undo fiction, or broader authority. The protected effect and observation service implementations, generic executor, registry, dispatch, intent, runtime, policy, confirmation, and existing test files are unchanged.

## Tests added; all runtime validation pending

`tests/test_pointer_verification.py` adds deterministic fake-only coverage for the exact VERIFIED wording and full insertion/observation status matrix; NOT_VERIFIED versus INDETERMINATE; missing/malformed/uninitialized/subclass evidence; invalid scalar fields; valid-looking tampering and same-value object replacement; one-use provider and wrong request/output; exception containment; standard result/protocol compatibility; preserved receipt identity and separate observation; coordinator use; original read/effect counts and closed-call nonreuse; no-attempt and read-only modes; binding/registry tamper; audit/cleanup exceptions; public result/audit privacy; no semantic-success wording; and source guards against a public route or alternate native mutation/read API.

Existing Phase 6.11 and 6.12 test sources remain unchanged and must run on the host to check sealed behavior. Host validation remains pending for the new fake-only suite plus affected pointer effect, post-observation, binding, target validation, verification, executor, and audit regressions, followed by appropriate deterministic regression and syntax checks. Tests use injected mocks and facade-construction guards; no live native smoke is included or authorized.

Static checks performed: repository checkpoint/status/index inspection; relevant architecture, provider, implementation, and test source review; diff inspection; `git diff --check`; explicit whitespace checks for new files; source scans for new native/public routes; protected-source and index inspection. This is an unverified review candidate, not a sealed milestone.
