# Phase 8.33: bounded offline delayed local status

18 October 2026. Implementation candidate under independently approved design
amendments v0.2/v0.3 and the 16-path SCOPE_GO. **Not a source GO or seal.**
The original background-worker/queue proposal is superseded. No worker-based
implementation is included in this phase.

## Product and authority contract

An accepted human Save offline first commits the existing immutable
USER/LOCAL_STATUS UNSENT_OFFLINE pair through the sealed conversation owner.
Only after that successful commit may the application request a fake local
status transition after 150 ms. The transcript remains unchanged by completion.
The status always says no AI request or action occurred. This is a local UI
simulation, not model output, execution evidence, or permission.

MODEL decides WHAT; AGENT decides HOW; POLICY decides WHETHER; SERVICE performs
IT; VERIFICATION proves RESULT; MEMORY retains appropriate context. This phase
adds no model interpretation, provider, network, credential, action, persistence
or policy bypass. The separate explicit Presentation Review/Save path retains
its existing ownership. Names remain presentation-only. Computer Control v1
and every sealed conversation-owner/source boundary remain frozen.

## Composition and correlation

One application root creates one `DelayedOfflineCompletion`. Its creator-thread
gate precedes every public ingress and callback. `application.py` has no
`after`, `after_idle`, `after_cancel`, worker, polling, or Tcl scheduling call.
All production simulation scheduling is explicit in
`offline_completion_admission.py`.

The helper accepts an exact successful `OfflineCommit`, exact immutable
postcommit snapshot and final user/status pair, with matching session identity,
epoch and revision. It installs one opaque ticket binding private owner, pane,
generation, monotonically increasing request index, operation identity, snapshot
identity and final pair sequences. The request index ranges from 1 through
65535; it never wraps or reuses a value. Ticket identity is authority; a copied
ticket, guessed integer, precommit submission, stale pane or stale snapshot is
insufficient. The application's current predicate binds actual root, view,
token, generation, conversation view authority and current snapshot.

The callback consumes its pending authority before any dependency or render
seam. It checks current view and exact postcommit identity, then gives the
trusted UI a pure eligibility probe. The UI checks that probe after its own
potentially reentrant current-view check. A cancelled A or nested B cannot
receive A's completion status. A duplicate callback has no pending slot.
No delayed render forwards user text or exception text: its only status is the
fixed bounded COMPLETE string. Snapshots remain in-memory owner data.

## Scheduler and lifetime contract

| State | Allowed transition / obligation |
| --- | --- |
| IDLE | Install A, enter REGISTERING and serialize checks before calling `after(150, callback)` |
| REGISTERING | Nested starts cannot register B; cancel/reentrant synchronous delivery revokes A; returned A handle is cancelled only by the outer transaction |
| PENDING | One exact owned returned handle; accepted B may retire A before B registration |
| CANCELLING | Revoke Python authority first; cancel only captured owned A handle; nested starts cannot register |
| POISONED | No further registration; conservatively retain at most one possible physical orphan until actual root retirement |
| CLOSED | Actual root lifetime is terminal; callbacks are inert |

Registration exceptions before or after effective registration, invalid returned
handles, cancellation exceptions before or after effective cancellation, helper
dependency failures and delayed rendering exceptions poison further admission.
Waiting-status publication failure retires a known pending handle and poisons
the helper. Unknown handles are never guessed. No retry, sweep, join, queue,
background thread, repeat timer, reset-expiry timer or replacement timer follows
uncertainty. A synchronously dispatched callback cannot publish success.

Explicit navigation, Cancel local simulation, accepted reset and close revoke
first and retire only the owned timer on the creator thread. Rejected Send,
dismissed review, rejected review and expired confirmation preserve pending A.
An accepted successor Send always retains its honest committed transcript even
if simulation is unavailable during a transaction or after poison.

External child/root Destroy handlers perform only Python revocation. A child
does not declare the root CLOSED. If an external child Destroy leaves a possible
registration, the helper becomes POISONED; later panes may save offline but
cannot register a replacement timer. An already-cancelled navigation leaves
IDLE. Actual root destruction sets CLOSED and retires the Tcl command graph.
No Destroy handler calls Tk, deletes Tcl commands manually, or cancels a foreign
timer. An unrelated timer F remains owned by its original caller until root
retirement. Production introduces zero workers/processes.

## Exact reviewed source scope

Seven additions:

- `docs/phase_8_33_offline_delayed_completion_rfc.md`
- `docs/phase_8_33_offline_delayed_completion_review.md`
- `nayeon/desktop_alpha/offline_completion_admission.py`
- `tests/test_phase_833_offline_completion.py`
- `tests/test_phase_833_tk_completion.py`
- `tests/phase_8_33_scope_migration.py`
- `tests/test_phase_833_scope_integrity.py`

Nine modifications:

- `nayeon/desktop_alpha/application.py`
- `nayeon/desktop_alpha/workspace_window.py`
- `tests/phase_8_32_scope_migration.py`
- `tests/test_phase_832_scope_integrity.py`
- `tests/test_phase_830_scope_integrity.py`
- `tests/test_phase_831_scope_integrity.py`
- `tests/phase_8_30_scope_migration.py`
- `.codex/CURRENT_STATE.md` (reserved exclusive host writer)
- `docs/pre_829_shutdown_ownership_failure_ledger.md`

No additional source path is implicitly admitted. No staging, commit, tag, push,
external service or workbook/dashboard write is authorized in this invocation.

## Source assurance and historical projections

The protected H is `03f247d8627bf1c51105f73b9de5c6bbdf389cf9`, full tree
`4caa8a65b22041b6e1abc2fdf4d249d181082431`, annotated 8.32 tag object
`9fb0f2da5d0e3666fad0c1534fe80fc3b6086c34`. The successor admits only clean
LEGACY H, a complete unstaged candidate, its exact fully staged snapshot, or
one exact child of H. It binds raw HEAD/index/disk records, complete deltas,
file modes, link/reparse/hardlink refusal, aliases, index flags, untracked and
ignored inventories, immutable history and all earlier annotated seals.

The current route is 8.30 -> 8.31 -> public 8.32 -> 8.33. Successor history uses
only 8.32's low-level `_history`, immutable pins and readers; it never calls
predecessor admission, current-source accessors or projection adapters. No
recursion flags, approval caches or monkeypatch routing are introduced.

The original 8.32 assertion body is preserved as `_assert_832_historical` with
its fourteen paths, pins and exact rejection texts. Explicit historical
fixtures read immutable H bytes, never current UI source. The newly modified
8.30 helper's raw historical fixture bytes also come from that sealed tree.
The 8.31 historical fixture enumerates the original product's Python inventory,
and models a committed historical snapshot with no untracked additions. These
private test fixtures cannot approve the actual candidate. Original second-tree
attack positions and specific reached assertions are retained.

Both 8.30 projection adapters preserve exact input validation and their original
integrity call. Only if the input contains the literal new production path do
they lazily import and call 8.33 again. They subtract that path only for explicit
COMPLETE_UNSTAGED, EXACT_STAGED or EXACT_CHILD. LEGACY, unknown values, import
failures and verification exceptions fail closed. Caller sets, similarly named
paths, unrelated paths, old allowlists and historical hashes remain unchanged.
The absent-path route retains its original projection behavior.

All sixteen candidate pin entries deliberately remain zero until the exclusive
host context write. Zero, missing or malformed pins fail closed. Candidate pins
use exact raw bytes; on this LF workspace source raw and LF-normalized digests
coincide. The helper's self entry alone uses SHA256 with its own literal value
zeroed, not a claimed raw self-hash fixed point. Host finalization must fill the
other fifteen pins first, compute and insert that normalized self pin last,
then report all sixteen actual raw SHA256 values externally for independent
review. No pin is independent approval.

## Open Failures & Prior-Issues Review / acceptance

The completion review and append-only failure ledger record the earlier CRLF
baseline mismatch, timer provenance/uncertainty findings, Tcl worker-GC incident,
historical reader migration and 833-SCOPE-01. Design/scope GO authorizes the
bounded repairs; runtime and independent source closure remain HOLD.

Acceptance requires deterministic admission adversaries, native after-info
inventory faults, reentrant A/B/cancel/Destroy checks, unchanged transcript and
input bounds, prohibited-effect counters, and isolated native child tests with
adversarial test-only worker GC during pending/navigation/close/root retirement.
Main-thread root weakref/GC cleanup must complete before unrelated worker GC.
This does not establish general Tk safety for future production workers.

The host must finalize context/pins, run focused, affected historical/trust-path,
full unittest and compileall checks, preserve exit codes and logs, and obtain
independent final source review. No tests have run in this sandbox and no RED or
GREEN result is fabricated. Subsequent human seal, exact staging, seal-time
regression, immutable commit/tag and any separately approved publication remain
distinct gates. Formal readiness stays 5/19 architecture phases and 0/12 release
gates. **Current disposition: implementation prepared; validation/review HOLD.**
