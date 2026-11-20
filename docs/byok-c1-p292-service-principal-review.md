# P292 disposable Windows SCM virtual-account witness

20 November 2026. **BYOK C1 IMPLEMENTATION IN PROGRESS. REAL-KEY NO-GO.
PRODUCTION RELEASE HOLD. Qualified external approval 0/7; full product
regressions 0/3. Original P96 HIGH OPEN; P76/P211/P216 acceptance OPEN.**

Codex is the single implementation writer. Nayeon independently reviews and
publishes. The user's explicit P292 authorization permits scoped source work
and disposable GitHub-hosted proofs only. It supplies neither qualified security
approval nor permission to install/change a service on Kristian. No local
generated executable or hosted review script may run. No staging, commit,
push, PR creation, tag, seal, merge, workbook or dashboard update by Codex.

## Frozen source and mandatory preview

Third-commit repair checkpoint verified before editing: pristine branch
`byok-c1-p292-ephemeral-scm-service-witness-20261120`, frozen SECOND P292 HEAD
`ab7999076cc0c07e2ca0e19d0a28e2a513de0e93`, single direct parent failed FIRST
`8b2ca2bf24b3ca388abc2268ede27f7d319ad093`, direct grandparent P291
`4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f`, 1,185 tracked paths, no tag at HEAD.
Draft PR #212, first hosted run 44739845249 (0/6) and second hosted run
44741869649 (4/6) are user-supplied evidence checkpoints. Both original commits,
all six first-run failures and all six second-run receipts remain preserved.
No amended/replacement commit or rewritten hosted logs. `.codex/CURRENT_STATE.md` still starts with
November 3 Phase 10.2 notes. Git is authoritative here; the entire inherited
tree, including that stale state, is frozen. This experiment is not a completed
product phase or a new regression baseline.

Only `HostedReview.ps1` and this document may change in the repair. After
independent review Nayeon alone may make ONE incremental single-parent repair
commit. Required topology: new event/checkout HEAD -> exact SECOND P292
`ab7999076cc0c07e2ca0e19d0a28e2a513de0e93` -> exact failed FIRST P292
`8b2ca2bf24b3ca388abc2268ede27f7d319ad093` -> exact P291
`4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f`. All three P292 commits must be
direct single-parent, exactly three commits ahead of P291. The immediate repair
delta against frozen SECOND must be exactly the two modified paths. The
cumulative delta from P291 remains exactly the five original additions below,
with 1,180 inherited entries intact.
The new repair SHA is unknown until Nayeon commits; it is taken from the new
same-repository draft PR event, never substituted for the failed SHA.

Mandatory preview: P281 principal/store decision, P291 trusted-owner boundary,
P290 message-identity decision, original P96 coordinator and negative fixture,
P282 executing custody, P279 read-only SCM/process-token observation and the
engineering failure gate. No broad historical rerun or repair.

P281 proves that frozen P99 `ServiceGate` names `NayeonV1ByokCustody` and
requires LocalSystem. P216 proposes `NT SERVICE\NayeonByokCustody`; the
conditional canonical candidate is `NT SERVICE\NayeonV1ByokCustody`. The name
discrepancy and principal conflict remain unresolved. Nothing in P292 changes
P99, approves that candidate, or uses either production name. P282's runner-user
binding is not reused as a service identity model. P279's observation/admission
distinction and retained-handle discipline inform the independent probe, which
imports no product source or DLL.

Exactly five additive paths:

1. `tests/p292_service_principal/P292DisposableService.cs`
2. `tests/p292_service_principal/P292ServiceIdentityProbe.cs`
3. `tests/p292_service_principal/HostedReview.ps1`
4. `.github/workflows/p292-windows-disposable-service-review.yml`
5. `docs/byok-c1-p292-service-principal-review.md`

## Actual mechanism, conditional on hosted execution

This is an actual SCM launch experiment, not a synthetic positive identity.
Three independent x64 and three x86 Windows-2022 jobs each have a nine-minute
limit. The script checks same-repository DRAFT event, exact base SHA and base/head
branches, actual head checkout, exact three-commit repair topology, exactly five additions,
all 1,180 inherited tree entries, all 1,185 raw disk/Git blob hashes and clean,
unignored, unlinked source before/after. Source SHA256 manifests and before/after
binary hashes bind the experiment to that head. Checkout and upload are pinned
to `11bd71901bbe5b1630ceea73d27597364c9af683` and
`ea165f8d65b6e75b540449e92b4886f43607fa02`. Contents is read-only, checkout
persists no credentials. No download, dependency restore or setup.
The unchanged checkout uses depth two. The script makes one bounded, exact-event
head `git fetch --no-tags --depth=4` to obtain P291 for ancestry/tree checks;
20-second command wait, five-second kill/join allowance, captured output,
credential helpers/askpass and terminal prompts disabled. Fetch failure is HOLD;
no checkout, branch rewrite or workflow change is made. This history read is not
a dependency download or a retry of any SCM operation.

