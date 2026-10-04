# Phase 6.19 - Bounded UIA Runtime Identity Foundation review

## Protected checkpoint and scope

Started on `nayeon-v1`, HEAD `f3742615f79da1be2cf34ce9c207b42bd9456245`,
tag `nayeon-v1-pre-effect-scoped-uia-trust-gate-01` at HEAD, with a clean tree.
No checkpoint discrepancy was found. HEAD and the tag remain unchanged.

Production changes are confined to:

- `nayeon/services/ui_element_observation.py`: only `_UIANative` changes.
- `nayeon/services/scoped_ui_element_observation.py`: bounded opaque tuple
  validation, scoped evidence field, and same-worker acquisition.

Tests change only `tests/test_ui_element_observation.py`,
`tests/test_scoped_ui_element_observation.py`, and `tests/test_pointer_uia_gate.py`.
Historical observation-service seals now permit the two explicitly approved
service extensions. Unrelated service seals remain. An AST guard proves all
Phase 6.14 module definitions outside `_UIANative` remain unchanged. The standalone
service still reads only control type/enabled and its evidence/result contract
is unchanged. This review document is the sixth changed/added file.

## Native contract and ownership

`IUIAutomationElement::GetRuntimeId` occupies vtable slot **4**: IUnknown slots
0 through 2, SetFocus slot 3, then GetRuntimeId. The exact signature is
`HRESULT GetRuntimeId(SAFEARRAY **runtimeId)`. The returned array contains
32-bit signed integers. Runtime ID is opaque, unique only within the current
desktop/UI instance, and may be reused over time; its format may change.
It is not semantic or durable identity and provides no click authority or
reusable authorization. No integer contents, prefixes, or structure are parsed.
See the [Microsoft GetRuntimeId contract](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationelement-getruntimeid).

The owning thread must already retain an initialized element. The reader binds
slot 4 with signed 32-bit HRESULT and an out pointer to SAFEARRAY pointer, calls
it once on that element, and performs no additional lookup or traversal.
OleAut32 functions have explicit argtypes/restype: SafeArrayGetDim returns UINT;
GetVartype writes a 16-bit VARTYPE; bounds and indices use signed 32-bit LONG;
GetElement receives a signed 32-bit output buffer; all HRESULTs use `c_int32`.
No dependency is added.

Every returned non-null SAFEARRAY is owned by this read, including a partial
array returned with failed HRESULT or an exception after the out pointer is set.
A finally block consumes its local ownership and attempts SafeArrayDestroy
exactly once on every such path. Null arrays have no destroy attempt. Destruction
is never retried. Failure or exception during destruction rejects the sample;
no tuple is returned before successful destruction. Native errors, HRESULTs,
and addresses are replaced by a fixed redacted failure message.

Validation requires exactly one dimension, successful GetVartype with **VT_I4
(3)**, successful exact signed-32-bit lower/upper bounds, and ordered bounds
with **1..64** elements. `MAX_RUNTIME_ID_INTS = 64` is shared from the private
native facade into the scoped module. Failed GetVartype is conservatively
rejected rather than guessing the storage type. Python integer arithmetic checks
the length without overflow before any item reads. Empty, reversed, excessive,
or overflow-sized ranges are rejected without item reads. GetElement reads each
item once in original index order into `c_int32`. Only an immutable tuple of
exact Python ints can be returned; no SAFEARRAY or native pointer is retained
or exposed in the result. SafeArrayAccessData is not used.

