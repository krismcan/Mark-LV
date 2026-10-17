# Phase 8.32 V7: timerless reset review and UI-thread admission

Date: 17 October 2026. **INCREMENT REVIEW HOLD.** Independent V7 DESIGN_GO
with the isolated-writer amendment is supplied by the user. It authorises this
bounded implementation, not a source GO, product seal or release. No independent
source review or authoritative execution has occurred for these bytes.

Protected detached HEAD: `c9d1b012b79b01897439775fb344819a9cf5367a`.
Protected `nayeon/` tree: `20094cd82e13be48c6cfca34dbac0a2725de2a10`.
The index and workspace were clean before edits. The old Codex state described
an earlier maintenance candidate; Git is authoritative. Original 8.30/8.31
product, documentation and maintenance tags must remain immutable.

## User-approved UX delta

The supplied approval explicitly accepts removal of automatic 30-second prompt
disappearance: expired Confirm and Dismiss controls may stay visible until an
interaction. The owner must refuse expired Confirm without deleting history;
a fresh Review is required. User response after that explanation: **"Go ahead
and finish"**. This acceptance covers this UX change alone. It does not remove
TTL, add live capabilities or waive independent review and regression gates.

The prompt states: **"Valid for 30 seconds. Expired confirmation is refused;
select Review again."** No automatic hiding is promised. Idle expiration neither
changes transcript nor grants authority. Refused Confirm displays **"Reset
expired or unavailable. Select Review again."** and retires that exact review.

## Security target and non-goals

MODEL decides WHAT; AGENT decides HOW; POLICY decides WHETHER; SERVICE performs
IT; VERIFICATION proves RESULT; MEMORY retains appropriate context. Preserve
Permission -> Policy -> Confirmation -> Execution -> Verification. Model output
is neither permission nor execution evidence.

The sealed `OfflineConversationSession` remains the sole root/view/session,
epoch/revision/ticket, one-use reset and TTL authority. Its 30,000 ms TTL and
`now_ms >= expires_at_ms` check are unchanged. Current root/view and exact review,
operation and monotonic time are required at Confirm. The UI is a projection,
never a new permission authority. The Python thread guard only admits calls on
the creator thread; it grants no action, storage or credential capability.

Send remains synchronous, in-memory USER plus LOCAL_STATUS/UNSENT_OFFLINE.
No actual asynchronous AI, provider, model reply, API key, network, WinCred,
native action, transcript persistence, autonomous GUI sequence or task-success
understanding is implemented. No production imports from `tests` are allowed.
Computer Control v1 and the legacy MARK entrypoints remain outside this change.

There is no new reply scheduler, thread, custom Tcl callback registry, timer
quarantine or cancellation adapter. The rejected V3 adapter is absent from this
clone and is not copied, patched or re-authorised. No original user data is read.

## First owned Python ingress

`OfflineWorkspaceApplication` records `threading.get_ident()` before its first
Tk access or owner construction. Each widget-owning base does the same before
`ttk.Frame` construction. Trusted construction occurs on the main/UI thread,
with the root on that same thread. No production worker is started.

The pure `_require_creator_thread` only compares `get_ident()` with that stored
integer and raises fixed `RuntimeError("WRONG_THREAD")`. It does not query Tcl,
owner state, liveness, time or permission; it does not mutate state. It is the
first executable statement in each owned application/view handler, including
read/display, existence, destroy/dispose, Settings trace/draft/review/save,
navigation, reset, Send, clock and cleanup helpers. Callback wrappers guard
before calling supplied Python callbacks. Return bindings guard before
`Button.invoke()`. Conversation validation remains intact and is also guarded.

The first direct arbitrary external worker call to `Button.invoke`,
`event_generate`, `destroy` or another native Tk API is outside the contract:
Python cannot guard before Tcl has already been entered. This is not a sandbox
for malicious same-process code. Tests invoke current-identity Python handlers
from workers with traps for the first owned Tcl, owner, clock and mutation.
Actual native events are dispatched on the main thread.

## Timerless transition table