Before SCM mutation, orchestration requires GITHUB_ACTIONS=true,
RUNNER_ENVIRONMENT=github-hosted, ImageOS=win22, Windows,
P292_DISPOSABLE_SCM_WITNESS=1 set only in the workflow job, and existing runner
administrator membership. No elevation/UAC/privilege adjustment. These are
accident barriers on an admin-controlled test machine, not hostile-runner
attestation or qualified approval.

Only random `NayeonP292_` plus twelve lowercase hex characters is eligible.
There is no collision retry. Native read-only absence must succeed immediately
before `sc.exe create`. Mutation commands are limited to create, sidtype
restricted, start, stop and delete for that generated name. Create specifies
own process, demand start, normal error control and
`obj= NT SERVICE\<random name>`, with no password argument. It never defaults
to LocalSystem or substitutes runner identity after failure. A virtual account
requires NULL password; see Microsoft's
[virtual-account configuration contract](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-changeserviceconfigw).
The service SID must occur in the token's actual restricted list, as documented
in [SERVICE_SID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info).
No ACL/profile/account/password/machine-policy workaround is permitted.

Service and probe compile separately under RUNNER_TEMP only, from the two new
guarded C# sources and builtin Framework references. Both require DEBUG,
C1_REVIEW_ISOLATED_ASSEMBLY and C1_P292_EPHEMERAL_SCM_ONLY and reject RELEASE.
Every individually omitted symbol, ALL absent and RELEASE with positive defines
must yield raw exit 1, only CS1029 and no binary. No unsafe code, external
assemblies, product code or production call edge. Local compilation only.

The service uses ServiceBase.Run with AutoLog disabled. It accepts fixed
disposable mode arguments, random name, frozen parent and head-shaped SHA,
requires noninteractive session 0 and a resolved matching virtual-account
identity with no effective impersonation. SCM does not inherit job environment:
the orchestrator checks that environment and supplies mode arguments in
ImagePath. Those arguments are accident guards, not authentication or approved
provenance. OnStart does no work and returns promptly; OnStop returns so the
dispatcher exits. A 55-second hard exit timer covers identity lookup/dispatcher
lifetime. No service file/network/user-data/IPC/store operations or installer.

The independent read-only probe uses native SCM config, restricted SID type and
status; it requires own-process RUNNING, exact account/ImagePath and expected
PID. PowerShell also checks exact Win32_Service StartName, PID and ImagePath.
Metadata is never substituted for kernel token evidence. OpenProcessToken and
GetTokenInformation inspect TokenUser, TokenStatistics, TokenSessionId and
TokenRestrictedSids; IsTokenRestricted must succeed. Its own thread token must
be absent with precisely ERROR_NO_TOKEN; impersonation/access denial refuses.
It validates x64/x86 layouts, variable-buffer lengths and embedded SID pointers
and lengths before reads. No unsafe memory access is used.

Resolved account SID must equal actual TokenUser, differ from runner TokenUser,
not be LocalSystem and occur in actual restricted SIDs. Session must be 0 and
token primary. Retained handles, two process opens, GetProcessTimes creation
times, unsignaled process handles, exact image, repeated SCM status/config and
token ID/authentication ID/modified ID/restricted-list equality reject sampled
PID ABA and token/config drift. These are observations, not continuous custody
against an administrator. Live negatives reject changed creation time, zero PID,
wrong image, wrong service name and changed ImagePath. A no-argument service
launch must refuse. Final recheck cannot erase any failure. There is no positive
client request or credential effect; all admission/effect/provenance/release
booleans are hard false.

Children are hidden, output-captured and bounded: compiler 20 seconds; probes
and sc create/sidtype/stop/delete eight seconds. ONLY the sc start client gets a
40-second command wait to obtain a native result. A timeout records
`SC_START_TIMEOUT`, raw exit UNAVAILABLE, NO_RETRY and HOLD. A returned result
records `SC_START_EXIT_<integer>` and fixed category: 0 SCM_RETURNED_SUCCESS,
5 ACCESS_DENIED, 1053 SERVICE_REQUEST_TIMEOUT, 1067 PROCESS_TERMINATED,
1069 SERVICE_LOGON_FAILURE, otherwise OTHER_NATIVE_ERROR. These are native
result categories, not a diagnosis from raw text. Start exit 0 alone proves no
mechanism PASS. No create/start/configure retry or account/ACL workaround.

