# P249 effect-free runtime authorization decision request

15 November 2026. **DOCUMENTATION/DECISION CONTRACT ONLY. PREPARATORY checkpoint.**

**Qualified Approval Requested. Runtime authorization and acceptance: HOLD.**
Actual executed P247 cases: **x64 0/54 executed AND x86 0/54 executed**.
The 54 loop-expanded cases per architecture are SOURCE INVENTORY ONLY, not
54 distinct C# methods. One dual-architecture pass requires **108
architecture-specific case executions**. Repeat runs do not increase unique
case coverage. No runtime evidence has been created.
P249 performs no compilation, runner/binary execution, test invocation, policy
change, signing, provisioning, network access or production operation.

## Exact source and permitted scope

Verified checkout: `D:\Nayeon\CODEX_P249_RUNTIME_AUTHORIZATION_20261115`.
Branch: `byok-c1-p249-effect-free-runtime-authorization-20261115`.
Clean intake HEAD: `3c4c8ce29cb95698926d3dc21db592014db4b143` (P248), with
exactly one parent, P247 `39dbb445fc08a1ef03c73f4a13c6f344be8dfa07`.
P247's parent is `e49810c0cc0982f73fb2d7f84ba516ab006f75a5` (P245).
The P249 branch currently points at P248; no new P249 commit exists.
No tag points at intake HEAD or P247. No tag is created or moved.
`.codex/CURRENT_STATE.md` starts with stale 3 November Phase 10.2 status;
Git and this explicit assignment govern this bounded task. That file is unchanged.

The original P247 commit adds exactly these four allowed paths. SHA-256 values
below were observed from raw checkout bytes during P249; `git hash-object
--no-filters` also matched each original P247 blob. P248 changes none of them.

| Original allowed path | Observed SHA-256 |
| --- | --- |
| `tests/p247_effect_free_service_ordering/EffectFreeServiceOrdering.cs` | `CB58CA6ED389817EA4F1BCF0C23DD51C244808CB54AE83DF83FBC36DCABC6C88` |
| `tests/p247_effect_free_service_ordering/OrderingTests.cs` | `3BF159595FC04A772151D3620E732014A7F1BB5BB3AE5A158A4CDF26C82D5450` |
| `tests/p247_effect_free_service_ordering/Run-Isolated.ps1` | `97ABBBE01D187BBFF711EBAE8BA1AAD9A48B100F050516F412C6B60553B66889` |
| `docs/byok-c1-p247-effect-free-service-ordering-decision.md` | `BED85F19D37ABD66B87B2639D9595F88944F6B7C29669F0AD71CA683ACC80B80` |

