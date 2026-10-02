# Phase 6.3 bounded keyboard text input review

Status: IMPLEMENTED, UNCOMMITTED; automated validation PASSED and human review is now the active gate. Controlled live smoke has NOT run. This is not yet a committed/tagged milestone.

Protected checkpoint: `nayeon-v1`, HEAD `a1079ea4ca4d60e1dc12c40e67231be9df907855`, tag `nayeon-v1-desktop-window-focus-01`. Starting tree was clean and matched exactly. HEAD/branch/tag remain unchanged. No commit, staging, tag operation, push, spreadsheet update, or live keyboard mutation occurred.

## Exact user contract

Capability `type_text` is LOCAL, requires no LLM, requires explicit confirmation, is non-reversible, and creates no undo entry. Structured caller arguments must be exactly `{"text": <string>}`. No caller HWND, native identity, desktop context, evidence, private binding, hotkey, modifier, virtual-key, key-sequence, or other argument is accepted.

The deterministic conversational form is `type text <JSON-string>`, for example `type text "Hello world"`. It reuses the explicit JSON-string convention of `create_text_file`, with one variable argument. The prefix is case-insensitive; whitespace outside the command/JSON string is stripped or accepted by the JSON decoder. Unquoted prose, JSON nonstrings, additional commands, and extra arguments are rejected. JSON escapes are decoded once by this mapper; decoded text still passes the same validation. Structured text is already decoded and has no escape interpretation.

The payload must be an exact built-in `str`, 1 through 256 Unicode scalar characters, with `str.isprintable()` true. Ordinary U+0020 spaces, including all-space payloads and leading/trailing spaces, are retained. Empty strings, controls (including newline, tab and escape), lone surrogate values, invisible formatting controls and non-ASCII separator characters are rejected. Supplementary characters count once; combining marks count individually. No case, whitespace or Unicode normalization changes the text. The narrower printable definition is intentional.

There is no key-command language: `keys`, `hotkey`, modifier chords and native/virtual-key instructions are rejected as inputs. Printable strings such as `Ctrl+C` or `{ENTER}` inside the explicit text string are literal characters only; they never invoke a chord or key sequence. This avoids guessing whether ordinary printable text is a command. The only output events are Unicode character down/up pairs with virtual-key field zero.

## Trust, approval and saved identity

Preparation reuses Phase 6.2 `WindowFocusService.prepare_focus()` and Phase 6.1's bounded foreground observation. A consistent complete observation freezes the exact `WindowIdentity` and `DesktopContext`. A private immutable/redacted `_TextBinding` adds the exact validated text. The capability returns only this private binding as normalized prepared arguments; the adapter, capability and session acquire no replacement target at approval or execution.

Existing central execution remains unchanged: the executor owns preparation, compares registration/implementation, original request and normalized arguments, binds a one-time expiring confirmation to the prepared action, reevaluates permission/policy after approval and rechecks registration before execution. `PreparedApprovalValidator` compares the caller's exact text to the saved text without IO and returns a copy of the saved preparation. Validation may perform read-only observation before policy evaluation, as in Phase 6.2; it performs no keyboard mutation.

Default deny, permission alone, rejection/cancellation, expiry, replay, changed text/request, replaced registration, changed confirmation binding and revoked/blocked permission cannot inject events. Raw callers cannot supply the internal binding. Approval remains an explicit trusted caller/UI action.

Execution encodes the bounded event array before revalidation. It reuses Phase 6.2's context/identity bracketing around the foreground sample, then takes one additional foreground sample after query cleanup, closest to mutation. Each successful read check has exactly four context acquisitions, two acquisitions of the saved HWND's identity, and two foreground samples. It never observes the replacement window's identity. Missing evidence fails closed; mismatched identity, context or foreground fails closed with zero injection before the attempt.

## Native mutation and receipts