Immediately after native create returns 0, a separate read-only metadata child
may observe for at most an eight-second command window, including PowerShell
startup and blocking CIM. Each CIM call has OperationTimeoutSec 5 and terminating
errors. ONLY a successful query with zero rows permits another read, separated
by 100 ms. The first visible row must have the exact case-sensitive generated
Name, StartName `NT SERVICE\<random name>` and full image PathName command.
Wrong name/account/image, multiple rows or any access/query error terminates
immediately; none is treated as transient. No mutation occurs in this observer.
The parent also refuses confirmation arriving at/after eight seconds. Child
kill/join has the existing separate five-second teardown allowance; it does not
extend metadata acceptance or permit another query after a failed observer.
No service name/path, SID/PID or raw exception is published by this observer.

Fixed runtime.log categories are CREATE_METADATA_NOT_VISIBLE (successful empty
reads exhausted the deadline), CREATE_METADATA_QUERY_ERROR,
CREATE_METADATA_MULTIPLE, CREATE_NAME_MISMATCH, CREATE_ACCOUNT_MISMATCH and
CREATE_IMAGE_MISMATCH. CREATE_METADATA_CONFIRMED is emitted only for an exact
match accepted before the parent deadline. Late exact results are
CREATE_METADATA_DEADLINE; unexpected child output/exit is
CREATE_METADATA_PROTOCOL_ERROR; child launch/watchdog/transport failure is
CREATE_METADATA_OBSERVER_ERROR_OR_TIMEOUT. All non-confirmed outcomes are HOLD,
with no retry of the observer or any SCM mutation. Native create0 remains a
separate receipt and cannot itself confirm metadata, SID setup or token proof.
Existing immediate Metadata checks at RECHECK and cleanup remain unchanged.

Only after sc start returns 0, one separate read-only CIM child polls exact
account/ImagePath/RUNNING/nonzero PID within an eight-second command window,
including PowerShell startup and CIM blocking. The parent also rejects results
arriving at/after eight seconds. Raw metadata stays in build custody, not
uploaded logs. The retained process/token probes, negative controls and recheck
are unchanged; token-stage failure is `SERVICE_TOKEN HOLD`. The unchanged
55-second service hard timer is never extended. A slow start leaves less time
for the complete proof and can still yield HOLD; no partial/token-expired proof
can become PASS. Child timeouts separately allow five seconds for kill/join;
that teardown allowance never extends a success window.

Finally separately attempts stop, exact-image and creation-time-bound retained
handle termination, ONE delete, then read-only absence observations. After a
returned delete success (or the pre-existing accepted 1060 already-absent
result), a single 25-second stopwatch covers late-child handling and absence
observations. Repeated native `absent` probes must return the unchanged probe's
exact PASS/exit 0, which requires OpenService ERROR_SERVICE_DOES_NOT_EXIST (1060).
A separately bounded read-only CIM child must find no exact-name service and
no exact-image process. Retained-child exit is also required. The observer uses
at most eight seconds per child and reserves five seconds of the 25 for a hung
observer's kill/join; active observation may therefore end earlier. No second
delete, start, configuration or credential effect. Native HOLD/exit 1 is merely
unproven absence, not proof of the reason; only read-only observations repeat.
`POST_DELETE_PENDING OBSERVATION_ONLY` may resolve to `POST_DELETE_ABSENT PASS`.
Malformed output, observer error/timeout, prior cleanup error or deadline keeps
`CLEANUP HOLD`. Unproven absence records `RUNNER_TEARDOWN_UNVERIFIED`: serious
limitation, ephemeral runner teardown is not verified. Delete exit or process
exit alone never proves cleanup. Late launch termination remains eligible only
under this run's unique image/start-time boundary; forced kill keeps the witness
HOLD. Job timeout/runner loss is not cleanup proof. No progress watchdog is
extended.

Exactly eight text artifacts: source-before.sha256, source-after.sha256,
compiler.log, compiler-exits.txt, test-binary.sha256, runtime.exit, runtime.log,
scope.log. Compiler evidence contains raw exits, diagnostic codes and raw-log
hashes; full errors remain in temp. Runtime evidence contains fixed categorical
PASS/HOLD labels and aggregate counts/raw exits. No actual SID, PID, username,
private token, random service name, raw SCM text, exception or executable is
uploaded. Unknown output remains in disposable build custody.

## Open Failures & Prior-Issues Review

Preimplementation disposition: GO only for explicitly authorized isolated
engineering; HOLD for product phase progression, security closure and release.
This experiment does not defer or waive inherited material failures. Independent
Nayeon repair-source review and new hosted runtime proof remain OPEN.

