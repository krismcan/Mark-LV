# P236 original timeout causal map and native ownership decisions

15 November 2026. OM v2.1, single writer. **HOLD. Documentation only.**

The four P234 timeouts are established, but their individual technical causes
cannot be proved from the preserved observations. Original source establishes
repeated, substantial immutable-history work; receipts establish three uncertain
tree cleanups. Neither establishes the operation executing at a deadline, a
deadlock, surviving descendants, or a runner-caused timeout. No diagnostic repair,
new runner, synthetic actor, workflow, historical test change or timeout change
is justified by this evidence. The next experiment below is proposed, not run.

## Checkout, source and evidence custody

Only `D:\Nayeon\CODEX_P236_TIMEOUT_CAUSALITY_20261115` was used for repository
work. Branch `byok-c1-p236-original-timeout-causality-20261115`, HEAD and exact
starting parent `979a7d31f793f50ee4431492a805eb8618dd50b1`; initially clean.
Git has three local commits, shallow history and no local tags. It cannot
independently revalidate the older historical seals. `.codex/CURRENT_STATE.md`
still leads with 3 November Phase 10.2 work and is inconsistent with this P235
checkpoint. It is preserved: this is no new product phase or completed milestone.
No other product/P234/P235 worktree was inspected or modified.

Read-only evidence root:
`D:\Nayeon\P235_HOST_EVIDENCE_20261115\p234_artifacts`.
Report `D:\Nayeon\P235_HOST_EVIDENCE_20261115\p235_real_p234_report_first.json`
has SHA256
`C46ABB551E885EB31C4CDC0B05D46B3B2B931F5E5D7BF6BD915AA02317DAE3FE`,
matching the supplied anchor. All eleven ZIP hashes match that report; all
253 listed internal file receipts were recomputed using streaming SHA256 and
matched. Archives were read in place through .NET ZipArchive, without extraction
or writes. This checks consistency with the supplied evidence, not independent
GitHub authenticity, signature, ZIP CRC certification or reviewer approval.

Run/attempt `43696205057-1`; tested source P233
`096048db17c7c1f9402dfd16a7deb31e9ebdc81d`; controller P234
`bc02f95f9dd241c5dace3129e918324e55dd6ee6`. Original discovery 3,629;
54 assigned and started, 50 stopped, 46 PASS, four genuine FAIL and four TIMEOUT;
3,575 retained but not executed. Report/certificate exit 125. Independent
provenance/security approval absent; full unfiltered release regressions **0/3**.

`git diff --name-only P233 HEAD` contains only the seven P234/P235 additions.
For 21 inspected original paths, raw bytes streamed directly from
`git show P233:path` have SHA256 equal to the preserved plan manifest. This
covers the two test modules; BYOK A/B and Phase10 migration helpers; Phase
8.30/8.31/8.32/8.33/8.34/8.36/8.37 helpers; P227/P231/P232/P233 scripts;
the two candidate service files; original P96 coordinator; local user controller
and WinCred backend. Important anchors:

| Original path | P233 Git-blob SHA256 |
| --- | --- |
| `tests/test_phase8_byok_b_scope_integrity.py` | `65DAD89298A587D6BB5DDE5455DF4D701BB1A1FD9A7A96CECF3E647800E3AE8B` |
| `tests/test_phase_834_scope_integrity.py` | `8DC69EC770EA008DFF9CD13E15299A73E38044F1671FD4FE78FBE2A431CCF57A` |
| `scripts/p233_windows_unittest_lifetime_recovery.py` | `4B29DE93CBA11971A00AF00F2C6E62D27B287FF53CBF5B08E905311258301FCB` |
| `tests/p96_native_transaction_negative/PendingCustodyTransaction.cs` | `D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB` |

An initial direct disk-byte check exited 1 on the first module. Investigation
confirmed `core.autocrlf=true`, index LF / working file CRLF. Subsequent exact
Git-blob checks passed; local text for all 21 paths matches after CRLF-to-LF
comparison. That text comparison is only a source-reading check, never a
substitute for the original raw-byte pins or admission. Configuration and files
were not converted. This checkout is unsuitable for claiming original raw-byte
historical admission even if a Python interpreter becomes available.

## Open Failures & Prior-Issues Review

