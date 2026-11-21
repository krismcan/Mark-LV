# P294 dispatcher-first disposable service remediation candidate

21 November 2026. **NONDEPLOYABLE SOURCE CANDIDATE. RUNTIME UNACCEPTED.
REAL-KEY NO-GO. PRODUCTION RELEASE NO-GO.** Qualified external approvals
**0/7**, accepted complete product regressions **0/3**. Codex is the sole
implementation writer; Nayeon independently reviews security and owns Git
publication. No staging, commit, tag, push, PR creation, workbook or dashboard
update by Codex. No main workbook/dashboard update until complete BYOK C1.

This is the explicitly authorized investigation/remediation of one held
startup hypothesis, not forward product phase progress or P292 closure. No
material historical failure is waived by a compile/static result. The failure
gate remains HOLD for runtime, lifecycle, security and product acceptance.

## Custody and bounded scope

Pre-edit HEAD was exactly `4627157965bc978b5e502c85b6bc5eea5485050d`, branch
`byok-c1-p294-dispatcher-first-service-candidate-20261121`, clean, no tag at
HEAD. All **1,194 inherited regular-file raw blobs** matched the parent
using `git hash-object --no-filters`, before edits. P293 draft PR #214 is
the frozen parent. `.codex/CURRENT_STATE.md` still starts with November 3
Phase 10.2 notes; Git and this explicit task supersede that stale context.
It remains untouched because no product phase has completed here.

Exactly four additions, zero inherited modifications:

1. `tests/p294_dispatcher_first/P294DispatcherFirstDisposableService.cs`
2. `tests/p294_dispatcher_first/HostedStaticReview.ps1`
3. `.github/workflows/p294-windows-dispatcher-first-static-review.yml`
4. `docs/byok-c1-p294-dispatcher-first-security-review.md`

The future same-repository DRAFT PR must target
`byok-c1-p293-scm-lifecycle-witness-contract-20261121` at that exact parent,
with head `byok-c1-p294-dispatcher-first-service-candidate-20261121`.
The hosted script requires one direct single-parent child, **1,194 inherited
+ four added = 1,198** tree entries, exact added paths and raw clean bytes.
The author leaves the four paths untracked for Nayeon's review/publication.
Final four-file SHA256 values belong in the handoff, avoiding a circular
document self-pin. Nayeon must independently verify the reviewed bytes.

Frozen original source:
`tests/p292_service_principal/P292DisposableService.cs`, SHA256
`B226DD10506640F90D49E5EE0C27DB3D22DC21B759138469B94A7CC3E520F665`.
All original service, probe, harness, CI, tests, P293 and red historical
evidence remain unmodified. No old suite is skipped or declared obsolete.

## Open Failures & Prior-Issues Review

Reviewed: engineering failure gate, current state, frozen P292 service and
both P292 reviews, P293 review/hosted contract and supplied run history.
Run outcomes below are inherited/user-supplied historical evidence, not a
fresh external-archive audit. Independent outcomes are OPEN unless stated.

