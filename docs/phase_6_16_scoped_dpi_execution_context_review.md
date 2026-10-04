# Phase 6.16 - Scoped Per-Monitor DPI-Aware Coordinate Execution Context

## Candidate and narrow claim

This uncommitted three-file candidate starts from branch `nayeon-v1`, HEAD
`5c23c7504ff4c5d1100c1a39798781d9b805ee7f`, tag
`nayeon-v1-pointer-coordinate-contract-01`. The starting tree was clean and
matched the requested checkpoint. Phase 6.15 remains sealed and unchanged.

One new non-daemon owned worker is created per supported run and synchronously
joined. Its native facade is constructed inside that worker. A checked temporary
PER_MONITOR_AWARE_V2 scope surrounds exactly one callback on the same worker.
Only clean setup, callback completion, restoration, and restoration verification
permit publication of the callback value. This does not prove a callback effect,
semantic identity, actionability, or task success. Callbacks and factories are
trusted private local implementation seams, not model input or a public route.

## Why an owned scoped thread

Approved Option A confines the override to a short-lived owned thread without
changing caller awareness, process defaults, manifests, or startup code. The
supplied earlier audit reported caller awareness 0, a successful PMv2 override
with awareness 2 and exact restoration, and stable physical display geometry.
These are prior audit observations, not live validation of this candidate.

There is no pool, persistent worker, cache, retry, sleep, or polling. The blocking
join has no hard native deadline; a hung native call can block the caller. No
thread termination or timeout abandonment is introduced.

## APIs, setup, and restoration

The native facade binds only five APIs with explicit ctypes signatures:

- `GetThreadDpiAwarenessContext`: no arguments, HANDLE result.
- `GetAwarenessFromDpiAwarenessContext`: HANDLE argument, integer result.
- `IsValidDpiAwarenessContext`: HANDLE argument, BOOL result.
- `AreDpiAwarenessContextsEqual`: two HANDLE arguments, BOOL result.
- `SetThreadDpiAwarenessContext`: HANDLE argument, HANDLE result.

The target is `DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = HANDLE(-4)`;
reviewed per-monitor awareness is 2. Pointer-sized handle representation stays
private. Scope metadata and coordinate evidence contain no native context handle.

Setup captures a non-null exact integer pointer-sized prior context and exact
prior awareness 0, 1, or 2. It validates PMv2, sets PMv2, requires the setter's
returned prior to compare equal to the captured prior, fetches a fresh current
context, and requires equality to PMv2 plus awareness exactly 2. Only then does
the callback run, exactly once.

The finally path attempts restoration exactly once after any target setter
attempt. This conservative rule includes an exception or malformed return that
could conceal a changed context. Restoration uses the captured prior and is not
a retry of setup. It requires a non-null setter return equal to PMv2, a fresh
restored context equal to captured prior, and restored awareness exactly equal
to captured prior awareness. No restore is attempted if setup fails before the
setter attempt. Failed restoration is never retried; the owned worker terminates
and no callback value is published.

Any setup/callback/restoration/comparison/validation/worker exception or mismatch
fails closed to a redacted incomplete result with no callback value. Native
exception details are neither retained in results nor logged. Unsupported
platforms fail before worker/native construction or callback invocation. Private
objects are slotted and redacted and reject copy, deepcopy, pickle, and ordinary
JSON serialization. Scope results are frozen.

## Coordinate wrapper

`_ScopedPhysicalCoordinateService.certify(point)` accepts only the exact existing
`_ProposedPoint`. Coordinates must remain exact signed Windows LONG integers;
booleans and integer subclasses are rejected. It snapshots/revalidates before
the worker, immediately before certification on the worker, and after joining.
The callback constructs the existing `_PhysicalCoordinateContractService` and
calls its existing `certify(point)` on the scoped worker, so both Phase 6.15
awareness reads occur on that SAME thread.

After clean restoration the wrapper revalidates the exact existing
`_PhysicalCoordinateResult` and evidence, requires VERIFIED, identical point
object and unchanged coordinates, then returns that exact existing result.
All other paths return the standard INDETERMINATE result with no evidence.
Production emits no NOT_VERIFIED. A fake VERIFIED result is discarded if restore
fails. Evidence describes the past worker sample, not caller awareness or
reusable authority. Sequential checks do not detect changes away and back
between samples.

## Non-scope and future integration

No process DPI-awareness APIs, manifest/startup changes, coordinate conversion,
scaling, rounding, clamping, monitor arithmetic, UI Automation, COM, semantic
execution, pointer/cursor/focus/keyboard effects, or public/model routes are
added. No capability/intent/dispatch/audit/undo/policy/confirmation integration
is added. Existing execution boundaries remain untouched. New production code
does not import or couple to `pointer_binding.py`, `pointer_effect.py`, or
`ui_element_observation.py`; none is modified.

Phase 6.14's `_MTAWorker` creates another thread. Nesting current `observe()`
under this DPI worker loses the thread override. Future integration must place
coordinate certification and UIA `ElementFromPoint` on the SAME owned DPI-aware
MTA thread with deliberate lifecycle ownership. This phase implements neither
MTA nor UIA and supplies no nested-worker workaround.

Future integration must preserve the existing tiny final pre-SendInput TOCTOU
gap. Certification/observation placement requires separate review. This phase
adds no work to that path and makes no TOCTOU guarantee.

## Validation

Host validation completed successfully on the Windows Python runtime used for the sealed Phase 6.x baseline.

- Focused Phase 6.16: **19/19 passed**.
- Affected pointer/UIA/DPI set: **264/264 passed** (the prior 245-test affected baseline plus 19 Phase 6.16 tests).
- Full regression: **1444/1444 passed** (the sealed 1425-test baseline plus 19 Phase 6.16 tests).
- `compileall -q nayeon`: **PASS**.
- Tracked and untracked whitespace/diff checks: **PASS**.
- Sealed `pointer_binding.py`, `pointer_effect.py`, and `ui_element_observation.py` remained byte-for-byte equal to HEAD during candidate validation.

A controlled live smoke exercised the production `_ScopedPhysicalCoordinateService` once with an inert exact `_ProposedPoint(0, 0)`.

Results:

- caller awareness before: `0` (DPI_UNAWARE);
- caller awareness after: `0`;
- caller DPI-awareness context restored equal to the pre-smoke context: `True`;
- caller thread unchanged: `True`;
- Phase 6.15 coordinate result returned by the scoped worker: `VERIFIED`;
- evidence present: `True`;
- evidence awareness: `2` (PER_MONITOR_AWARE);
- evidence retained the same exact point object: `True`;
- smoke result: `PASS`.

The smoke made no UI Automation call and no pointer, keyboard, focus, window, or screen mutation. The only mutable native state was the owned worker thread's temporary DPI-awareness context, which the production boundary restored and verified before publishing the coordinate result.