All rows require creator-thread admission first. Exact view/token/generation
and owner view authority are rechecked after potentially reentrant boundaries.
The application busy/finally discipline remains in place.

| Event | Owner and UI transition |
| --- | --- |
| Review CLEAR / NEW_SESSION | Dismiss exact prior A; clear A controls; refuse to overwrite a successor installed during cleanup. Begin exact new review using monotonic milliseconds, then publish Python callbacks and controls. No `root.after` registration. |
| Begin refuses CLOCK / REVIEW / BUSY | Retire prior A exactly, preserve transcript, show fixed retry status. No UI-derived reset permission. |
| Partial `show_reset` or control configure fault | Dismiss newly issued A exactly; clear its callbacks before disabling controls. Attempt remaining visual cleanup even if one configure fails; restore busy. If visual cleanup remains unavailable, owner A is revoked and no successful reset is claimed. |
| Confirm before expiry | Owner consumes exact review and resets once; clear that exact UI instance, render owner snapshot, display truthful local-clear status only after successful rendering. |
| Confirm at/after expiry or refused CLOCK / REVIEW / BUSY | Exact dismiss plus exact UI clear, no transcript mutation; fixed retry status. A refusal cannot clear successor B. Repeated controls have no A callback or authority. |
| Dismiss | Exact owner dismissal and exact UI cleanup; no clock is needed and history stays unchanged. |
| Rejected Send | Retain pending review explicitly because no transcript commit occurred. Show fixed bounded refusal; validation/capacity stay unchanged. |
| Accepted Send | Owner atomically commits immutable offline pair and invalidates review. Clear only the captured stale review. A render/status exception cannot undo the commit, fabricate an AI reply or claim provider execution. |
| Navigation / close / destruction | Revoke owner view/tickets/review before Tk disposal; clear stale controls where possible. Child Destroy revocation remains Python-only. Root close is terminal before later callbacks. A cleanup must not consume B. |

Lazy cleanup occurs on Review replacement, Confirm, Dismiss, accepted Send,
navigation or close. Read-only display does not expire reviews. Separate test
fake-completion timers and unrelated foreign F timers remain independently
owned. Normal widget Tcl commands are legitimate and are not prohibited.

`ConversationWindow.clear_reset` detaches matching Python callbacks before
visual work, checks for successor publication before each configure, and reports
partial failure to the application. The application revokes exact owner review
before invoking visual cleanup. If an injected failure occurs before the body
of `clear_reset`, visible controls may remain; their exact revoked owner review
still cannot commit. Reopen Conversation is the recovery path. No cleanup may
retry a commit or falsely declare history cleared after an exception.

## Exact source and history boundary

Only these fourteen paths may differ; no deletion or migration of history:

| Change | Path |
| --- | --- |
| ADD | `docs/phase_8_32_reply_admission_rfc.md` |
| ADD | `docs/phase_8_32_lifecycle_assurance_review.md` |
| ADD | `tests/test_phase_832_lifecycle_assurance.py` |
| ADD | `tests/phase_8_32_scope_migration.py` |
| ADD | `tests/test_phase_832_scope_integrity.py` |
| MODIFY | `nayeon/desktop_alpha/application.py` |
| MODIFY | `nayeon/desktop_alpha/workspace_window.py` |
| MODIFY | `nayeon/desktop_alpha/presentation_window.py` |
| MODIFY | `tests/test_phase_831_workspace.py` |
| MODIFY | `tests/phase_8_31_scope_migration.py` |
| MODIFY | `tests/test_phase_830_scope_integrity.py` |
| MODIFY | `tests/test_phase_831_scope_integrity.py` |
| MODIFY | `.codex/CURRENT_STATE.md` |
| MODIFY | `docs/pre_829_shutdown_ownership_failure_ledger.md` |

