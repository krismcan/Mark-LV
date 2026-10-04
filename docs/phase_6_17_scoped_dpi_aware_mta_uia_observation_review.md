# Phase 6.17 - Scoped DPI-aware MTA UIA observation integration

## Candidate and protected checkpoint

This uncommitted candidate starts on branch `nayeon-v1`, HEAD
`ab646bc51f34d9fd4a7ee747671465c92c0aada5`, with tag
`nayeon-v1-scoped-dpi-execution-context-01` at HEAD. The starting tree was clean
and matched every protected checkpoint requirement. No discrepancy was found.

Only these three files are added:

- `nayeon/services/scoped_ui_element_observation.py`
- `tests/test_scoped_ui_element_observation.py`
- `docs/phase_6_17_scoped_dpi_aware_mta_uia_observation_review.md`

Phases 6.14, 6.15, and 6.16 production modules remain unchanged. The pointer
binding and effect modules also remain unchanged. No commit, tag, push, workbook
edit, package installation, or networking was performed. A separate controlled
read-only live UIA smoke was run by the human orchestrator after deterministic
validation and is recorded below.

## Exact narrow VERIFIED claim

VERIFIED means only that the exact original point was certified physical under
per-monitor awareness and one complete bounded UIA sample was obtained at those
same snapshot coordinates on the same owned PMv2/MTA worker, with clean UIA
teardown and clean DPI restoration verified before publication.

It does not establish intended element identity, clickability, actionability,
visibility, semantic match, action success, task success, or reusable authority.
An enabled value of `False` is a valid descriptive sample and can be VERIFIED.

`_ScopedUIElementObservationService.observe(point)` is private, with no public
exports or execution/model route. Its exact private evidence contains only the
original point object, awareness `2`, reviewed control-type integer, and exact
enabled bool. Evidence and result types are frozen/slotted, redacted,
noncopyable, and nonserializable. They retain no native context, COM pointer,
HRESULT, exception, HWND, PID, name, AutomationId, class, rectangle, or native
object. Factory seams are trusted local deterministic test seams, not untrusted
inputs or authorization.

## Same-thread lifecycle and sealed primitive reuse

The caller rejects unsupported platforms and snapshots/revalidates one exact
existing `_ProposedPoint` before creating the scope. Each observation creates a
fresh Phase 6.16 `_ScopedDpiExecutionContext`; its `run` owns one non-daemon
worker and joins it synchronously.

On that single worker, in order:

1. Phase 6.16 captures the prior context, establishes temporary
   `DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2`, and verifies PMv2/awareness `2`.
2. The callback constructs Phase 6.15 `_PhysicalCoordinateContractService`
   directly, revalidates the snapshot immediately before certification, and
   certifies the same original point. Both contract awareness reads execute on
   this worker. After certification it revalidates the snapshot and the exact
   `_PhysicalCoordinateResult`, including exact evidence, VERIFIED status,
   awareness `2`, and original point object identity.
3. The callback constructs Phase 6.14 `_UIANative` directly on this worker.
   `initialize` performs MTA `CoInitializeEx`; `activate` performs
   `CoCreateInstance`. Immediately before lookup it revalidates the snapshot.
4. One `ElementFromPoint` consumes the original snapshot integers unchanged.
   One `CurrentControlType` read precedes one `CurrentIsEnabled` read. The sealed
   `_sample_valid` checks the reviewed ID set and exact bool. The point is
   revalidated after sample acquisition.
5. Cleanup attempts `release_element`, `release_automation`, then `uninitialize`
   exactly once each whenever native construction completed. The sealed facade
   releases acquired references and balances successful initialization with
   `CoUninitialize`, including the successful S_FALSE initialization case.
6. The callback revalidates after cleanup and constructs only private composite
   evidence/result data. No COM reference crosses the worker boundary.
7. Phase 6.16 restores and verifies the prior DPI context. Failed restoration
   discards the callback value. Only clean scope completion can publish it.
8. After the joined scope returns, the caller revalidates the exact scoped
   result, completion bool, exact composite result/evidence, point object
   identity, and unchanged snapshot before returning VERIFIED.

The composition imports existing private primitives; it binds no native API.
It never calls Phase 6.14's observation service or Phase 6.16's scoped coordinate
wrapper, which would introduce a second worker and lose the DPI override.

## Failure semantics

Unsupported/non-Windows, malformed, subclass, fake, tampered, incomplete,
exception, coordinate-certification failure, UIA lifecycle failure, UIA cleanup
failure, scope failure, or DPI restoration failure produces INDETERMINATE with
no evidence. Production has no NOT_VERIFIED path. Native exceptions and HRESULT
details do not escape or become result data.