Reviewed the engineering failure gate, P234 design/controller/workflow, P235
report/reconciliation review, P227 comparison source/workflow, P231-P233 runners,
P179 performance review and P219/P221 native ownership/race reviews.

| Issue | Severity / actual evidence / affected boundary | Cause, containment, review and disposition |
| --- | --- | --- |
| Four P234 timeouts | Material regression blocker; exact original start-only journals and exit-124 receipts below | Per-method technical cause unknown. No repair or new execution. Independent causal review absent. HOLD. |
| Three uncertain tree cleanups | Material diagnostic containment issue; taskkill reports unsupported termination for descendants | Termination failure confirmed; identities, survival and effect on later singles unmeasured. G2 cleanup reports success. No cleanup waiver. HOLD. |
| Four original P76 failures | Material historical regression; raw failure traces inspected for G0 M1/M2, G1 M3, G6 M3 | Public successor chain reaches exact P76 branch refusal. No assertion weakened or branch spoofed. Unwaived; HOLD. |
| P231/P232 retained Tk ownership | Historical harness defect documented in P233 worker | P233 deletes extra case owners; P234 uses a fresh single stdlib suite. These two target modules have no Tk lifecycle hooks. No evidence connecting this old defect to these four timeouts. Not a new repair claim. |
| P96 revoke/effect race | High security blocker; actual final-check/effect gap and original negative source inspected | Still open. Candidate denial fence and synthetic monitor examples do not repair the old coordinator or its alternate actors. HOLD. |
| SEC03/SEC04, unsigned service/broker | High architectural blocker; no qualified decisions; candidate OnStart refuses, release pins empty | Ownership, signed loaded image, authenticated consent, terminal serialization and recovery not independently accepted. Existing intake PR #147 per task remains decision intake only. HOLD. |
| Native validation / historical seals | Missing evidence; local py absent, shallow Git/no tags, CRLF disk | Static analysis only, host validation required; no complete regression or independent review inferred. HOLD. |

GO only for this authorized read-only investigation and one additive factual
document. No product progression, seal, release or failure closure.

## Method-specific original work and observed receipts

All method counts below are planned source-level iterations if execution reaches
them, **not observed completed subtests or measured Git process counts**.
BYOK methods belong to `tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests`;
G6 belongs to `tests.test_phase_834_scope_integrity.Phase834CandidateTests`.

| Case / exact method | Original work and rejection reach | Preserved process observation |
| --- | --- | --- |
| G1 M0 `test_every_candidate_source_byte_is_bound` (lines 177-191) | Sorted 23-path ENVELOPE; each iteration constructs a fresh `candidate(disk_mutation=tamper)`, invokes the real private B body, requires its exact byte-mismatch message and `hits == [target]`. B parent/history authentication precedes candidate pin comparison. Rejection is before the frozen-disk loop, so its immutable `sealed_bytes` cache cannot eliminate this history work. | `single-0`: start only; no result JSON/footer. Actual killed worker exit 1, diagnostic 124, cleanup UNCERTAIN. Descendants 3760/1152 report unsupported termination; worker 7040 reports killed. |
| G2 M3 `test_raw_git_rename_status_blob_modes_counts_and_worktree_refused` (267-290) | Three states x eight mutations = 24 fresh candidates/admissions. Empty/truncated delta, rename/delete status, mode, blob, alias and extra record attacks; injection asserts bytes really changed. The chosen RAW / cached / parent-child query is checked after history; staged/child full delta validation also follows candidate/frozen checks. | `single-3`: start only; no result JSON/footer. Actual 1, diagnostic 124, TREE_TERMINATED. taskkill reports success for child 6388 and worker 6928. |
| G3 M0 `test_unknown_ignored_alias_and_index_flags_refused_in_every_state` (243-265) | Three states x (five inventory suffixes + three flags) = 24 fresh candidates/admissions. Unknown untracked, ignored pyc, case alias, linked/unmerged index records, h/S/s flags. Even early index refusals follow full B parent authentication; unknown untracked rejection is later in topology classification. | `single-0`: start only; no result JSON/footer. Actual 1, diagnostic 124, UNCERTAIN. Descendants 2600/9232 unsupported; worker 5816 killed. |
| G6 M5 `test_stale_each_candidate_pin_and_disk_mutation_after_positive` (409-428) | One complete positive then two fresh candidates for each of 20 paths = 41 admissions. Each pin-negative proves the path was read; each disk-negative requires exact mismatch and one tamper hit. The entire frozen tracked-file walk precedes candidate pin/disk mismatch. Candidate setup alone reads 2 immutable brain blobs + 14 test blobs + A02 = 17 real `git show` requests per context (697 planned across 41 contexts), plus tree/history queries. | `single-5`: start only; no result JSON/footer. Actual 1, diagnostic 124, UNCERTAIN. Descendants 6028/1652 unsupported; worker 5060 killed. |