| Issue / severity / evidence | Symptom, root cause, affected paths | Containment, tests, review and disposition |
| --- | --- | --- |
| Pre-dispatcher lookup startup hypothesis / material, source-confirmed ordering | Frozen P292 Main performs GetCurrent, NTAccount.Translate and exact SID comparison before ServiceBase.Run. Microsoft requires prompt dispatcher connection. Blocking lookup is plausible; causal attribution of x86 failure is NOT PROVEN. | Only this separate candidate moves synchronous identity checks into OnStart. Static placement/equivalence and compile guards test source properties, not actual latency or service acceptance. Qualified causal review OPEN; HOLD. |
| P292 FIRST RED 0/6, run 44739845249 | All start clients time out at 8s; post-delete absence failures leave cleanup HOLD. Root SCM/service cause unknown. | Preserve original source/run. Moving lookup is not evidence of repair or cleanup. No mutable reproduction here. Independent closure OPEN; HOLD. |
| P292 SECOND RED 4/6, run 44741869649 | Two early x86 CIM metadata failures after create0, before restricted-SID setup. Empty result, query/rights failure and mismatch cannot be distinguished retrospectively. Supplied cleanup 6/6 passed. | No CIM implementation change, retry, mismatch relaxation or missing-create claim. Root cause OPEN; HOLD. |
| P292 THIRD RED 3/6, run 44766866901 | x64 trial1 CIM QUERY_ERROR, x64 trial2 CIM child deadline. x86 trial2 create/config/restricted-SID succeeded, then 40s start timeout AND native post-delete absence timeout. Source origin unknown; native teardown UNVERIFIED. | Both remaining CIM failures and unverified native deletion remain separate blockers. No claim of solely CIM delay, x86 root cause or timeout cure. HIGH missing cleanup evidence; independent review OPEN; HOLD. |
| P292-DIAG stable controls / limited evidence | Six supplied read-only jobs, 144/144, observe stable services, not newly created service lifecycle. | Preserve frozen controls. They do not recreate startup/deletion races, prove candidate launch or close P292. HOLD. |
| P96 HIGH OPEN | Final StillCurrent/fourth IsOwned check remains separated from SAVE/REPLACE/DELETE effect; revocation/effect/restart atomicity unproved. Older Python and native callers remain relevant. | No product import, store, effect callback or new route into those callers. No repair or downgrade. Qualified atomicity review OPEN; HOLD. |
| Principal/provenance/consent/store/restart HIGH OPEN | SEC03/SEC04 LocalSystem admission versus proposed virtual account, configured versus runtime image/token, installed provenance/ACL, user-present consent, profile/DPAPI/WinCred and restart custody remain unresolved across processes. | No weakening of original token predicates and no new installation/credential authority. Static SID equivalence is not runtime principal, restricted-token, provenance or consent proof. Qualified decisions OPEN; HOLD. |
| P76/P211/P216 acceptance OPEN | P76 four failures, P211 test02, P216 test02/test06 and alternative Python native-effect reachability remain unwaived. | No historical assertion/test/source changes, no rerun claimed. Accepted full regressions 0/3. Independent acceptance OPEN; HOLD. |
| P294 author static harness setup / bounded tooling failures | First author command extracted a function AST body without its signature parameters and returned exit1, Method structure HOLD on empty inputs. A later broad text scan returned exit1 on the forbidden-pattern literal InstallUtil and the permitted compiler path csc.exe. An author workflow scan also counted the defaults.run mapping as a second executable step. No hosted script or EXE was executed. | Attached the declared two-string param block to the extracted pure checker; positive and seven negative source-data checks then passed. Used AST command allowlisting and the fixed compiler-launch check to distinguish code/data and the authorized compiler. Counted scalar workflow run values separately from defaults.run. Failure records retained in author temp. Author-harness causes resolved; not independent approval. |
| P294 author binary hashing / tooling evidence HOLD | x64 positive compiler exit0 with no diagnostics, but immediate and deferred Get-FileHash failed with a file-sharing violation. No csc process remained at diagnostic inspection; locking process/source is unknown. A read-only shared-open probe also failed for x64; x86 shared-read SHA succeeded. | All 32 compiler raw exits/logs retained. Hosted script hashes the binary once after guard compiles and fails closed on hash failure; no retry, executable launch, lock manipulation or claimed resolution. Author x64 binary hash UNAVAILABLE, auxiliary binary-hash evidence HOLD; qualified review OPEN. Source SHA/custody is unaffected. |
| Missing external OS/lifecycle and security decisions | Seven qualified approvals and three accepted complete product regressions absent. Timer does not guarantee OS termination; delete0 does not mean absent. | No candidate EXE launch, SCM mutation or test-script migration. External approvals 0/7; product regressions 0/3. OS launch/teardown security approval required before any mutating hosted retest. HOLD. |

**Disposition: source preparation and compile/static evidence only. Product,
P96, P292 mechanism/root cause/teardown, security and release HOLD.** The
user's bounded candidate authorization does not close any ledger item or
approve a risky deferral. Author self-review is not independent review.

## Architecture and precise delta

Before, the frozen Main validates mode/session, arms the 55s timer, obtains
WindowsIdentity, translates the service virtual account, validates its token,
constructs ServiceBase and finally calls Run. Its OnStart does no work.

After, Main validates the same four fixed ImagePath argument contracts and
Windows/noninteractive/session-zero conditions, arms the same 55s timer,
constructs the service with the exact name as immutable expected account
data, and immediately calls `ServiceBase.Run(service)`. No SID/LSA translation,
WindowsIdentity, WMI, environment-derived identity or discovery occurs before
Run. Bounded null/length checks precede fixed linear regex checks; the temporary
current-process wrapper is disposed. No fallback service name/account exists.