| Issue / severity / source | Root cause, evidence and affected path | Containment, test, review and disposition |
| --- | --- | --- |
| Original P96 HIGH OPEN; coordinator/fixture | StillCurrent then fourth IsOwned then SAVE/REPLACE/DELETE effect permits revoke between final check and effect. Original deterministic fixture documents the race. | Frozen 15-case original negative referenced, not rerun/waived. No P292 owner/effect edge. Qualified actual atomic owner/journal proof OPEN; HOLD. |
| Principal conflict HIGH OPEN; P281/P99/P216 | LocalSystem gate and differing virtual-account names disagree across old admission/config/runtime routes. | Random name only; no gate edit. Kernel equality is mechanism evidence, not principal approval. SEC03 OPEN; HOLD. |
| Provenance/client/consent HIGH OPEN; P290/P291 | Account identity does not authenticate protected client code or user-present one-use consent. Unsigned runner-writable image lacks trusted installation. | No issuer/broker/ncalrpc/consent/admission capability. Qualified external design OPEN; HOLD. |
| Profile/store/rollback HIGH OPEN; P281/P282 | Approved profile, user-DPAPI/WinCred ownership, ACLs and independent recovery not proven. | No credential/profile/store operation. Separate external setup/acceptance required; HOLD. |
| Historical P76/P211/P216 acceptance OPEN | Inherited genuine failures/native expectations remain unwaived; no full product audit requested. | All inherited bytes frozen. No skips/xfails/changed tests. External disposition OPEN; HOLD. |
| P292 FIRST hosted startup timing, material HIGH HOLD; 20 Nov, run 44739845249, all six ZIPs (user-supplied receipts) | All create/sidtype exits 0; sc start hit the script's eight-second client wait, RAW_EXIT=UNAVAILABLE NO_RETRY; sc-start HOLD / START HOLD. Underlying first-run service/SCM outcome and root cause remain unknown. Affected alternate paths: success-only RUNNING/token proof and partial-start teardown. | SECOND retained single start with 40-second native-result wait; four of six second-run mechanism trials PASS, two stop before SID configuration at metadata. No retry/account/permission/ACL fallback. Preserve original RED; four samples are not full closure or production approval. Independent review OPEN; HOLD. |
| P292 FIRST hosted cleanup timing, material HIGH HOLD; same six ZIPs | sc stop 1062, sc delete 0, immediate native after-absent probe 1 and CLEANUP HOLD in every trial. Marked-for-delete latency is a possible explanation, not an established diagnosis; delete success does not prove absence. | SECOND uses single-delete then bounded read-only native/CIM/process observation, up to 25 seconds including observer termination reserve. Second-run cleanup 6/6 confirmed in user-supplied receipts, including both metadata failures. Preserve first-run RED and distinguish sampled cleanup recovery from independent closure; third-source review/runtime OPEN; HOLD. |
| P292 SECOND immediate CREATE metadata, material HIGH HOLD; 20 Nov, run 44741869649 | x64 3/3 and x86 trial3 PASS; x86 trials1/2 fail stage CREATE AFTER sc-create RAW_EXIT=0 and before-absent0, BEFORE restricted-SID configuration. Immediate Get-CimInstance Win32_Service or exact StartName/PathName comparison failed. Empty visibility versus strict mismatch versus query/access error is not distinguishable from old generic HOLD. This is not evidence of OS CREATE failure. | THIRD adds bounded read-only zero-row-only visibility polling and fixed failure categories; visible wrong name/account/image, multiplicity or query error is terminal. No create/start/reconfigure retry, principal/ACL/policy change or weakened equality. Root cause remains unknown pending exact third-source hosted receipts and Nayeon independent review; HOLD. |
| P292 SECOND evidence attribution error; material review finding, 20 Nov | Prior review incorrectly said the two failing archives lacked sc-create receipts. BOTH contain sc-create RAW_EXIT=0, before-absent0, sc-stop1062, sc-delete0, after-absent0, after-cim-absent0 and CLEANUP PASS. | Explicitly corrected here from user-supplied archive findings. Native create succeeded; post-create metadata failed. No invented CIM-delay or account/logon diagnosis. All first/second receipts retained; Codex has not independently downloaded the ZIPs. Independent evidence review OPEN; HOLD. |
| Local compiler invocation defect, 20 Nov; tooling | Forward-slash relative paths were misread by Framework csc; initial raw CS1504 / exit 1. | Failed raw logs retained; Resolve-Path absolute source arguments fixed local/hosted invocation. x64 preflight then exit 0. Final matrix below; author check only. |
| P292 draft cleanup gaps, 20 Nov; security-sensitive source finding | A metadata exception could skip STOP; a late process was initially only reported. Affected partial-start/failure teardown, not product paths. | STOP independent for an owned service; retained-handle image/time-bound late termination follows deletion. Second-run two metadata-failure cleanups PASS, as do all six cleanups; no proof of every late-child branch. Cleanup errors stay sticky HOLD. Independent review OPEN; HOLD. |
| Local receipt parser defect, 20 Nov; tooling | Get-Content returned null for four empty positive compiler logs; original summary emitted four parser errors. Raw compiler exits/logs were preserved. | Revalidated all 24 raw receipts with ReadAllText, source hashes and output-binary checks; clean validated-summary below replaces that summary as evidence. No compiler failure hidden, no runtime retry. |
| Qualified decisions 0/7, regressions 0/3 | No reviewer-signed exact-source decision or three accepted full native product regressions. | No seal/signoff. Independent external review OPEN; HOLD. |

