# Phase 6.11 bounded pointer effect review

Status: candidate test/documentation completion; validation pending host. No verified milestone is claimed.

## Exact trust claim

After exact approval/confirmation/policy and fresh eligibility plus fresh coordinate mapping, one executor-owned SendInput batch of move/down/up was attempted. The receipt only reports insertion count, never semantic UI success.

This claim applies to an attempted batch after all gates pass. A blocked route returns NOT_ATTEMPTED. Even INSERTED means only that the API reported insertion of three records; it does not establish delivery to the intended application, acceptance by a control, or completion of the user's intended UI action.

## Private execution boundary

The route is ActionExecutor._pointer_invocation with exact trusted private service objects. Preparation binds the exact target, single-left-click action, and original native-screen point to an expiring, one-use confirmation. The private _execute_effect consumes that confirmation, reevaluates permission/policy, checks registry and service identity and the immutable scalar snapshot, obtains fresh target/hit eligibility, then calls coordinate.normalize with the original approved point. Only exact VERIFIED eligibility and exact VERIFIED, validated coordinate evidence for that same point may reach effect insertion.

The effect service receives coordinate evidence, not model authorization. It validates evidence locally and constructs exactly three INPUT_MOUSE records in one batch: absolute virtual-desktop move (0x0001 | 0x8000 | 0x4000), left down (0x0002), left up (0x0004). Unused fields are zero. There is one SendInput call with count 3 and the exact INPUT structure size. There is no public click/move/execute route or retained executor authority. Existing approve remains read-only even when effect services are injected.

The operation closes and clears its private binding/services on every consume outcome. It registers no undo and does not invoke the registered capability implementation as an alternative effect path. Sanitized POINTER_EFFECT_OUTCOME audit events report the bounded insertion outcome without coordinates, target identity, or private native exception details. Audit failure after insertion must not erase the receipt.

## Receipt interpretation

| Native result | Receipt | Meaning |
| --- | --- | --- |
| No native call | NOT_ATTEMPTED | A prerequisite or local construction/validation failed. |
| 3 | INSERTED | API reported insertion of all three records. |
| 1 or 2 | PARTIAL | API reported partial insertion. |
| 0 | INDETERMINATE | Attempt occurred; zero insertion reported. |
| Exception, negative, greater than 3, boolean, or non-integer | INDETERMINATE | Attempt occurred; insertion count is unavailable or invalid. |

No receipt claims semantic UI success. Once the effect seam has been called, malformed results or exceptions remain an indeterminate attempt. There is no retry, additional cleanup input, or undo.

## Residual risks

Fresh observations are sequential samples, not an atomic desktop lock. Residual TOCTOU exists between foreground/hit observations, coordinate sampling, and insertion: windows, targets, geometry, or controls may change after the final sample. Rectangle normalization does not prove monitor coverage or that the original point still names the intended control.

UIPI can block injection across integrity levels; the insertion count alone does not diagnose UIPI or establish application delivery. Physical user interference can move the pointer, change focus, or change button state around the batch. The route does not reserve exclusive desktop ownership or prove user intent after those changes.

Partial insertion may leave a move or a button-down without the corresponding release. No retry or cleanup batch is issued because it would be an additional effect outside the bounded approved attempt. There is no undo for native pointer insertion and no promise that an application action can be reversed.

## Test scope and pending validation

Tests use exact _PointerEffectService(platform="win32", native=fake), never real native input. Native construction is patched to fail and asserted unused. Integration tests inject exact target, hit, coordinate, and effect services with deterministic native fakes; effect-contract failure tests patch _PointerEffectService._insert on the exact class rather than substituting a subclass.

Coverage includes record order/flags/normalized coordinates/zero fields and padding/count/cbSize; insertion outcomes and no retry; platform/evidence/type/tamper/privacy guards; exact confirmation, policy, registry, snapshot and service gates; fresh eligibility then original-point normalization; receipt preservation, clearing, sanitized audit, read-only approve, and no undo.

