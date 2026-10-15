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

### Remote closure and bounded final fault-injection follow-up — 11 Oct 2026

**Remote closure of the PRIOR maintenance** (the historical HOLD passages above
remain evidence of what was pending at the time):
- User approved GitHub push. `origin/nayeon-v1` independently reports exact
  branch commit `db8f5ce224f4677f4bc5050939a943c2a7142a08`.
- Remote annotated tag
  `nayeon-v1-pre-8-29-shutdown-ownership-native-mutex-maintenance-01`
  resolves as tag object `e6747ac373605297b0ba6315012498ee4f5f9706`,
  peeled product-security commit `28b417fe1c97cdcb7f5907ecc0db92e7d3ac6622`.
  Historical tags preserved.
- Existing SAME-ID Google Drive workbook
  `Nayeon_v1_Master_Architecture_Audit_Progress_Updated.xlsm`, file ID
  `1n0tDiBQCkPWluX6eakRiRfq57tflRW5L`, has been updated in place;
  Drive readback confirms original ID and macro-enabled MIME type,
  modification time `2026-10-11T17:02:48.571Z`.
  Project readiness remains 5/19 planned phases, 0/12 release gates.
- The earlier pre-push and pre-workbook statements in this append-only audit
  remain chronological evidence, NOT the current remote disposition.

**User-approved LOCAL scope**: add deterministic fake-only Win32 native cleanup
exception tests and real Windows/Tk tests that externally destroy metadata and
credential management roots *inside an actual approve_from_button callback*
for both refused results and exception paths; reconcile Codex handoff; run
focused/affected/full regressions and an independent read-only Codex review,
then prepare a separate local maintenance commit/tag. No production code change,
live credential, native kernel call, provider request, new product phase or push
is authorised by this follow-up.

New `tests/test_pre_829_final_fault_injection.py` exercises:
- ReleaseMutex native exception, CloseHandle native exception, both native
  exceptions; process admission remains BUSY after each unproven release.
  Every test patches a disposable process lock and fake kernel32.
- Metadata and credential management Tk roots destroyed by synchronous,
  instrumented *approval calls* while busy, both on synthetic refusal and
  synthetic exception. Teardown defers until `finally`, old review/tenure is
  cancelled, callbacks remain inert, no fake backend mutation occurs, and fresh
  reconciliation/new UI ownership can succeed. Only temporary metadata and a
  fake credential backend/validator are used.

**Initial focused validation**: 7/7 passed. Full regression and independent
security review are pending at this entry; **Phase 8.29 remains HOLD**.

**Independent final-hardening static review**: GPT-6.1 Sol / High,
read-only sandbox, separately run through Codex CLI; result saved to
`C:\Users\krist\AppData\Local\Temp\nayeon_pre829_final_hardening_review_result.txt`.
**CLEAR for bounded LOCAL test-hardening scope: zero HIGH/MEDIUM findings**.
Codex independently checked that all native API calls and the process gate
are fake, and the metadata/credential Tk tests destroy real Toplevel widgets
synchronously INSIDE production approve callbacks. No files edited or real
credentials/providers/native calls used by reviewer; the earlier 7/7 and 82/82
figures were author test evidence, not reviewer-executed tests.

Coverage limitations recorded honestly: mocked approval service bodies do NOT
validate genuine partial backend writes or real provider effects, nor the
existing durable IN_FLIGHT journal. Direct Python invocation reaches real
approval callback logic and Tk Destroy events but not Tk button dispatch.
Combined native exception test checks latch; individually injected exception
tests also verify a second admission stays BUSY. Earlier security suites cover
stale token/ticket isolation across tenure transitions. These are bounded
test-review caveats, not permission to relax existing sealed trust contracts.

GitHub branch and peeled tag were independently verified in the connected
host before this follow-up. Codex's read-only environment could not access
GitHub; it verified only local cached refs. Google Drive metadata verified
the existing macro-enabled workbook ID and modification timestamp; **cell
contents were not re-read by this Codex review**. Neither claim substitutes
for direct evidence or a new release/readiness approval.

**Disposition**: independent test-hardening review CLEAR; maintenance
seal-time full regression, commit/tag and postcommit verification PENDING.
**Phase 8.29 HOLD; no push approval for this follow-up.**

### Final fault-injection maintenance: local seal complete — 11 Oct 2026

- Independent read-only Codex Sol High assessment: **CLEAR** for exact
  test-only scope (zero HIGH/MEDIUM). Reviewer noted mocked approval services
  do not simulate partial backend writes; those protections remain covered
  under distinct existing recovery/journal architecture tests and have not
  been expanded or bypassed in this follow-up.
- Seven new adversarial tests: **7/7 passed**, zero skips. Affected/cross-phase
  suite: **82/82 passed**, zero skips; Python compileall and staged diff check
  passed. No production file modified.
- Exact staged seal files: `.codex/CURRENT_STATE.md`,
  `docs/pre_829_shutdown_ownership_failure_ledger.md`,
  `tests/test_pre_829_final_fault_injection.py`. No unrelated staging.
- Windows Python 3.12 staged full regression: **2,256/2,256 passed**,
  0 failures/skips, runtime **129.435s**; log
  `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_final_hardening_staged_full.log`.
  PowerShell captured normal unittest summary stderr as a non-fatal
  `NativeCommandError` wrapper; exit code remained 0, and test summary OK.
- Separate local maintenance commit:
  `6cb0e702cab9532c8fc1a46491182b8c9c30feda`
  (parent `db8f5ce224f4677f4bc5050939a943c2a7142a08`).
  NEW annotated tag:
  `nayeon-v1-pre-8-29-final-fault-injection-maintenance-01`,
  pointing exactly to the above commit. Historical product and earlier
  maintenance tags remain unchanged.
- Clean isolated postcommit full regression: **2,256/2,256 passed**,
  0 failures/skips, runtime **130.092s**; log
  `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_final_hardening_postcommit_full.log`;
  postcommit compileall and Git clean-tree verification passed.
