# Pre-8.29 Open Failures & Prior-Issues Review — shutdown ownership repair candidate

Date: 11 October 2026. Branch: `nayeon-v1`.
Protected starting HEAD and remote-tracking HEAD: `85909c175397e45e79700f8720c2967f155a0967`.
Prior product seal: `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01`.
Prior security maintenance seals: `nayeon-v1-pre-8-29-metadata-owner-maintenance-01`,
`nayeon-v1-pre-8-29-recovery-dialog-lifecycle-maintenance-01`.
**Historical audit-entry decision: HOLD — the repair was then uncommitted. See final local-seal evidence and remaining remote/phase gates below.**

## Provenance and scope guard

At audit entry exactly two tracked production files were dirty:
`nayeon/brain/onboarding_metadata_commit.py` (+18 lines) and
`nayeon/desktop_alpha/first_run_metadata_management_window.py` (+31/-13).
The pre-existing diff added `close_ui_owner`, introduced `_claim_owners`,
reordered constructor owner claim after `_sync`, and changed metadata window close.
It was not staged; its exact author and origin cannot be established from Git.
It was reviewed against HEAD rather than discarded or assumed to be sealed.

This maintenance candidate preserves those pre-existing changes, modifies the
shared recovery controller and credential-management window to close alternate
cross-UI paths, and adds fake-only adversarial tests. No actual API key, provider
call, native credential backend, generic model authority or release acceptance.

## Failure-ledger and relevant historical issues

| ID | Severity | Symptom, root cause, trust path | Reproduction/repair | Status |
| --- | --- | --- | --- | --- |
| H-8281 | Previously high | Abandoned or released short-lived mutex with missing marker could admit another process without persisted uncertain evidence. | Phase 8.28.1 tenure-bound state machine, journal IN_FLIGHT readback, fresh human review and fake child-process tests; sealed 3cf53d0. | Historical CLOSED; invariants in cross-phase suite. |
| H-META | Previously medium | Two metadata windows shared mutable review without origin ticket; wrong-window CLEAR possible. | Path-wide UI owner, exact one-use review ticket, CLEAR acknowledgement; sealed e3e5e96. | Historical CLOSED, retested. |
| H-REC | Previously medium | Destroyed recovery-child stale reject consumed another tenure's newer fingerprint review. | Exact fingerprint validation before consume and terminal child callbacks; sealed 4363fd8. | Historical CLOSED, retested. |
| C-01 | Medium, confirmed | Credential Tk close called pooled controller.close directly, revoking another metadata owner's mutex tenure and pending metadata review. Credential UI was an alternate caller outside metadata-only owner binding. | New deterministic red test and genuine Windows Tk foreign-close test; shared exact UI owner token and owner-scoped close for credential and metadata windows. | Candidate repaired, independent review outstanding. |
| C-02 | Medium, confirmed | Recovery controller.close cleared _ctx and UI owner **before** the mutex context __exit__. If exit raises without releasing mutex, an active lock becomes invisible and a new UI owner may be granted. | Exit-fault fake lock reproduced loss of owner; move state reset after successful __exit__, latch unavailable on failure, preserve token. | Candidate repaired, independent review outstanding. |
| C-03 | Medium, confirmed | A credential window destroyed externally (not via WM_DELETE) retained callable methods; a stale approval handler raised TclError on a destroyed status widget after attempting UI cleanup. | Real Windows Tk adversarial red test; credential callbacks now require live Tk root and owner. | Candidate repaired, independent review outstanding. |
| C-04 | Medium, confirmed by independent Codex | External destruction of an owning Tk root stranded its token and mutex in a live process; subsequent explicit close could not identify owner because it required a live widget. | Both metadata and credential panels now have exact-root `<Destroy>` handlers sharing idempotent widget-independent owner-scoped teardown, with deferred close while busy. Real Windows Tk tests verify handover, destroyed callback denial, descendant no-op and busy deferral. | Candidate repaired, independent re-review outstanding. |

## Affected dependency paths

- Metadata: Tk metadata window -> TrustedMetadataCommitHost owner/review ticket
  -> pooled TrustedOnboardingRecoveryController -> same-thread held Windows mutex,
  journal and verified metadata poststate.
- Credential: Tk credential window -> CooperativeOnboardingCoordinator -> shared
  pooled controller -> credential host, typed operation ticket, fake backend/validator.