Raw log SHA256, respectively:

- G1: `C1205243592DD7E0771219D5BF941144DC260BEE773E75DEB9604BDE72E97D13`
- G2: `7FC925EC2DDFC95403B6A022F8EA71FAD18A4D96D4107D6C305364F05619EF0C`
- G3: `F7DA8E6E93CD701A9D52169AB6AEB52C223E06B77779B9DFEF36B8F283D73E9D`
- G6: `635FFED56144072B53FC551F01C8AD2455A39890DA80CD02FA7EFF271A7D7CBB`

Each ZIP contains matching `single-N-process.json`, `.log`, `.events.jsonl`,
`driver.json` and `SHA256SUMS.txt`; missing single result JSON is itself relevant.
The actual exit 1 is the terminated process status, **not** an original unittest
FAIL result. The four genuine FAILs elsewhere have real footers and are separate.

### Source call graph and actual Git operations

In the B test module, `candidate()` lines 49-132 performs real setup *before*
installing seams: `gate.prior._tree(gate.PARENT)`, then
`successor._baseline()` authenticates sealed B, then 23 `actual('show',
SEALED_B_HEAD + ':' + path)` preimage/pin checks. `_baseline()` itself reads the
23 sealed B blobs and calls B `_parent_tree()`. Thus setup includes 46 B blob
shows per context, in addition to all ancestor work. This is repeated per
subtest; `_baseline()` and `_parent_tree()` have no success cache.

The fixture explicitly selects `gate._assert_byok_b_historical`, patches
`gate.prior._git` (Phase8.37), `_disk`, and `_frozen`, and delegates every
unhandled query to the saved real Git function. Current HEAD/index/delta replies
are synthetic; immutable historical authentication remains real. The assertion
itself repeats B `_parent_tree()`:

```text
test -> candidate setup -> Phase10._baseline -> B._parent_tree
test -> B._assert_byok_b_historical -> B._parent_tree
  -> A._parent_tree -> Phase8.37._seal -> Phase8.36._seal
  -> Phase8.34._history -> Phase8.33._history -> Phase8.32._history
```

Relevant definitions: B helper `_parent_tree` 155, historical body 189; A
`_parent_tree` 129; Phase8.37 `_seal` 226; Phase8.36 `_seal` 171; Phase8.34
`_history` 214; Phase8.33 `_history` 205; Phase8.32 `_history` 211. Wrappers
ultimately reach `tests/phase_8_30_scope_migration.py:_git` line 76:
`subprocess.check_output(['git', *args], cwd=ROOT, stderr=DEVNULL, timeout=20)`.
Every call keeps its original 20-second bound and exception conversion.

Historical routines enumerate `ls-tree -r -z --full-tree`, read pinned blobs
with `show <immutable-commit>:<path>`, verify `rev-parse` tree identities,
`rev-list --parents -n 1`, exact `show-ref --verify --hash -- refs/tags/...`,
`cat-file -t`, and immutable annotated-tag peel. Phase10 also reads raw tag
and commit objects. These calls are substantive security work, not stubs.
Neither replacing mutable branch/index queries nor caching successful admission
would be an acceptable inference from this performance observation.

In the 8.34 module, `candidate()` 51-177 reads a real baseline and immutable
preimages, then patches `prior._git` (Phase8.30), `_disk`, literal synthetic pins,
selected frozen preimages and `scope._assert_834_historical`. Unhandled calls
still reach the original Phase8.30 Git transport. Its historical body at 252
runs `_history`, inventories, then **all frozen tracked regular-file disk
hashes** before iterating candidate pins. Most frozen disk reads retain real
link/mode/parent checks. G6 therefore repeats both Git and filesystem work even
when the intended negative is a single candidate pin. It is distinct from B's
frozen-blob cache. Public current routes are not substituted in the live tests.