- Prior approved GitHub remote seal was branch `db8f5ce`, annotated
  shutdown/mutex tag at `28b417f`. The new `6cb0e70` test-only maintenance
  commit/tag are **LOCAL ONLY** and have **not been pushed**.
  The prior same-ID master .xlsm remains the canonical Drive workbook;
  do not silently publish or update its readiness metrics for an unpushed
  local test-only maintenance.

**Local test-hardening maintenance seal: COMPLETE. Previous security repair
remote seal: VERIFIED. New maintenance remote seal: NOT AUTHORISED. Phase 8.29
and new product development: HOLD** pending separate explicit push/phase
approval and fresh pre-phase failure gate. No live provider, key, credential
store or native Windows mutex was used in the test hardening.

### Verified final remote/workbook close-out and Phase 8.29 RFC preparation — 11 October 2026

This chronological entry supersedes earlier statements that the latest
fault-injection hardening was still local or that the Drive workbook update
was pending. Those older entries remain intact as historical audit evidence.

**Authoritative verified current state**
- Clean nayeon-v1 at 65fddace7276fd0c3daaddd75b6301d12f72a5e0;
  origin branch independently queried with exactly the same commit.
- Latest maintenance annotated tag
  nayeon-v1-pre-8-29-final-fault-injection-maintenance-01;
  remote tag object ae6cc15468dd5285a7ff0d887fcd992e0ed639ac,
  peeled commit 6cb0e702cab9532c8fc1a46491182b8c9c30feda,
  both confirmed. Older security maintenance product and tags preserved.
- Windows Python 3.12 tests: 7/7 new, 82/82 affected and staged/isolated
  postcommit 2,256/2,256 passed; earlier independent read-only Sol High
  maintenance security reviews CLEAR for their bounded scopes.
- Original Google Drive file ID 1n0tDiBQCkPWluX6eakRiRfq57tflRW5L,
  existing macro-enabled .xlsm, was updated in place and fetched back after
  final maintenance. Drive metadata independently reconfirmed now: 168012
  bytes, modified 2026-10-11T18:00:11.411Z; earlier workbook readback
  established the retained 16 sheets and 5/19, 0/12 formal audit.
- There is no user-authorised change to the readiness accounting or prior
  annotated product seals.

**Pre-8.29 independent read-only gate:** Codex Sol High's final bounded audit
found no known unresolved HIGH/MEDIUM production security defect in the
reviewed trust paths. It distinguished **GO for RFC planning** from **HOLD
for implementation**, because the Phase 8.29 RFC and its exact fake-only
integrated acceptance scope require separate independent architecture review
and human implementation approval. It identified stale governance statements
about remote status as confirmed medium-severity process inconsistency,
resolved by this append-only entry and refreshed concise Codex handoff.

**Relevant historical cause / disposition** (do not reopen prior seals):
- H-01 HIGH abandoned/short-lived mutex with missing durable admission
  evidence -> Phase 8.28.1 continuous tenure + fresh human reconciliation
  + journal IN_FLIGHT verified before effects; reviewed/sealed.
- M-01 MEDIUM wrong metadata owner/CLEAR, stale recovery child consuming newer
  fingerprint -> exact owner/ticket/operation/CLEAR acknowledgment,
  fingerprint checked before consumption; reviewed/sealed.
- M-02 MEDIUM destroyed-root callbacks, foreign close, stranded UI tenure,
  native BOOL/exception failure, failed generator exit/retry, legacy owner
  release while active -> owner-scoped exact-root teardown, deferred busy
  cleanup, native uncertainty latch, 7 fake-only final injection tests;
  independent CLEAR, 2,256 full tests, remotely sealed.
- Existing unresolved *scope limits*, not verified defects: only cooperating
  same-session named-mutex writers, external writer and credential ABA,
  journal valid-prefix malicious rollback, directory durability after power
  loss, and absent live exact-key/provider entitlement proof.
- The next RFC must test real Tk event dispatch and fake service effects
  across the pre-effect/during-effect/post-effect recovery boundaries; current
  tests that mock approval-body effects do not themselves establish these.

**New RFC (architecture documentation only):**
docs/phase_8_29_integrated_first_run_acceptance_recovery_rfc.md.
It defines a human opt-in, fake-only integration of existing status, recovery,
metadata and credential management panels, no new privileged controller,
no production auto-wiring and no real backend/provider/native secret calls.
Its exact source allowlist and security acceptance gates require independent
review and separate approval BEFORE implementation.

**Current decision:** GO to bounded read-only RFC review; HOLD for Phase
8.29 implementation, live acceptance, seal/push and any new release claims.
This scope allows documentation edits and review only. Stop on any new
HIGH/MEDIUM reviewer finding or ambiguity. No current product code change
or formal release gate advancement.


### Phase 8.29-A targeted independent RFC review and documentation-only reconciliation — 12 October 2026

**Chronological supersession:** This entry supersedes only the preceding GO-to-RFC-review *planning* gate. Existing Phase 8.28.1 and pre-8.29 maintenance seals, tests, remote verification and master-workbook evidence remain historical and intact. This entry does **not** retract those repairs or assert that a previously closed defect reopened.

**Authorisation / guard:** The user approved only bounded Phase 8.29-A read-only review followed by a separate documentation-only RFC/failure-ledger revision; no new source code/tests, live credentials/provider/native calls, full scan, staged changes, commit/tag/push or workbook updates. Protected branch nayeon-v1 / HEAD 65fddace7276fd0c3daaddd75b6301d12f72a5e0; two previously modified documents and the untracked RFC retained. A GitHub compare confirmed branch and historical HEAD identical before this edit.

**Independent review evidence:** Codex CLI, GPT-6.1 Sol / Medium, ephemeral read-only sandbox, one focused review, no security scanner/tests/subagents. Its output is saved outside the repository at C:\Users\krist\AppData\Local\Temp\nayeon_829a_bounded_review_20261012\review_final.txt. Exact dependency paths and design-contract decisions are recorded in RFC sections I-L. Reviewer result: **HOLD**; static analysis only, not a tested security clearance.

