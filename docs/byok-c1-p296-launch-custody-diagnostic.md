# P296 launch-custody diagnostic: source only, HOLD

22 November 2026; OM v2.1. Codex is the sole implementation writer. Nayeon
owns independent review and any separately authorized publication. This is
bounded investigation of held launch-custody assumptions, not a product phase,
runtime qualification, seal, real-key upgrade or production upgrade.
Qualified external approvals remain **0/7**; full accepted regressions **0/3**.

## Custody and exact scope

Initial clean worktree:
`D:/Nayeon/CODEX_P296_LAUNCH_CUSTODY_20261122`, branch
`byok-c1-p296-launch-custody-diagnostic-20261122`, HEAD
`c1bb282f0224b22902cdba7740de71bbeaf07b8a` (P295), no tag at HEAD,
1,201 inherited tracked paths. Git matches the requested checkpoint.
`.codex/CURRENT_STATE.md` starts with stale 3 November Phase 10.2 notes.
It is intentionally unchanged under the explicit source-only instruction;
no phase completion or replacement regression baseline is asserted.

Exactly three additions, no inherited edits:

1. `docs/byok-c1-p296-launch-custody-diagnostic.md`
2. `tests/p296_launch_custody/P296LaunchCustodyDiagnostic.cs`
3. `tests/p296_launch_custody/P296LaunchCustodyDiagnosticTests.cs`

No project/default production assembly, integration, workflow, launcher script,
SCM change, install, service start, deletion, account/token/credential access,
network/download, staging, commit, tag, push or context-file change. Only
existing Framework compilers were invoked for compilation. No generated
assembly, P295/P296 test, test-only launcher, P292/P294 service EXE or hosted
runner was invoked. No Application Control bypass or alternate runtime
launcher was attempted. Compiler outputs/logs stay outside the worktree.

## Exact source references and interpretation

References below are frozen by the P295 HEAD above, not a future moving source:

| Reference | Relevant behavior / implication |
| --- | --- |
| [P292 HostedReview.ps1, Source-Hashes, line 88](../tests/p292_service_principal/HostedReview.ps1#L88), blob `5e249b6dd1bb2bcc267215dd0b273450f91788bb` | Raw inherited disk/blob comparison and source manifests. Lines 519-521 compare the final manifest. Equal source bytes do not prove a child launched or teardown succeeded. |
| [P292 Child, line 137](../tests/p292_service_principal/HostedReview.ps1#L137) | Redirects both streams, starts async ReadToEndAsync, bounded child wait, raw exit or TIMEOUT RAW_EXIT=UNAVAILABLE, finally kill/join/dispose. ReadToEndAsync retains unbounded output; subsequent GetResult has no independent stream-drain deadline. P296 does not edit or invoke it. |
| [P292 Sc, line 182](../tests/p292_service_principal/HostedReview.ps1#L182), [Create-Metadata, line 205](../tests/p292_service_principal/HostedReview.ps1#L205) | sc-start gets 40s; other child windows 8s. CIM catch exits raw11; child timeout is unavailable, distinct from raw11. No historical timeout/exit is rewritten. |
| [P292 Find-DisposableChild, line 298](../tests/p292_service_principal/HostedReview.ps1#L298), [cleanup, line 425](../tests/p292_service_principal/HostedReview.ps1#L425) | Retained image/birth/handle binding, late-child handling, native/CIM absence, CLEANUP PASS/HOLD. Delete0 and stop1062 are not independent absence proofs. |
| [P294 service source](../tests/p294_dispatcher_first/P294DispatcherFirstDisposableService.cs), blob `4235f255546e1a059995da1e401b8f75ddd92920` | OnStart line 28 performs synchronous identity lookup/disposal before flag; Main line 54 uses dispatcher line 73 and managed 55s timer line 69. Timer arming/flag/exit0 are not independent OS supervision or startup proof. |
| [P294 security review](byok-c1-p294-dispatcher-first-security-review.md) | Read in full, including frozen-source, binary-sharing, deadline, failed-wrapper and migration limitations. Supplied P294 hosted 6/6 is compile/static only. |
| [P295 preflight](byok-c1-p295-qualified-runtime-preflight.md), failure review line 43 and validation line 133 | Read in full. Historical author synthetics 85 cases on each architecture, with reported exits0, remain historical; no rerun here. These do not override the separately supplied Application Control refusal. |
| [Mandatory failure gate](engineering_failure_review_gate.md), [AGENTS.md](../AGENTS.md) | Material unknown causes and missing independent evidence remain HOLD. Source preparation here is expressly authorized investigation, not forward phase admission. |

## Open Failures & Prior-Issues Review

Historical ZIP observations below are the user's supplied observations from
retrieved genuine P292 third-run artifacts. This turn did not fetch/reopen
remote ZIPs. Exact artifact paths/hashes not supplied here remain unavailable;
source references explain the classification, not artifact authentication.

| Issue / date-source / severity | Evidence, cause and affected boundary | Containment / tests / independent review / disposition |
| --- | --- | --- |
| P292 first run 44739845249, inherited; HIGH | Overall 0/6, start-client deadlines and missing teardown evidence. SCM/service root cause unknown; launch -> running -> cleanup affected. | Frozen unchanged; no mutable reproduction/repair. External causal review OPEN, HOLD. |
| P292 second run 44741869649, inherited; HIGH | Overall 4/6; two x86 metadata failures AFTER create0, before SID setup; supplied cleanup 6/6. Visibility/query/mismatch root cause unproven. | Do not invent missing create or a CIM-delay cure. Missing/incomplete receipt tests only; independent closure OPEN, HOLD. |
| P292 third run 44766866901, x64t1, supplied 22 Nov; HIGH | create-metadata **raw11**, CIM observer catch. Native after-absent **0**, CIM absent **0**, **CLEANUP PASS**. Observer exception cause unknown. | Preserve raw11 and independent cleanup success simultaneously. `raw11_cleanup_pass` models this separation; not a historical repair. Independent causal review OPEN, HOLD. |
| Same third run, x64t2; HIGH | create-metadata **timeout, exit unavailable**, **CLEANUP PASS**. Deadline is distinct from a returned query-error code. | `timeout_cleanup_pass` retains unavailable exit and HOLD despite cleanup. No actual deadline reproduced; independent review OPEN, HOLD. |
| Same third run, x86t2; HIGH | sc-start **timeout, exit unavailable**; sc-stop **1062**, delete **0**; after-absent **TIMEOUT, exit unavailable**; **CLEANUP HOLD**. Teardown unverified; service persistence is NOT established. | `timeout_cleanup_hold` and raw1062 rejection retain distinct errors. No retry or deletion/kill experiment. Independent OS review OPEN, HOLD. |
| Third-run source custody; limited | All three supplied before/after manifests equal, **1,185 lines each**; overall **3/6**. This differs from this worktree's 1,201 inherited paths. Equal historical manifests do not resolve any of the three HOLD causes. | Preserve historical source and exits; no inference of persistent service, successful launch or current provenance. HOLD. |
| P294 static 6/6 and prior x64 binary sharing; material missing evidence | Supplied six successes are compilation/static only. Prior x64 binary hash unavailable because of sharing failure; locking cause unknown. | Equal before/after hashes are insufficient when sharing is ambiguous. Before/after sharing negatives fail closed. No lock manipulation or claimed closure. Independent review OPEN, HOLD. |
| P295 author / independent launch disagreement, supplied 22 Nov; HIGH | Author 85 x 2 synthetics reported success. Independent direct PowerShell launch was refused by Application Control while Codex process-start reported success. Actual launch custody remains ambiguous; root cause unknown. | Treat disagreement as HOLD, preserve both reports. Denied/ambiguous/unavailable launch tests. No alternate launcher, policy exception, bypass, rerun or claim that either report wins. Qualified independent review OPEN. |
| Managed deadline / cross-process cleanup; HIGH missing guarantee | Blocked launch/read/dispose or host/runtime failure may defeat an in-host timer. Pipes may remain open in descendants after parent exit. PID lookup alone risks reuse. | Retained identity, externally supervised deadline, both EOFs/disposals and descendant receipts required. Pure fixture negatives only; OS supervisor absent by design. Independent OS/teardown review OPEN, HOLD. |
| P96; inherited HIGH OPEN | Final StillCurrent/fourth IsOwned and SAVE/REPLACE/DELETE still separate across older Python/native callers, shared owner state and restart. No atomicity proof. | No owner/effect/store route introduced; no repair or downgrade. Independent qualified review OPEN, HOLD. |
| Principal/provenance/consent/store/restart; inherited HIGH OPEN | LocalSystem versus virtual account, installed image/ACL, token restriction, one-use consent, profile/DPAPI/WinCred and restart custody unproved. P292/P294 dispatcher and alternate native/Python routes remain relevant. | No product imports, credential backend, native observation or new bypass. Hash equality/receipt labels do not prove any of these properties. SEC03/04 and qualified review OPEN, HOLD. |
| P76/P211/P216; inherited material OPEN | P76 four failures, P211 test02, P216 test02/test06 and alternate native-effect reachability unwaived; accepted full regressions **0/3**. | No skipped/edited historical tests, no product suite run. Independent regression acceptance OPEN, HOLD. |
| GOV01/02, SEC03/04, REL05/06/07; material missing evidence | Qualified approvals **0/7**. Nayeon independent exact-source review, OS launch/teardown approval and user-approved runtime scope absent. | No synthetic approval values or release authority. No risky deferral approved; runtime/real-key/production HOLD. |
| P296 author tooling, 22 Nov; bounded | `rg` unavailable during initial read (shell exit1). First compiler command raw exit1, two CS1504 missing-source diagnostics with relative forward-slash paths; no output DLL. | PowerShell enumeration used without installation. Resolved absolute native paths compile successfully; original diagnostics retained, no source change for CS1504. Tool-path repair only; not independent source/runtime validation. |

**Failure gate: HOLD.** No material original issue is reproduced on the OS,
closed, waived or deferred. No historical suite/entrypoint is modified.

## Implemented receipt lifecycle and inert launch boundary

The library implements ordered receipt consumption, rather than accepting a
single success flag or an unordered checklist. The sequence is before-hash ->
external-supervisor-armed -> launch -> both async drains started -> interleaved
bounded stdout/stderr plus EOF and retained exit -> cleanup -> after-hash ->
external-supervisor-closed. A deadline event may replace the normal exit path;
it always produces HOLD with unavailable raw exit unless a genuine earlier
exit receipt exists. Exit and EOF may arrive in either order. Duplicate launch,
extra terminal records, out-of-order transitions and reuse fail closed. Faults
accumulate; later successful cleanup cannot erase an earlier launch/exit fault.

The fixed compiler-bound candidate is a future review-only location
`D:\Nayeon\P296_REVIEW_ONLY\P295PreflightContract.exe`, empty arguments and
working directory `D:\Nayeon\P296_REVIEW_ONLY`. Expected SHA256 is the
historically recorded P295 x64 synthetic assembly digest
`F95D6EBEB557B54B03100C55E3BF679A617C97BA4C474AE4EB9E6E2ECD8B0544`.
There is no claim of an existing file, authorized installation or current
binary hash. No P292/P294 service command is a candidate. Inputs are receipts
about these fixed literals, not commands; no path, arguments, working directory,
digest, shell command or environment override can be selected by user/model
input. All receipts must be synthetic; changing the candidate requires new
reviewed source, not an opt-in argument.

`InertOsBoundary.RequestLaunch` returns a fixed Disabled HOLD. It has no input,
Process.Start, native process API, launch delegate, adapter, enable symbol or
runtime switch. It is not invoked, including by the tests. A future supervisor
and OS launcher are deliberately **absent**: implementing executable OS launch
under this authorization would introduce unapproved side-effect capability.
This is the requested safe fallback: working receipt-processing source and a
bounded drain algorithm, plus explicit future diagnostic barriers, without
actual launch capability. It does **not** implement or demonstrate OS custody,
wall-clock termination, native cleanup or a real independently supervised run.

Retained identity includes PID, birth ticks, exact image and a retained-handle
fixture label on every child/stream/exit/cleanup observation. No PID-only
reacquisition/kill or retry exists. This immutable label is not a kernel handle;
future collectors must retain an actual handle through final exit observation
and disposal. Drift makes identity and cleanup HOLD. Before/after digest must
each equal the expected digest at the exact image path. Missing exclusive-read
evidence or any sharing ambiguity fails closed even if digests match. Receipt
equality is not signing, protected installation, file-object continuity or
protection against replace-and-restore races.

Child deadline is fixed at 8,000ms from the external supervisor's monotonic
origin (including preflight/launch), cleanup at 10,000ms, total receipt closure
at 12,000ms. Observation times must be nonnegative and nondecreasing; child
exit at/after 8,000ms is HOLD. Streams may finish within the cleanup window.
At most 128 immutable events are cloned/consumed; oversized sequences reject
before cloning. Each stream retains at most 4,096 UTF-16 characters (8,192
combined); overflow is HOLD, never silent successful truncation. Raw output
is retained only in memory, not printed or exported. Error classes distinguish
protocol, policy denial, ambiguous launch, hash, sharing, identity, deadline,
stream, output limit, nonzero/unavailable exit, supervisor, cleanup and reuse.

`BoundedAsyncDrain.CollectAsync` uses Framework 4.5+ TextReader.ReadAsync and
a 256-character buffer, retains only a bounded prefix and continues draining
excess output to avoid pipe backpressure. It reports EOF, overflow,
cancellation, read error and dispose error separately, including error paths
through finally disposal. There are no callers here. A future adapter must
start stdout and stderr drains concurrently before waiting for exit and map
every helper failure to an incomplete stream/HOLD receipt. Cancellation cannot
reliably interrupt Framework ReadAsync or Dispose; the helper is expressly not
an independent watchdog. No unbounded WaitForExit/GetResult is introduced.

The first exit receipt retains the raw signed integer exactly, or explicit
`RAW_EXIT=UNAVAILABLE`; later receipts cannot overwrite it. Thus raw11 plus
cleanup PASS remains diagnostic HOLD; timeout plus cleanup PASS remains HOLD;
timeout plus cleanup HOLD remains HOLD with both uncertainties preserved.
Disposal of a Process wrapper alone would not prove child death. Process exit,
both stream EOFs, stream/process disposal and no descendants are separate
cleanup requirements; forced termination cannot turn deadline HOLD into success.

Every result denies launch, runtime qualification, production and real keys;
accepted approvals/regressions are literal zero. A coherent synthetic sequence
returns only `SYNTHETIC_RECEIPT_ONLY`. Actors, times, hashes and handle labels
are unauthenticated fixture data and can be forged coherently. No live evidence
admission, durable replay ledger, clock, audit signer or OS authority is created.
Permission -> Policy -> Confirmation -> Execution -> Verification is unchanged;
model output is neither authority nor proof.

## Barriers before any future executable diagnostic

Separately approved exact-source scope and all required qualified decisions
must precede an OS adapter. Independent owners must bind the actual reviewed
binary, immutable exact command/directory/environment, protected file object,
before/after exclusive hash custody and installed provenance. They must provide
an independently running supervisor armed before launch, with its own retained
host/child handles, monotonic absolute deadline, bounded launch/read/cleanup
coverage, containment of descendants and authenticated complete receipts even
if the launch host blocks or dies. Framework in-host timers are insufficient.

The future adapter must avoid shell interpolation, arbitrary executables,
ambient environment/path lookup, PID-only killing, and retries. It must hold
the exact child handle through signaled exit/raw exit acquisition, enforce
independent drain/join/disposal deadlines, classify all failures, preserve raw
receipts and retain cleanup HOLD on drift, surviving/late children or missing
evidence. Application Control denial/disagreement requires qualified resolution
through the original approved route; no alternate launcher or weakened policy.
Source hash equality alone cannot fill these gaps. Nayeon independent source
and adversarial review remains OPEN; runtime activity needs a separate explicit
authorization. No future approval is implied by this document or build.

## Brief author validation report

Both entire translation units require exactly
`DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P296_SOURCE_ONLY && !RELEASE`.
Every other four-symbol combination emits CS1029 in both files. No default or
production build is supplied. These are review barriers, not a malicious-code
sandbox. C#5 and installed .NET Framework 4.x references are used; the async
helper requires Framework 4.5 or later within 4.x. No targeting-pack, package,
compiler or runtime was installed/downloaded/copied.

| Check | Actual evidence / limit |
| --- | --- |
| First compiler attempt | Raw exit1, exactly two CS1504 missing relative-source errors; no DLL. Preserved in `positive-x64.txt` / `.exit`. |
| Resolved absolute-path initial x64 build | Raw exit0, zero diagnostics; source was then tightened for bounded pre-clone rejection and incomplete-stream cleanup handling. This is not the final-source result. |
| Final-source x64 and x86 library builds | **2/2 raw exit0, zero diagnostics**, `/noconfig /nostdlib+ /langversion:5 /warn:4 /warnaserror+ /target:library`; only these two new C# files and installed mscorlib/System/System.Core references. DLLs NOT_EXECUTED/NOT_LOADED. |
| Other symbol combinations | **30/30 expected raw exit1**, exactly two CS1029 diagnostics each, only `P296_DEBUG_ISOLATED_SOURCE_ONLY_REQUIRED`, no output DLL. No other final compiler errors/warnings. |
| Test inventory | **56 source cases**, including **47 named rejection cases** and historical raw11/timeout/cleanup separation, replay/raw preservation and output bounds. Pure in-memory receipts; **0 executed**, no test PASS count claimed. Neither inert launch entry nor drain helper is called by tests. |
| Static surface / custody / whitespace | PASS: both exact guards, no process/native launch surface or product imports in the checked code, no test calls to the inert entry/drain helper; 47 unique rejection names and 56 case increments. All **1,201 inherited raw disk blobs equal the unchanged index/HEAD**, including `.codex/CURRENT_STATE.md`; exactly three requested untracked files, zero inherited edits, empty index. Tracked `git diff --check` exit0; each addition's `git diff --no-index --check` exit1 (added-file difference), zero whitespace diagnostics. Text scans are not a formal C# control-flow proof or independent review. |
| Runtime/product | P295/P296 executions0; P292/P294 launches0; SCM/account/token/credential/network operations0. Full discovery/compileall intentionally not run under this source-only instruction. Qualified approvals0/7, accepted full regressions0/3. |

Compiler evidence directory:
`C:\Users\krist\AppData\Local\Temp\p296-compile-5333a38464db4ba6b0fed05af4a47c3b`.
Each final architecture/mask has a `.txt` diagnostic log and `.exit` raw exit.
Final `matrix-summary.txt` SHA256:
`BBD3FCBF63547C8EC5D025B90D42BB4B47698D6957FAD453046F4C881D8698A7`.
The earlier failed attempt remains separate and is not replaced by the matrix.

Final C# source SHA256 (document self-hash belongs in the handoff):

| Path | SHA256 |
| --- | --- |
| tests/p296_launch_custody/P296LaunchCustodyDiagnostic.cs | `9EA16EEA4765BD10E7C2C47DB9C8BCD1100F37971DA7F3F2D584735D000BD48D` |
| tests/p296_launch_custody/P296LaunchCustodyDiagnosticTests.cs | `B3D8FBA3B5A16EBC2BD2FB6AF09C3463E28314583B71D287B38FDB2DA6FE3C01` |

Compiler verification establishes syntax/types/guards for this source, not
executed test results, independent security review or any historical closure.
**Final disposition: HOLD** for runtime, cleanup qualification, original
failures, real keys, production and release. No milestone completion claimed.