Python tests, compilation, and environment diagnostics were not run in this completion pass, as explicitly prohibited. Host validation remains pending: run the two focused unittest modules with the compatible repository interpreter, then the deterministic regression suite and syntax/environment checks. Confirm the guards remain active and review any failures before changing production. These proposed host checks are not evidence of a passing suite.

**NO LIVE EFFECT SMOKE AUTHORIZED.** This pass authorizes no real SendInput, desktop click, or live insertion smoke test. Fake-only host validation does not expand that authorization.

Production candidate files pointer_effect.py, pointer_binding.py, executor.py, and audit/service.py are outside this pass's edit scope unless a test exposes a concrete defect. No production edit, commit, tag, push, or historical-document review is part of this completion.

## Current-tree review and implementation boundary

Baseline HEAD is `4bd49f1624ff23162d784936b042f1bab653bf1f`, branch `nayeon-v1`, milestone tag `nayeon-v1-pointer-coordinate-foundation-01`. This session must leave HEAD unchanged and must not commit, tag, stage, or push.

At startup, the working tree contained tracked edits in `nayeon/agent/executor.py`, `nayeon/agent/pointer_binding.py`, and `nayeon/audit/service.py`, as well as the untracked effect facade. These edits were reviewed as unfinished implementation, not accepted as proof. Concurrent writes also supplied tests and this document during review. The draft's effectful `approve()` was corrected: `approve()` always remains read-only, including when trusted effect services are supplied. The new private `_execute_effect()` method consumes the exact approved operation in the same invocation. It accepts neither coordinate evidence nor a previously returned VERIFIED eligibility result from its caller.

The private invocation requires exact target, hit-validation, coordinate, and effect service types. It retains their identities locally and rejects replacement, including replacement with another instance of the same exact type. Registered metadata and implementation identity must still match; immutable operation identity and its independent scalar snapshot are checked before confirmation, after policy, after fresh eligibility, and after fresh normalization. Exact result types and their invariants are revalidated. These are trusted in-process conventions, not a security sandbox against hostile Python code or arbitrary monkeypatching.

The receipt, effect service, and native facade are frozen, slotted, redacted, noncopyable and nonpickleable. ABI structures are private, zero-initialized, transient ctypes buffers constructed only for the batch; they are not approval or verification evidence. The INPUT layout is checked for supported 32/64-bit sizes (28/40 bytes); mouse fields use fixed-width signed/unsigned Windows integers and pointer-width extra information.

Unsupported platform, malformed or inconsistent coordinate evidence, unsupported ABI layout, or native setup failure causes NOT_ATTEMPTED, with no insertion call. After an insertion attempt, exact integer counts 3/2/1/0 are retained; malformed counts (including bool or integer subclasses) and exceptions carry no count and remain INDETERMINATE. A malformed effect-service return after that service has been invoked is conservatively reported as an indeterminate attempt. No result repairs, retry, fallback mutation, or compensating LEFTUP is allowed. A partial batch can leave button state uncertain; cleanup only discards local invocation state and confirmation bindings, never issues native input.

Auditing occurs after the effect boundary; no audit/file I/O is inserted between coordinate sampling and native insertion. Audit messages are fixed and details remain empty. They report insertion status and sampled eligibility separately, without coordinates, target identity, tokens, exception text, or semantic success. An audit or cleanup exception after insertion must not erase its receipt. Local state is cleared even if confirmation cleanup fails; cleanup failure is sanitized and audited when auditing remains available. The existing read-only cleanup failure behavior is preserved.

## API insertion, TOCTOU, and UIPI interpretation

One SendInput call submits the MOVE/LEFTDOWN/LEFTUP sequence in order, but it does not make the preceding target and geometry reads atomic with input processing. Foreground, desktop context, hit target, geometry, user input, process identity, or UI content can change between samples and delivery. There is no continuity, OS deadline, physical pixel/DPI equivalence, monitor-shape coverage, semantic control identity, or application acknowledgement claim. The approved Phase 6.10 integer normalization is used unchanged; no clamp, alternate point, reprojection, or geometry repair is introduced.

