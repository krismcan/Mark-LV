# P295 qualified-runtime preflight: offline synthetic plan contract

22 November 2026. **IMPLEMENTATION ONLY; NONDEPLOYABLE; RUNTIME HOLD;
REAL-KEY NO-GO; PRODUCTION HOLD.** External qualified approvals **0/7**;
accepted complete product regressions **0/3**. Under the requested OM v2.1
role split, Codex is the sole implementation writer; Nayeon independently
reviews and owns Git publication. Author checks are not independent review.
No staging, commit, tag, push, PR, hosted run, seal, workbook or dashboard update.

This is authorized offline investigation of held assumptions, not a new product
phase, service migration, runtime qualification or failure-gate waiver. The
only executable is the new in-memory P295 test assembly. No P292/P294 service
EXE, old test assembly, hosted script or production source is compiled into or
executed by these tests. No SCM action, account/token query, native call,
process launch, privilege change, network, credentials, provider, WinCred,
DPAPI, file access or product integration exists in either C# file. Console
output contains fixed test names and counters only. The external validation
wrapper may launch the existing framework compilers and this P295 test assembly
and retain temporary logs; those are not service or runtime experiments.

## Custody and exact source envelope

Initial worktree was clean on
`byok-c1-p295-offline-runtime-preflight-20261122`, at inherited exact P294
`fc45574cb513f82af7d127846fd0b96b41129a4d`, no tag at HEAD, 1,198 inherited
tracked files. Git controls; `.codex/CURRENT_STATE.md` starts with stale
3 November Phase 10.2 notes. It remains byte-identical as explicitly required;
this increment establishes no completed phase or replacement regression baseline.
No inherited source, test, CI or documentation file may change.

Exactly three additive paths:

1. `docs/byok-c1-p295-qualified-runtime-preflight.md`
2. `tests/p295_runtime_preflight/P295PreflightContract.cs`
3. `tests/p295_runtime_preflight/P295PreflightContractTests.cs`

No project, service executable, workflow, deployment script or integration file
is added. Expected review envelope is those three untracked files, empty index,
unchanged HEAD and all inherited disk blobs equal to Git with filters disabled.
An eventual independently authorized publication would have 1,201 source entries;
no future commit, topology or publication result is asserted here.

## Open Failures & Prior-Issues Review

Read: AGENTS.md, current state, engineering failure review gate, P292 service
principal and SCM/CIM diagnostic reviews, P293 decision review/tests, P294
security review/candidate, and the relevant P281 approval identifiers. Historical
hosted findings are inherited review evidence, not a new audit of remote ZIPs.
The affected route remains dispatcher -> synchronous OnStart identity/disposal
-> framework return -> independent process/token/image proof -> stop/delete ->
closed handles/native absence/child exit. Config, CIM, self-reported flags,
timers, later success and runner teardown cannot substitute for those boundaries.