The P292 mode literal, `NayeonP292_` plus exactly twelve lowercase hex digits,
fixed historical P291 SHA argument and final forty-lowercase-hex argument are
preserved for security equivalence, not upgraded to authentication. They do
not authenticate SCM, installed provenance or a trusted process. No Main
selftest, manual OnStart invocation, alternate dispatcher or fake SCM mode
exists. Noninteractive/session-zero alone never proves an SCM launch.
`ServiceBase.Run` is the sole service-dispatch execution boundary; SCM's Start
callback is the only route to OnStart. There is no protected work even after
a successful identity check, and no admission/effect/production capability.

OnStart synchronously obtains `WindowsIdentity.GetCurrent()` and computes
`(SecurityIdentifier)new NTAccount("NT SERVICE", expectedServiceName)
.Translate(typeof(SecurityIdentifier))`. It preserves the original predicate:
impersonation level must be None, User nonnull, User not LocalSystem, and
User exactly equal to the translated expected virtual-account SID. No account
alias, LocalSystem acceptance, cached/fallback SID, skipped lookup or async
continuation exists. Mismatch throws. Every caught exception throws a fresh
fixed `P294_START_DENIED` exception without identity-bearing inner exception.
Identity disposal also precedes successful completion. AutoLog remains false.
There is no service log, stdout or identity-bearing exception output.

A private start flag is set only after these checks/disposal; Main returns
nonzero if Run returns without verified OnStart. This preserves refusal even
if framework startup handling consumes the OnStart exception. The flag is
neither exposed as proof nor usable by any client/product. OnStop remains
empty. No protected operation was moved outside a guard.

The managed deadline is still **55,000ms**, armed before service construction
and Run, including blocked OnStart lookup. No RequestAdditionalTime or timeout
extension exists. Its callback exits with denial. It is **not OS kill-proof**:
thread-pool scheduling, runtime failure or OS blocking can defeat timely timer
execution. This is not a guaranteed startup fix, process termination guarantee,
native absence proof or teardown repair.

Debug compile requires DEBUG + C1_REVIEW_ISOLATED_ASSEMBLY +
C1_P294_DISPATCHER_FIRST_ONLY and !RELEASE, with CS1029 otherwise. The internal
sealed class has a private constructor, no installer or product integration.
These barriers make this a nondeployable review artifact in this repository;
they cannot prevent an externally privileged actor installing arbitrary debug
code. No installer, privileged actor or production install authorization is
provided. No network, IPC, keys, WinCred, DPAPI, registry, ACL or privilege API
is added. ServiceBase framework dispatch is not application IPC authority.
Permission -> Policy -> Confirmation -> Execution -> Verification remains
unchanged; model output is never authority or proof.

## Microsoft contract and inference limits