UIPI can prevent insertion into applications at higher integrity. Zero insertion or an exception does not prove that nothing happened, and it does not identify UIPI as the cause. Three inserted records prove only the API insertion count, not eventual cursor placement, button delivery, a semantic click, or successful application state change. No post-effect semantic verification exists in this patch.

## Static-only handoff

Codex does not run Python, unittest, compilation, environment diagnostics, or live native queries/effects in this session. Tests are source additions awaiting host execution. New effect tests inject fake native/services; the real `_PointerEffectNative` factory is guarded, and facade signature checks inspect source only without constructing the real facade, even with a mocked DLL. Integration tests cover order, original-point identity, one-time confirmation, fresh evidence, partial/indeterminate insertion, malformed/replaced services and results, tampering, policy and registry gates, cleanup, sanitized audits, and absence of undo/public routes.

Host should run the focused effect/binding suites, affected pointer/coordinate/target/executor/policy suites, full deterministic regression discovery, compilation, and environment diagnostics. No pass count or verified milestone is claimed here. Static handoff checks are `git diff --check`, untracked-file whitespace checks, status, diff stat, and changed-production source/route scans. Existing keyboard/focus/observation APIs elsewhere in the repository are outside this patch and are not called by the new pointer effect path.

**NO LIVE EFFECT SMOKE AUTHORIZED. NO LIVE SendInput OR REAL CURSOR EFFECT MAY BE RUN FOR THIS TASK.** No public pointer capability, intent, dispatch route, persistence, refocus, undo, or reusable VERIFIED authority is added.
## Host non-mutating validation result

Focused Phase 6.11/pointer-binding validation: **88/88 passed**. Broader affected trust-boundary validation: **328/328 passed**. Full regression discovery: **1,370/1,370 passed**, 0 failures/errors. `compileall`, Windows environment diagnostics (Windows 11 AMD64 / Python 3.12.10), `git diff --check`, alternate pointer/keyboard mutation API scan, and public capability/intent/runtime route scan passed.

The dedicated effect tests inject fake native seams and guard construction of the real `_PointerEffectNative` facade; integration tests likewise inject the private exact service with fake `_send_input`. Therefore these passing tests do **not** constitute a live pointer-effect smoke. No real `SendInput`, pointer movement, or click was intentionally performed during this validation.

Repository remains uncommitted at the protected Phase 6.10 HEAD `4bd49f1624ff23162d784936b042f1bab653bf1f`. Phase 6.11 is ready for the separate human-controlled live-effect smoke decision; it is not sealed until that gate is resolved and final validation/review is complete.

## Controlled live-effect smoke

Human authorization was obtained separately before live native input. Two initial attempts against the first disposable Tk target failed closed during `prepare()` because the exact proposed point could not be verified against the acquired foreground/root identity. `SendInput` was not reached on either attempt; no pointer effect occurred. No trust check was weakened to force success.

A fresh disposable blank Tk client surface was then created. After the human explicitly focused that window, the production Phase 6.11 chain was invoked once at the derived neutral centre point `(508, 361)` with no intervening foreground probe. Preparation and fresh validation passed. The private native effect returned `INSERTED`, `attempted=True`, `inserted=3`; the effect audit outcome was `inserted`; pending confirmations were 0 and undo records were 0. The human independently confirmed that the pointer visibly moved to the neutral point and left-clicked once.

This smoke proves that the bounded production path can insert the exact three approved Windows input records (`MOVE -> LEFTDOWN -> LEFTUP`) and that the expected physical pointer action was observed in this controlled test. It does **not** prove semantic UI activation, general click reliability, arbitrary-coordinate authority, or permission for any broader GUI automation.