Relevant older paths reviewed are P96 ownership, P279/P282 observation and
P290/P291 denial. P292 neither repairs those production dependencies nor routes
around them. No broad historical investigation or acceptance promotion.

## Exact-source qualified external seven-gate intake / decision form

All seven rows UNAPPROVED (0/7). This is a request for qualified decisions, not
Codex or Nayeon signing for external reviewers. EACH row requires: full reviewed
commit SHA; five-file SHA256 and frozen-parent manifests; reviewer identity,
organization, qualifications and independence; UTC date; evidence paths/hashes;
threat assumptions; findings/severity; explicit APPROVE/REJECT/HOLD and rationale;
accepted residual risk; signature/attestation. Blank fields mean HOLD.
Exact repair child commit: NOT CREATED, to be filled by Nayeon/publisher/reviewer;
FIRST and SECOND SHAs above are preserved and cannot stand for the THIRD repair.

| Gate / current decision | Questions for qualified exact-source review |
| --- | --- |
| GOV01 — UNAPPROVED | Which exact production service name/SID/principal and SCM type/restricted SID are approved? Resolve frozen LocalSystem versus P216/P281 names. What installer authority and lifetime/ABA/token evidence are required? Separate random test identity from installed service acceptance. |
| GOV02 — UNAPPROVED | Which signed binary/publisher/version, protected installed image/directory ACLs, service configuration/DACL, update and rollback owner are accepted? Address replacement, injection, writable parent paths and privileged-installer abuse. |
| SEC03 — UNAPPROVED | For the approved principal, prove profile lifecycle, user-DPAPI/WinCred store/target/persistence ownership, per-principal/cross-user denial and independently protected rollback/recovery. No machine-DPAPI shortcut or implicit interactive-key migration. |
| SEC04 — UNAPPROVED | How are unrelated same-user apps excluded from a fixed protected client/consent broker? Specify authenticated ncalrpc mutual/per-call checks, protected broker key, user-present ceremony and operation/target/digest/ID/epoch/session/expiry binding. Test borrowed handles, replay, proxy, downgrade and injection. |
| REL05 — UNAPPROVED | Does one trusted P96 owner serialize issue/consume, revoke/stop/fault and actual effects with durable InFlight journal and continuous custody? Prove revoke-first zero effect and dispatch-first sticky MAY_HAVE_EFFECT/TooLate across crash/restart/ABA/alternate routes. Original HIGH stays open until accepted. |
| REL06 — UNAPPROVED | What source-bound disposition closes original P76/P211/P216/native-adapter acceptance without weakening tests? Which original negatives were reproduced, repaired and independently reviewed? |
| REL07 — UNAPPROVED | Have affected/trust-path checks, three full native Windows product regressions, compileall, exact source/staging/child integrity and independent CTO/security/human seal gates passed? Who authorizes release/real-key use and operational recovery? |

This is an intake mapping, not replacement governance definitions. Reviewers
must reconcile official domain ownership, including SEC03/04 principal/store
decisions, explicitly. Engineering source hashes alone never approve a row.

## Limitations and P293 restart

FIRST hosted runtime RED, 0/6 PASS; SECOND 4/6 mechanism PASS and 6/6 cleanup
confirmed from user-supplied receipts; THIRD repair runtime NOT RUN. Local compilation
proves no hosted mechanism, cleanup or runtime PASS. The GitHub-hosted machine
has an unrelated admin runner.
Virtual-account privileges might not permit this unsigned RUNNER_TEMP image,
especially with restricted SID checks. Any startup/access/configuration failure
stays HOLD; no ACL change, alternative account, privilege enablement or retry to
green. Report sanitized stage and raw exit. No installed-production proof.

