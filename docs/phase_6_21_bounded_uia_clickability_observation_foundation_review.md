# Phase 6.21 — bounded UIA clickability observation foundation review

## Protected checkpoint and scope

Protected branch: \`nayeon-v1\`.

Protected Phase 6.20 checkpoint:

- commit \`e3b65139ea715df9afe35ef996b01a0ccd430a3c\`;
- annotated tag \`nayeon-v1-approval-bound-uia-runtime-identity-continuity-01\`;
- full regression baseline: 1,507 tests.

Phase 6.21 is observation-foundation work only. Production changes are limited to:

- \`nayeon/services/ui_element_observation.py\`;
- \`nayeon/services/scoped_ui_element_observation.py\`.

The Phase 6.20 pointer binding, executor, confirmation service, pointer effect, coordinate
normalization, hit validation and DPI execution context remain unchanged. Phase 6.21 adds
no pointer authority, no new confirmation semantics and no new execution route.

## Native contract

The new private reader uses exactly:

\`IUIAutomationElement::GetClickablePoint(POINT *clickable, BOOL *gotClickable)\`

through IUIAutomationElement vtable slot **84**.

The existing private \`_POINT\` structure uses two signed 32-bit LONG-compatible fields.
The BOOL output is read into a local \`ctypes.c_int32\`.

The low-level reader:

1. requires the existing owning initialized UIA thread and retained element;
2. resolves slot 84 once through the existing private \`_method\` helper;
3. allocates one local \`_POINT\` and one local 32-bit BOOL;
4. calls GetClickablePoint exactly once;
5. requires S_OK through the existing exact HRESULT check;
6. accepts only BOOL values 0 and 1;
7. when BOOL is 1, validates the local POINT values as signed Int32-compatible values;
8. returns only exact Python \`False\` or \`True\`;
9. discards the provider-returned coordinates before returning;
10. sanitizes every failure to \`OSError("Private clickability sample unavailable.")\`.

No clickability coordinate, native pointer or new retained object state is added to
\`_UIANative\`.

The Phase 6.14 standalone \`_UIElementEvidence\`, \`_UIElementResult\` and
\`_UIElementObservationService\` remain structurally and behaviorally unchanged. The
standalone service does not call GetClickablePoint.

## Same-worker composite ordering

The sealed Phase 6.19 scoped PMv2/MTA composition is extended on the same retained
ElementFromPoint result and same owned worker.

The reviewed UIA sampling order is:

1. exact-point physical coordinate certification;
2. COM MTA initialization;
3. CUIAutomation activation;
4. one \`ElementFromPoint\` at the original point;
5. \`CurrentControlType\`;
6. \`CurrentIsEnabled\`;
7. \`GetRuntimeId\`;
8. \`GetClickablePoint\`;
9. local validation and exact-point recheck;
10. release retained UIA element;
11. release automation object;
12. CoUninitialize;
13. exact-point recheck;
14. construct the private composite result;
15. Phase 6.16 restores and verifies the exact prior DPI context;
16. only then may the caller publish the scoped result.

No nested worker, retry, polling, focus change, window mutation, pointer mutation or
alternate click location is introduced.

## Evidence contract

\`_ScopedUIElementEvidence\` now contains:

- the exact original \`_ProposedPoint\`;
- awareness = 2;
- reviewed control type;
- exact enabled bool;
- validated opaque Runtime ID tuple;
- exact \`clickable\` bool.

The clickability field accepts only the exact Python bool type. Integer 0/1, bool/int
subclasses, floats, strings, None and other values are rejected.

Both \`clickable=True\` and \`clickable=False\` are complete descriptive observations and
may produce a VERIFIED Phase 6.21 result. False is **not** NOT_VERIFIED and does not deny
pointer execution in this phase.

The provider-returned clickable POINT is deliberately not retained. In particular it is
not:

- a replacement for the human-approved point;
- placed in the operation or confirmation binding;
- stored in an audit, verification result, memory or cache;
- exposed to a model/public capability;
- sent to coordinate normalization or SendInput.

## Narrow VERIFIED meaning

VERIFIED means only that, for the same exact physical point certified under PMv2, one
complete bounded UIA sample was obtained from the same retained element on the same
owned MTA worker, including a valid control type, exact enabled state, opaque Runtime ID
and exact provider-reported clickable-point availability bool, followed by clean UIA
teardown and exact DPI restoration.

It does **not** establish:

- semantic target correctness or user intent;
- that the exact human-approved point is itself clickable;
- durable element identity;
- future visibility or lack of occlusion;
- click delivery;
- application action success;
- UI state success or task success;
- elimination of sequential-sample TOCTOU.

A provider may expose imperfect or inconsistent UIA information. A reported clickable
point is descriptive provider evidence only.

## Authority boundary

Phase 6.20 pointer binding is byte/content protected and contains no reference to
\`clickable\`.

Therefore Phase 6.21 does not branch execution on the new field. Integration, if later
approved, belongs to a separate Phase 6.22 architecture/safety review.

The final existing pointer path remains unchanged:

fresh target/hit/UIA Runtime-ID continuity -> coordinate normalization -> bounded insertion.

Coordinate normalization remains the final native desktop/state sample before the
existing SendInput insertion path.

## Validation

Codex GPT-6.1 Sol / Medium produced the initial two-file production edit under the
approved scope. Its workspace sandbox could not resolve the installed host interpreter,
so it was stopped rather than allowed to download/install another runtime. It did not
download or install Python, packages or tools in Phase 6.21.

All authoritative runtime validation below was performed independently on the Windows
host with:

\`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe\`

Python 3.12.10.

Final validation:

- focused native/scoped/pointer compatibility: **85/85 passed**;
- affected UIA/DPI/pointer/confirmation/verification/executor suites: **454/454 passed**;
- full unittest discovery: **1,517/1,517 passed**;
- \`python -m compileall -q nayeon tests\`: PASS;
- \`git diff --check\`: PASS;
- production scope scan: exactly the two approved UIA observation service files changed;
- protected Phase 6.20 pointer/executor/confirmation/effect/coordinate/hit/DPI files: unchanged;
- \`GetClickablePoint\` native contract reference: one reviewed production occurrence;
- scoped \`.clickable_point_available()\` call: exactly one;
- \`pointer_binding.py\` occurrences of \`clickable\`: zero;
- forbidden mutation/action/selector APIs: absent from production changes.

New/updated tests cover:

- exact vtable slot 84 and POINT*/BOOL* ABI;
- one native call only;
- BOOL 0 -> False and BOOL 1 -> True;
- malformed BOOL/HRESULT/exception failure sanitization;
- owner-thread and retained-element requirements;
- provider-coordinate non-retention;
- same-worker ordering and cardinality;
- True/False descriptive evidence semantics;
- exact bool invariants and tamper rejection;
- clickability-stage failure cleanup and DPI restoration;
- point mutation and restoration-failure fail-closed behavior;
- redacted/frozen evidence;
- Phase 6.20 authority-file protection and absence of pointer integration.

## Controlled read-only native smoke

After deterministic validation, human authorization was obtained for one
production-default read-only Windows smoke through the exact scoped observation
service at `_ProposedPoint(0, 0)`.

The first orchestration attempt was blocked by the remote-execution safety layer before
the smoke process started; therefore no UIA sample or desktop mutation occurred on that
attempt. The same authorized smoke was then executed in smaller steps.

Observed result:

- caller DPI awareness before: `0`;
- scoped result: `VERIFIED`;
- evidence present: `True`;
- scoped awareness: `2`;
- control type: `50026`;
- enabled: `True`;
- clickable: `True`;
- clickability Python type: exact `bool`;
- evidence retained the identical original point object: `True`;
- Runtime ID type: exact `tuple`;
- Runtime ID length: `6`;
- every Runtime ID item: exact Python `int`;
- every Runtime ID item: within signed Int32 range;
- caller DPI awareness after: `0`;
- caller DPI context equal before/after: `True`;
- caller thread unchanged: `True`.

The raw Runtime ID values and the provider-returned clickable coordinates were not
printed, logged, hashed or persisted. The smoke did not move the cursor, click, type,
focus/refocus a window, modify a window, call SendInput, or substitute any provider
point for the approved point.

This establishes interoperability for one real Windows UIA provider/sample on this
host: slot 84 returned a valid BOOL under the existing PMv2/MTA lifecycle and cleanup
and DPI restoration completed successfully. It does not establish provider behavior
across applications, semantic intent, exact-point clickability, click delivery, UI
state success, task success, durable identity, or elimination of TOCTOU.

## Residual risk and next gate

No live effect or native mutation smoke has been performed. No commit, tag, push or
workbook update has been made.

Phase 6.21 has now validated the new read-only native primitive against one real Windows
provider. Remaining risks are provider/application diversity, imperfect provider
metadata, sequential-sample TOCTOU, and the fact that `clickable=True` remains
descriptive evidence only. Pointer-authority integration remains a separate Phase 6.22
architecture/safety decision.