- Recovery child: Tk recovery window -> fingerprint/epoch/generation -> controller
  reconciliation; callbacks from destroyed child must not consume a new review.
- Alternate close paths: metadata host owner-close, credential panel owner-close,
  trusted controller close, foreign controller claim, stale destroyed Tk callback,
  mutex context exit failure. No model or unauthorised native secret pathway added.

## Deterministic evidence

- Protected initial working-tree regressions: focused 59/59 passed.
- **Before C-01/C-02 repair:** two new adversarial tests failed (2 failures).
- **After repair:** 34/34 targeted tests passed, then full 2237/2237 passed.
- **After adding real Tk cross-window cases:** 4/4 targeted and full 2239/2239 passed.
- **Before C-03 repair:** destroyed Tk root test errored with TclError on dead status widget.
- **After C-03 repair:** credential-window + shutdown adversarial tests 25/25 passed.
- Final complete Windows Python 3.12 working-tree regression including C-03:
  **2240/2240 passed, zero failures or skips**, 124.363s.
  Log: `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_shutdown_full_final.log`.
- `python -m compileall -q nayeon tests` and `git diff --check` passed
  immediately before this final regression.
- Independent Codex Sol High review of earlier candidate: **HOLD, five MEDIUM**;
  each is tracked in the follow-up section below. No independent re-review
  of the newly repaired working tree has yet occurred.
- Exact staged tests, commit/tag, remote peeled-tag verification, Codex handoff,
  same-ID master workbook update: PENDING, deliberately untouched.

## Residual limitations and GO/HOLD rule

The named mutex is a cooperating-process same-Windows-session contract, not
protection from external adversarial filesystem modification or every Windows
session. Journal hash-chain cannot independently detect malicious valid-prefix
rollback; file fsync is not a claim of physical-power-loss directory durability.
No real key or provider poststate is verified; CONNECT/REPLACE remain uncertain.

**HOLD** until independent security review clears C-01 to C-03 and resolves C-04,
the final affected/full suite and compileall pass, exact staged seal-time tests
pass and separate immutable maintenance commit/tag and approved remote push are
independently verified. Only then refresh Codex handoff and same-ID workbook.
Do not start Phase 8.29 or the five-phase batch while this HOLD remains.

## Independent Codex Sol High review — five MEDIUM HOLD findings and candidate response

Codex independent read-only audit (11 Oct 2026) examined the four initial
candidate production files and read-only related trust paths, and returned
**HOLD: 5 MEDIUM**. That reviewer executed five fake-only in-memory probes but
did **not** execute the author's 2,240-test full regression. No changes were
made by the reviewer. The following describes subsequent *author repair
candidates*, not independent re-review or GO.

1. **R-01 — Destroyed metadata Tk callbacks can still approve.**
   The prior `_closed` flag was not set by external `Toplevel.destroy()`.
   Added metadata `_live_window` gating on every review/approval/rejection
   callback; owner-scoped exact-root Destroy teardown cancels this window's
   pending ticket, and stale Python references cannot reach approval.
   Real Windows Tk test confirms metadata remains unchanged and a new
   human-reconciled owner can claim.
2. **R-02 — Win32 ReleaseMutex/CloseHandle BOOL failures not observed.**
   `WindowsOnboardingMutex.hold` now checks both native BOOL results and
   exceptions. On any unproven release it raises and retains the process-wide
   admission lock to prevent a subsequent local contender from being admitted.
   New fake kernel32 tests exercise ReleaseMutex=0 and CloseHandle=0 without
   calling actual native credential operations.
3. **R-03 — Repeated close of exhausted context erased owner.**
   Controller adds `_release_uncertain` terminal latch across `__exit__`.
   If context exit throws, repeated close raises; `_ctx`, owner and UI token
   cannot be cleared by the exhausted generator; fresh claims remain blocked.
   New fault-injection test repeats close and verifies no handover.
4. **R-04 — Live stale recovery-child unscoped close revokes new tenure.**
   Child dialog no longer calls unscoped controller.close. Its exact
   fingerprint rejection can only consume the review it owns. Only the
   management owner performs owner-scoped tenure close. Real Tk stale-live
   child test shows new review remains owned and approvable.