| Issue / severity / source | Evidence, root cause and affected paths | Containment, tests, independent review and disposition |
| --- | --- | --- |
| P292 FIRST RED 0/6, run 44739845249; material HIGH | Six start clients timed out at 8s; stop1062/delete0 and failed immediate native absence left cleanup HOLD. Underlying SCM/service cause remains unknown. | Preserve source and receipts; startup, delete0 and absence adversaries model rejection only. No mutable reproduction or repair claimed; external closure OPEN, HOLD. |
| P292 SECOND RED 4/6, run 44741869649; material HIGH | Two x86 trials returned create0 then failed immediate metadata before SID setup; visibility, query failure and mismatch cannot be distinguished retrospectively. Supplied cleanup 6/6. | Preserve the correction: create receipts existed. No invented CIM-delay diagnosis. Disagreement and missing-receipt controls reject; independent causal review OPEN, HOLD. |
| P292 THIRD RED 3/6, run 44766866901; material HIGH | x64 trial1 CIM QUERY_ERROR, trial2 CIM deadline; x86 trial2 configured restricted SID then 40s start timeout and native post-delete timeout. x86 teardown UNVERIFIED; origin unknown. Frozen mutable HEAD 1083919da53f808105522dd8e11dba9fdf844fa0. | Native1060, closed handles, retained exit and late-child requirements remain separate. No repeat mutable run, fake repair or cleanup closure. Independent review OPEN, HOLD. |
| P292-DIAG stable controls, limited evidence | Supplied six read-only jobs, 144/144, concern stable services rather than newly created lifecycle. | Not a P292 repair, candidate launch, image-provenance or deletion proof. HOLD. |
| P294 pre-dispatcher lookup hypothesis; material | Frozen P292 performs identity/LSA translation before dispatcher. P294 moves synchronous checks into OnStart; no causal attribution of the x86 timeout is proven. Framework may swallow OnStart failure; Main flag is not independent evidence. | Missing/failed OnStart, swallowed error, premature flag, lookup/disposal failure controls. All old/new entrypoints remain frozen; no manual OnStart route. Independent OS review OPEN, HOLD. |
| P294 exact author compile/static status; limited evidence plus tooling HOLD | 2/2 x64/x86 positive compiles exit0, no diagnostics; 30/30 forbidden builds exit1, only CS1029, no binary. Source checker positive plus seven altered-source rejections; PowerShell AST zero errors. Candidate EXE launches0, SCM operations0. x64 binary SHA UNAVAILABLE due unresolved sharing violation; x86 SHA 7D28C957FE47F5A87D3C4746F44BB1C9C755705A4A2E98CD4BE55BD1FED68461. | Compiler-summary SHA F848F0C5FA12ABA73432D03201D2B3DBB2DE25AFF72501A3B005F3B17E658870. Earlier checker/wrapper errors were documented; no fully green artifact or hosted/runtime acceptance claimed. Preserve hash blocker; independent artifact/security review OPEN, HOLD. |
| 55s managed timer; HIGH missing OS guarantee | Thread-pool scheduling, managed/runtime failure and OS blocking can prevent callback execution. Arming a 55,000ms timer does not establish process death, native1060 or absence of late children. | Explicit fault-control firing expectation plus independent deadline/exit source. No actual wait, timer or kill here. Does not prove an OS-enforced deadline or repair P294; qualified signoff OPEN, HOLD. |
| Original P96 HIGH OPEN | Final StillCurrent/fourth IsOwned and SAVE/REPLACE/DELETE remain separated; revoke/effect/restart atomicity unproven across old native/Python callers. | No owner, journal, callback, store or effect edge. No original concurrency reproduction or repair. Qualified review OPEN, HOLD. |
| Principal/provenance/consent/store/restart HIGH OPEN | P99 LocalSystem versus proposed virtual account, mutable installation, service ACL/client provenance, one-use consent, profile/DPAPI/WinCred and recovery custody remain unresolved across windows/processes/restarts. | Independent source checklist plus token/ABA/image negatives only; no production wiring, installation, custody or credential proof. SEC03/04 and remaining qualified decisions OPEN, HOLD. |
| P76/P211/P216 and full acceptance OPEN | P76 four failures, P211 test02, P216 test02/test06 and alternate Python native-effect reachability remain unwaived. | No historical suite changes, skips or substituted acceptance. No product regression run; accepted 0/3. Independent acceptance OPEN, HOLD. |
| Missing external approvals / independent review | GOV01/02, SEC03/04, REL05/06/07: 0/7 accepted. Nayeon exact-source and external qualified OS launch/teardown/security decisions absent. | Approval entries are required future decision sources, never signed approvals. Incomplete/unbound/optional entries reject. No risky deferral or material issue closed; HOLD. |
| P295 author validation wrapper failure; tooling | First Start-Process wrapper returned no captured ExitCode for the all-symbols-absent x64 compile. It emitted the two expected CS1029 diagnostics, but raw exit is UNAVAILABLE; outer wrapper exit1. No assembly execution occurred. | Preserve the attempt, do not infer exit1 from diagnostics. A direct Process wrapper with bounded waits/captured streams obtained reliable exits; separate compiler-help probe exit0. Complete 32-build matrix and both synthetic executions below passed with no C# source repair. Author wrapper correction only, not independent review or historical closure. |

**Disposition: HOLD** for runtime, cleanup, product, original failures, security,
real keys and release. The user authorized only this bounded plan-contract
implementation. Synthetic green assertions do not close any ledger entry.

## Contract and independent evidence-source obligations

All types are internal, sealed immutable data; arrays are cloned on construction.
There are no input delegates, serializers, native handles or dynamic execution.
`Review` takes a proposed one-instance plan and fixed synthetic fixtures only.
These are acceptance-condition examples, not an actual runtime timeline or
authenticated receipts. In particular the managed timer firing fixture is a
separate proposed fault control, not a claim that a normal startup fired its
deadline before succeeding. The model checks both the normal-start fixture and
the deadline-control fixture, with an independent exit obligation in either case.

Initial result is `PRECHECK`. Malformed, incomplete, conflicting, failed,
replayed or authority-seeking proposals yield sticky `HOLD`. One complete,
coherent synthetic control yields **`PLAN_ONLY`**, never runtime admission,
qualification, approved provenance, real-key use or production release.
All four capability/provenance properties are literal false in every state;
accepted approvals/regressions remain literal zero. No authority object is issued.
Permission -> Policy -> Confirmation -> Execution -> Verification is untouched;
model output and a coherent synthetic claim remain untrusted.