| ID | Classification | Affected trust path; root cause / observed evidence | Required repair or containment and verification | Disposition |
| --- | --- | --- | --- | --- |
| A-01 | MEDIUM, unresolved future integration contract; **not confirmed existing exploit** | CooperativeOnboardingCoordinator.approve(candidate=...) consumes current pending credential operation with no UI owner/ticket/expected-operation arguments (onboarding_coordination.py:201); current credential Tk callback checks ownership locally (first_run_credential_management_window.py:259). Trusted shared/new caller could otherwise retarget a review. Metadata host's approve_ui already binds owner/ticket/operation. | Future privately trusted coordinator-UI one-use owner/ticket/operation/epoch/generation/evidence/expiry binding; reject wrong/foreign/mismatched callbacks before consuming, block raw bypass while UI ticket pending. Adversarial cases K2. | **OPEN; Phase 8.29 HOLD** |
| A-02 | HIGH-impact future integration risk, **not confirmed current production vulnerability** | credential_onboarding_composition.py:17 unconditionally constructs OpenAICredentialValidator, so fake backend alone does not prove fake-only execution. Existing real factory must never be invoked by new test harness. | Design separate exact fake-backend + fake-validator + fake observer + fake mutex dependency factory, canonical temporary path, no default fallback, import/construction/approval tripwires. Import closure remains unverified. Cases K3. | **OPEN; Phase 8.29 HOLD** |
| A-03 | **MEDIUM current UI availability defect, independently identified by static trace; runtime repro PENDING** | first_run_onboarding_recovery_window.py:64 installs WM_DELETE but no Destroy-event cleanup for externally destroyed recovery-child root; onboarding_recovery.py:261 refuses another review while old controller._review exists. Existing tests cover stale child after parent closes, not child-only destroy while parent stays open. | Reproduce real Tk child-only destruction, then smallest root-specific idempotent cancellation of **exact fingerprint only**; never close parent tenure or consume a newer review. Add adversarial red/green, nested/reentrant/double destroy and retained callback tests. Suggested narrow repair sources and tests in RFC J1/K1. | **OPEN; pre-8.29 repair needed before implementation** |
| A-04 | MEDIUM future integration evidence gap; **existing protections reviewed, no confirmed bypass** | Recovery journal, epoch/generation and current-process pooling distinguish persisted READY from fresh admission, but simulated process death/restart lifecycle has not been proven by integrated fake-only acceptance (onboarding_recovery.py:63,193,261,344). | Distinguish graceful teardown from crash; retain journal/marker/fake effects but discard all process-local permits, epoch, ticket, reviews, owners, pool; demand fresh reconciliation and operation review, no retry/false key proof. Cases K5/K6. | **OPEN; Phase 8.29 HOLD** |

**Additional review limitations:** No genuine code execution, Tk event dispatch, credential effects, native mutex, actual provider operation or re-run of the 2,256 full Windows tests was carried out during the independent Phase 8.29-A review. The latest historical 2,256/2,256 is valid for earlier maintenance only. No new HIGH/MEDIUM existing production exploit has been demonstrated beyond the A-03 availability concern.

**Resource governance incident:** A reviewer prompt requested an indicative 45k token target and <=70k cap, but the CLI provided no enforceable runtime cutoff and reported **413,568 total input tokens (including 356,992 cached input) plus 4,344 output tokens** at completion. This budget was **not enforced**, even though scope and read-only sandbox were. Until a genuinely externally enforced budget/watchdog is established, avoid further automatic Codex reviews; a written prompt limit alone cannot be relied upon. This is a review-operations control gap, not evidence of a product vulnerability.

**Mandatory next decision / STOP:** GO for preservation of these documentation-only amendments; **HOLD Phase 8.29 product implementation and independent security clearance**. Next exact separately approvable scope: pre-8.29 **child-only destroyed recovery-dialog lifecycle** red/green repair confined to nayeon/desktop_alpha/first_run_onboarding_recovery_window.py and tests/test_pre_829_recovery_child_lifecycle.py plus tests/test_onboarding_recovery_ui.py, with dependent read-only inspection permitted and any scope expansion requiring separate approval. Run affected/cross-phase/full authoritative Windows regressions, compileall, diff checks, fake-only Tk probes and independent review before any local maintenance seal request. No Git or workbook actions authorised here. Review and close remaining A-01/A-02/A-04 contracts separately before proposing integrated 8.29 implementation.



### A-03 recovery-child exact review-instance repair — verified LOCAL maintenance seal and documentation reconciliation, 12 October 2026

**Chronological disposition supersession ONLY:** This entry supersedes the earlier 12 October A-03 `OPEN / runtime reproduction pending` planning status and the intermediate review HOLD. Those entries are retained verbatim as historical evidence. A-01, A-02 and A-04 remain OPEN, and Phase 8.29 RFC clearance/implementation remain HOLD. Earlier Phase 8.28.1 product and pre-8.29 maintenance seals are not reopened or modified.

**Root cause and deterministic red evidence (A-03, MEDIUM availability/review-isolation defect):**
- In `nayeon/desktop_alpha/first_run_onboarding_recovery_window.py`, only `WM_DELETE_WINDOW` previously cleaned a child; external child-only Tk `<Destroy>` left the controller's review pending. Original red test reproduced the stranded review while the owning parent window and mutex tenure stayed alive.
- The first local child-lifecycle repair exposed a second reentrant review-instance ABA risk: `TrustedOnboardingRecoveryController.approve_reconciliation` matched only a SHA-256 evidence fingerprint. Within an unchanged epoch/evidence baseline, cancellation of review A and creation of B can produce distinct `RecoveryReview` objects with identical fingerprints. A's delayed cancellation/approval then consumed B. A real-Tk fake-only reentrant test reproduced RED (`None is not <RecoveryReview ...>` at the successor-review isolation assertion).
- Separate RED stale Tk approval and rejection tests showed same-fingerprint successor review B could also be consumed by an older live child's buttons. These are review isolation/availability defects; no live credential mutation or bypass to provider was demonstrated.