Cleanup proceeds through all three steps despite a failed acquisition/property
read or an earlier cleanup failure. Native-construction failure has no returned
facade to clean. The sealed facade owns partial activation/lookup references,
so conservative cleanup also handles partially acquired references. There are
no retries, sleeps, polling, persistent workers, pools, caches, hard termination,
or timeout abandonment. The synchronous join has no hard native deadline; a
hung native provider can block the caller.

## Explicit non-scope and limitations

No pointer movement/click, SendInput, cursor API, pointer execution/verification
integration, keyboard/focus/window mutation, screenshot, OCR, vision,
InvokePattern, ValuePattern, SetValue, tree walk, selector/search, semantic
matching, capability, intent, dispatch, model route, audit, undo, policy,
confirmation, or public tool is added. No process-wide DPI API, manifest/startup
change, conversion, scaling, rounding, clamping, or monitor arithmetic is added.

This composes Phase 6.14's bounded observation, Phase 6.15's physical identity
contract, and Phase 6.16's scoped DPI worker without altering their baselines.
It remains detached from pointer execution. It makes no claim about final
pre-SendInput timing or the existing execution TOCTOU gap. All checks are
sequential point-in-time checks; mutation away and back between checks and UI
changes between samples are not excluded. Observation is not reusable authority.

After Codex completed and the candidate files were frozen, the human orchestrator
ran one production-default, read-only Windows UIA smoke using exact
_ProposedPoint(0, 0). It performed no pointer, keyboard, focus, window,
screenshot, model, or network mutation.

Live results:

- caller DPI awareness before: 0 (DPI_UNAWARE);
- composite result: VERIFIED;
- evidence present: True;
- evidence awareness: 2 (PER_MONITOR_AWARE);
- UIA control type: 50033;
- UIA enabled: True;
- evidence retained the same exact point object: True;
- caller DPI awareness after: 0;
- caller thread unchanged: True;
- smoke result: PASS.

This live smoke proves the reviewed composition can establish the scoped PMv2
coordinate contract, initialize/use/tear down real UI Automation on that worker,
restore DPI state, and publish bounded evidence on this host. It still proves no
semantic intent, clickability, action result, task success, or pointer-execution
TOCTOU property.

## Validation actually performed

Validation used the existing Windows virtual environment, Python **3.12.10**.
The sandboxed interpreter launch initially failed to access its base executable;
approved execution outside that sandbox used the same environment successfully.
The first focused run had 18 tests with one test error caused by an incorrect
sealed pointer-binding path in the new test. Correcting it to
`nayeon/agent/pointer_binding.py` resolved the local test defect; no production
baseline was modified.

Final results (counts are unittest test methods; parameterized subcases exercise
additional malformed values and failure stages):

- `.\.venv\Scripts\python.exe -m unittest tests.test_scoped_ui_element_observation -v`:
  **18/18 passed**, no skips.
- `.\.venv\Scripts\python.exe -m unittest tests.test_pointer_binding tests.test_pointer_coordinates tests.test_pointer_coordinate_contract tests.test_pointer_effect tests.test_pointer_hit_validation tests.test_pointer_observation tests.test_pointer_post_observation tests.test_pointer_verification tests.test_ui_element_observation tests.test_dpi_execution_context tests.test_scoped_ui_element_observation -q`:
  **282/282 passed**, no skips (sealed affected baseline 264 plus 18 new tests).
- `.\.venv\Scripts\python.exe -m unittest discover -v`:
  **1462/1462 passed**, no skips (sealed full baseline 1444 plus 18 new tests).
- `.\.venv\Scripts\python.exe -m compileall -q nayeon`: **PASS**.
- `git diff --check`: **PASS**. Separate `git diff --no-index --check` checks
  against `nul` cover all three untracked candidate files: **PASS**.

Independent orchestrator validation then reran the final frozen candidate with
C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe
(Python 3.12.10): 18/18 focused, 282/282 affected, 1462/1462 full
regression, compileall PASS, tracked git diff --check PASS, and separate
untracked-file whitespace checks PASS. Candidate SHA-256 hashes remained
unchanged across that validation.

Focused tests prove exact lifecycle order/cardinality, fresh scope/worker,
same-thread certification and native construction/use, snapshot coordinates,
coordinate-result exactness/status/evidence/awareness/identity, every UIA
lifecycle failure and conservative cleanup, malformed/incomplete scopes,
restoration discard, point mutation across lifecycle stages and after joining,
reviewed control types and exact bools, early platform rejection, private
invariants and copy/serialization protection, and static no-route/no-mutation/
no-nested-worker guards. A Git-content comparison verifies the three sealed
production modules plus pointer binding/effect against the protected commit,
normalizing Windows checkout line endings only.

HEAD and milestone tag remain unchanged. The intended handoff tree contains
only these three untracked candidate files, with no staged changes. No
commit/tag/push was performed.
