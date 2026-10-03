# Phase 6.12 bounded post-effect observation review

## Candidate and authorization

Exact clean starting baseline: branch `nayeon-v1`, HEAD `adec0ddcac6a3c7fcd8a8fe50038077b07007038`, annotated tag `nayeon-v1-bounded-pointer-effect-01` peeled to that HEAD. This is an uncommitted static-only candidate. No tests, Python, compilation, environment diagnostics, or live native queries/effects were run. No passing test result or verified milestone is claimed until host validation.

**NO LIVE NATIVE SMOKE AUTHORIZED.** Prior Phase 6.11 smoke authorization does not authorize Phase 6.12 live reads or effects. Host validation for this candidate must use deterministic fakes/mocks. No staging, commit, tag, push, history rewrite, or spreadsheet update is authorized here.

## Exact trust claim and evidence separation

After the private Phase 6.11 effect seam returns or raises and a conservative effect receipt exists, the invocation performs at most one fresh read-only verification of the original approved target through the same exact trusted `_TargetVerificationService`. A valid unchanged operation snapshot, exact service identities, and unchanged registry binding are required before the read and checked again before accepting its result. No replacement target or acquisition baseline is produced.

The Phase 6.11 `_PointerEffectReceipt` type, status/count interpretation, native batch, and return API are unchanged. `_execute_effect()` still returns that receipt, including the identical exact receipt object when valid. Post-observation cannot rewrite INSERTED, PARTIAL, INDETERMINATE, or NOT_ATTEMPTED. A malformed/raising effect seam retains the existing conservative attempted INDETERMINATE receipt; it may receive independent observation.

A separate private `_PointerPostObservationResult` contains only one `VerificationStatus`. It is frozen, slotted, redacted, exact-type checked, noncopyable, and nonpickleable. The invocation retains this scalar result in `_post_observation` after cleanup for local inspection; all original binding, token, snapshot, registration, and service references are cleared through existing cleanup. No raw target verification result, identity, coordinates, timestamps, reason, or token is retained in the observation result. This status supplies no reusable authority and is never consumed by planning, approval, eligibility, insertion, undo, or a public route. It is not persisted as invocation state.

The claim is only sampled original-target equality under the existing target verifier. It is not delivery, cursor placement, button state, application acknowledgement, control activation, causal attribution, or semantic UI success. Neither target persistence nor a foreground/identity change implies semantic success.

## Private taxonomy

| Observation | Exact meaning |
| --- | --- |
| VERIFIED | A complete fresh sample matches the original trusted target identity/context and foreground, within the existing original-binding age window. |
| NOT_VERIFIED | Complete fresh evidence contradicts that equality. The original target is no longer verified/matching in the sample; no explanation or semantic outcome is inferred. |
| INDETERMINATE | Read/validation/resource-cleanup failure, incomplete or expired evidence, malformed result, or broken local binding prevents a conclusive observation. No cause is asserted. |
| No result (`None`) | No attempted effect, or read-only approval/abandonment. No post-observation event is emitted. |

Unavailability that prevents complete trusted evidence remains INDETERMINATE rather than being asserted as a known target change. The Phase 6.5 age rule is preserved exactly: `acquired_from <= acquired_to <= t0 <= t1 <= acquired_to + MAX_AGE_NS` (currently one second). Confirmation delay or a slow effect can expire the original binding even when fresh pre-effect eligibility passed. No timestamp refresh, replacement baseline, or weakened age check repairs that result.

## Ordering and bounded reads

1. Existing preparation binds the original target, single-left-click action, and point to exact one-use confirmation.
2. Existing consume path checks exact binding/services/registration, consumes confirmation, reevaluates policy, obtains fresh target/hit eligibility, normalizes the original point, and checks the binding again.
3. Existing local receipt fallback/construction and one native batch execute unchanged. No Phase 6.12 code runs in the final pre-SendInput gap.
4. After the seam returns/raises, its valid receipt replaces the conservative fallback exactly as before. The existing eligibility audit is attempted on the normal path.
5. During finalization, only an attempted receipt triggers post-observation. The original binding is checked, one `verify_target(original_target)` is called, and exact result/binding validation follows. The finite sequence is clock, context, foreground, original-target identity, original-target identity, foreground, context, clock; failures can terminate it early. Existing native resource cleanup is read-resource cleanup only.
6. A separate fixed-message `POINTER_POST_OBSERVATION_OUTCOME` audit is attempted. Existing `POINTER_EFFECT_OUTCOME` audit and local confirmation/binding cleanup follow independently. A failure in eligibility audit still reaches post-observation finalization. Observation, either audit, or cleanup failure cannot erase an obtained effect receipt or accepted observation evidence.

There is no retry, polling, sleep, refocus, replacement target, screenshot, or second effect. Finite cardinality is not a wall-clock OS deadline. Audit delay before finalization can contribute to age expiry. The observation result survives repeated closed-invocation calls without granting additional reads or effects through the consume path. `approve()` remains read-only and gathers no post-effect observation.

Audit outcomes use enum values with fixed messages and empty details. Effect and observation have distinct event types. No HWND/PID/TID/process identity/coordinates/tokens/exceptions/titles are added to audit, and no EXECUTION_SUCCEEDED or undo claim is emitted for sampled equality.

## Residual TOCTOU and limitations

Samples are sequential, not atomic or continuous. Desktop context, foreground, identity, and application state may change between reads, after the sample, or during input processing. A target can change away and back undetected. Complete matching evidence cannot show that the application received or acted on the input, nor distinguish a neutral surface from a semantic control. The post read cannot resolve UIPI, partial insertion, unknown delivery, physical user interference, coordinate/monitor limitations, or uncertain button state. Original-binding expiry deliberately limits usefulness for long confirmations. Exact Python types and snapshots are trusted in-process conventions, not a sandbox against hostile Python monkeypatching.

## Non-scope

No new SendInput/mutation API, retries, compensating LEFTUP, SetCursorPos, mouse_event, pyautogui, keyboard or focus mutation. No double/right click, drag, scroll, arbitrary movement, autonomous GUI sequence, screenshot/OCR/CV/UIA/browser DOM, semantic control detection, semantic success, undo fiction, public pointer route, persistence, reusable authorization, or broader authority. Phase 6.11 effect implementation and executor API are unchanged.

## Tests added and validation pending

`tests/test_pointer_post_observation.py` adds fake-only coverage for INSERTED with matching and changed targets; unavailable, expired, malformed, and raising observation evidence; PARTIAL and INDETERMINATE attempts; NOT_ATTEMPTED with no post reads/events; exact receipt identity preservation; effect-seam exception; one post verification and fixed read ordering; repeated consume no retries; exact types/subclasses/tampering before and during reads; sanitized separate audits; audit and cleanup exception preservation; private frozen/redacted/noncopyable/nonpickleable result; read-only approve; no public route or alternate mutation source guards. Existing Phase 6.11 tests remain unchanged and preserve insertion/API expectations.

Static validation uses source/diff/status inspection, `git diff --check`, explicit new-file whitespace checks, mutation/public-route scans, and verification that protected Phase 6.11 implementation and HEAD/index remain unchanged. These checks are not runtime validation. Host must run the new fake-only suite and affected effect/binding/target/audit regression suites, then deterministic regression and syntax checks, before any pass or milestone claim. No test count here is a passing-test claim. No live native smoke is part of those checks.

Open review points: whether the deliberately preserved original-binding age window provides adequate observation availability after human confirmation; and host confirmation of exception/order/privacy cases. Any age-policy or return-API change requires a separately scoped review, not an implicit expansion of this candidate.