[Service Entry Point](https://learn.microsoft.com/en-us/windows/desktop/Services/service-entry-point)
directs an own-process service to connect to its dispatcher immediately from
Main, placing service initialization after startup. This makes pre-dispatcher
LSA translation a concrete source-ordering concern. Inferring that it caused
any particular P292 timeout would require new evidence.

[ServiceBase.Run, .NET Framework 4.8.1](https://learn.microsoft.com/en-us/dotnet/api/system.serviceprocess.servicebase.run?view=netframework-4.8.1)
registers the service with SCM; SCM Start then invokes OnStart. The candidate
retains identity refusal inside that synchronous callback before success.
[Service Startup](https://learn.microsoft.com/en-us/windows/desktop/Services/service-startup)
distinguishes simple dispatcher initialization from service initialization
and pending/running status. Its OS timing guidance is not permission to
increase this candidate's 55s limit or infer success from compile checks.

[DeleteService](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-deleteservice)
marks a service for deletion; removal awaits stopped service and closed
handles. No candidate change touches deletion. Delete success is not native
absence, and the third-run x86 post-delete timeout remains unverified.

## Compile/static review and migration obligations

Author validation is limited to native Windows x64/x86 compiler positives,
all fifteen forbidden four-symbol truth-table combinations per architecture,
PowerShell AST parsing, static ordering/predicate/SHA review, raw inherited
custody and whitespace. No generated EXE or hosted script is run locally.
Final results and raw log hashes are recorded after validation below. No
Python product suite/compileall or runtime milestone is claimed by this
compile-only, four-addition task; accepted full regressions remain 0/3.

Six GitHub-hosted windows-2022 jobs (three x64, three x86) compile only. Each
checks exact draft/repository/base/head/single-parent topology and 1,198 clean
raw disk/blob matches before and after. SHA256 manifests cover every file;
links/reparse paths, ignored/untracked files, index/disk/Git drift refuse.
The frozen original SHA and a literal candidate SHA pin bind static review.
Text method extraction verifies only OnStart has identity lookup, synchronous
throw-before-success ordering and predicate equality against frozen P292;
PowerShell is parsed as AST. These are source checks, not C# control-flow or
Windows runtime proofs. The raw candidate pin also rejects unreviewed code.
Seven source-data negatives reject the original pre-dispatcher source, removed
translation, removed LocalSystem refusal, absent success flag, extended timer,
manual OnStart call and swallowed identity failure. They do not execute code
or validate a real service.

Only framework csc.exe may be launched by the script: fixed x64/x86 framework
path, explicit mscorlib/System/System.Core/System.ServiceProcess references,
/noconfig /nostdlib+ /warnaserror+. No generic EXE launcher or assembly load is
present. Allowed compile is exit0/no diagnostics. Forbidden builds must be
exit1/only CS1029/exact guard/no output executable. Compiler child deadline
15s, bounded kill/join/output drain, total admission budget 360s and job
ceiling 8min; no retries or runtime timeout changes. Progress is emitted per
compile. Any stall or unavailable exit is HOLD, not successful evidence.

Only allowlisted text manifests, compiler numeric exits/codes/raw-log hashes,
binary hashes with NOT_EXECUTED, static labels and summary upload. Raw compiler
and failure output stays privately in temporary build storage; no binaries,
identity/token observations, raw exceptions or environment dumps upload.
Receipts always deny production and real keys, mark runtime NOT_TESTED,
SCM operations zero and P292 cleanup UNVERIFIED. A green CHECK proves only
its compile/static checks; missing/skipped jobs are missing evidence.

Before **any** hosted SCM-mutating retest, Nayeon and qualified external
OS launch/teardown security owners must approve exact-source migration and
security test equivalence: original service-mode/virtual-account binding,
all mismatch/exception/impersonation/LocalSystem negatives, synchronous
pre-success identity enforcement, 55s deadline limitations, independent
runtime image/token/restricted-SID evidence, native/CIM disagreement handling,
partial-start failure and native handle/process/child absence after deletion.
Moving the callback invalidates timing assumptions; it cannot weaken any
original token, restricted-SID, provenance, cleanup or uncertainty gate.
Original P292 harness/CI/tests must stay frozen; any future migration requires
separate authorized scope and adversarial review. Approvals are presently
0/7. No hosted mutable retest or candidate EXE execution is authorized here.

## Author evidence, limited to compile/static results

Both native framework compilers completed the positive build at raw exit0,
no diagnostics. All fifteen forbidden symbol masks per architecture completed
at raw exit1, only CS1029 with the exact P294 guard, and no output executable:
**2/2 compile positives, 30/30 expected compile denials**. No compile was retried
or source changed to make a failed build pass. The earlier outer author command
failure occurred during binary hashing after successful x64 compilation;
its successful compiler receipt was reused, not overwritten or recompiled.
All raw compiler logs and numeric exits remain in the author temp directory.
Compiler-summary SHA256:
`F848F0C5FA12ABA73432D03201D2B3DBB2DE25AFF72501A3B005F3B17E658870`.

The x64 output binary hash remains unavailable because of the unresolved
file-sharing failure above. The x86 shared-read SHA256 is
`7D28C957FE47F5A87D3C4746F44BB1C9C755705A4A2E98CD4BE55BD1FED68461`.
No binary hash is a runtime result. No claim of fully green local artifact
validation, six hosted job results, independent review or lifecycle acceptance
is made. Hosted failure to hash must remain HOLD. Source-only candidate handoff
is still within the authorized investigation scope, not a seal or closure.

Author source checker: positive accepted; all seven altered source inputs
refused, including frozen P292 ordering. PowerShell AST parsing has zero
errors. Final custody/whitespace checks and four raw source hashes accompany
the handoff. Candidate executable launches **0**, SCM operations **0**,
credentials/provider operations **0**. Runtime production acceptance is
**NOT CLAIMED**. All qualified security, migration and lifecycle review remains
with Nayeon/external owners; 0/7 approvals and 0/3 full regressions persist.