Even six passes would prove only the sampled SCM virtual-account mechanism.
Unsigned image, runner-writable path and unqualified install/config are not
approved execution provenance, a signed installed Nayeon service, protected
profile/store, WinCred service-owner, authenticated broker, consent, durable
custody or P96 effect proof. Product admission still requires LocalSystem.
All product admission/release booleans remain false.

Meaningful P293: qualified principal decision and separately approved external
test setup for signed installed image/path plus protected broker/client and
user-present consent, followed by profile/store and actual effect-owner proof.
This virtual-account kernel receipt cannot close those dependencies. BYOK C1
stays IN PROGRESS; REAL-KEY NO-GO / PRODUCTION RELEASE HOLD. No master Google
workbook/dashboard update until whole BYOK C1 completion.

## Observed local evidence and exact source custody

No generated executable, HostedReview.ps1, SCM/service command, credential API,
Python or production regression was executed locally. No host service/account,
ACL, privilege or policy was changed. Full product regressions remain 0/3;
compileall is not run under the explicit local static/compiler-only restriction.
Independent CTO/source verdict OPEN. External qualified decisions remain 0/7.

Raw failed first invocation:
`%TEMP%\p292-compile-20261120-124347`: 24 raw exit 1 / CS1504 because of
relative source path syntax, not passing guard tests. Corrected absolute-path
x64 preflight at `%TEMP%\p292-preflight-20261120-124404`: both builds exit 0.
All raw compiler output is retained, including failures.

Final C# matrix: `%TEMP%\p292-final-compile-20261120-124924`.
Each invocation has its own raw `.raw` compiler log and `.exit` file. The
original summarizer's empty-log errors were repaired by independent receipt
revalidation within this same author session; this is not external review.
`validated-summary.txt` SHA256:
`76C9E3B3FCEDBBC7A5961032AD111F244E8FF746F2C52AE9B2A7994E387480DA`.

| Architecture | Actual positive exits | Actual deliberate negative exits |
| --- | --- | --- |
| x64 | Service 0; probe 0; zero compiler diagnostics | 10/10 exit 1, only CS1029 / P292_DEBUG_ISOLATED_EPHEMERAL_ONLY; no output EXE |
| x86 | Service 0; probe 0; zero compiler diagnostics | 10/10 exit 1, same guard and no output EXE |

The ten negatives per architecture are five modes for each separate executable:
ALL absent, RELEASE added, DEBUG omitted, isolated symbol omitted, P292 symbol
omitted. Flags include /noconfig /warn:4 /warnaserror+ and explicit references.
Compiled-source SHA256 values remain identical after receipt validation.

Historical FIRST-candidate author static checks: hosted PowerShell AST zero errors; literal workflow
parent/base/head/action/matrix/timeout checks; probe read-only native imports;
separate service/probe compilation; no unsafe code or product/effect import;
zero tracked/index changes at that earlier precommit checkpoint; all five added-file whitespace checks and git diff
--check clean. These checks do not validate Windows service behavior or substitute
for independent adversarial runtime review. The cleanup repair has source/AST
evidence only, not a runtime PASS.

Raw inherited-byte check: 1,180/1,180 disk blobs match frozen-parent Git OIDs
with filters disabled. All inherited SHA256 entries are retained at
`%TEMP%\p292-final-20261120-124845\inherited-1180.sha256`, manifest SHA256
`AE811AD2B222A6D75A126D392A487E99F6EDB97BCD2FF7623F7E5BB95971B77C`.
This first full raw manifest was taken after additions existed; the clean
pre-edit Git status is a separate observation, not a manufactured earlier hash
receipt. The final handoff manifest includes all five additions outside this
document to avoid a self-referential hash. HEAD/branch/index remain unchanged.

FIRST-candidate non-document source SHA256 (historical, not repair pins;
this document deliberately has no self-pin):

| Path | Raw SHA256 |
| --- | --- |
| tests/p292_service_principal/P292DisposableService.cs | B226DD10506640F90D49E5EE0C27DB3D22DC21B759138469B94A7CC3E520F665 |
| tests/p292_service_principal/P292ServiceIdentityProbe.cs | 7A54B05456992C7188233F9338B53D622C0B956DC2E4F47F740875F247B47641 |
| tests/p292_service_principal/HostedReview.ps1 | AF2A6CCF4643988A2EB3E50B904BD338B6161A65FC7FFF52AD1604D4E58EBC30 |
| .github/workflows/p292-windows-disposable-service-review.yml | 6E499F6227CF01CE2058EAED54025ACD4845E16203BB729FA7360345C3AF23A9 |