### Deadline semantics, elapsed evidence and certainty

P234 `SECONDS=180`; `run_process` starts this bound around the entire child
process, not at `startTest`. Child `verify_source()` runs before imports/test
and again after writing its result. It hashes every tracked source and validates
15 tags through many real Git commands (transport bound 45s). This overhead
consumes the same worker deadline. Parent verification/discovery is separate.
This is a confirmed scope-of-budget fact, not proof that overhead caused a
particular timeout. No timeout-budget change is proposed.

`JournalResult` emits only ID and start/stop, without timestamps, subtest progress
or stack. `run_process` stores no start/deadline/elapsed timestamps or process
names/CPU. Consequently **180s is the configured worker wait, not a measured
180s test-body duration**. Cleanup can add a taskkill wait and root wait, each
bounded at 30s. No exact per-method elapsed-to-timeout, completed iteration count,
current command, preflight cost or surviving-tree lifetime can be recovered from
these files. ZIP write dates do not supply those missing measurements.

Same-run completed original controls provide context, not extrapolated proof:
B three-topology control G2 M5 47.927s; B historical-A-pin loop G0 M5 105.909s;
B frozen commit/index/disk G1 M2 57.304s; 8.34 three-positive controls G3 M2
12.256s; 8.34 partial-index loop G4 M0 97.262s. Their unittest footers measure
suite time, excluding child source preflight/postflight. Different operations,
negative reach, caches and hosted VM scheduling prevent direct multiplication
into a causal runtime estimate for the four timed-out methods.

P227 comparison (`scripts/p227_windows_byokb_immutable_git_equivalence.py` and
its workflow) targets **B `test_frozen_commit_index_and_disk_stay_bound`**, not
one of these four. Both arms have a 125s bound. Its isolated candidate replaces
only 19 pinned Phase8.36 immutable `show` requests with freshly verified
`cat-file --batch` reads, retaining real baseline byte comparisons, SHA1,
normalized SHA256 and negative checks; mutable queries delegate unchanged.
No historical source is changed, but the candidate transport is instrumented
and cannot be called original unmodified execution. Its ledger computes an
elapsed ratio only if both arms pass. The supplied P234/P235 evidence contains
no P227 raw ledger/logs, so no P227 measured speedup or original result is claimed
here. P179's older review reports sampled Git waits and a 165.125s module timeout;
those are prior observations on different work, not stacks for these four.

| Explanation | Certainty for this investigation |
| --- | --- |
| Substantial repeated original test work | Confirmed by actual loops, setup and guard bodies. Legitimate negative-test obligations remain. |
| Slow cumulative immutable Git / frozen-file scans caused each deadline | Plausible leading hypothesis, supported by source and adjacent elapsed controls; not measured per timed-out method. |
| Single Git hang / deadlock | Unproven. Individual transport has timeout=20, but no command timing/stack at death was retained. |
| Subprocess/tree leakage caused the timeout | Unproven. Descendants existed at cleanup; three cleanup errors do not prove post-cleanup survival or prior leakage. No process image names were captured. |
| P234 budget overhead contributed | Possible; preflight shares the bound. No split timings, so magnitude unknown. |
| Runner falsely classified a completed method as TIMEOUT | No supporting evidence: all four lack stop/footer/result and record TimeoutExpired. Classification is consistent. A boundary race cannot be ruled out from untimed receipts. |
| Old P231/P232 Tk lifetime defect recurred here | No supporting evidence. P234 single lifetime differs and modules have no Tk fixtures. |

P234 also continues to later singles after an UNCERTAIN cleanup, while carrying
125 into the driver. That containment limitation can contaminate later timing
if descendants survive; no such survival is proved. No hypothetical containment
repair is represented as solving these original timeouts.

## One next targeted experiment (not implemented or executed)

Use Nayeon's authorized host orchestration on disposable Windows, starting with
**only G1 M0**, on a separate full-history/tag checkout of exact P233 raw blobs,
with the exact P234 controller. Preserve existing host/branch/source assertions,
no credentials, no P134 authority and the same 180-second **whole-child** bound.
Do not use this CRLF/shallow checkout or the protected worktrees for execution.

