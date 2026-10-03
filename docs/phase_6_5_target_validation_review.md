# Phase 6.5 private timestamped target validation candidate

Status: **HUMAN-APPROVED AFTER INDEPENDENT VALIDATION AND CONTROLLED SMOKE**.
The implementation has passed 26/26 focused Phase 6.5 tests and 1237/1237
full regression tests on the authorized Windows host using Python 3.12.10.
Environment diagnostics, compileall, and git diff --check also passed.

A controlled external disposable-window read-only smoke was then run after a
forbidden-mutation API preflight. The operator manually activated/clicked the
fixture; the harness performed one baseline acquisition followed immediately by
one fresh validation and returned `SMOKE_FRESH status=verified`. The harness
performed no automated mouse movement/clicking, keyboard input, focus/refocus,
screenshots, OCR, UI Automation, browser automation, or content scraping. The
temporary harness was terminated and deleted after the result was captured.

The human reviewed the result and approved Phase 6.5 for local milestone sealing.
No push or spreadsheet update is implied by that approval.

## Protected checkpoint and scope

Branch `nayeon-v1`, HEAD `127a5080511875d5c8b9bb948176fdd0c244411b`, tag
`nayeon-v1-desktop-pointer-observation-01`, and the local `origin/nayeon-v1`
reference match the requested checkpoint. The remote-tracking reference was
checked locally; no network fetch or remote-state claim is made. Startup had
only this untracked document from the previous stopped run. It has been replaced
with this candidate review. No baseline product files were edited.

The human-approved private trust-model extension is implemented in
`nayeon/services/target_validation.py`; new mocked checks are in
`tests/test_target_validation.py`. These and this document are the only changes.
No commit, staging, tag, push, spreadsheet operation, or live desktop work occurred.

## Private binding and acquisition

`_TargetBinding` is frozen, slotted, and repr/str-redacted. Its four fields are
exact `WindowIdentity`, exact `DesktopContext`, `acquired_from_ns`, and
`acquired_to_ns`. Construction requires existing identity/context validity,
root HWND equality, native pointer-width HWND/root bounds, exact built-in int
timestamps (bool and int subclasses rejected), nonnegative values, and ordered
acquisition endpoints. Validation rechecks binding validity before any IO.

The narrowest safe layer is a separate private read-only service. Phase 6.1's
foreground observation starts its clock AFTER initial context acquisition, so
its historical timestamps cannot bracket all required baseline evidence.
Phase 6.2 `_FocusBinding` retains no times; Phase 6.3 `_TextBinding` contains that
binding plus text. None can be converted into the new binding by adding a later
time. Their preparation, exact saved approval validation, executor comparison,
permission/policy/confirmation rechecks, and mutation eligibility remain unchanged.
The new binding is deliberately rejected by their existing binding validators.
No 1s expiry is silently imposed on legacy focus or text approval.

`_TargetVerificationService.acquire_target()` begins with its monotonic clock,
then initializes the query-only native facade and samples:

`C0 -> F0 -> I0(F0) -> I1(F0) -> F1 -> C1 -> final clock`.

Only complete matching context, identity and positive foreground samples produce
a baseline. The exact first/final clock values are retained, without substituting
observation timestamps or a later recapture. Acquisition failure raises a fixed
sanitized ValueError and returns no binding. Cleanup inside every native query
must finish successfully before evidence can be returned. No native setup/read
occurs during service construction. Unsupported platforms initialize no native
facade. The facade reuses existing `_WindowsNative` query and cleanup machinery.

The trusted internal caller owns the binding for one invocation, using acquisition
and validation on the same service and its one clock source (`perf_counter_ns` in
production). Injected native/clock/platform seams are trusted mocked-test inputs,
not model or external inputs. There is no public route, conversion API, approval
token, serialization importer, retained target, persistent cache, or registration.
Python privacy/redaction is not a security boundary against arbitrary in-process
code; hosts must not serialize private dataclasses wholesale or treat reconstructed
fields as trusted provenance. This primitive adds no transferable action authority.
No production capability calls it in this phase.

## Fresh validation and exact claim

`verify_target(binding)` samples once, without retries or reacquisition:

`t0 -> C0 -> F0 -> I0(approved hwnd) -> I1(approved hwnd) -> F1 -> C1 -> t1`.

It queries only the saved root identity, even when another window is foreground.
Successful scoped cleanup precedes each query's return and the final clock.
Both acquisition and validation use the same service clock callable and default
process-local monotonic domain. No wall clock or native FILETIME is used for age;
process creation FILETIME remains an identity field only.