[SafeArrayGetElement](https://learn.microsoft.com/en-us/windows/win32/api/oleauto/nf-oleauto-safearraygetelement)
manages its own lock/unlock for each element. The sole explicit cleanup uses
[SafeArrayDestroy](https://learn.microsoft.com/en-us/windows/win32/api/oleauto/nf-oleauto-safearraydestroy).

## Same-worker lifecycle and evidence

The existing single joined PMv2/MTA worker now performs this exact order:

1. Establish and verify PMv2 scope.
2. Verify the physical coordinate contract for the identical original point.
3. Initialize COM MTA.
4. Activate CUIAutomation.
5. Call ElementFromPoint once with the exact coordinate snapshot.
6. Read CurrentControlType.
7. Read CurrentIsEnabled.
8. Read GetRuntimeId from the same retained element, validate its SAFEARRAY,
   and destroy the array before returning the tuple.
9. Validate exact reviewed control type, exact bool, and bounded runtime tuple.
10. Recheck the exact point snapshot.
11. Release the element once.
12. Release automation once.
13. CoUninitialize once when initialized.
14. Recheck the exact point snapshot.
15. Construct the scoped evidence/result.
16. Restore and verify the prior DPI context through the unchanged Phase 6.16 scope.
17. Validate and publish on the caller only after clean joined scope completion.

`_ScopedUIElementEvidence` is frozen, slotted, redacted, noncopyable and
nonpickleable. Its fields are the identical original `_ProposedPoint`, exact
awareness integer 2, exact reviewed control-type integer, exact bool enabled,
and exact tuple `runtime_id` of 1..64 exact ints within signed int32 range.
Lists, subclasses, bools, floats, non-ints, empty/excessive tuples and out-of-range
ints fail the invariant. There are no parsing helper properties. Runtime values
live only in temporary read state and ephemeral scoped evidence; they are not
hashed, logged, audited, persisted, cached, placed in memory, or exported to
public verification evidence.

VERIFIED means only same-point physical certification plus one complete bounded
descriptive sample, clean UIA teardown, and verified DPI restoration. It does
not establish intended element identity, semantic match, visibility, clickability,
actionability, action result or task success. Runtime acquisition, validation or
destroy failure gives INDETERMINATE with no evidence, while UIA teardown and DPI
restoration still run.

## Preserved Phase 6.18 authority and ordering

`pointer_binding.py`, `executor.py`, `pointer_effect.py` and
`pointer_coordinates.py` were never written. Guards compare protected HEAD
content (accounting for the existing LF/CRLF checkout representation), require
empty Git diffs, and check raw checkout SHA-256 bytes for all four files. The
checkout contains mixed newline representations; a guard must preserve them.

Phase 6.18 still validates the scoped result/evidence, requires enabled=True
as a prerequisite only, ignores runtime_id, discards all UIA evidence, then
normalizes coordinates and inserts exactly as before. The extended evidence
invariant validates tuple shape locally; pointer code does not read or branch
on its contents. Every reviewed control type remains equivalent, and different
valid opaque tuples give the same deterministic gate outcome. Permission,
policy, confirmation, audits, post-effect verification and undo remain unchanged.

No CompareElements or CompareRuntimeIds is introduced yet. No selector, tree
search, extra element property, pattern, focus/window/input mutation, public
capability, model/browser/vision route, persistence, retry, polling, timeout
worker pool or reusable identity authorization is added.

## Validation actually run

All Python commands used `.\.venv\Scripts\python.exe`, verified **Python
3.12.10**. Bare `python` is unavailable in the shell. The sandbox could not
initially access the virtual environment's base interpreter; approved escalation
allowed the same interpreter to run. No alternative interpreter or installation
was used. Tests use deterministic fakes/mocks, including a ctypes fake COM
vtable callback and mocked OleAut32; no real COM/UIA activation occurred.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_element_observation tests.test_scoped_ui_element_observation tests.test_pointer_uia_gate -q
```

**60/60 passed, no skips.** Covers slot/ABI, signed int32 order, 64-item limit,
invalid dimensions/type/bounds, null/partial arrays, each SAFEARRAY failure and
exception, late item failure, destruction failure without retry, thread/element
ownership, unchanged Phase 6.14 contract, exact same-worker lifecycle, failure
cleanup/restoration, evidence invariants/privacy, pointer tuple equivalence and
disposal, forbidden routes, production scope, and protected pointer bytes.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_pointer_uia_gate tests.test_pointer_binding tests.test_pointer_coordinates tests.test_pointer_coordinate_contract tests.test_pointer_effect tests.test_pointer_hit_validation tests.test_pointer_observation tests.test_pointer_post_observation tests.test_pointer_verification tests.test_target_validation tests.test_ui_element_observation tests.test_dpi_execution_context tests.test_scoped_ui_element_observation tests.test_verification tests.test_executor tests.test_structured_executor -q
.\.venv\Scripts\python.exe -m unittest discover -q
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
git diff --no-index --check -- nul docs/phase_6_19_bounded_uia_runtime_identity_foundation_review.md
```

**410/410 affected tests and 1492/1492 full regression tests passed, no skips.**
Compilation and tracked/untracked whitespace checks passed. Static source guards
and an explicit scan found no new forbidden native mutation, selector,
comparison, persistence or public route. Only the two approved production files
changed. A separate controlled read-only native smoke was authorized and run after the deterministic candidate was frozen; results are recorded below.
The untracked `--no-index --check` command returns 1 because the new document
differs from `nul`; it produced no whitespace diagnostics. Git's CRLF notices
are checkout-conversion notices, not whitespace failures.

The initial focused run exposed a fake vtable indirection error and a byte guard
that incorrectly assumed uniform CRLF. Both test defects were corrected before
the passing runs. No pointer production change was needed.

## Controlled read-only native smoke

After deterministic validation and independent host regression, human authorization
was obtained for one production-default read-only Windows smoke. It used the exact
_ScopedUIElementObservationService at _ProposedPoint(0, 0) with no pointer,
keyboard, focus, window, screenshot, model, network, or other side effect.

The first wrapper attempt failed before UIA because the diagnostic code called the
DPI helper with the wrong signature. No UIA sample or mutation occurred on that
attempt. The wrapper was corrected and the single native observation then returned:

- caller DPI awareness before: 0;
- scoped result: VERIFIED;
- evidence present: True;
- scoped awareness: 2;
- control type: 50020;
- enabled: True;
- evidence retained the identical original point object: True;
- runtime ID Python type: exact tuple;
- runtime ID length: 6;
- every runtime ID item: exact Python int;
- every runtime ID item: within signed Int32 range;
- caller DPI awareness after: 0;
- caller DPI context equal before/after: True;
- caller thread unchanged: True.

The raw Runtime ID integers were deliberately not printed, logged, hashed, or
persisted. A VERIFIED result demonstrates that the real provider on this host
returned a one-dimensional VT_I4 SAFEARRAY satisfying the bounded reader and
that array cleanup, UIA teardown, DPI restoration, and caller publication all
completed successfully. This is interoperability evidence for one real Windows UIA
provider/sample only; it does not establish semantic identity, durability,
clickability, actionability, task success, or behavior across all providers.
## Residual risks and handoff

Native provider calls and the joined worker still have no hard deadline. The
64-integer ceiling bounds reads, not native call latency. Provider data can be
unavailable or rejected by the conservative VT_I4 contract. Actual native
provider interoperability remains untested in this fake-only validation.
SafeArrayDestroy failure may leave native resources unreclaimed; the reader
never retries or publishes evidence on that path. Python exceptions cannot
contain native process faults from corrupt pointers. Sequential point-in-time
samples do not eliminate TOCTOU; reuse over time prohibits durable identity
claims. No new identity comparison or authority guarantee is made.

Handoff: five modified tracked files and this untracked document; nothing
staged. No commit, tag, push, workbook update or live effect. One separately authorized read-only native UIA smoke was completed as recorded above.
The candidate remains at the exact protected HEAD for review.