Capture observation externally: worker creation/deadline/exit monotonic times,
fresh PID plus creation identity; read-only process-tree snapshots with image,
parent, CPU time and lifetime; real Git command start/finish, exit and duration;
bounded Python stack samples and method/subtest progress if available without
changing bodies, return values or transport. Include source-admission phase
timing, not just test time. Restrict recorded command data to these known Git
queries and avoid environment/secret dumps. Any observation requiring injection
is a separately labelled instrumented diagnostic, never an original regression
PASS. A source-preserving implementation and focused adversarial validation of
its observer would need review before execution; none is added in P236.

At timeout retain 124; snapshot the tree before existing bounded termination,
then observe whether identified descendants survive. Stop the job on uncertain
cleanup; dispose that VM before another single. Do not run subsequent cases in
possibly contaminated state. Prefer existing host process tracing/debugging
capabilities over another generic runner wrapper. No longer timeout, batch
substitution, admission cache or modified negative is part of this experiment.

Decision evidence: many successfully completed immutable queries plus advancing
subtests supports cumulative cost; one long outstanding process with stable
stack/CPU distinguishes a stall; preflight timestamps quantify consumed budget;
post-kill same-identity survivors establish leakage; a stop/footer preceding the
deadline would instead challenge runner classification. If G1 resolves, repeat
one at a time for G2, G3 and G6 on fresh disposable VMs under the same bounds.
Until measured, all four root causes remain OPEN.

## Actual native and legacy paths; required independent decisions

`native_c1_candidate/CustodyService.cs` owns one
`ServiceOwnedAdmissionBoundary`. Requests call `RefuseRequest` or
`RefuseBoundRequest`; `OnStop` calls that object's `Stop`. `OnStart` both checks
the old ServiceGate and unconditionally throws. There is no Main/installer,
consent issuer or native credential dispatch. In the boundary, the same private
monitor serializes refusal, Revoke/Stop/Fault and read-only J2 observation.
`CanDispatchNativeCredentialEffect`, `AuthenticatedConsentAvailable`,
`ProductionReleaseEligible` and `RetryAllowed` are hard false. The positive
`C1_SYNTHETIC_TEST` methods change integer metadata only, and a fixed fake effect
returns RecoveryRequired. This service fence does not invoke the old P96 Apply.

Original `tests/p96_native_transaction_negative/PendingCustodyTransaction.cs`
has a separate authority structure: atomic one-use Apply -> snapshot bytes ->
approval Consume/StillCurrent -> custody lease -> journal/anchor verification ->
write/read back IN_FLIGHT -> final ApprovalCurrent -> final `lease.IsOwned` ->
`state.SaveOrReplace(owned)` / `DeletePending` -> terminal persist/readback ->
MarkTerminalVerified. Approval and state are separate injected interfaces.
The custody lease does not serialize approval revocation with native effect.
Original `NativeTransactionRaceProof.cs` explicitly completes a separate-thread
revoke in the fourth IsOwned getter, after the last StillCurrent, then counts
one fake effect after revoke for Save/Replace/Delete. Passing that negative
reproduces the flaw; it does not prove remediation. P221 review-only wrappers
assume all actors enter their own monitor, not the actual service-owned monitor.

The genuine alternate Python path remains in the source:
`LocalByokLaunchBridge.launch` source mode -> fixed
`nayeon.desktop_alpha.local_byok_window` child -> `main` /
`compose_user_scope_local_byok` -> `LocalByokController` -> manual review /
`approve_from_button` -> controller `approve` -> exact
`WindowsCredentialBackend.put/delete`. Backend methods lazily reach
`_Advapi32Adapter.write/delete` -> CredWriteW/CredDeleteW; presence calls
contains -> CredReadW/Free. The fixed identifier is `openai.api_key`, target
prefix `nayeon-v1/secret/`. Direct backend get also exists. No such method was
called here. Per-controller RLock and cooperative onboarding mutex do not join
the service monitor or prevent other same-user backend callers.

P206's hold explicitly cannot restrict direct backend access. P211/P216 source
inventories are not OS isolation. Frozen launch has blank main/helper/signer
pins and Code Integrity approval false in `frozen_signed_byok_companion.py`;
source-mode launching remains a distinct route. A renamed helper, boolean or
synthetic actor cannot supply loaded-image trust or remove this alternate actor.