**Approved bounded product repair and exact trusted call contract:**
- In `nayeon/brain/onboarding_recovery.py`, `approve_reconciliation(..., expected_review: RecoveryReview | None = None)` checks exact type and `expected_review is self._review` **before consuming the active review**, in addition to the original fingerprint, tenure/epoch, human boolean, expiry/evidence, journal and native-mutex protections. The optional parameter preserves previous trusted direct-call compatibility; it must **not** be used as an identity-free approval route by future UI composition.
- In `nayeon/desktop_alpha/first_run_onboarding_recovery_window.py`, root-specific Tk Destroy handling and all child-originated approve/reject/cancel paths pass the exact original `RecoveryReview` object, even for an interrupted request or reentrant Destroy. Descendant Destroy is inert; the recovery child cannot close/release the parent's owner-scoped tenure. Stale callbacks and mismatched review objects are rejected without consuming a successor.
- Only test file `tests/test_pre_829_recovery_child_lifecycle.py` was extended. Synthetic Tk/fake mutex/temporary journal tests cover child-only Destroy, same-fingerprint successor and stale buttons, request/approval reentry, descendant events, cancellation exceptions, destruction **after** consent consumption, observation failure, and a synthetic failed READY checkpoint after a real RECONCILING journal write. The latter preserves an uncertain journal and blocks admission; a previously acknowledged normal reconciliation can finish after the child closes when verification succeeds.

**Tests and independent review evidence (Windows Python 3.12; no real keys/provider/native Credential Manager):**
- Local A-03 stage gate: exactly `nayeon/brain/onboarding_recovery.py`, `nayeon/desktop_alpha/first_run_onboarding_recovery_window.py`, `tests/test_pre_829_recovery_child_lifecycle.py` staged. Other pending documents deliberately excluded. Staged `git diff --check` and `compileall` PASSED.
- Seal-time **18/18 focused**, **159/159 affected/cross-phase**, **2,269/2,269 full** PASSED; full runtime **147.215s**, exit 0. Logs: `C:\Users\krist\AppData\Local\Temp\nayeon_a03_seal_20261012_focused.log`, `nayeon_a03_seal_20261012_affected.log`, `nayeon_a03_seal_full_20261012.log`.
- Bounded **independent read-only** staged-snapshot review via Sol Medium, with host-enforced 85-second watchdog, completed in 38 seconds, inspected staged source/test diff plus exact Git scope, reported **GO; no confirmed HIGH/MEDIUM** within this maintenance scope. Evidence `C:\Users\krist\AppData\Local\Temp\nayeon_a03_seal_independent_final_20261012.txt`. Reviewer did **not** execute the tests. Earlier bounded source repair and test-hardening reviews also returned GO; they do not clear Phase 8.29 integration.
- Isolated **postcommit 18/18 focused** and **2,269/2,269 full** PASSED; full runtime **147.113s**, exit 0. Logs: `C:\Users\krist\AppData\Local\Temp\nayeon_a03_postcommit_focused_20261012.log`, `nayeon_a03_postcommit_full_20261012.log`.
- Reviewer LOW/limited coverage: injected READY persistence failure occurs before the READY write (not after a successful write that then raises); cancellation exceptions may leave a pending review blocked (fail-closed, not automatic recovery); native release counts, uncooperative writers and live provider or key correctness were **not** established by these fake-only tests. Scope limitation retained, not silent release clearance.

**Exact immutable LOCAL seal evidence:**
- Branch `nayeon-v1`; local commit `74814715433e184ecb1f0932666f710d4e92a632`; parent `65fddace7276fd0c3daaddd75b6301d12f72a5e0`; exactly the three approved source/test files.
- New annotated LOCAL tag `nayeon-v1-pre-8-29-recovery-review-instance-maintenance-01`; tag-object `1736b04224890693120e2279a54db69a171194ba`, peeled exactly to `74814715433e184ecb1f0932666f710d4e92a632`.
- All prior historical product/maintenance tags unchanged. Previous remotely verified branch and current locally observed origin tracking ref remained `65fddace7276fd0c3daaddd75b6301d12f72a5e0`. **This new commit and tag were NOT pushed or independently remotely verified.**
- Pending **documentation-only, unstaged** files: `.codex/CURRENT_STATE.md`, this append-only `docs/pre_829_shutdown_ownership_failure_ledger.md`, and untracked `docs/phase_8_29_integrated_first_run_acceptance_recovery_rfc.md`. They were not included in the maintenance commit. Same-ID Google Drive macro-enabled master workbook **NOT updated**.

**Final issue disposition and STOP gate (as of this entry):** `A-03 = LOCAL REPAIR + ADVERSARIAL VALIDATION + INDEPENDENT REVIEW + ANNOTATED LOCAL SEAL COMPLETE; REMOTE PUSH / WORKBOOK RECONCILIATION NOT AUTHORISED.` `A-01 = OPEN` (credential approval owner/ticket), `A-02 = OPEN` (strict fake-only factory/validator), `A-04 = OPEN` (simulated crash/restart evidence). **Phase 8.29 RFC architecture approval and implementation = HOLD.** Formal architecture program remains **5/19 completed phases, 0/12 release acceptance gates**, Phase 8 IN PROGRESS. No production phase progress or live integrations authorised. Separate user approval required for any new stage/commit/tag, push, workbook update, or future integration.


### Phase 8.29-A A-01/A-02/A-04 independent architecture-contract review and documentation finalisation — 12 October 2026

**Chronological controlling update:** This append-only entry supersedes earlier instructions to *start* A-01/A-02/A-04 reviews; it does **not** mark those OPEN issues as fixed, tested or security-cleared. Phase 8.29 implementation is HOLD. A-03 remains the **separately verified LOCAL-ONLY** repair at `74814715433e184ecb1f0932666f710d4e92a632`, tag `nayeon-v1-pre-8-29-recovery-review-instance-maintenance-01` (annotated object `1736b04224890693120e2279a54db69a171194ba`, peeled to that commit). Historical product/maintenance seals, last verified remote branch checkpoint `65fddace7276fd0c3daaddd75b6301d12f72a5e0` and prior remote tag `ae6cc15468dd5285a7ff0d887fcd992e0ed639ac` remain unchanged.

