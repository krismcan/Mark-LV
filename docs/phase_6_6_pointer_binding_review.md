# Phase 6.6 executor-owned target and pointer intent binding candidate

Status: HOST VALIDATED — HUMAN SEAL APPROVED. This document records the validated pre-seal candidate state.

## Protected starting checkpoint and changed files

Branch nayeon-v1, HEAD c4b2b6163c632c0e9928eaa73cd426098af3c60a,
local origin/nayeon-v1, and the dereferenced annotated tag
nayeon-v1-target-validation-01 matched at startup. The working tree was clean.
No fetch was performed; origin is a local remote-tracking reference.

Changes are limited to nayeon/agent/executor.py, the new private module
nayeon/agent/pointer_binding.py, tests/test_pointer_binding.py, the narrow historical
assertion update in tests/test_target_validation.py, and this document.
Phase 6.5 production target validation, policy, confirmation, legacy focus, keyboard,
capability registration, semantic interpretation, dispatch, and undo are unchanged.
No commit, staging, tag, push, workbook update, or live desktop operation occurred.

## Exact trust contract

ActionExecutor._pointer_invocation owns a lexical context containing exactly one
private _PointerInvocation. It creates no executor cache or pending-operation
registry. The owner can prepare once, approve once, and is closed on context exit,
approval success, mismatch, error, or repeated preparation. It clears the operation,
target, action, independent scalar snapshot, confirmation, and acquisition service.
The existing ConfirmationService retains only its normal short-lived in-memory
pending confirmation while the invocation is open; closing consumes/rejects it.
An escaped object cannot reopen the owner or be accepted by another invocation.
This API is private trusted orchestration only; no model/public capability or
human-facing approval UI is added. Calling its approval method represents a trusted
human-approval handoff in deterministic tests, not evidence of actual human approval.
A future UI adapter must supply that handoff; models must never call it.

_PointerAction and _PointerOperation are frozen, slotted, and redacted. The action
vocabulary has exactly SINGLE_LEFT_CLICK and an exact empty tuple of parameters.
All nonempty parameters are rejected, including bool/int/coordinate tuples; wrong
exact types and subclasses are rejected. There are no integer action parameters.
Existing Phase 6.5 exact timestamp/identity validation rejects bool-as-int.
The intent has no executable location, current-cursor default, button/control
identity, DPI, hit-test, coordinate space, or implicit execution semantics.

Preparation requires authoritative registered non-reversible metadata explicitly
requiring confirmation. The metadata is copied privately to detect later changes.
The central PolicyService checks permission and policy before any target acquisition.
Only a CONFIRM decision permits preparation. The same trusted Phase 6.5 service
acquires the original target; there is no caller-supplied target or timestamp input.
The exact acquired object is retained, without reconstruction or refreshing its age.
Construction itself performs no native setup or reads. Injecting a service is an
exact-type trusted test seam, never a model/external data path.

ConfirmationService.create binds its one-time token to the exact operation object,
using a fixed sanitized request describing the location-free intent. Approval checks
identity of the operation, target, and action, validates their types/fields again,
and compares independent immutable scalar snapshots of target evidence and action
kind/parameters. Equal reconstruction, substitutions, and accidental frozen bypass
changes fail closed. It then consumes existing confirmation with the exact operation
identity and reevaluates central policy. Only a CONFIRM decision remains acceptable.
The return is a boolean binding-comparison result. No private evidence appears in
public ExecutionResult, audit details, or confirmation text. No execution-success
or undo events are emitted, and no undo is registered.

The new objects reject copy/deepcopy/pickle and have no serialization importer,
public export list, persistence path, global authority registry, or execution API.
These are misuse barriers, not protection against code that deliberately extracts
private fields (for example dataclasses.asdict) or modifies trusted process state.
The private owner is mutable lifecycle state; the bound operation and action are
immutable models. Existing Phase 6.5 evidence is not retrofitted with new export rules.

## Fresh validation and future mutation seam

