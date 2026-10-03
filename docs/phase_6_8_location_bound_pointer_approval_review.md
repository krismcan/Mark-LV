# Phase 6.8 exact location-bound pointer approval review

Status: HOST VALIDATED — READY FOR HUMAN SEAL REVIEW.
No commit, tag, push, or Google Drive workbook update has occurred.

## Protected predecessor

Phase 6.8 started from the clean sealed Phase 6.7 checkpoint:

- branch: `nayeon-v1`
- commit: `b569118752404365e7d53c659b348b5af14b5296`
- tag: `nayeon-v1-pointer-hit-validation-01`
- `origin/nayeon-v1`: same commit
- predecessor full regression: 1,276/1,276

## Exact Phase 6.8 claim

Phase 6.8 changes the private approval identity from:

`target + SINGLE_LEFT_CLICK`

to:

`target + SINGLE_LEFT_CLICK + exact proposed native screen point`

The approved point must first pass the existing Phase 6.7 bounded read-only
pointer hit validation against the newly acquired Phase 6.5 target binding.

The approval claim is therefore:

> The human-confirmation token is bound to one exact private composite operation
> containing the acquired target, the single-left-click intent, and the exact
> proposed native screen point that passed preparation-time hit validation.

This is an approval-identity claim only.

It is NOT a claim that the location is still fresh at approval time or execution
time, and it is NOT click authority.

## Why Phase 6.8 exists

Phase 6.6 protected target and action identity but deliberately had no location.

After Phase 6.7 established a bounded point-to-approved-root validation primitive,
leaving the point outside the confirmation binding would create a substitution
gap: a different point could theoretically be supplied after target/action
approval.

Phase 6.8 closes that gap before any input mutation exists.

## Private operation contract

`_PointerOperation` now contains exactly:

- `target: _TargetBinding`
- `action: _PointerAction`
- `point: _ProposedPoint`

All types are exact private classes.

The operation remains:

- frozen;
- slotted;
- redacted;
- non-serializable/copy-resistant through the existing private model barriers;
- non-persistent;
- invocation-local;
- non-executable.

The operation has no `execute`, `click`, `move`, `focus`, `validate_hit`,
or native-input method.

The old location-free constructor/preparation path is no longer a valid private
approval path.

## Approval snapshot

The independent scalar snapshot now contains:

- all target identity fields;
- all desktop context fields;
- original target acquisition timestamps;
- action kind;
- action parameters;
- point X;
- point Y.

Approval requires:

- the exact retained operation object;
- the exact retained target object;
- the exact retained action object;
- the exact retained point object;
- unchanged operation references;
- unchanged scalar snapshot;
- unchanged authoritative capability registration;
- the same one-time confirmation binding;
- a fresh central policy recheck after token consumption.

Equal-looking replacement objects are rejected even when their scalar values are
the same. Snapshot comparison additionally detects trusted-process frozen-field
bypass/tampering.

## Preparation order

The private preparation sequence is:

1. validate authoritative capability metadata;
2. validate exact private action type;
3. validate exact private point type and Windows LONG bounds;
4. central permission/policy evaluation;
5. acquire the Phase 6.5 private target binding;
6. run Phase 6.7 `validate_hit(point, target)`;
7. require an exact `_PointerHitResult` with status `VERIFIED`;
8. construct the private target+action+point operation;
9. snapshot its scalar identity;
10. create the one-time confirmation token bound to that exact operation.

Permission/policy denial occurs before target acquisition or hit-test native reads.

`NOT_VERIFIED`, `INDETERMINATE`, native failure, stale Phase 6.5 target age,
malformed input, or a fake object merely claiming `VERIFIED` all prevent
confirmation creation.

There is no retry or target/location rescue.

## Coordinate semantics

Phase 6.8 reuses the exact Phase 6.7 `_ProposedPoint` contract.

The point is:

> Native Windows screen-space coordinates interpreted by this process.

It is not claimed to be:

- a physical pixel;
- a control identity;
- a button identity;
- DPI-normalized input coordinates;
- a `SendInput` coordinate;
- proof of future hit delivery.

No coordinate translation is added in this phase.

## Critical freshness distinction

Phase 6.8 explicitly separates:

### Approval identity

> What exact target/action/point combination did the confirmation authorize?

from:

### Execution eligibility

> Is that exact approved target/location still valid right now, immediately
> before a native effect?

Phase 6.8 solves only approval identity.