Before any P96 production successor, the minimum **written, source-bound,
qualified independent SEC03/SEC04 decisions** must specify:

1. **SEC03 principal and custody ownership:** select the actual service account,
   SID/token/profile/logon semantics and store (service-user DPAPI/WinCred or
   reviewed alternative); fixed target namespace and ACL/key access; which
   principals can read/write/delete. Decide durable journal/anchor and independent
   rollback/enrolment witness ownership, crash/reboot/recovery authority, backup
   and deletion. Define cross-user/process/restart denial tests on a separately
   approved disposable VM. P216's virtual-account/DPAPI proposal is not an accepted
   decision. No automatic read/move/delete/re-enrol of existing user credentials.
2. **SEC03 plus SEC04 alternate-actor closure:** decide exact packaging exclusion
   and OS isolation for P132/P133/direct Python/native effects. Prove the old
   interactive-user route cannot mutate the new service-owned target, across
   windows, processes and restarts; Python allowlists or a wrapper are insufficient.
3. **SEC04 signed broker and real user consent:** decide installer/main/helper
   signer and exact source/binary pins, protected install/update policy and loaded
   image enforcement under approved Windows Code Integrity policy. Specify IPC
   endpoint ACL and authenticated peer/image/user/session checks; trusted human
   approval issuance, operation/target/candidate binding, one-use nonce, expiry,
   replay and destructive acknowledgement. Caller metadata, a digest or
   StillCurrent boolean is not that authority. No signer or policy GO exists.
4. **SEC04 terminal ownership and ordering (with SEC03 persistence):** choose one
   actual service-owned serialization domain shared by consent consumption,
   Revoke/Stop/Fault publication, verified durable IN_FLIGHT and one fixed pending
   native effect. Define the linearization point: committed revoke first means
   zero effects; effect first cannot later be reported as cancelled/no effect.
   Define bounded blocking/stop/watchdog behavior, no arbitrary effect callback,
   one-use attempt, no automatic retry, unknown-result recovery and durable
   terminal readback before release. Include real custody mutex/restart fault
   publication and exclusion of every older Apply/effect bypass. Require causal
   Save/Replace/Delete race, stop/fault, crash and restart adversaries on that
   actual successor, retaining the immutable P96 negative as historical evidence.

Reviewer identity/qualification, disposition, exact reviewed source, accepted
test scope and residual issues must be recorded in the existing PR #147 intake
before implementation authority is claimed. No decisions are inferred from this
document, prior synthetic tests or GitHub job success. No service, installer,
signed profile, approval interface, credential effect or production source changed.

## Validation and restart checkpoint

- Read-only PowerShell/.NET report/ZIP/receipt checks: exit 0; all eleven ZIP
  hashes and 253 listed file digests match. Original source-blob checks: exit 0,
  21/21 match; local text matches after accounting for CRLF as described above.
- Initial raw local disk-byte check: exit 1, correctly exposed CRLF mismatch;
  original raw source verification subsequently used Git blobs, without changing
  pins or checkout. This is not a failed historical test or a waiver.
- `py -3.12 -B -c "import sys; print(sys.version); print(sys.executable)"`:
  PowerShell CommandNotFoundException; **no interpreter/native process exit**.
  No download, alternate runtime, host bypass or package workaround attempted.
- New selftests/native C# tests, original focused tests, full discovery and
  compileall: **NOT RUN**. No executable file changed; documentation-only result.
  Prior P219/P221 native results are historical reports, not P236 executions.
- Final `git diff --check`: exit 0. New-document
  `git diff --no-index --check -- NUL docs/byok-c1-p236-original-timeout-causal-map.md`:
  exit 1 (new-file differences), no whitespace errors; Git warns that a future
  Git write would convert LF to CRLF. Independent text scan: zero trailing
  whitespace lines. Protected tracked-path diff against exact starting parent:
  exit 0; index empty, HEAD unchanged, only this document untracked.
  No staging, commit, tag, push, release, credential access or workbook/dashboard
  action.

Restart at the G1-only observation experiment, with an independently reviewed
source-preserving observation plan and host execution. Keep four genuine P76
failures, four unknown timeout causes, uncertain cleanup, original P96 race,
SEC03/SEC04 and unsigned service/broker blockers OPEN. BYOK C1 remains HOLD;
full unfiltered regression acceptance stays 0/3.