5. **R-05 / C-04 — External destruction strands ownership in a live process.**
   Both management windows now bind exact-root `<Destroy>` and share
   idempotent, widget-independent owner cleanup with WM_DELETE. Destroyed
   descendant widgets are ignored; active work defers close until callback
   completion; no implicit fresh READY or owner handover. Real Tk tests
   verify external destroy, subsequent fresh human reconciliation and
   both busy-deferred cleanup paths.

**Existing test-contract migration:** Prior new test
`test_destroyed_credential_root_callbacks_are_inert` expected a dead owner's
pending review to remain pending. That expectation was unsafe under R-05:
a destroyed owner now cancels its own pending operation. The test retains its
inert-callback/no-backend-mutation assertions and now expects pending=False.
Historical frozen security guards were not modified or bypassed.

### Candidate validation and outstanding gates

- New Codex-followup adversarial suite: 8/8 Windows/fake-only passed.
- Cross-phase affected suite: 127/127 passed; compileall and diff check passed.
- Working-tree complete regression before the final two busy/descendant cases:
  **2,246/2,246 passed** in 142.720s (exit 0, zero failures/skips).
- Final complete regression after final two new tests: PENDING.
- Independent read-only Codex **re-review of amended diff**: PENDING.
- Exact staging, staged full suite, maintenance commit and annotated tag:
  NOT PERFORMED; prior tags preserved.
- Explicit push approval, remote peeled-tag verification, refreshed Codex
  handoff and same-ID macro-enabled master workbook update: NOT PERFORMED.

**Disposition: HOLD** while any independent review finding remains unverified
and until all maintenance seal gates are completed. Phase 8.29 is not started.

### Adjacent alternate trusted-host path identified during candidate validation

**C-05 — MEDIUM candidate blocker, author-identified:** the legacy
`TrustedMetadataCommitHost.release_ui_owner` remained callable while the
pooled controller's mutex was active. Under the old contract it released the
UI owner token without closing the tenure, so another trusted window could
claim the live READY session. This is an internal trusted method, **not** a
model or direct public action route, but it violates the path-wide ownership
invariant and is therefore treated as material pending independent review.
A new deterministic fake-only test reproduced the unsafe True return
before repair. The bounded repair makes
`TrustedOnboardingRecoveryController.release_ui_window_owner` refuse release
while `_ctx` is not None (or native release remains uncertain). Only
`close_ui_window_owner` may release a live tenure after verified exit.
The new test passes; existing sealed history is unchanged.

After the C-05 repair, targeted cross-window tests passed 26/26, and a
complete Windows working-tree diagnostic passed **2,249/2,249** in 211.070s,
exit 0, without failures/skips. This run overlapped briefly with a separate
full-suite process; therefore it is *diagnostic only*, not sole-running
seal-time evidence. Independent Codex Sol High re-review must explicitly
evaluate C-05. Do not claim peer approval from author test results.

### Final sole-running regression and read-only reviewer watchdog — 11 Oct 2026

- Starting and ending source baseline for this candidate remains uncommitted
  above protected HEAD `85909c175397e45e79700f8720c2967f155a0967`.
- A new **sole-running** authoritative Windows Python 3.12 complete discovery
  passed **2,249/2,249**, 0 failures/skips, 163.213 seconds, exit code 0.
  This supersedes the earlier concurrent diagnostic for working-tree evidence;
  it is NOT staged seal-time or postcommit verification.
- `compileall -q nayeon tests` and `git diff --check` passed before the
  previous 2,248/2,248 pass; the extra C-05 regression was targeted green.
- An independent read-only Codex CLI re-review was launched with
  `gpt-6.1-sol`, high reasoning, `-s read-only`, and a prompt covering
  all five earlier MEDIUM findings and C-05. It read source and relevant
  history but provided **no final verdict**. After more than five minutes
  without new meaningful output, process responsiveness/CPU and output were
  inspected; the attempt was terminated per the mandatory watchdog.
  No independent CLEAR may be inferred from this incomplete attempt.
- No real app credentials, native credential writes, provider validation
  calls, Git staging/commit/tag/push, Codex handoff update, or same-ID
  master workbook update occurred as part of this repair candidate.

**Final decision: HOLD.** All known reported issues have repair candidates
and author-side regression evidence, but independent final security clearance
and seal-time evidence remain outstanding. Do not begin Phase 8.29.

### Subsequent independent review and isolated candidate validation — 11 Oct 2026

