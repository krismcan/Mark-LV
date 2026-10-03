# Phase 6.7 bounded pointer hit validation review

Status: HOST VALIDATED — READY FOR HUMAN SEAL REVIEW.
No commit, tag, push, or Google Drive workbook update has occurred.

## Protected predecessor

Phase 6.7 started from the clean Phase 6.6 checkpoint:

- branch: `nayeon-v1`
- commit: `18dbc4f73d12d01fbbc1cddd7d674b647faa5b23`
- tag: `nayeon-v1-pointer-action-binding-01`
- `origin/nayeon-v1`: same commit
- predecessor regression baseline: 1,257/1,257

Phase 6.6 target+action binding semantics remain unchanged.

## Exact trust claim

Phase 6.7 establishes only:

> During one bounded read-only validation interval, the same proposed native
> screen-space point consistently resolved through Windows hit-testing to a
> window whose sampled root identity matched the approved root-window identity
> and supported desktop context.

This is sampled equality only. It is not continuous identity, click authority,
control identity, button identity, recipient certainty, or an atomic
validation+mutation transaction.

## Implementation

Candidate files:

- `nayeon/services/pointer_hit_validation.py`
- `nayeon/services/windows_pointer.py` — narrow native refactor only
- `tests/test_pointer_hit_validation.py`
- `docs/phase_6_7_pointer_hit_validation_review.md`

The Windows pointer native layer now separates:

- `_HitTestNative`: `WindowFromPoint` + root lookup only
- `_PointerNative`: extends `_HitTestNative` and retains `GetCursorPos` for
  the existing Phase 6.4 pointer-observation path

Phase 6.7 uses `_HitTestNative`, not `_PointerNative`.

The `_HitTestNative` refactor first appeared during the Codex worker handoff.
It was subsequently inspected, retained deliberately, and independently covered
by the host regression suite. Its provenance is therefore resolved for this
candidate.

No public capability, intent, router path, executor route, confirmation token,
audit authority, persistence layer, or undo entry is introduced.

## Coordinate contract

`_ProposedPoint(x, y)` contains two exact Python `int` values constrained to
Windows signed LONG bounds:

`-2^31 <= value < 2^31`

`bool`, integer subclasses, non-integers, malformed arity, and overflow are
rejected.

The coordinates mean only:

> Native Windows screen-space coordinates interpreted by this process and passed
> unchanged to `WindowFromPoint`.

They are deliberately not called physical pixels. Phase 6.7 makes no claim about
DPI normalization, monitor scaling, `SendInput` mapping, client coordinates,
visual control identity, or semantic UI meaning.

The point/result models are frozen, slotted, redacted, private, and reject normal
copy/deepcopy/pickle/JSON serialization.

## Approved target consumption

The service consumes an existing exact Phase 6.5 `_TargetBinding`.

It does not acquire, reconstruct, refresh, retimestamp, replace, or retain a
target. Legacy focus/text bindings are rejected. No failed or stale validation is
rescued by taking a replacement baseline.

Python process privacy is not a cryptographic provenance boundary. Trusted
orchestration must still supply the original approved private object. Arbitrary
malicious in-process Python is outside this trust claim.

## Freshness

The original Phase 6.5 age bound is unchanged:

`MAX_AGE_NS = 1_000_000_000`

Let:
- `acquired_to` = completed Phase 6.5 baseline timestamp
- `t0` = start of Phase 6.7 hit validation
- `t1` = end of Phase 6.7 hit validation

Eligibility requires:

`acquired_to <= t0 <= t1 <= acquired_to + MAX_AGE_NS`

A stale target returns `INDETERMINATE` before native hit-test reads. There is no
reacquisition or timestamp substitution. One second is an age/eligibility bound,
not an OS deadline or continuity guarantee.

## Fixed read sequence

After exact private input, platform, and freshness checks:

1. `t0 = perf_counter_ns()`
2. construct/reuse the private hit-test native facade
3. `C0 = context()`
4. require `C0` valid and equal to the approved target context
5. `W0 = WindowFromPoint(point)`
6. `R0 = GetAncestor(W0, GA_ROOT)`
7. `I0 = identity(R0)`
8. repeat `WindowFromPoint(point)`
9. repeat root resolution
10. repeat root identity
11. `C1 = context()`
12. `t1 = perf_counter_ns()`

There is no retry.

If the initial context is invalid or differs from the approved target context,
validation stops before `WindowFromPoint`.

