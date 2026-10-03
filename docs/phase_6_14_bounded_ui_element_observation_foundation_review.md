# Phase 6.14 — Bounded UI Element Observation Foundation

## Candidate status

Implemented and locally validated as an **unstaged candidate** on branch `nayeon-v1`, protected baseline HEAD `e634a9d2f91d67617c802fd9696f1b1460f673ab` (Phase 6.13).

No commit, tag, push, spreadsheet update, live UI Automation observation, GUI action, or package installation has been performed.

## What Phase 6.14 adds

Phase 6.14 introduces one private read-only Windows UI Automation observation service. Given one exact trusted `_ProposedPoint`, it performs one bounded UIA lookup and captures only:

- the original exact point,
- the UIA control-type identifier,
- the exact enabled-state boolean.

The service uses `IUIAutomation::ElementFromPoint`, then reads `CurrentControlType` followed by `CurrentIsEnabled` in fixed order.

A complete validated sample maps to `VerificationStatus.VERIFIED`. Every unsupported, malformed, incomplete, failed, tampered, or cleanup-failed case maps to `INDETERMINATE`. Production does not emit `NOT_VERIFIED`.

## Minimal private COM boundary

The implementation uses a private ctypes COM boundary with no type-library generation and no pywinauto dependency.

Each observation owns one fresh windowless worker thread. COM is initialized on that owning thread with `CoInitializeEx(..., COINIT_MULTITHREADED)`. The UI Automation object and returned element remain on that thread. Cleanup releases the element, releases the automation object, and balances successful COM initialization with `CoUninitialize`.

There is exactly one `ElementFromPoint` lookup and exactly two required property reads. There is no retry, polling, sleep, tree traversal, selector search, cache, persistent native reference, or reusable authority.

Cleanup failure invalidates the sample. Native exceptions/HRESULT details never become evidence.

## Evidence and privacy boundary

Evidence/result objects are private, exact-type validated, frozen/slotted, redacted, noncopyable, and nonserializable. No UIA name, AutomationId, class name, rectangle, HWND, PID, native COM object, exception, or raw HRESULT is retained.

The reviewed control-type set is the standard UIA control-type ID range 50000 through 50040. Unknown IDs fail closed. Enabled state must be an exact Python bool after conversion from the native Windows BOOL.

## Exact VERIFIED claim

VERIFIED means only:

> One complete bounded UI Automation sample was obtained and validated for the supplied point, containing a reviewed control-type identifier and enabled-state value.

It does **not** establish that the element is the user's intended control, clickable, actionable, visible, semantically correct, related to a successful click, or evidence that any action/task succeeded.

## Coordinate-system limitation

Microsoft documents `IUIAutomation::ElementFromPoint` as consuming physical desktop screen coordinates. The existing Nayeon `_ProposedPoint` contract is a native Windows screen-space point and deliberately does not claim physical-pixel equivalence.

Therefore Phase 6.14 remains a **detached observation foundation**. It is not integrated into Phase 6.11–6.13 pointer execution or verification. A future integration phase must explicitly establish the DPI/coordinate mapping contract before using this primitive as evidence about an approved click location.

No silent logical-to-physical assumption is made here.

## Explicit non-scope

Phase 6.14 adds no clicking, pointer movement, keyboard input, focus change, InvokePattern, ValuePattern, SetValue, screenshots, OCR, computer vision, model vision, pywinauto, UI tree traversal, fuzzy search, selector engine, semantic element matching, executor route, capability registration, intent route, audit integration, undo behavior, retries, or autonomous GUI workflow.

## Validation performed

Using the project's exact Python 3.12 interpreter:

- Phase 6.14 focused fake-only tests: **12/12 passed**.
- Affected pointer/UIA suites: **229/229 passed**.
- Full regression: **1409/1409 passed**.
- `compileall`: passed.
- `git diff --check`: passed.
- Protected Phase 6.13 files were not modified.

The focused tests cover the successful bounded sample, exact read order/cardinality, every native lifecycle failure, cleanup failures, worker failures, malformed/tampered input, control-type and bool validation, unsupported platform behavior, exact result invariants, subclass rejection, privacy/nonserialization, and source guards.

## Runtime/live status

No live UI Automation query has been performed. The current evidence proves the deterministic service contract and regression compatibility; it does not yet prove successful interaction with a real Windows UIA provider on this host.

A harmless live read-only smoke, if desired, is a separate human-authorized validation step.

## Candidate files

- `nayeon/services/ui_element_observation.py`
- `tests/test_ui_element_observation.py`
- `docs/phase_6_14_bounded_ui_element_observation_foundation_review.md`

## Next gate

Candidate is ready for final static review. If that remains clean, the next human gate is whether to authorize a harmless live read-only UIA smoke before sealing Phase 6.14.