The FIRST candidate has since been committed/published by Nayeon as SHA
`8b2ca2bf24b3ca388abc2268ede27f7d319ad093`, draft PR #212. Its original run
44739845249 and raw artifacts remain unchanged. SECOND commit
`ab7999076cc0c07e2ca0e19d0a28e2a513de0e93` and run 44741869649 are also
preserved. This THIRD narrow repair is uncommitted
and unstaged; Codex cannot publish or create a PR. Nayeon must independently
review, make the single incremental commit and publish before new hosted trials.
Mechanism acceptance, cleanup acceptance, qualified review and production release
remain HOLD until their respective evidence exists. A genuine access denial
must remain red for qualified review, with no account/image ACL workaround.

## FIRST hosted findings and repair expectations

User-supplied original run 44739845249 findings, preserved for every original ZIP:

| Original trial | Create / restricted SID raw exit | Start client | Cleanup raw exits / result |
| --- | --- | --- | --- |
| x64 trial 1 | 0 / 0 | eight-second TIMEOUT; UNAVAILABLE; NO_RETRY; HOLD | stop 1062; delete 0; after-absent 1; HOLD |
| x64 trial 2 | 0 / 0 | eight-second TIMEOUT; UNAVAILABLE; NO_RETRY; HOLD | stop 1062; delete 0; after-absent 1; HOLD |
| x64 trial 3 | 0 / 0 | eight-second TIMEOUT; UNAVAILABLE; NO_RETRY; HOLD | stop 1062; delete 0; after-absent 1; HOLD |
| x86 trial 1 | 0 / 0 | eight-second TIMEOUT; UNAVAILABLE; NO_RETRY; HOLD | stop 1062; delete 0; after-absent 1; HOLD |
| x86 trial 2 | 0 / 0 | eight-second TIMEOUT; UNAVAILABLE; NO_RETRY; HOLD | stop 1062; delete 0; after-absent 1; HOLD |
| x86 trial 3 | 0 / 0 | eight-second TIMEOUT; UNAVAILABLE; NO_RETRY; HOLD | stop 1062; delete 0; after-absent 1; HOLD |

All original positive/negative C# compiler guards passed and 1,185 hashed source
records were consistent (user-supplied evidence). No host effects/real keys;
Kristian untouched. This author session has not independently downloaded or
re-reviewed the original ZIPs. No simulated positive or logon diagnosis.

New six-trial matrix remains x64/x86, three each. Required adversarial review:

- Start returning 1053 or 5 after eight but before 40 seconds must preserve that
  native exit/category, HOLD and exact-resource cleanup; it must not hit the
  former eight-second client deadline. More than 40 seconds remains TIMEOUT /
  UNAVAILABLE / NO_RETRY / HOLD with cleanup. Exit 0 alone never passes.
- RUNNING after its separate eight-second window, hard-timer exit, wrong account,
  image, PID, birth, restricted token, impersonation, or drift must remain HOLD.
  All original live negative controls and both kernel probes remain required.
- After one delete 0, transient native/CIM presence may resolve within the
  observation budget. Require native 1060 and empty CIM service/exact-image
  process plus retained-child absence. Access denial, malformed output, hanging
  observer, remaining child/service or deadline means CLEANUP HOLD and serious
  unverified teardown, even with delete 0 or an exited process. No mutating retry.
- Admit only event-bound THIRD HEAD -> frozen SECOND -> failed FIRST -> P291; reject a direct
  P291 child, extra/merge/rebased commit, wrong event SHA, extra path, inherited
  drift, changed C#/workflow or disk/HEAD mismatch. Fail closed on history fetch.
- Inspect all uploaded artifacts for fixed categories/raw numeric exits only;
  no actual SID/PID/service name/user/client secrets or raw SCM/exception output.

These are expectations for Nayeon's independent hosted review, not local runtime
tests or passing results. Forward phase/seal decision remains HOLD. Routine
engineering GO covers only this user-authorized two-path timing/observation
repair; no material failure has been waived or declared closed.

## SECOND hosted evidence correction and THIRD review cases

User-supplied run 44741869649, preserved without overwriting the FIRST table:

| Second-run trial | Mechanism | CREATE evidence / failing boundary | Cleanup |
| --- | --- | --- | --- |
| x64 trials 1, 2, 3 | 3/3 PASS | Successful mechanism receipts preserved | 3/3 PASS |
| x86 trial 1 | HOLD at CREATE | before-absent0; sc-create RAW_EXIT=0; immediate Metadata failure before restricted SID | stop1062; delete0; after-absent0; after-cim-absent0; PASS |
| x86 trial 2 | HOLD at CREATE | before-absent0; sc-create RAW_EXIT=0; immediate Metadata failure before restricted SID | stop1062; delete0; after-absent0; after-cim-absent0; PASS |
| x86 trial 3 | PASS | Successful mechanism receipts preserved | PASS |