**Scope and evidence:** User authorised bounded source-focused **read-only independent architecture reviews**, followed by a separate **documentation-only** contract finalisation. Three reviewer reports were saved outside the repository:
- **A-01** `C:\Users\krist\AppData\Local\Temp\nayeon_829a_a01_independent_final_20261012.txt`. GPT-6.1 Sol / Medium, two read-only source inspections, completed. **MEDIUM existing API-origin-binding design gap:** coordinator `approve(candidate=...)` / `reject()` accept no exact owner, ticket, operation or review-instance identity. An interleaving in which a trusted caller replaces review A with B (even the same operation) can retarget old window callbacks; an exploit via normal current application buttons was **not** demonstrated. Window owner checks, busy, REMOVE acknowledgement and epoch/generation do not alone bind the initiating review. The host's TEST_CANDIDATE ticket is not a CONNECT/REPLACE/REMOVE grant. Outcome: **GO for bounded RFC contract specification, HOLD for implementation**, A-01 OPEN.
- **A-02** `C:\Users\krist\AppData\Local\Temp\nayeon_829a_a02_independent_final_20261012.txt`. Two read-only source inspections with an explicit process watchdog; reviewer report and `turn.completed` exist, but host returned **TIME_LIMIT after approximately 87s**. Treat as scoped design input, **not compliant timeout clearance**. **HIGH-impact prospective integration misuse**, not confirmed current production vulnerability: `compose_openai_credential_onboarding` constructs a real `OpenAICredentialValidator`; validation can reach OpenAI SDK/client/network despite fake backend. `BoundCredentialLifecycle` constructor attribute lookups can have dependency-defined side effects; missing mutex defaults to a native mutex; canonical-path recovery pool binds concrete observer/mutex identities. Complete import closure and runtime side effects remain UNVERIFIED. Outcome: A-02 OPEN; RFC/design may use findings but integration remains HOLD.
- **A-04** `C:\Users\krist\AppData\Local\Temp\nayeon_829a_a04_independent_final_20261012.txt`. Two read-only source inspections, completed approximately 36s. **MEDIUM integration acceptance evidence gap**, no confirmed new HIGH/MEDIUM production defect: fresh recovery controller begins with no READY, epoch or permit and requires fresh reconciliation; however same-process `for_path()` pools existing live authority, so host/window reopen or `close()` is NOT simulated process death. Earlier tests provide controller/host unit evidence but not actual crash barriers, persisted fake-effects continuity, stale-ticket rejection or full integrated uncertainty proof. Outcome: A-04 OPEN; Phase 8.29 HOLD.
- All these were **static, bounded independent reviews**; no Phase 8.29 test executed, no real credentials, SDK/network/WinCred/native actions invoked by the reviews, and no claimed clean integrated acceptance. A-03's 18/18 focused, 159/159 affected, 2,269/2,269 seal-time and 2,269/2,269 postcommit full Windows tests are historical LOCAL maintenance evidence only.

**Contract resolution and ordered future approval gates (see controlling RFC Section N):**
1. **FIRST A-02**: an independently authorised `tests/`-only explicitly injected exact fake backend, validator, observer, fake mutex and temporary canonical path, with a strictly separate composition factory and deny/spy guards covering import, construction, review and approval; provider SDK/network, Windows credential store, native mutex and unintended real filesystem side effects attempted/completed counts must be zero. A deliberate blocked production-validator probe must prove the tripwire works. Production `credential_onboarding_composition.py`, `openai_validation.py`, real secret backend and native mutex remain OUT OF SCOPE for changes.
2. **SECOND A-01**: independent human approval for bounded production edits only to `onboarding_coordination.py`, `first_run_credential_management_window.py`, plus one named trusted adapter if type-safe architecture requires it and matching tests. Coordinator-enforced opaque one-use exact owner/root + host/coordinator + operation + review instance + expiry + epoch/generation + fresh metadata/observer binding; REMOVE explicit acknowledgment; raw legacy approve/reject cannot consume UI-bound review. Adversaries: equal-operation A/B succession, duplicate/foreign/replayed/expired/wrong-operation tickets, destruction/reentrancy, two managers, observer/epoch changes and forged consent. No new model route.
3. **THIRD A-04**: separately approved `tests/`-only parent/child process crash harness with temp disk journal and durable synthetic effect ledger. Terminate Child A without `close()`; run fresh Child B with no inherited owner/tickets/epoch/READY; cover persisted READY, IN_FLIGHT before/after fake effect, RECONCILING, marker and corrupt/missing journals, fake ABANDONED, fsync/readback failures, archive and fake native-release errors; no automatic retries and no retrospective credential success claims. Never monkeypatch production `_POOL` to fake a restart.
4. **FOURTH**: separately approved read-only holistic RFC security/architecture review; only after all issues closed may a new Phase 8.29 implementation allowlist be brought for distinct human approval. Then, if authorised, full fake-only Tk integration, red/green/affected/full Windows regression, source review and separate local/remote/workbook gates.

**STOP and authority:** Halt for ANY new or unresolved HIGH/MEDIUM finding, unsafe fallback/import, real SDK/network/credential store/native mutex attempt, stale approval or successor consumption, false READY, automatic retry, unknown partial effect, unexplained test failure or skip, review timeout, unapproved source expansion, or attempt to bypass human approval. No broad automated security scan or prompt-only token budget accepted as hard control. Contract specificity does **not** constitute a code authorisation.

**Exact documentation-only reconciliation in this turn:** append controlling Section N to `docs/phase_8_29_integrated_first_run_acceptance_recovery_rfc.md`, update `.codex/CURRENT_STATE.md`, append only this entry to `docs/pre_829_shutdown_ownership_failure_ledger.md`. Do not alter prior ledger entries, source/tests, Git index, commit/tag/remote or master workbook. The three documents remain UNSTAGED/UNCOMMITTED pending separate approval. **Final program state:** Phase 8 IN PROGRESS; **5/19 completed planned phases, 0/12 verified release gates**; A-03 LOCALLY SEALED/NOT PUSHED; **A-01/A-02/A-04 OPEN; Phase 8.29 RFC clearance and implementation HOLD**.