Phase 6.6 does not call verify_target. Confirmation delays commonly exceed the
Phase 6.5 one-second acquisition age, and binding equality must not imply fresh
execution eligibility. No validation result or boolean grants native authority.
For future approved mutation, the executor must consume its exact approved operation,
verify the ORIGINAL _TargetBinding on the SAME acquisition service immediately before
the effect within that same operation, and fail closed on anything except VERIFIED.
This must occur after exact human confirmation and the permission/policy recheck.
It must never substitute a new target/timestamp to rescue an expired operation.
The current approval closes immediately because there is no effect to perform;
a future executor-owned verify-and-act seam is not implemented here.

Adding a location later changes the action contract and approval identity and
requires a separately reviewed coordinate/control contract and a new approval.
Existing location-free confirmations cannot authorize a later parameterized click.
Phase 6.5 sampled-equality and 1,000,000,000 ns semantics remain exactly unchanged.
They establish equality across bounded samples, not continuous OS identity, control
safety, an atomic transaction, a native deadline, or elimination of TOCTOU races.
A window can change or its identifiers can be recycled between observations.

Python in-process privacy is not a cryptographic provenance boundary. Arbitrary
trusted code can construct _TargetBinding or bypass frozen fields with object
mutation. Provenance rests on executor ownership calling the trusted acquisition
service, exact retained object identity, independent snapshots, and the absence of
untrusted import/target-supply routes. The owner rejects later reconstruction;
it cannot protect against malicious code replacing the owner/service itself.
Legacy _FocusBinding/_TextBinding cannot construct a pointer operation. No legacy
approval semantics or new expiry requirement is imposed on them.

## Validation

Independent host validation used C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe on Windows 11 AMD64 / Python 3.12.10.

Focused Phase 6.6 and affected-boundary suites:

    python -m unittest -q tests.test_pointer_binding tests.test_target_validation tests.test_executor tests.test_structured_executor tests.test_policy_confirmation tests.test_window_focus tests.test_keyboard_text tests.test_pointer_observation

Result: 269 tests run; 269 passed; 0 failures/errors.

Full regression:

    python -m unittest discover -q

Result: 1,257 tests run; 1,257 passed; 0 failures/errors/skips reported by unittest.

Additional validation passed:

    python -m compileall -q nayeon
    python -m nayeon.environment
    git diff --check

Environment diagnostics reported Windows 11 (AMD64) and Python 3.12.10 as OK. The host validation found no executable pointer mutation route and no regression in the affected focus, keyboard, policy, confirmation, executor, target-validation, or pointer-observation boundaries.

The earlier Codex sandbox interpreter block was a worker-environment limitation only; it is superseded by the successful independent host validation above.
## Non-scope and proposed later read-only smoke

No pointer movement, click, input injection, keyboard mutation, focus/refocus,
screenshot, OCR, vision, UIA, browser automation, native mutation implementation,
public pointer capability, legacy rewrite, persistent authority, or undo semantics.

After independent deterministic validation and explicit operator authorization,
a disposable-window read-only harness could invoke this private binding seam:
permission/policy evaluation, one baseline acquisition, human confirmation of the
location-free intent, exact binding comparison, and immediate disposal. A separate
existing Phase 6.5 read-only verification may demonstrate fresh sampled equality
without promoting its result into authority. All results must be sanitized; no
private evidence/tokens retained. Expiry or context mismatch is a failed observation,
not a reason to recapture and continue. No automated desktop mutation is permitted.
No smoke was run in this implementation session.

## Final filesystem review

The successful independent host validation above supersedes the earlier Codex sandbox
interpreter limitation. The obsolete temporary session-block document was removed.
The final candidate is limited to the five expected Phase 6.6 files: executor integration,
the private pointer-binding module, pointer-binding tests, the narrow Phase 6.5 guard
update, and this review document. HEAD remained the protected
c4b2b6163c632c0e9928eaa73cd426098af3c60a until the explicit human seal gate.
No live desktop mutation occurred and no workbook update is part of this seal.