One `SendInput` call submits the entire array. No retry, fallback, clipboard, paste, UI Automation, OCR, screenshot, title/content read, mouse input, focus/refocus, restoration, thread attachment or foreground workaround is performed. Win32 `INPUT` uses its full union layout and pointer-sized extra-info fields, including the mouse/hardware members solely for ABI alignment; only `INPUT_KEYBOARD` entries are populated. Expected INPUT size is 40 bytes on Windows x64, 28 on x86.

Each UTF-16 code unit gets one down event (`KEYEVENTF_UNICODE`) and one up event (`KEYEVENTF_UNICODE | KEYEVENTF_KEYUP`), with wVk/time/extra-info zero. Supplementary scalars generate both surrogate code units in original order. Maximum planned sequence: 1024 events (256 supplementary scalars); BMP-only maximum: 512. No key-state correction or extra cleanup keystrokes occur on partial failure.

Every attempted call, including one that raises, is followed by a fresh bounded target/context/foreground check. Exceptions and malformed native counts are sanitized. No native error text, error code, returned value, or event array is included in public receipts or audit.

| Receipt state | Meaning |
| --- | --- |
| `typed` | Exactly the full planned event count was accepted and the saved target/context/foreground passed the post-check. This does not assert application text contents. |
| `partial` | A strict positive integer smaller than the planned event count was accepted, with a valid post-check. This may end inside a scalar or down/up pair. Never VERIFIED. |
| `not_typed` | The native count was exactly zero and the post-check passed. Never VERIFIED. |
| `target_changed` | Confirmed saved identity/context/foreground mismatch before or after the attempt. Pre-attempt mismatch injects nothing; post-attempt mismatch may follow partial/full mutation. Never VERIFIED. |
| `inconclusive` | Insufficient reads, unsupported platform, native exception, malformed/out-of-range count, or cleanup failure. If after the attempt, input may already have occurred. |

Post-check failure or drift takes precedence over insertion classification. Thus `target_changed`/`inconclusive` do not establish whether any text was delivered; never retry automatically. `partial` remains distinct from full and zero acceptance when fresh post-evidence is available.

Capability verification separately repeats the eight-query read check for a `typed` receipt. VERIFIED means only complete planned sequence acceptance plus a matching exact target/context in the fresh check. Drift yields NOT_VERIFIED; missing evidence yields INDETERMINATE. Negative receipts cannot be upgraded by a later foreground change. No verification reads application text content or mutates anything.

Generic executor `EXECUTED`, `succeeded`, and execution-success audit events retain their existing meaning that capability execution returned a receipt, not that input succeeded. Consumers must use the typed receipt and separate verification status. No generic executor, policy, confirmation, session, undo or Phase 6.1/6.2 code was changed.

## Privacy and native resources

Public receipts expose only a bounded enum. Binding/text/identity/context repr and str are redacted; audit records contain no text, request, target binding or output. Pending normalized actions hold text only in a private immutable binding. Raw structured requests and conversational request fields necessarily contain the supplied text; callers must not log them or serialize private dataclass fields wholesale. No secrets, real user content or credentials were used in tests.

Phase 6.1 queries own and release process handles, input-desktop handles and WTS allocations inside each acquisition, including exception paths. HWND, thread-desktop and station identifiers are borrowed and never closed. No native handle ownership escapes preparation or execution. Cleanup failure prevents positive verification; synchronous calls have fixed cardinality, not a guaranteed OS deadline.

## Files and deterministic coverage

New files only:

- `nayeon/capabilities/type_text.py`: exact mapper, validation, saved approval and verification.
- `nayeon/services/keyboard_text.py`: bounded text validator, private binding, typed receipt and service boundary.
- `nayeon/services/windows_keyboard.py`: pointer-width Win32 ABI, bounded UTF-16 events, one injection and fresh checks.
- `tests/test_keyboard_text.py`: 60 focused test methods plus subtests.
- `docs/phase_6_3_keyboard_review.md`: this handoff and disposable smoke procedure.