Preparation-time Phase 6.7 validation is deliberately NOT retained as a reusable
authority object or promoted to execution eligibility.

Human confirmation can easily take longer than the Phase 6.5 one-second freshness
window. Therefore approval does not call Phase 6.5 `verify_target` again and
does not rerun Phase 6.7 merely to manufacture a misleading approval-time freshness
claim.

A future phase must gather new post-confirmation evidence and compare it against
the approved target/action/point without altering what the user approved.

## Executor ownership

`ActionExecutor._pointer_invocation` remains the only private executor pointer
seam.

It now constructs/accepts exactly:

- `_TargetVerificationService`
- `_PointerHitValidationService`

Injected services are trusted deterministic-test seams only and must be exact
service types.

No public capability, semantic intent, router dispatch, or model-facing tool is
added.

Nothing new is retained on `ActionExecutor` after the lexical invocation closes.

## Cleanup and one-time use

On success, rejection, mismatch, exception, second-prepare attempt, or lexical
context exit, the invocation clears:

- operation;
- target;
- action;
- point;
- scalar snapshot;
- confirmation;
- target service;
- hit-validation service.

Confirmation bindings are consumed/rejected using the existing
`ConfirmationService` one-time semantics.

Cross-invocation reuse and the legacy generic confirmation execution route cannot
approve the private location-bound operation.

## Public evidence and privacy

Audit messages and confirmation text remain sanitized.

They do not expose:

- target HWND/process identity;
- executable/class metadata;
- target timestamps;
- point coordinates;
- private model representations.

No execution-started, execution-succeeded, or undo registration event is emitted
by this approval-only path.

The fixed confirmation request states that one future single-left-click intent at
the approved native screen point is being prepared, without serializing the private
coordinates into the public request text.

## Python in-process limitation

Frozen/slotted/private Python objects and exact identity checks are defensive
architecture, not a cryptographic security boundary.

Arbitrary malicious trusted-process code could still inspect or mutate Python
memory. The contract assumes trusted orchestration owns the private objects and
that no untrusted/public route can construct or substitute them.

## Explicit non-scope

Phase 6.8 adds NO:

- mouse movement;
- click/double-click/right-click;
- `SendInput`;
- `SetCursorPos`;
- `mouse_event` / `pyautogui`;
- drag/scroll/hover;
- keyboard input;
- focus/refocus;
- screenshot/OCR/computer vision;
- UI Automation;
- browser automation;
- DPI/input-coordinate translation;
- post-confirmation freshness authority;
- persistent/reusable pointer authority;
- click undo;
- live mutation smoke.

## Validation

Initial focused host validation after implementation/test reconciliation:

```
python -m unittest -q \
  tests.test_pointer_binding \
  tests.test_pointer_hit_validation \
  tests.test_target_validation \
  tests.test_executor \
  tests.test_policy_confirmation
```

Result: **105/105 passed**.

The first focused attempt exposed test-harness assumptions only:
- slotted service instance methods were incorrectly monkey-patched;
- an empty audit tuple was compared with an empty list;
- the historical Phase 6.7 guard correctly detected the new private integration.

Those tests were corrected without weakening production behaviour.

Broader affected-boundary validation:

```
python -m unittest -q \
  tests.test_pointer_binding \
  tests.test_pointer_hit_validation \
  tests.test_target_validation \
  tests.test_pointer_observation \
  tests.test_executor \
  tests.test_structured_executor \
  tests.test_policy_confirmation \
  tests.test_window_focus \
  tests.test_keyboard_text
```

Result: **292/292 passed**.

Full host regression:

```
python -m unittest discover -q
```

Result: **1,280/1,280 passed**, 0 failures/errors.

Additional validation passed:

```
python -m compileall -q nayeon
python -m nayeon.environment
git diff --check
```

Environment diagnostics:
- Windows 11 AMD64: OK
- Python 3.12.10: OK

An explicit scan of the changed production path found no:
- `SendInput`;
- `SetCursorPos`;
- `mouse_event`;
- `keybd_event`;
- `pyautogui`;
- `GetCursorPos`;
- `SetForegroundWindow`;
- `AttachThreadInput`.

The only Git messages were the repository's normal LF/CRLF normalization warnings;
`git diff --check` itself passed.

No live pointer movement, click, focus, keyboard, screenshot/OCR/UIA, or other
mutation smoke was run.

No commit, tag, push, or Google Drive workbook update has occurred.
