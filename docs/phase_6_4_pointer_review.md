# Phase 6.4 bounded pointer observation review

Status: IMPLEMENTED, UNCOMMITTED; independent deterministic validation PASSED; controlled READ-ONLY disposable-window smoke PASSED. Human review is now the active gate.

## Protected checkpoint and scope

Verified at review startup and handoff:
- branch `nayeon-v1`
- commit `424f7f8448f9a3b6ebc7844a5ea5141ba99dc92c`
- tag `nayeon-v1-desktop-keyboard-text-smoke-01` points at HEAD
- exactly the five supplied Phase 6.4 candidate files are untracked
- existing tracked product and test files are unchanged; nothing is staged

No commit, tag, push, spreadsheet update, environment repair, or mouse/keyboard mutation was performed during this review. One controlled READ-ONLY pointer observation was performed only against a disposable Tk smoke window after deterministic validation passed.

## Exact contract

Capability `observe_pointer` uses the deterministic local phrase `inspect current pointer`. Local request mapping accepts the exact phrase after surrounding-whitespace and case normalization and maps its sole `request` argument to `{}`. Suffixes and different phrases in that mapping are rejected. Explicit structured empty mappings are accepted independently of the original prose, matching the existing foreground-observation contract; that prose is not native targeting authority.

Structured arguments must be exactly `{}` after mapping. All nonempty capability arguments, including coordinates, HWND/PID/TID, identities, contexts, evidence, titles, paths and private bindings, are rejected without native reads. Legacy string execution is rejected. Construction, discovery, mapping and validation perform no native IO.

Metadata is LOCAL, `requires_llm=False`, `requires_confirmation=False`, `reversible=False`, service `computer_control`. The existing session/orchestration/executor path validates arguments and evaluates central permission/policy before execution. Default-deny requires an explicit `observe_pointer` permission grant. There is no pending confirmation or new undo entry.

Public receipts expose only typed bounded state/reason enums:

| State | Reason |
| --- | --- |
| `observed` | `bounded_snapshot_consistent` |
| `no_target` | `no_target_sampled` |
| `partial` | `required_evidence_changed` |
| `partial` | `required_evidence_incomplete` |
| `unavailable` | `supported_context_unavailable` |

No coordinates, identifiers, names, paths, or private evidence are included in receipt repr/str, verification evidence or audit details. Internal Python objects carry private evidence for historical verification; they must not be serialized with generic dataclass field extraction or exposed as a public API.

## Private evidence and consistency

Frozen, slotted, redacted samples contain the signed screen point, exact borrowed WindowFromPoint HWND, its GA_ROOT, the current foreground GA_ROOT, and existing Phase 6.1 `WindowIdentity` values for both non-null roots. Frozen evidence also contains the initial/final existing `DesktopContext` and monotonic timestamps. This reuses the existing trust types and query/resource machinery; it introduces no action-authorizing binding or persistent target cache.

Both samples must be complete and equal, both contexts valid and equal, and timestamps nonnegative and ordered. Each identity must match its sampled root and desktop/session context. If both roots are the same HWND, their separately acquired identities must agree within each sample as well. Handle and point fields reject malformed types and out-of-range native values.

Detected pointer, hit HWND, root, foreground root, process-instance, identity or context changes fail closed. Missing, malformed or inaccessible evidence, native exceptions and cleanup failures prevent a positive receipt. A stable null target can return `no_target` only after both samples and contexts pass the same checks, including identity checks for any non-null foreground root. A stable null foreground does not invalidate a complete pointer-target sample.

Negative receipts carry no private evidence. Verification accepts only an `observed / bounded_snapshot_consistent` receipt with complete matching immutable historical evidence and non-null target roots. Complete contradictory evidence yields NOT_VERIFIED; incomplete, invalid or negative receipts remain INDETERMINATE. Verification performs no native calls, never resamples, and cannot upgrade a negative receipt even if one is constructed with positive evidence.

## Fixed query sequence and resources

The new native facade adds only GetCursorPos and WindowFromPoint signatures to the existing query-only Windows facade. It reuses GetAncestor(GA_ROOT), GetForegroundWindow, identity acquisition and DesktopContext acquisition.

On a complete non-null target/foreground path:
1. Acquire and validate initial DesktopContext; read the start clock.
2. Read GetCursorPos; query WindowFromPoint at that point; normalize pointer and foreground roots; acquire both root identities.
3. Query WindowFromPoint again at the same private point; repeat root, foreground and both identity reads; read GetCursorPos again as the trailing bracket.
4. Acquire final DesktopContext and end clock; validate immutable evidence.

The cursor is read exactly twice, bracketing the two target/identity passes. The late sample must have the same cursor point as the first, so drift fails closed. There are no retries. Null roots omit only their associated root/identity calls; errors terminate acquisition.

For the complete non-null path, deterministic native expectations are GetCursorPos=2, WindowFromPoint=2, GetForegroundWindow=2, GetAncestor=8 (four normalization queries plus four identity checks), and four exact root-identity acquisitions. Even when the roots coincide, identities are acquired separately. No optional geometry or DPI state query is performed.