### A-02 fake-only isolation — exact LOCAL maintenance seal, independently reviewed and postcommit verified (12 October 2026)

**Chronological disposition update; APPEND ONLY.** This entry supersedes the earlier A-02 `OPEN / not yet implemented` planning status **only for the separately approved test-only isolation gate**. Retain the original A-02 prospective high-impact integration finding, the first independent remediation HOLD, and all preceding A-03 / Phase 8.28.1 evidence unchanged. A-02 is **LOCALLY SEALED IN ITS TRUSTED TEST-ONLY SCOPE, NOT AN INTEGRATED PHASE 8.29 SECURITY CLEARANCE**. A-01 and A-04 remain OPEN; Phase 8.29 RFC security sign-off and implementation remain HOLD.

**Bounded implementation and actual adversarial chronology:**
- User-approved exact code-file allowlist: only new `tests/a02_fake_isolation_support.py` and `tests/test_pre_829_a02_fake_isolation.py`. No `nayeon/` production, real provider/validator, native mutex, Windows Credential Manager, policy, desktop or CLI changes. No live secrets, SDK/provider network requests or native credential mutation.
- Initial fake composition passed 8 focused tests, but an independently timed static read-only source review returned **HOLD**, reporting three **MEDIUM fake-fixture design findings**: (1) mutable module class identity / poisoned property getter could defeat a purported exact-type check; (2) `object.__setattr__` could retarget observer/backend after initial composition; (3) a mutable temporary-directory manager name could substitute another owner's directory, and a pre-existing regular `provider.json` was accepted. Reviewer also found a test I/O `completed` counter hardcoded at zero (not genuine completion measurement). Those findings were scoped **test-fixture isolation defects**, not demonstrated real credential effects. Earlier HOLD evidence: `C:\Users\krist\AppData\Local\Temp\nayeon_a02_isolation_independent_final_20261012.txt`.
- Four targeted tests reproduced the mutable-class, direct backend-retarget, temp-owner substitution, and pre-existing-file cases deterministically **RED (4 failures)** against the initial fixture. A separately approved bounded repair (same two files) captured exact trusted fake class/method/property descriptors, required observer/backend identity at each observation, introduced an internally allocated and anchored `FakeTempRoot`, and rejected existing `provider.json` and path aliases before test composition. Invalid dependencies, explicit real SDK/native/WinCred/socket tripwires and the synthetic validator tri-state are also exercised.
- Removed the fabricated `completed=0` metric. The `ProhibitedIO` fixture now accurately records **attempts to reach selected instrumented forbidden entrypoints**. Its deliberate real-production-factory negative control is expected to hit the SDK loader poison and stop **before delegate/client/network use**. Allowed test paths exhibit no recorded forbidden attempts, not a guarantee of globally zero effects.
- Follow-up independent *read-only* bounded repair review returned **GO**, no confirmed HIGH/MEDIUM within the fixed test-only scope: `C:\Users\krist\AppData\Local\Temp\nayeon_a02_remediation_review_final_20261012.txt`. Four RED cases then pass GREEN; 12/12 focused, 304/304 affected and 2,281/2,281 full Windows regressions passed before staging. A minor two-line trailing-whitespace check failure was corrected *before* running the final affected/full suite; compilation, whitelist and whitespace then passed. Earlier findings and repair history remain visible.

**Exact independent local sealing gates (authoritative Windows Python 3.12):**
- Protected pre-seal branch `nayeon-v1`, starting local HEAD `74814715433e184ecb1f0932666f710d4e92a632` (A-03). Only the two A-02 new test files staged, mode `100644` each, **600 inserted lines** and no other tracked/test/production/documentation files added to the index. `git diff --cached --check`, `compileall -q nayeon tests`, stage-vs-worktree and staged whitelist **PASS**.
- Independent fresh read-only Sol Medium review of the **actual staged diff** **GO**, no confirmed HIGH/MEDIUM, completed within externally enforced 110-second host timeout in about **70 seconds**. Its exact scope and static-only limitations were explicitly reported: `C:\Users\krist\AppData\Local\Temp\nayeon_a02_seal_staged_review_final_20261012.txt`; machine event log `nayeon_a02_seal_staged_review_events_20261012.jsonl`. The reviewer did **not** execute tests or inspect every native provider route.
- Seal-time focused **12/12 PASSED**; affected/cross-phase **304/304 PASSED** (42.862s); full authoritative Windows **2,281/2,281 PASSED** (146.856s), zero recorded failures or skips, exit 0. Logs in `C:\Users\krist\AppData\Local\Temp`: `nayeon_a02_local_seal_20261012_focused.log`, `nayeon_a02_local_seal_20261012_affected.log`, `nayeon_a02_local_seal_20261012_full.log`.
- Only after stage review and full test gates passed: exact two-file LOCAL commit `5550349ac41bca957c25ddc257b2982a0c2c2d65`, exact parent `74814715433e184ecb1f0932666f710d4e92a632`. Annotated LOCAL tag `nayeon-v1-pre-8-29-a02-fake-isolation-maintenance-01`, tag object `7dd5b9a4d61c63f29880644f15250db301121b3c`, peeled to exact new commit.
- Exact committed file names: `tests/a02_fake_isolation_support.py`, `tests/test_pre_829_a02_fake_isolation.py`; no other code, tests or documentation committed. **Postcommit 12/12 focused PASSED** (0.223s); **postcommit full Windows 2,281/2,281 PASSED** (150.267s), exit 0. Logs: `nayeon_a02_postcommit_20261012_focused.log`, `nayeon_a02_postcommit_20261012_full.log`. Postcommit HEAD, exact parent, annotated tag object/type/peeled target, empty stage and remaining docs-only worktree independently checked.
- A-03 historical annotated local tag remains `nayeon-v1-pre-8-29-recovery-review-instance-maintenance-01` (object `1736b04224890693120e2279a54db69a171194ba`, peeled `74814715433e184ecb1f0932666f710d4e92a632`); older pre-8.29 tag object `ae6cc15468dd5285a7ff0d887fcd992e0ed639ac` unchanged. Last independently remotely verified branch and local `origin/nayeon-v1` tracking ref remained `65fddace7276fd0c3daaddd75b6301d12f72a5e0`. **A-02/A-03 local commits and tags NOT pushed or remotely re-verified; same-ID master workbook NOT updated**.