P248 is a one-child, three-addition checkpoint: its property-mapping document,
`scripts/p248_p76_properties.py` and `tests/test_p248_p76_properties.py`.
Only its document was read for status; no P248 source/test execution is authorized.
P249 adds only this document. All inherited bytes and histories remain intact.
Existing review links, supplied by the assignment and not fetched here:
[P247 draft PR #169](https://github.com/krismcan/Mark-LV/pull/169) and
[P248 PR #170](https://github.com/krismcan/Mark-LV/pull/170).

Source inspection finds no unexpected production/effect APIs in the two C#
files: the model uses fixed metadata, collections and monitor locking; it has
no credential, provider, network, filesystem, service, P/Invoke or injected
effect port. The test driver uses console output, reflection and bounded native
threads, delegates and synchronization objects. The PowerShell runner intentionally
uses temporary filesystem output, installed compilers and native process launch;
it is execution orchestration, not an effect-free authority boundary. Source
inspection alone is not assembly/loaded-code attestation or proof of isolation.

## Preserved evidence and Open Failures & Prior-Issues Review

Historical compiler/runtime facts below are recorded in the unchanged
[P247 decision](byok-c1-p247-effect-free-service-ordering-decision.md), not
rerun or independently authenticated from external raw logs in P249.
The [P248 mapping](byok-c1-p248-p76-property-mapping.md) preserves separate
historical/current-property gaps. Neither document grants runtime authority.

| Issue / evidence | Severity, root cause and impacted boundary | Containment, review and GO/HOLD |
| --- | --- | --- |
| P247 x64/x86 positive compilation | Evidence limitation: both installed .NET Framework compiler commands with both defines reportedly exit 0; compilation is not execution | Preserve genuine compile PASS separately. Independent raw receipt review required; runtime HOLD |
| P247 no-flags builds | Missing negative evidence: x64 reportedly exit 1 with CS1029 for both source guards; x86 no-flags compile/refusal remains unresolved | Require real negative compile receipts for both architectures. No no-flags binary runtime is claimed or requested; HOLD |
| First P247 relative-source compiler attempt | Tool invocation failure: CS1504; absolute resolved source paths corrected it without source changes | Preserve failed command and corrected receipts; no test execution credit |
| PowerShell runner launch | Enforced OS protection: `PSSecurityException`, scripts disabled, before runner execution | Script policy remains intact. Not a C# assertion failure and not authorization to bypass; HOLD |
| Direct generated executable launch | Separate enforced OS protection: Windows Application Control, `ApplicationFailedException`, before test execution | WDAC remains intact; no alternate loading or unsigned execution route. x64 0/54 executed AND x86 0/54 executed; 108 architecture-specific case executions required for one dual-architecture pass; HOLD |
| Runner evidence gaps | Material acceptance gap: immediate build-to-launch, incomplete compiler receipt retention and no independent count parser | External qualified evidence plan required before use, as specified below. No runner repair in P249; HOLD |
| Original P96 check-to-effect race and alternate Python WinCred routes | High unresolved architecture failure: model lock/metadata do not own production effects, old callers or process/restart custody | No repair, integration or independent P96 clearance claimed. Independent architecture/security review outstanding; HOLD |
| Four authentic historical P76 FAIL records | Material unresolved regressions: original public historical admission is refused; later assertions have no coverage credit | Preserve four FAIL/native exit 1 records and guards, without waiver or substitutions. P248 assertions do not close them; HOLD |
| SEC-03/SEC-04 | High missing production principal/store/custody and signed loaded-code/IPC/consent evidence | No service/store/signing decision approved. Production no-go; HOLD |

Under the [failure gate](engineering_failure_review_gate.md), the disposition is
**HOLD for execution, runtime closure, product progression and seal**. Only this
explicitly authorized preparatory decision document can advance. No new tests,
repair or independent review occurred here; no prior issue is waived.

## Proposed environments: explicit independent authorization required

1. **Approved disposable Windows VM.** A qualified security/environment owner
   must approve its provenance, isolation, explicitly documented test execution
   and App Control policy, and explicit synthetic-only unsigned-code test
   permission for these exact sources and binaries. Disposable status alone
   grants no permission. No network, provider, WinCred, real keys, privileged
   service or shared host secrets may be available to the test workload.
2. **Approved signed executable/broker execution chain.** A qualified owner must
   approve the publisher/certificate chain, signer custody, complete compiler,
   script, broker, executable and dependency chain, enforced Code Integrity
   scope and loaded-code attestations. Signing is a separate authorized activity,
   not something P249 performs or implicitly requests permission to perform.
   The unchanged runner builds unsigned binaries; this alternative cannot be
   satisfied merely by signing a prebuilt file that the runner later replaces.
   Any necessary successor orchestration needs a separately approved scope.

These are **PROPOSALS ONLY**, not automatic authorization. Do not lower script
policy or WDAC on Kristian. Do not use policy bypass flags, alternative assembly
loading, an alternate interpreter/loader, untrusted signing or another unsigned
execution route to evade either protection. No explicitly authorized environment
and execution chain means **HOLD**, including when compilation succeeds.

## Strict before-execution checklist

Every item needs a source-bound, dated receipt accepted by independent reviewers
before the first binary starts. Unknown, absent or mismatched evidence means HOLD.

- Qualified owner legal/organizational identity, role, authority, independent
  reviewer identity, approval reference, exact scope, expiry and revocation route.
  Author/self-approval is invalid. Name the operator and evidence custodian.
- VM provenance (image origin/hash, creation record, snapshot and instance ID),
  disposal owner, isolation and host-sharing/network controls. Record physical
  host and guest specs, OS edition/build/patch level, CPU and process/OS
  architectures, x86 support, runtime and PowerShell identity/version.
- Read-only effective PowerShell execution-policy and Code Integrity/App Control
  snapshots, policy IDs/hashes, enforcement/audit mode, applicable event logs and
  timestamps. Approval must explicitly cover the actual script and native chain.
  For a signed chain, retain leaf/intermediate/root certificate identities,
  publisher, thumbprints, validity, timestamp and trust/revocation evaluation,
  dependency manifest and loaded-image enforcement attestations.
- Exact source commit, all four raw SHA-256 values above, clean source-copy
  manifest and custody transfer receipt; rehash after transfer and after runs.
  No normalization, local source edits or additional compilation inputs.
- Compiler full path, file SHA-256, publisher/version and real version output;
  runtime/dependency identities; exact working directory, source arguments,
  `/nologo /target:exe /platform:x64` or `/platform:x86`, and positive
  `/define:C1_REVIEW_ISOLATED_ASSEMBLY,C1_SYNTHETIC_TEST` flags. Preserve exact
  command, separate stdout/stderr and native exit code for every invocation.
- Negative compile without either define for **both x64 and x86**, real nonzero
  compiler exits, explicit CS1029 guard diagnostics for both files and no emitted
  executable. Do not execute a no-flags output. Positive builds must each exit 0.
- SHA-256 and file identity of each actual binary **before launch**, including
  post-signing bytes if applicable. Bind reviewed source, compiler inputs, outputs,
  assembly metadata, architecture and dependency manifest. Inspect source and
  assembly using approved non-executing inspection tooling for unexpected
  entrypoints, P/Invoke, dynamic loading, effect APIs or dependencies. Metadata
  review must not load/execute the target assembly as a workaround.
- Verify synthetic-only data, no real keys, provider or WinCred access and no
  privileged service. Record approved evidence/output directory, ACL/owner,
  bounded execution/termination plan and exact artifact cleanup identities.

**Runner readiness gap:** the original runner does not provide this whole
checklist. It launches immediately after building, emits no pre-launch binary
hash/inspection pause, does not retain compiler version or all compiler streams
and individual exit codes, and does not implement cleanup. Its negative check
requires nonzero exit, absent output and a model guard phrase; independently
verify both files' diagnostics. An owner-approved trusted external orchestration
or launch-admission mechanism must supply the missing pre-launch evidence and
receipts without bypassing policy or altering the four originals. P249 neither
implements nor assumes such a mechanism. If unavailable, stop before running
the runner; a later hash cannot retroactively satisfy a before-execution gate.

## Native procedure: authorized environment only, not executed here

1. Have the environment authorizer and independent evidence reviewer sign off
   the checklist and the exact orchestration/launch chain, including its
   pre-launch inspection gate. Retain immutable approval and source receipts.
   Use a clean evidence directory outside the source copy; record UTC start/end,
   operator, environment/instance identity and command provenance for each step.
2. On the authorized Windows environment, use only its permitted PowerShell and
   installed .NET Framework compilers. The original runner's intended entrypoint
   is below; this is a procedure reference, not an instruction to run on Kristian
   or in P249. No execution-policy override is permitted.

   ```powershell
   & .\tests\p247_effect_free_service_ordering\Run-Isolated.ps1
   ```

   Record the actual host executable/version, full command, all host streams and
   outer process exit. The runner announces `P247_ARTIFACTS=<directory>` and
   iterates x64 then x86 using `%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe`
   and `Framework\v4.0.30319\csc.exe`, respectively. Its positive and negative
   compile command shapes are the exact checklist flags with absolute source
   arguments and `/out:<architecture-specific-path>`. Capture each native
   compiler exit immediately; an outer PowerShell exit does not replace it.
3. Preserve each architecture's guard log, all additional compiler receipts,
   binary and pre-launch SHA/inspection receipt, `*-stdout.log`, `*-stderr.log`,
   native PID/image identity and actual exit. The runner bounds each executable
   to 30 seconds. It prints `P247_x64_NO_FLAGS_REFUSED=PASS` and corresponding
   x86 text only on its guard checks, and `P247_x64_EXIT=0` / x86 only after
   observing native exit 0. Do not infer missing x86 evidence from x64 success.
4. Independently reconcile the **real full native output** for each executable:
   exactly 54 distinct expected case PASS lines, zero FAIL and zero skip,
   `P247 PASSED=54 FAILED=0`, the model-only/P96-open disclaimer, and native
   exit 0. Expected inventory is 18 forced-order + 15 uncertainty + 9
   category/replay + 7 restart + 5 standalone cases = 54. These are loop-expanded
   `Run` cases per architecture, not 54 distinct C# methods. One dual-architecture
   pass requires 108 architecture-specific case executions. The executable
   reports its count and returns 0 only for 54/0; the runner relays stdout but
   does not independently parse counts/names. Review must close this accounting
   gap using raw output.
5. Separate native-launch corroboration of each retained, hash-matched executable
   requires an independently approved orchestration contract for the exact
   permitted native chain. The authorized environment operator must approve the
   actual procedure in a future authorization; this document supplies no launch
   implementation or execution permission. Before any result is given, that
   procedure must separately account for start, the 30-second execution timeout,
   identity verification, any required kill request, and a separately bounded
   wait for termination with final process identity/state verification. Bind
   each step to the approved PID, start time and image path/hash; verify identity
   before termination and retain each step's outcome and timestamps. A kill
   request alone is not proof of termination. Preserve start, timeout, kill,
   wait and identity-verification errors without masking the original failure.
   Retain the actual native exit whenever observed, including after timeout or
   termination and when nonzero; otherwise explicitly log the exit as unavailable
   and why. Never substitute a shell exit, timeout label or invented code for it.
   Missing termination or identity evidence remains HOLD. The same contract
   applies to an approved signed/broker chain and its identified native child.
   Separate x64 and x86 logs and count reconciliation are required. Repeat runs
   do not increase unique case coverage or count as whole-product regressions.
6. The independent reviewer validates raw receipts against source and binary
   hashes, policies, actual commands, architecture and instance identity,
   pre-launch evidence and complete counts. SHA-256 alone is not provenance;
   bind who collected each receipt, when and where, protected retention and
   custody transfers. Only a later explicit P247 runtime acceptance decision
   can credit execution. No sample, fabricated, replayed or substituted synthetic
   PASS logs may replace real output from these intentionally synthetic tests.

## Failure, timeout, revocation and cleanup

Any policy refusal, compilation/inspection failure, assertion failure, missing
stream/count, timeout, approval expiry/revocation or identity drift stops the
procedure's further launches and acceptance; bounded termination and evidence
retention must still follow the independently approved contract in step 5.
Preserve exact command, original exception/diagnostic, native exit
where one exists, host exit, timestamps and architecture reached. If no process
started or native exit was not observable, record that explicitly; never invent
an exit code or PASS. Separate compilation from execution and partial from full
completion. An interrupted attempt counts as no completed acceptance run, even
if earlier PASS lines or one architecture succeeded. Preserve all attempts,
including failed/aborted receipts; do not overwrite them with a retry.

On five minutes without meaningful progress inspect live process/log state and
stop or pivot, preserving checkpoints; each binary still has its stricter
30-second bound. On revocation, prevent further launches and have the authorized
operator terminate only the identified test process under the approved plan.
Record PID, start time, image path/hash, identity checks, kill request outcome,
bounded termination-wait outcome and final process state. Preserve every
termination/verification error and any actual observed native exit, or explicitly
record its unavailability and reason; never use broad process kills. These
receipts must precede any result. Uncertain termination or cleanup remains HOLD.

Before cleanup, retain protected evidence with SHA-256 manifest for logs,
approvals, policy/CI receipts, binaries and sources. The authorized owner records
exact artifact directory/file IDs, ownership, hashes and removal/disposal
receipts, including VM/snapshot identity and any residual process or artifact.
The original runner leaves temporary artifacts behind. Never delete by an
unvalidated path or remove unrelated work. No cleanup or VM action occurs here.

## Independent decisions and risk matrix

| Required independent decision | Qualified accountable reviewer / requested output | Current disposition |
| --- | --- | --- |
| Environment authorization | Security/App Control owner and VM/platform owner, independent of author; named signed approval for exact chain, unsigned synthetic permission if chosen, expiry and revocation | UNISSUED / HOLD |
| P247 runtime acceptance | Independent native validation reviewer and security reviewer; complete x64/x86 source-bound receipts, real 54/0 counts and native exit 0 for each; 108 architecture-specific case executions for one dual-architecture pass | UNISSUED / HOLD; x64 0/54 executed AND x86 0/54 executed; no runtime evidence created |
| P96 architecture/security | Independent architecture and security reviewers tracing original and alternate effect routes, shared ownership, processes and restart custody | OPEN / HOLD; P247 model cannot fix or close P96 |
| SEC-03 / SEC-04 production admission | Qualified principal/store/custody and signing/loaded-code/IPC/consent decision owners | NO-GO pending separate decisions and evidence |

| Risk | Impact | Required containment / next action |
| --- | --- | --- |
| Treat compile success or model metadata as effect authority | High: false runtime or production assurance | Keep compile/runtime/production decisions separate; no production effect admission |
| Evade enforced script/WDAC block | High: unauthorized machine execution | Qualified environment authorization first; otherwise HOLD |
| Hash/inspection after launch or wrong loaded binary | High: source/evidence substitution | Pre-launch identity gate and independent CI/provenance review |
| Missing counts, skipped x86, interrupted run or shell-exit substitution | Material: false acceptance | Complete per-architecture native logs/counts/exits; preserve blockers |
| Infer P96/P76/SEC closure from 54 loop-expanded model cases per architecture | High: cross-phase architecture regression | Independent decisions remain separate; preserve all authentic failures; x64 0/54 executed AND x86 0/54 executed; one dual-architecture pass requires 108 architecture-specific case executions; repeat runs do not increase unique case coverage |

**Qualified Approval Requested:** identify qualified independent owners, select
and explicitly authorize one environment/chain and approve its complete evidence
plan. This request grants no execution permission. Next engineering action is
review of this document and those approvals; absent authorization, remain HOLD.
The author must never self-approve environment, runtime or production admission.
Runtime accounting remains **x64 0/54 executed AND x86 0/54 executed**; one
dual-architecture pass requires **108 architecture-specific case executions**
of the 54 loop-expanded cases per architecture, not 54 distinct C# methods.
Repeat runs do not increase unique case coverage. No runtime evidence has been
created; governance and runtime acceptance remain **HOLD**.

P76 remains **four authentic FAIL**, qualified approvals **0/7**, full native
whole-product regressions **0/3**, **REAL-KEY NO-GO**, **PRODUCTION RELEASE HOLD**.
No claim that P96 is fixed. No executable, policy, service, binary, workflow or
source change; no staging, commit, tag, push, PR publication, credentials,
provider, WinCred or real-key operation. Google Drive workbook/dashboard untouched.

P249 readiness means only that this single document is ready for independent
review. It is not runtime closure, a verified product milestone or a seal.