HWNDs, thread desktops and window stations are borrowed and never closed. Each existing owned OpenProcess handle is closed once within identity acquisition; each owned OpenInputDesktop handle and WTS allocation is released by existing finally-based cleanup. The complete path opens/closes four process handles and two input desktops and frees two WTS allocations. Exceptions or reported cleanup failures fail closed without retrying cleanup or observation. An OS cleanup failure cannot guarantee release, but no positive receipt is issued and no ownership is retained for later use.

There is no pointer movement, click, double-click, drag, scroll, hover automation, keyboard injection, clipboard access, UI Automation, title/content scraping, screenshot, OCR, vision, browser automation, focus/refocus or legacy pyautogui routing.

## Review changes and deterministic coverage

The five candidate files remain the entire change scope:
- `nayeon/capabilities/observe_pointer.py`
- `nayeon/services/pointer_observation.py`
- `nayeon/services/windows_pointer.py`
- `tests/test_pointer_observation.py`
- `docs/phase_6_4_pointer_review.md`

Review added foreground-root WindowIdentity evidence and validation, same-root identity consistency, native-width sample handle bounds and a positive-reason verification guard. The candidate initially recorded only the foreground-root handle and could miss foreground process-instance drift. Tests were expanded for these checks and the documentation's unverified PASS claims were removed.

The focused file contains **57 test methods**, and the independent focused run passed **57/57**. Automated native calls are mocked. Tests cover metadata, discovery/no-IO construction, exact phrase/argument mapping, default-deny/exact permission and policy blocking, the real ConversationSession path, no confirmation/undo, stable and null targets, null foreground, pointer/hit/root/foreground drift, identity and context fields, incomplete/malformed native values, exceptions, unsupported platform, immutable/redacted evidence, public/audit privacy, historical verification, negative-receipt non-upgrade, native signatures/cardinality, resource ownership and early/late cleanup failures. Source checks include the inherited query facade and exclude mutation/scraping routes. Existing tracked tests are untouched.

## Independent validation results

Codex could not start the repository venv from its sandbox, so the orchestrator reran the required commands directly from the repository root using the intact repository environment:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest tests.test_pointer_observation -v` | **PASS — 57/57** |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | **PASS — 1211/1211** |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | **PASS — Windows 11 AMD64, Python 3.12.10** |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | **PASS** |
| `git diff --check` | **PASS** |
| `git status --short` | Exactly the five intended Phase 6.4 files, all untracked |

The protected HEAD remains `424f7f8448f9a3b6ebc7844a5ea5141ba99dc92c`, and the annotated Phase 6.3 smoke tag still dereferences to that exact commit. Existing tracked files remain unchanged. Supplemental no-index whitespace checks for the five untracked candidate files reported no whitespace defects; LF/CRLF normalization warnings are non-failing.

## Limitations

Win32 queries are synchronous and non-atomic: bounded means fixed call cardinality, not a guaranteed OS deadline. Matching snapshots cannot detect an intervening move-away-and-back, or replacement that reproduces every sampled identity field. Neither HWND nor cursor lifetime can be pinned continuously.

WindowFromPoint follows Windows hit-test semantics. The exact hit HWND is compared across passes; the trusted WindowIdentity is acquired for its root, not a separately trusted child-control identity. A recycled child HWND within an otherwise identical root may be indistinguishable. Root identities include process creation time but no per-window generation token. These limits must be reviewed before any later mutation phase; this receipt grants no such authority.

Root normalization does not establish a child control or future input recipient. Private coordinates are query evidence only. Desktop switching, access/integrity restrictions, destroyed windows and native failures can yield negative receipts. VERIFIED describes historical internal consistency only, not current/future pointer or window state. The completed read-only smoke does not grant authority to any later pointer mutation phase; such a phase requires its own explicit scope, trust review and validation.

## Controlled READ-ONLY disposable-window smoke — PASSED

The controlled smoke ran only after independent deterministic validation passed. A temporary external harness created one disposable Tk window and enforced a private allowlist for that window's root at the native query boundary. Any hit or foreground root outside the disposable root was rejected before identity acquisition. The harness contained no pointer movement, focus, keyboard mutation, screenshot, OCR, UI Automation, scraping, browser-automation or retry route.

Observed public results:
- default-deny leg: **PASS** — `DENIED`, zero guarded native reads, no pending confirmation, undo count `0`
- explicitly granted `observe_pointer` leg: **PASS** — `EXECUTED`, `observed / bounded_snapshot_consistent`, verification `VERIFIED`, no pending confirmation, undo count `0`
- no automatic retry was performed
- no coordinates, HWND/PID/TID values, executable/class names, paths or private evidence were recorded in the smoke result

The operator manually activated the disposable window by clicking the smoke button and kept the pointer over that window for the positive observation. Nayeon performed no mouse, focus or keyboard mutation.

No commit, tag, push or spreadsheet update has been performed. The remaining gate is human review of the Phase 6.4 candidate before checkpoint creation.

Verdict: **PASS FOR HUMAN REVIEW; controlled READ-ONLY smoke completed successfully.**