The 8.30 migration and its literal hashes are untouched. The 8.31 literal
hashes are also unchanged. The public 8.31 check delegates to the successor;
it never chooses a historical bypass using a mutable HEAD. The old complete
assertion body is retained privately for six explicitly decorated synthetic
fixture entrances: `_postcommit`, `_docs_descendant`, `_maintenance_descendant`,
partial staging, complete precommit staging and second maintenance descendant.
Those fixtures read immutable original product831 bytes and supply fake Git
snapshots. The current-reader accessor replacement is confined to the approved
8.30 consumer test file and routes through the complete successor guard.
Historical malformed/index/committed-source/alias traps remain active, with
positive controls and assertions that the second ls-tree injection was reached.

The successor enumerates complete raw HEAD/index/untracked/ignored inventories
before filtering, validates path syntax/duplicates/modes/object IDs, verifies
frozen source and tag history, and checks exact raw non-renamed deltas. It
rejects backslash/case/dot/space/ADS aliases, linked/reparse/hardlinked candidate
files, missing paths, extra/partial/stale index states, mode/type changes,
ignored or untracked source, wrong parents/merges and arbitrary descendants.
Frozen production disk bytes also remain checked. Normal `__pycache__/*.pyc`
artifacts are excluded from source inventory authority.

States: H LEGACY only with no candidate files or changes; H COMPLETE_UNSTAGED
only with all fourteen exact pinned files, nine modified tracked paths, five
new untracked paths and unchanged index; H EXACT_STAGED only with the entire
fourteen-file index agreeing with disk; one EXACT_CHILD only directly above H
with exact full committed/index/disk contents. Detached H is accepted by the
isolated-writer amendment; a named branch must be `nayeon-v1`. No further child,
partial manifest, unknown source or mutable auto-approved hash is allowed.

Candidate hashes are literal, populated once at final source preparation, not
learned during verification. Line endings use the existing LF-normalisation
convention. A hash fixed point for the helper itself is impossible; its one
self entry hashes the helper with only its own 64-character literal zeroed.
All other thirteen entries hash the full normalised bytes. The exact raw
fourteen-file SHA256 manifest is supplied externally for independent review.
**This self-pin representation is an implementation detail requiring explicit
independent source review; do not treat it as a reviewed raw self-hash.** No
independent approval is inferred from candidate-manifest admission.

## Assurance and gates

The old 8.31 workspace test count and unrelated security assertions remain.
Only timer-specific tests migrate to owner TTL, exact A/B cleanup, zero reset
scheduling, foreign-F ownership, reentrant destruction and real widget canaries.
All test-owned root weakref/main-thread collection safeguards remain. The
separate sealed fake queue is unchanged. New native direct-application tests
cover strict deadline just before/at/after, partial show/clear/status faults,
owner refusals, accepted/rejected Send, nested close, wrong-thread current
identities and prohibited-effect attempt counts from app construction through
teardown. Synthetic storage is resolved before construction.

Authoritative host Python is inaccessible in this sandbox. Per repository
instructions, no interpreter/package installation/copy/network workaround is
allowed. Tests, compileall and native Tk execution are **NOT RUN** here. Do not
run authoritative full discovery before the complete exact candidate guard
admits. Host must first run focused guard/lifecycle, 8.29/8.30/8.31 affected and
cross-phase checks, compileall and whitespace. Failed results must be preserved,
diagnosed and repaired only within this envelope. No five-minute stalled
process or unbounded retries are permitted.

Independent source GO with no HIGH/MEDIUM, full native Windows pre-stage,
independent exact staged review, staged full suite, human seal review, exact
commit/annotated tag and postcommit full suite remain separate later gates.
Staging, commit, tag, push, branch changes, fetch, reset/clean/checkout, live
provider/credential/action operations and workbook writes are not authorised
in this implementer run. Formal programme remains 5/19 phases, 0/12 release
gates. No actual AI feature or general Tk safety is claimed.

**Implementation stop notice:** sandbox denied the required context-file append.
Only thirteen of the fourteen approved paths are changed; CURRENT_STATE remains
unchanged, literal hash pins remain zero, and exact-complete admission must fail.
This RFC remains the design/obligation record, not evidence of complete source.
Host-authorised context update, source completion, final pins, authoritative
execution and independent source review remain required. No full suite or seal.