The fixed ordered checklist has 23 mandatory evidence kinds. Each names the
expected source role, a bounded collector label, unique capture, exact synthetic
run/instance and ordinal, complete-receipt and required-on-failure obligations.
Different source roles require distinct collector labels. Same-role collector
drift, swapped source, duplicate capture, wrong instance/run or self-report
rejects. These labels model intended independence; an attacker can invent
coherent labels. There is no authentication, OS provenance or real collector here.

| Independent planned source | Mandatory named observations / limitations |
| --- | --- |
| Native SCM observer | Pre-create absence1060, exact configuration, RUNNING status, STOPPED status, raw delete result, all SCM/service handles closed, post-delete native1060. Configuration and returned start0 do not establish running identity. |
| Startup observer, separate from service self-report | Dispatcher registration, actual OnStart entry, synchronous successful LSA lookup and identity disposal, completed OnStart, framework return and verified flag set only after disposal, 55s managed timer fault control. Framework exit0 or a flag alone is insufficient. |
| External deadline observer | Independent bounded exit evidence when managed deadline does not fire. The contract implements no watchdog and cannot guarantee OS termination. |
| Retained process observer | PID plus creation time and continuous retained-handle identity, then signaled retained process exit. No pending/stopped SCM PID supplies running identity. |
| Independent kernel token observer | Two distinct captures of primary session0 token, exact virtual-principal fixture distinct from runner/LocalSystem, no subject/observer impersonation, TokenId/AuthenticationId/ModifiedId continuity, actual restricted-SID membership and IsTokenRestricted-equivalent proof. Configured SID type alone is insufficient. |
| Image custody reviewer | Exact before/after image digest plus independent immutable installed provenance requirement; equal digests alone cannot prove signing, protected path or SCM/client ACL. Actual signature/ACL/install policy is for qualified review. |
| CIM observer | Exact service/image absence reconciled with native findings. Empty CIM never substitutes for native1060; disagreement/error/deadline is HOLD. |
| Child observer | Complete exact-run child receipts, retained-child exit and bounded late-child sweep. Surviving/late child or missing receipt is HOLD; finite samples cannot prove permanent absence. |

Synthetic fixtures also reject start failure/unavailable exit, non-RUNNING or
non-STOPPED state, drift in PID/birth/token IDs/retained handle/image, mutable
image, missing provenance, impersonation, wrong principal and restricted SID.
Deletion0 or1072 may be recorded, but neither establishes absence: native1060,
closed handles, reconciled CIM, retained exit, all children absent and complete
receipts are mandatory. A 1072 record is not converted to delete success or an
authorized retry. Any earlier failure remains HOLD even after matching data.

Seven ordered approval obligations name GOV01, GOV02, SEC03, SEC04, REL05,
REL06, REL07 external decision sources. Each must require exact-source binding
and signoff before any runtime activity. They carry no approval value. This
source-completeness check cannot accept or verify those seven decisions.
External qualified OS launch/teardown/security signoff, Nayeon independent
review and distinct user-authorized runtime scope remain mandatory.

Run reservations are bounded to 4,096 within this process, shared between
checkers and fail closed on exhaustion. Reusing a checker invalidates even
PLAN_ONLY. Failure then success in either the same checker or a new checker
cannot clear a reserved run. This is not durable replay protection across
restarts, an OS clock, continuous custody or a production security boundary.

## Build, source expectations and validation record

Both entire C# translation units require
`DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P295_OFFLINE_ONLY && !RELEASE`;
otherwise only an explicit CS1029 guard compiles. No release/default fallback.
These are nondeployable review artifacts by source contract and lack of service
or product integration; preprocessor symbols are not a hostile-code sandbox.
The code uses Framework-compatible C# 5 and base library collections/Console,
with no package, external assembly or product dependency. Existing Windows
Framework compilers are used, never downloaded/installed/copied. A 4.8.1
reference pack was not found in the standard location; compatibility of the
restricted API/language surface is distinct from a 4.8.1 targeting-pack build.

Each proposed plan names three ordered source-path/SHA256 expectations: frozen
P294 service candidate, P295 contract, P295 tests. Shape/nonzero checks model
the obligation only; fixtures deliberately use synthetic digests and the C#
contract reads no files or Git. A syntactically valid forged digest can remain
PLAN_ONLY. Nayeon must independently bind real reviewed raw bytes and source
custody before any later qualified runtime proposal; none is admitted here.

Frozen P294 candidate raw SHA256:
`2B7D87F8770BED1B21C756DE0344D34C5A87584D800AF58A430B9864CB1B81FC`.
Final P295 C# raw SHA256 pins after implementation:

| Exact path | Raw SHA256 |
| --- | --- |
| tests/p295_runtime_preflight/P295PreflightContract.cs | `5BE876B0A5631D37656BCA9C0E68CBA7310E07AF5F0D82AAE6F275026CDA4180` |
| tests/p295_runtime_preflight/P295PreflightContractTests.cs | `C9101ACC3618289DEC108BB598071F0651DFDDBDF7747030189659F291A6D211` |

The fixture's lowercase digest format is deliberate; real manifest values would
need canonical lowercase representation in a separately reviewed proposal.
No such runtime proposal is accepted here. This document has no circular self-pin; its final raw
SHA256 belongs in the handoff manifest with all three exact paths. Any later
byte change requires a fresh manifest/review. Source pins are not runtime proof.

Author validation actually executed, with 15s per compiler/test child, no retries
of a failed synthetic test, and no package installation:

| Check | Actual result / scope |
| --- | --- |
| Allowed x64 and x86 builds | 2/2 raw exit0, empty diagnostics, C#5, `/noconfig /nostdlib+ /warn:4 /warnaserror+ /target:exe`, explicit installed-framework mscorlib/System/System.Core references. Only the two P295 sources are passed. |
| All other four-symbol truth-table combinations | 15 per architecture, 30/30 raw exit1, exactly two CS1029 diagnostics (both source guards), no output binary. Includes each absent symbol, all absent, and every RELEASE combination. |
| P295 x64 synthetic execution | Raw exit0; **85/85 named cases, 2,367 executed assertions**; one coherent PLAN_ONLY control and 84 refusal/adversarial cases. No test failure. |
| P295 x86 synthetic execution | Raw exit0; **85/85 named cases, 2,367 executed assertions**, same unique cases; no test failure. |
| Output completeness | Both raw stdout logs match every literal named case in source order; 85 unique names, none missing/duplicated; stderr empty. All states explicitly check four denials and zero approvals/regressions. |
| Binary custody | Before/after hashes equal for each P295 assembly; no claim about P294's unresolved x64 binary hash. |
| Static C# surface scan | Passed both files for prohibited native/unsafe, IO/network/process/service/security/threading/reflection, environment, dynamic and assembly-load surfaces. Compiler supplies syntax/type/warning checking; no separate C# AST tool or formal control-flow proof claimed. |
| Source custody | All 1,198 inherited raw disk blobs equal HEAD using `git hash-object --no-filters --stdin-paths`; zero mismatches. `.codex/CURRENT_STATE.md` included. HEAD unchanged, index empty; exactly three new paths. |
| Whitespace | Tracked `git diff --check` exit0; all three additions separately checked with `git diff --no-index --check /dev/null <path>`, exit1 meaning added-file difference, zero whitespace diagnostics. |

Temporary evidence directory:
`C:\Users\krist\AppData\Local\Temp\p295-validation-1fa1aea20c604131b8488a05718c67ef`.
It retains individual compiler stdout/stderr/numeric exits, summary, two test
stdout/stderr/numeric exits and P295 binaries. No evidence/binary file is added
to this worktree. The failed initial wrapper is preserved separately at
`C:\Users\krist\AppData\Local\Temp\p295-offline-e95822ea41fc4b5cacd2898564608986`;
its blank exit file is not a valid compiler exit receipt. Early inventory also
returned shell exit1 because `rg` is unavailable; PowerShell file enumeration
replaced it without installation. Neither tooling failure was a synthetic test
failure or an inherited source repair.

| Evidence artifact | SHA256 |
| --- | --- |
| compiler-summary.txt | `68C98D4697F3876A0BE77A8E03E2E087DAA5A3A3C02A0A65947BFA12A1E74630` |
| x64-runtime.stdout and x86-runtime.stdout (identical bytes) | `2DC9DA9B7E99675B1D65414D17BDC30A08D69005F060CF4D40A290D661FA2082` |
| x64-mask-7.exe (P295 only) | `F95D6EBEB557B54B03100C55E3BF679A617C97BA4C474AE4EB9E6E2ECD8B0544` |
| x86-mask-7.exe (P295 only) | `0840D185B79FF0E9C58BA226C764DA85ED725B8734F93FB50B00BA7BEB8EA589` |

Only the P295 synthetic assembly was executed. P292/P294 EXE executions **0**;
SCM/service operations **0**; account/token queries **0**; credentials/provider
operations **0**. Full Python/product discovery and compileall are outside this
explicit in-memory-only test scope; accepted regressions remain **0/3**.
Qualified approvals remain **0/7**. The missing 4.8.1 targeting pack, genuine OS
startup/termination/native absence, source authenticity, installed provenance,
cross-process/restart custody and independent security review remain limitations.
**Final disposition: HOLD.** No fake green release or runtime authorization.