Focused tests cover default deny; permission/confirmation; no injection before approval; rejected, expired and repeated tokens; saved-target/text/request/action binding; approval without recapture; metadata/implementation and policy changes (including a registration change during the policy recheck); all identity/context fields; foreground drift including the final samples; input shape, controls and scalar bounds; spaces, combining characters and surrogate pairs; event type/flags/UTF-16 order/cardinality; strict full/partial/zero/invalid counts; native exceptions; fresh post-checks and verification; negative receipt non-upgrade; privacy/audit/redaction; resource cleanup and cleanup errors; discovery; local session cancellation and attempted prose approval; no undo and no refocus.

All automated mutation calls use mocks: native inject is a Mock, and the SendInput ABI test uses mocked DLLs. Existing tests were not edited. No live provider or desktop mutation is needed.

## Validation results

Validation was rerun directly from `C:\AI\mark-lii` after the Codex session ended, using the repository virtual environment:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_keyboard_text -v
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m nayeon.environment
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
```

Results:

- Focused Phase 6.3 suite: **60/60 PASS**.
- Full regression: **1154/1154 PASS**.
- Environment diagnostics: **PASS** — Windows 11 AMD64, Python 3.12.10.
- `compileall`: **PASS**.
- `git diff --check`: **PASS**.

No live keyboard mutation was used for automated validation; native keyboard injection remained mocked in the test suite. The worktree contains exactly the five intended untracked Phase 6.3 files listed above. No staging, commit, tag, push or spreadsheet update has occurred.

## Limitations and review gate

Win32 cannot atomically pin a borrowed HWND or its foreground ownership across query/injection calls. The final foreground sample reduces the unchecked interval but cannot eliminate races; after-the-fact checks cannot retract injected events. The target is a root/foreground window, not a frozen child edit control, caret or selection. Routing within that exact window can change without changing its identity. Unicode packet handling, integrity restrictions, hooks, application behavior and already-held keys may prevent or alter visible text. A complete accepted event count is not proof of rendering, consumption or exact text contents. Partial insertion can include an unmatched event or surrogate; this capability does not repair it.

Review readiness: READY — code, deterministic tests and this handoff are available for human inspection. Live-smoke readiness: READY FOR CONTROLLED HUMAN-APPROVED SMOKE using only the disposable-window procedure below; smoke has not run.

## Controlled disposable-window smoke procedure (not executed)

After executable validation passes and a human approves this gate, copy the following harness to a temporary `.py` file in the repository, review it, and launch it with the validated interpreter from the repository root. Tkinter availability must be checked first. It creates its own disposable window and entry, uses a local-only ConversationSession and the central executor, and refuses to prepare or inject for any other root window. It never focuses/refocuses or reads the entry's contents. Counters expose only attempts and accepted event counts. No product code is changed for the smoke.

```python
import ctypes
import tkinter as tk

from nayeon.agent.executor import ActionExecutor
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService
from nayeon.capabilities.type_text import TypeTextCapability
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.services.keyboard_text import KeyboardTextService
from nayeon.services.windows_keyboard import WindowsKeyboardAdapter, _KeyboardNative
from nayeon.undo.service import UndoService

root = tk.Tk()
root.title("Disposable Phase 6.3 smoke")
entry = tk.Entry(root, width=60)
entry.pack(padx=20, pady=20)
status = tk.StringVar(value="Human gate: select a preparation button, then click the empty entry.")
tk.Label(root, textvariable=status, wraplength=600).pack()
root.update_idletasks()

class SmokeNative(_KeyboardNative):
    attempts = 0
    accepted = None
    def inject(self, events):
        # Extra harness restriction; no exception details or text are logged.
        if self.foreground() != own_hwnd:
            raise ValueError("Disposable target no longer foreground.")
        self.attempts += 1
        self.accepted = super().inject(events)
        return self.accepted

native = SmokeNative()
own_hwnd = native.u.GetAncestor(root.winfo_id(), 2)
if not own_hwnd:
    root.destroy()
    raise SystemExit("Disposable root identity unavailable.")