The current cursor position is never read or moved by Phase 6.7.

## Result semantics

The private result exposes only `VerificationStatus`.

### VERIFIED

Requires fresh complete evidence where:

- `C0 == C1 == target.context`
- both hit HWNDs and roots are valid
- both root identities are valid
- identity HWND equals sampled root
- both sampled roots are equal
- both sampled identities are equal
- sampled root equals the approved target root
- sampled identity equals the approved target identity

### NOT_VERIFIED

Returned only when complete, stable, fresh evidence is trustworthy but proves a
stable mismatch, for example:

- the point consistently resolves under another root window; or
- the same root handle now has a different valid process/window identity.

### INDETERMINATE

Covers insufficient or unstable evidence, including:

- unsupported platform
- malformed point or binding
- stale target
- invalid/changed desktop context
- no window at the point
- malformed native handles
- invalid identity
- root drift
- identity drift
- clock anomaly
- native/query/cleanup failure

Root/identity drift is deliberately `INDETERMINATE` because the interval did
not establish one stable alternative target.

## Foreground rule

Foreground is neither sampled nor required.

That is deliberate: Phase 6.7 proves only a point-to-root hit-test relationship.
Foreground and actual input routing belong in a later fresh execution-eligibility
contract immediately before mutation.

A successful Phase 6.7 result does not prove a future click would reach the same
recipient.

## Child HWND rule

`WindowFromPoint` may return a child HWND.

The child is not promoted to target authority. Phase 6.7 resolves it to
`GA_ROOT` and validates the root identity against the approved Phase 6.5 root.

Therefore different child HWNDs beneath the same stable approved root may verify,
while child windows beneath another root do not.

No control/button identity is established.

## Resource ownership

Existing Windows desktop ownership rules remain unchanged:

- owned process/input-desktop resources are cleaned up by existing native helpers
- borrowed HWNDs are never closed
- borrowed thread desktops/window stations are never closed

Native failures produce sanitized `INDETERMINATE` results. No native evidence is
returned in the result.

## DPI and TOCTOU limitations

Phase 6.7 does not prove:

- physical-pixel identity
- DPI-safe future input mapping
- UI element identity
- visibility/occlusion safety
- click delivery
- continuous root identity
- atomic validation+mutation

The desktop can change immediately after `t1`. A future mutation phase must
perform fresh target/location eligibility checks inside the same executor-owned
operation immediately before one bounded effect.

## Explicit non-scope

No:
- cursor movement
- `GetCursorPos` in the Phase 6.7 service
- `SetCursorPos`
- `SendInput`
- `mouse_event` / `pyautogui`
- click/double-click/right-click
- drag/scroll/hover
- keyboard input
- focus/refocus
- screenshot/OCR/computer vision
- UI Automation
- browser automation
- coordinate binding into Phase 6.6
- persistent/reusable location authority
- undo
- live mutation smoke

## Worker handoff note

The Codex worker was stopped after it became verbose without timely visible file
progress. Its termination overlapped with late writes of the service/native
refactor, tests, and review document.

Those late writes were not accepted blindly. The resulting code was inspected,
one overly broad native dependency was tightened from `_PointerNative` to
`_HitTestNative`, initial-context failure was changed to stop before hit reads,
two incorrect worker test assumptions were corrected, and missing mutation/public
route guards were added.

All final claims below come from independent host validation, not from the Codex
sandbox.

## Validation

Focused affected-boundary validation:

```
python -m unittest -q \
  tests.test_pointer_hit_validation \
  tests.test_target_validation \
  tests.test_pointer_observation \
  tests.test_pointer_binding \
  tests.test_executor \
  tests.test_policy_confirmation
```

Result: **158/158 passed**.

The focused count reflects the final reconciled Phase 6.7 test suite. No existing
production regression tests were removed.

Full host regression:

```
python -m unittest discover -q
```

Result: **1,276/1,276 passed**, 0 failures/errors.

Additional validation passed:

```
python -m compileall -q nayeon
python -m nayeon.environment
git diff --check
```

Environment diagnostics:

- Windows 11 AMD64: OK
- Python 3.12.10: OK

`git diff --check` passed. The only Git message was the repository's normal
LF/CRLF normalization warning for the modified Windows pointer source.

No live pointer movement, click, focus, keyboard, screenshot/OCR/UIA, or other
mutation smoke was run.

No commit, tag, push, or Google Drive workbook update has occurred.