The exact eligibility condition is:

`0 <= acquired_from_ns <= acquired_to_ns <= t0 <= t1 <= acquired_to_ns + 1_000_000_000`.

Every timestamp must be an exact built-in int. Equality between adjacent clock
samples is allowed by the nondecreasing monotonic interval contract. Exactly at
the upper bound is eligible; one ns beyond it is INDETERMINATE. The age comparison
uses **acquired_to_ns**, as approved, not acquired_from_ns. A long baseline interval
is retained honestly but does not change the approved age reference. The 1s bound
is eligibility/staleness only, not an OS deadline or uninterrupted lifetime claim.

VERIFIED requires complete valid supported evidence, eligibility, and
`C0 == C1 == approved context`, `I0 == I1 == approved identity`, and
`F0 == F1 == approved hwnd`. Its only claim is:

> The same approved root-window identity fields, supported desktop context,
> and foreground relationship were observed again during one fresh bounded
> validation interval.

NOT_VERIFIED requires complete fresh valid contradictory evidence. INDETERMINATE
takes precedence for missing, malformed, invalid, inaccessible, unsupported,
native/cleanup-failed, stale, reversed/overlapping-clock, or inconclusive evidence.
A supported session change with internally valid sampled identities is a
contradiction. Unsupported desktop/station/activity, nonroot identities, and
identity/context-incompatible session/desktop fields are invalid evidence and
remain INDETERMINATE rather than being promoted to trustworthy contradictions.
Zero/malformed foreground identifiers are missing/invalid, not positive evidence.

Matching fields cannot distinguish same-field HWND replacement or changes away
and back between samples. The tests explicitly demonstrate this indistinguishability.
There is no continuous window-object lifetime, subsequent input recipient,
child-control identity, DPI/occlusion/routing, or click-effect guarantee. No input,
focus, clipboard, title/content scraping, screenshots, OCR, UIA, browser, or model
targeting authority is introduced. The private result contains only a typed status
and is redacted; no new public receipt or audit integration exists.

## Deterministic coverage and execution status

The 26 new test methods cover order/cardinality and clock-before-native-setup,
strict binding validity, bool/subclass rejection, native HWND widths, frozen/slotted
redaction, defensive validity rechecks, no legacy authority conversion, identity
and context mismatch paths, foreground/process-instance drift, invalid/missing
evidence precedence, exceptions, exact freshness edges, reversed/malformed clocks,
unsupported platforms, indistinguishable same-field replacement/change-away-and-back,
no mutation authority, and scoped native resource cleanup.

Independent validation on the authorized Windows host completed successfully:
- Phase 6.5 focused suite: **26/26 PASS**
- Full unittest discovery: **1237/1237 PASS**
- `python -m nayeon.environment`: PASS (Windows 11 AMD64, Python 3.12.10)
- `python -m compileall -q nayeon`: PASS
- `git diff --check`: PASS

Codex's sandbox itself could not execute the repository venv because its isolated
environment could not access the configured host interpreter. That was an
environment-isolation limitation, not a test failure; no venv repair or substitution
was made inside the Codex sandbox.

## Controlled disposable-window READ-ONLY smoke (RUN)

An external Tk disposable root-window fixture was created outside the repository.
Before launch, the harness source was checked for forbidden mutation/input APIs.
The operator manually clicked its READ-ONLY verification button. One
`acquire_target()` call was followed immediately by one `verify_target()` call
using the same private service and monotonic clock domain.

Observed public result:

`SMOKE_FRESH status=verified`

This proves the real Windows path can establish the approved fresh sampled-equality
claim for the disposable fixture. It does **not** prove uninterrupted HWND/window
lifetime and grants no later interaction authority. No automated activation, mouse
movement/clicking, keyboard input, focus manipulation, screenshot/OCR/UIA/browser
automation, or content scraping was performed. The smoke process was terminated
and `C:\AI\phase6_5_target_smoke.py` was deleted after the test.

## Git handoff and verdict

Before milestone sealing, the protected predecessor remained
`127a5080511875d5c8b9bb948176fdd0c244411b` with its Phase 6.4 tag intact.
The Phase 6.5 candidate consists only of this review document,
`nayeon/services/target_validation.py`, and `tests/test_target_validation.py`.

Verdict: **APPROVED FOR LOCAL PHASE 6.5 MILESTONE SEALING** after independent
automated validation and the controlled read-only Windows smoke. Push and master
workbook update remain separate external-change gates.