class SmokeService(KeyboardTextService):
    def prepare_text(self, text):
        binding = super().prepare_text(text)
        if binding.target.identity.hwnd != own_hwnd:
            raise ValueError("Only the newly created disposable root may be prepared.")
        return binding

impl = TypeTextCapability(service=SmokeService(adapter=WindowsKeyboardAdapter(native=native)))
registry = CapabilityRegistry()
registry.register(impl.capability, impl)
permissions = PermissionService(default_allowed=False)
undo = UndoService()
executor = ActionExecutor(registry, PolicyService(permissions), ConfirmationService(), AuditService(), undo)
session = ConversationSession(
    resolver=IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(registry))),
    registry=registry, executor=executor)
job = None

def show(result):
    state = getattr(getattr(result, "output", None), "state", None)
    state = getattr(state, "value", "no_receipt")
    status.set(f"{result.status.value}; {state}; {result.verification.status.value}; "
               f"attempts={native.attempts}; accepted={native.accepted}; undo={undo.peek() is not None}")

def schedule(callback):
    global job
    if job is not None:
        return
    status.set("Five seconds: click the disposable entry, release all keys, and keep this window foreground.")
    def run():
        global job
        job = None
        show(callback())
    job = root.after(5000, run)

def prepare(allowed):
    if job is not None or session.has_pending:
        return
    if allowed:
        permissions.grant("type_text")
    else:
        permissions.revoke("type_text")
    schedule(lambda: session.request('type text "Smoke A \\u00e9 \\ud83d\\ude42"'))

def cancel():
    global job
    if job is not None:
        root.after_cancel(job)
        job = None
    show(session.reject_pending())

def close():
    cancel()
    root.destroy()

tk.Button(root, text="Prepare: default deny", command=lambda: prepare(False)).pack()
tk.Button(root, text="Prepare: permission granted", command=lambda: prepare(True)).pack()
tk.Button(root, text="Approve saved action in 5 seconds",
          command=lambda: schedule(session.approve_pending) if session.has_pending else None).pack()
tk.Button(root, text="Cancel", command=cancel).pack()
root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()
```

Steps and expected results:

1. Use a dedicated unlocked Windows test desktop/session at ordinary integrity. Close unrelated applications before smoke. Create the harness window; do not target any pre-existing application. The initial entry must be empty. No preparation or injection happens at startup.
2. Click **Prepare: default deny**, then manually click the entry during the five-second delay. Expect `denied`, attempts=0, no undo.
3. Click **Prepare: permission granted**, manually click the entry, release all keys and keep the disposable root foreground. Expect `requires_confirmation`, attempts=0. Text has not been injected.
4. Click **Cancel**. Expect the pending action to be consumed, attempts=0. Repeat preparation for the positive case.
5. Click **Approve saved action in 5 seconds**, manually click the disposable entry, release all keys and keep the root foreground until status updates. Expect `typed`, `verified`, exactly one attempt and 24 accepted events for `Smoke A` plus spaces, U+00E9 and U+1F642; undo=False. A human may visually inspect the new text. That manual inspection is supplementary smoke evidence, not product verification or content readback.
6. For a drift case, restart the harness with a new empty entry; prepare the original disposable root. Create a second disposable test window in a separate harness/process solely for this negative test. Arm approval on the original, then manually click the second disposable window during the delay. Expect `target_changed`, attempts=0 and no undo in the original. Do not bring any pre-existing application foreground for this test. No code may automatically refocus the original.
7. Close both disposable windows and remove only the temporary harness file you created. Record receipt state, verification, attempt/count/undo values, interpreter/platform and manual observations without text/identity/native-error details. Do not commit/tag or claim closure without subsequent human review.

The expected native cardinality above is 12 UTF-16 code units x 2 events = 24 events. A denied/partial/inconclusive outcome must be recorded as such and never retried automatically. Resource balance is covered by deterministic tests; do not infer it solely from a visible successful smoke. This harness and Tkinter/Unicode behavior remain unvalidated while Python execution is blocked.