- Earlier long-running Codex CLI attempt above was terminated per watchdog with
  no verdict; it is **not** used as review evidence.
- Fresh, separately invoked GPT-6.1 Sol / High Codex CLI in `read-only`
  sandbox independently reviewed six reported MEDIUM lifecycle paths against
  protected HEAD `85909c175397e45e79700f8720c2967f155a0967`, including
  C-05. Outcome: **CLEAR in the narrow reviewed scope**, no new HIGH/MEDIUM.
  Result: `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_scoped_security_rereview_result.txt`.
  Reviewer ran nine read-only shell calls and did not edit repository files,
  run tests, touch credentials or call providers.
- Reviewer explicitly noted test coverage limits: native tests prove zero BOOL
  handling but do not inject every thrown Win32 wrapper exception; busy teardown
  tests simulate busy/deferred completion rather than destroying a root from
  inside a real approval callback. No material reviewer finding was raised for
  those limits. Do not silently treat this as release acceptance.
- Before full discovery, affected/cross-phase targeted suite: **75/75 passed**;
  `compileall -q nayeon tests` and `git diff --check` both succeeded.
  No competing Python test runner was present at the start of full discovery.
- Fresh independently orchestrated **sole-running working-tree** Windows
  Python 3.12 discovery: **2,249/2,249 passed**, zero failures/skips,
  142.202s, exit code 0. Log:
  `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_solo_review_cleared_full.log`.
- **Security-review gate: CLEAR** for the six assessed lifecycle findings.
  **Phase-progression / maintenance-seal gate: HOLD** until human staged-scope
  review, exact staged regression, separate maintenance commit and annotated
  tag, explicitly approved push plus remote verification, Codex handoff and
  same-ID master workbook update. No phase 8.29 implementation is authorised
  by this narrow CLEAR alone.

### Local maintenance seal, exact verification and outstanding remote gates — 11 Oct 2026

- Human continuation authorised bounded local maintenance sealing only;
  GitHub push still requires explicit user approval.
- Exactly nine paths were staged and reviewed: six bounded production files,
  the failure ledger and two new adversarial test modules. No unrelated
  working-tree paths, no unstaged diff, no historical tag movement.
- Staged seal-time full unittest discovery, authoritative Windows Python 3.12:
  **2,249/2,249 passed**, zero failures/skips, runtime **130.770s**,
  exit code 0. `compileall -q nayeon tests` and
  `git diff --cached --check` passed. Log:
  `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_shutdown_seal_staged_full.log`.
- Product-security maintenance committed locally:
  `28b417fe1c97cdcb7f5907ecc0db92e7d3ac6622`,
  parent `85909c175397e45e79700f8720c2967f155a0967`.
  New **annotated** tag:
  `nayeon-v1-pre-8-29-shutdown-ownership-native-mutex-maintenance-01`;
  tag object `e6747ac373605297b0ba6315012498ee4f5f9706`
  targets this exact commit.
- An attempted first postcommit run was terminated because a separate
  simultaneous full-suite runner was detected; overlapping runs were
  explicitly **not** counted as postcommit evidence. Neither product
  source nor sealed commit/tag was modified by this runner orchestration.
- Fresh isolated postcommit Windows full discovery:
  **2,249/2,249 passed**, zero failures/skips, runtime **134.851s**,
  exit code 0. Log:
  `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_shutdown_postcommit_isolated.log`.
  Source/tag verification and postcommit working tree were clean.
- Independent read-only Codex Sol High security re-review returned
  **CLEAR** for all six earlier MEDIUM findings; no fresh HIGH/MEDIUM
  finding in its bounded review. Native-throw and real busy-in-callback
  injection remain documented coverage limitations; no automatic
  release gate or credentials were enabled.
- Separate local documentation/handoff reconciliation now records this
  maintenance seal. Current product phase remains **8.28.1**.

**Local maintenance seal: COMPLETE. Remote seal and phase-progression
decision: HOLD.** No GitHub push, remote peeled-tag/branch verification,
same-ID macro-enabled master workbook update or Phase 8.29 work has
been performed. Obtain explicit push approval, push only reviewed branch
and new annotated tag, independently verify remote exact hashes,
then update the same-ID master workbook and run the mandatory phase GO/HOLD
retrospective before starting 8.29. No real keys, credential stores or
provider calls are authorised by this local maintenance seal.