**Explicit non-security guarantees and unresolved evidence:** A Python test fixture cannot isolate malicious arbitrary code running in the same interpreter. Descriptor snapshots are checked at composition time; later monkeypatching, coordinated private-field writes via `object.__setattr__`, temporary filesystem races, complete transitive import closure, uncovered network/native entrypoints, real credential/SDK behavior and universal synthetic-secret log hygiene remain **outside demonstrated coverage**. The test-owned temporary directory and fake journal are permitted filesystem I/O. Real factory access in the deliberate negative control is **poisoned at the SDK loader** and does not establish global interception of all routes. No A-01 exact UI ticket binding, A-04 genuine crash/restart acceptance, Phase 8.29 real Tk integration, real key correctness or user-facing release proof has been demonstrated.

**Controlling current disposition:** `A-02 = VERIFIED + LOCALLY SEALED (TEST-ONLY FAKE-COMPOSITION GATE); REMOTE PUSH / WORKBOOK NOT AUTHORISED.` `A-03 = LOCALLY SEALED (RECOVERY CHILD); REMOTE PUSH / WORKBOOK NOT AUTHORISED.` `A-01 = OPEN`; `A-04 = OPEN`; **Phase 8.29 RFC security clearance and implementation = HOLD**. This entry documents an already completed seal, not another permit to stage/commit/tag/push or to begin A-01/A-04/Phase 8.29. Pending documentation-only worktree changes are `.codex/CURRENT_STATE.md`, this append-only ledger, and the untracked Phase 8.29 RFC. Formal program stays **Phase 8 IN PROGRESS; 5/19 completed architecture phases, 0/12 independently verified release acceptance gates**.

### A-01 exact owner UI ticket — local seal, independent reviews and postcommit Windows regression (13 October 2026)

**Controlling chronological append-only update:** This supersedes earlier A-01 OPEN implementation statuses ONLY for the bounded locally verified coordinator/Tk ticket maintenance. Preserve the earlier MEDIUM origin-binding gap and HIGH reentrant expiry-clock finding as historical defects and regression obligations. A-01 is LOCALLY SEALED, NOT pushed or remotely sealed. A-02 test-only isolation and A-03 recovery child remain earlier local-only seals; A-04 genuine fresh-process restart evidence OPEN; Phase 8.29 combined security review and implementation HOLD.

**Implementation and adversarial evidence:** Coordinator-enforced one-use UI approval tickets bind exact owner/root, operation, captured pending review identity, recovery epoch/generation and expiry. Legacy raw approve/reject cannot consume ticket-owned pending reviews. Same-operation stale A callbacks cannot approve/reject successor B; exact owning shutdown can revoke B without A revoking B. Replay, wrong owner/root/operation, expiry, unexpected RNG/clock failures, issuance reentrancy, and Tk Destroy during approval are covered. The original HIGH finding was approval-time clock reentry replacing A with B while returning a valid float: fixed by checking full exact identity after expiry clock returns and before executing approval. REMOVE acknowledgment and earlier native mutex/Tk fault-injection assertions remain protected. A-02 fake-only fixtures with synthetic keys and temporary paths; no real SDK/provider/WinCred mutation performed.

**Independent review:** Bounded staged production completion report Windows Temp/nayeon_a01_staged_prod_completion_final_20261012.txt = PRODUCTION_COMPLETION_REVIEW=GO; inspected previously omitted _approve_pending and _approve_recovered, no confirmed HIGH/MEDIUM. Independent staged tests report Windows Temp/nayeon_a01_staged_tests_review_final_20261012.txt = TEST_STAGED_REVIEW=GO, no confirmed HIGH/MEDIUM or weakened historical fault assertions. Both static read-only reviews (GPT-6.1 Sol Medium), not universal runtime proof.

**Seal provenance:** Protected pre-A-01 parent 5550349ac41bca957c25ddc257b2982a0c2c2d65. Four exactly staged 100644 files, 750 insertions / 18 deletions: nayeon/brain/onboarding_coordination.py (blob efb7b41813dd1438d4744b1535548e062b7214f8), nayeon/desktop_alpha/first_run_credential_management_window.py (66bce8c57ff86a5a99d96707e335db1d9170ab73), tests/test_pre_829_a01_review_identity.py (093ec5c6c0547cf1983897027bef7526319d56f3), tests/test_pre_829_final_fault_injection.py (ea86d37d29fce5e9f9e0f02d8de2031ab72c279e). Manifest SHA-256 and documentation unchanged through seal; compileall and git diff --cached --check PASS. Seal-time focused 22/22, affected 322/322, full 2,299/2,299 Windows unittest PASS, original process exit 0 independently recovered from Desktop Commander history. No duplicate pre-seal regression launched.

**Exact LOCAL Git seal:** commit 7d20eb3e75a0072efd2c4abed64363d74ebdd72c, annotated tag nayeon-v1-pre-8-29-a01-review-owner-ticket-maintenance-01, tag object e7ca635fb07c93711f10dcec173d86ec44623110, peeled to A-01 commit. Postcommit full Windows unittest 2,299/2,299 PASS, 157.420 seconds, exit 0; Windows Temp/nayeon_a01_postcommit_full_20261013.log. Final HEAD/parent/four-file tree/staged index/annotated tag/document hashes/historical A-02 and A-03 tag objects independently verified. Local origin/nayeon-v1 unchanged at 65fddace7276fd0c3daaddd75b6301d12f72a5e0. Prior remote-sealed pre-8.29 tag object ae6cc15468dd5285a7ff0d887fcd992e0ed639ac unchanged. No GitHub push or same-ID master workbook update.

**Residual limitation / HOLD:** After coordinator pending state is consumed, an early refusal or exception from an unexpected trusted dependency might leave host pending state uncleared. Source review did NOT prove that real host can reach this, gain authority, consume B or bypass consent. This inherited host cleanup concern remains UNVERIFIED (not confirmed HIGH/MEDIUM), and must be explicitly dispositioned in later combined security review. No universal fake test isolation, malicious in-process mutation containment, live BYOK correctness or A-04 crash evidence is claimed.