The prior claim of missing sc-create receipts was incorrect. The native create
returned success in both failing trials. CIM consistency delay, strict mismatch
and query error remain competing explanations; no one cause has been proved.
Third-source instrumentation must distinguish them and must never convert a
visible mismatch/error into a retry or positive receipt.

Required independent hosted adversarial review (NOT executed on Kristian):

- Zero rows followed by exact metadata before eight seconds may confirm;
  zero rows throughout must HOLD NOT_VISIBLE or watchdog category. No second
  create/start/configure. Never-visible or hung CIM cannot produce PASS.
- First visible wrong name, account or image is terminal with the exact category,
  even if a hypothetical later query would match. Multiple rows and access/query
  errors are terminal. Inspect fixed numeric exits and absence of further reads.
- Late exact data, startup delay, child failure or unexpected output remain HOLD;
  confirmation requires exact equality and parent elapsed time below eight.
- Recheck/cleanup Metadata, restricted SID, one 40-second start, eight-second
  running window, both kernel probes, live negatives, 25-second absence and all
  source/PR/credential guards remain unchanged. Third runtime and independent
  CTO review are OPEN; qualified decisions 0/7, product regressions 0/3.

## THIRD candidate author static and compiler receipts, 20 November 2026

Pre-edit Git status was empty at exact frozen SECOND HEAD on the required
branch; both known ancestry edges were verified and no tag pointed at HEAD.
Post-edit scope is exactly two unstaged modifications, empty index and no
untracked files. No commit, stage, push, tag, merge, PR creation or master
workbook/dashboard action occurred. The future THIRD-child guard was inspected
as source only; no future commit/topology or hosted PASS is claimed.

Static receipts: `%TEMP%\p292-third-static-b876cdc532be48e487eeb294e1423ef4`.
`static-summary.txt` SHA256
`A81FD820EEEC3373480851E3DF927408C500AB3F370B9D0FF13B97E7E0BA5399`.
Outer AST and all three embedded child-program ASTs have zero parse errors.
The new observer's parsed commands are limited to Get-CimInstance,
Set-StrictMode and Start-Sleep; all eight fixed exit codes and exact comparison
clauses were checked. All eleven pre-existing function bodies remain equal
to frozen SECOND source, ignoring CR line terminators only for this text
comparison. This is static inspection, not executed fault-injection coverage.

All 1,180 inherited disk files again match their original P291 raw Git blobs
with filters disabled; `inherited-1180.sha256` SHA256 is
`AE811AD2B222A6D75A126D392A487E99F6EDB97BCD2FF7623F7E5BB95971B77C`.
All three other P292 additions match frozen SECOND raw blobs. Service/probe
C# SHA256 values remain exactly the frozen values in the historical table;
the workflow SHA256 remains `6E499F6227CF01CE2058EAED54025ACD4845E16203BB729FA7360345C3AF23A9`.
THIRD HostedReview.ps1 SHA256:
`5CAE59AA706911A09D8ADEF5F58824BFFE940CDA90F2FCEFBA076044BADDFB20`.
This document has no self-pin; final hashes are held in an external receipt.

Compiler receipts: `%TEMP%\p292-third-compile-60d347cc0227435c89db04aa7d6a4bde`.
`compiler-summary.txt` SHA256
`CDCB9B0EA4E734FF8533C6850F418B69109DADAC3DAB0E4120927A9472478722`.
The 24 invocations retain individual raw logs and numeric exit files: four
positive service/probe x64/x86 builds exit 0 with no diagnostics, and twenty
deliberate missing-symbol/RELEASE negatives exit 1 with only CS1029 and no
output executable. Absolute source paths, /noconfig, /warn:4, /warnaserror+ and
explicit references were used. No generated executable or hosted/nested
program was run, and no local SCM/service or credential operation occurred.
The prior first/second-run and historical compiler receipts were not replaced.

Author static/compiler checks support review of this candidate only. They do
not establish the metadata root cause, runtime repair, cleanup of every failure
branch or independent approval. Nayeon/CTO exact-source review and new 3 x64 +
3 x86 hosted trials remain required. Qualified external decisions stay 0/7,
three full product regressions stay 0/3, and all signed installed
broker/consent/service-profile/WinCred decisions remain unapproved. REAL-KEY
NO-GO and PRODUCTION RELEASE HOLD remain in force.