**Gate status:** A-01 LOCALLY SEALED / NOT PUSHED; A-02 TEST-ONLY LOCALLY SEALED / NOT PUSHED; A-03 LOCALLY SEALED / NOT PUSHED; A-04 OPEN. Phase 8.29 security approval and implementation HOLD. Phase 8 IN PROGRESS; 5/19 architecture phases complete, 0/12 release acceptance gates. This documentation-only reconciliation does not authorise doc stage/commit/tag, push, workbook edits, code or tests, or moving to A-04.

### CONTROLLING Open Failures & Prior-Issues Review — Phase 8.29-A, 15 October 2026

Chronological append only; supersedes earlier current-status statements, preserving their historical findings. Current scope is three-file docs-only reconciliation. **RFC independent re-review OPEN / HOLD; implementation HOLD.** Controlling design/evidence: RFC Section Q.

| Issue / source | Severity, root cause and affected boundary | Evidence, containment, next proof / disposition |
| --- | --- | --- |
| A01/A02/A03 prior seals; A04 host handoff | Historical maintenance findings; closure limited to each sealed scope | A04 protected HEAD `fb6e182bad421a3d26e11d3f4db12f4a3aa59a87`; annotated tag `nayeon-v1-pre-8-29-a04-two-process-recovery-acceptance-01`, object `2f1bbe927d356135bb8a92e7f4d6ccde0e8b94a2`, locally verified peel. User reports pushed/remote peel, 22/22 focused, 112/112 affected, 2321/2321 seal-time and post-commit full Windows; independent final GO, no HIGH/MEDIUM. A04 bounded maintenance CLOSED; no integrated RFC GO inferred. |
| 829-R1 / first integrated independent architecture review (reported) | MEDIUM design gap: metadata-first pooled controller can conflict with credential observer; status closure identity underspecified | Read-only source confirms `for_path` pooling and active-tenure observer rejection. Proposed Q2: exact A02 credential-first assembly, metadata second, status third, one canonical temp path/controller/mutex/observer and assertions before windows; no late/mixed/default assembly. No runtime reproduction in this turn. Independent re-review pending: OPEN/HOLD. |
| 829-R2 / same review (reported) | MEDIUM design gap: no-owner startup conflicts with both management constructors claiming path ownership | Source confirms constructor claims. Proposed Q3: import no GUI, explicit start one status/navigation Tk only; explicit navigation creates one management Toplevel; fail-closed second panel, owner-scoped teardown, fresh reconciliation on handover. Real dispatch/teardown proof pending; OPEN/HOLD. |
| 829-PENDING / inherited A01 question | UNVERIFIED severity/reachability; coordinator consumes pending before delegated processing while real host retains independent review | Read-only `approve_ui/_approve_pending/_approve_recovered` trace supports exception-path test obligation, not bypass/repair. Normal refusals reject host; unexpected pre-host exception cleanup remains unproven. Q4 requires unchanged real host/body plus narrowly injected fake dependency failures, both pending states, raw/stale routes, no replay and successor safety. No tests run or defect closed: OPEN/HOLD before RFC GO. |
| 829-IMPORT / bounded source audit | Unresolved contract evidence: A02 transitively imports pure Python Windows mutex definitions; Tk uses GUI runtime | Literal zero native-related-module import is unsupported by unchanged path. No provider/SDK/backend/native service loading or invocation allowed. Independent disposition of minimal definition-only/Tk import boundary and Tk-compatible tripwire coverage required; otherwise HOLD. No stubs, new features or silent scope expansion. |

Dependency coverage: credential lifecycle/real host/coordinator, metadata host, read-only status closure, shared recovery pool, both management constructors and close paths, old raw approve/reject, same-process handover and separately sealed A04 fresh-process proof. Original A01 review identity/reentry, A02 descriptor/backend/path isolation, A03 child identity and A04 no-inherited-authority/no-replay obligations remain regression requirements. Proposed repairs are contracts only; A1–A6 evidence is NOT EXECUTED. Independent integrated re-review has not accepted these resolutions.

Git/startup audit found clean `nayeon-v1` at protected HEAD with matching local origin tracking ref and exact A04 three-test-file commit. Older docs' A04 OPEN/local-only/current-HEAD assertions are stale. Remote push and same-ID macro-enabled workbook update/verification are supplied completed host evidence, not newly queried here; workbook ID `1n0tDiBQCkPWluX6eakRiRfq57tflRW5L`. Product remains Phase 8.28.1, Phase 8 IN PROGRESS, **5/19 phases and 0/12 release gates**.

**Disposition:** GO only for this authorised append-only documentation reconciliation; **HOLD for RFC architecture clearance and implementation** pending independent re-review and Q4/import disposition. Future new test-only allowlist is exactly `tests/phase_829_integrated_support.py`, `tests/phase_829_simulated_first_run.py`, `tests/test_phase_829_integrated_acceptance.py`; production excluded. No tests/compileall, implementation, staging, commit/tag/push, workbook change or historical rewrite in this turn. STOP on unexpected scope; broader five-phase/repair authorisation does not override these gates.

**Execution limitation and completed handoff (15 October):** The Codex workspace-write attempt to append `.codex/CURRENT_STATE.md` failed with `UnauthorizedAccessException` under its sandbox permission map; no permissions were altered. The user-authorised Desktop Commander documentation append subsequently succeeded through its own permitted file access. Thus the RFC, this ledger and `.codex/CURRENT_STATE.md` now contain the controlling A04 and Phase 8.29-A checkpoint; all three remain unstaged. Static `git diff --check` passed; no production/test changes, implementation or seal claimed by this docs-only reconciliation. Protected HEAD/index remained unchanged. The 15 October independent RFC architecture re-review returned `PHASE_829_RFC=GO` (design clearance only); Q4 real-host exception tests and all integrated acceptance/release gates remain unexecuted and mandatory.
