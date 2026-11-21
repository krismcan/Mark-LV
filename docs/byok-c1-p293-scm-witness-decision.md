# P293: fake-only SCM lifecycle decision contract

21 November 2026. **NONDEPLOYABLE. REAL-KEY NO-GO. PRODUCTION HOLD.**
Qualified independent security approvals **0/7**; complete accepted product
regressions **0/3**. Codex is the sole implementation writer. Nayeon owns
independent CTO/security review, evidence audit, staging and Git publication.
No product phase, release seal, merge, tag, workbook or dashboard change.

This is authorized development-only investigation of held failure assumptions,
not forward product authorization or a waiver of the engineering failure gate.
A pure fake-only state machine is not a substitute for genuine Windows service
identity/cleanup evidence or a qualified external reviewer decision.

## Custody and exact scope

Pre-edit checkout was clean at branch
`byok-c1-p293-scm-lifecycle-witness-contract-20261121`, HEAD
`7c1b70c041010a19262e7772d0f4782c20542041` (P292-DIAG PR #213).
No tag pointed at HEAD. All **1,189** inherited regular-file raw disk blobs
matched Git object IDs with filters disabled before edits; a separate SHA256
manifest was retained in the author's temporary directory. The inherited
`.codex/CURRENT_STATE.md` starts with stale November 3 Phase 10.2 status.
Git and this explicit task scope control. That file remains unchanged: this
increment neither completes a product phase nor establishes a new baseline.

Exactly five additions, with no inherited modification:

1. `native_c1_successor/P293NonDeployableScmWitnessGate.cs`
2. `tests/p293_scm_witness/P293WitnessTests.cs`
3. `tests/p293_scm_witness/HostedReview.ps1`
4. `.github/workflows/p293-windows-scm-witness-contract.yml`
5. `docs/byok-c1-p293-scm-witness-decision.md`

The future same-repository draft PR must target
`byok-c1-p292-readonly-scm-cim-diagnostic-20261120` at the exact HEAD above.
The published candidate must be exactly one commit with that single direct
parent: 1,189 inherited entries plus five additions = **1,194** entries. Codex
does not stage, commit, push, create a PR, launch a hosted job or publish.
Final raw five-file hashes belong in the author handoff, avoiding a circular
self-pin in this document. Nayeon must independently verify final bytes.

## Open Failures & Prior-Issues Review

Sources: repository engineering failure gate, P291 boundary review, both frozen
P292 review documents and hosted harness, and the user's supplied P292
history and P293 constraints. Hosted findings below are historical supplied
evidence, not a fresh Codex audit of external archives. No root cause or
independent closure is invented.

| Issue / severity / source | Reproduction, cause and affected boundary | Containment, tests, independent review / disposition |
| --- | --- | --- |
| Original P96 HIGH OPEN | Original final StillCurrent/fourth IsOwned check is separated from SAVE/REPLACE/DELETE effect. Revocation may intervene; durable effect/owner/restart custody is unproved. Older Python and native callers remain relevant. | No product import, effect callback or owner exposure here. `REVOCATION_EFFECT_RACE`, `LATE_REVOCATION`, `ALTERNATE_LIVE_EFFECT_ROUTE` refuse fake claims. These do not repair or reproduce the actual concurrent original effect. Qualified atomicity review OPEN; HOLD. |
| P292 FIRST RED 0/6, run 44739845249 | Six create0/restricted-SID0 receipts; start clients time out at eight seconds. Stops1062/delete0 do not prove removal; immediate native absence probes fail. Underlying SCM/service cause unknown. | Original PR #212 unchanged. Fake start timeout, delete0-without-absence and native absence error tests refuse. Actual cause and cleanup closure OPEN; HOLD. |
| P292 SECOND RED 4/6, run 44741869649 | x86 trials1/2 have create0 then immediate metadata failure before restricted-SID configuration. Query failure, missing visibility and mismatch cannot be distinguished retrospectively. Supplied cleanup 6/6 passed. | No claim of missing create receipts or universal CIM delay. Query-error/config-drift adversaries refuse. Independent root cause OPEN; HOLD. |
| P292 THIRD RED 3/6, run 44766866901 | x64 trial1 metadata QUERY_ERROR; x64 trial2 CIM timeout. x86 trial2 create/config/restricted-SID succeeded, start timed out at 40s and native after-absence query timed out. Original x86 teardown **UNVERIFIED**. | Preserve frozen mutable-service HEAD `1083919da53f808105522dd8e11dba9fdf844fa0`. No new mutable-service experiment or cleanup claim. Native timeout and child/retained-handle uncertainty refuse. HIGH missing cleanup evidence; HOLD. |
| P292-DIAG PR #213 stable controls | User supplies six hosted green read-only jobs, **144/144**, at current parent. Stable SCM/CIM observations do not recreate newly created-service start/deletion races. | Preserve all source/CI bytes. No inference of mutable P292 recovery, runtime image provenance or permanent absence. Independent mutable-service closure OPEN; HOLD. |
| SEC03/SEC04 HIGH OPEN | LocalSystem service admission conflicts with proposed virtual account. SCM configured account/image can differ from running image/token. Process PID alone admits reuse/ABA. | Fake exact account/image, independent birth/retained handle and two kernel-token captures required. They are synthetic claims, not principal/installation approval. Qualified account decision OPEN; HOLD. |
| Installed provenance / ACL HIGH OPEN | Signed protected installed image path, SCM ACL, client code provenance and protected service ownership not established. | Exact fake strings do not authenticate executable code, signature or protected paths. No installation/ACL/privilege effect. Qualified decision OPEN; HOLD. |
| Consent / store / restart HIGH OPEN | Protected one-time user-consent broker, service profile/DPAPI/WinCred ownership and restart journal/anchor/effect ordering unresolved. Shared objects, new processes and restarts remain affected. | No consent, account, profile, store, key, user-presence or credential access. Process-local replay reservations do not survive restart. Qualified decisions OPEN; HOLD. |
| P76/P211/P216 acceptance OPEN | Original P76 four failures, P211 test02, P216 test02/test06 and historical native-effect expectations remain unwaived. Alternative Python mutation reachability is unresolved. | No old test rewritten, weakened, skipped as acceptance, or relabelled green. No dispatch integration. Product regressions 0/3; HOLD. |
| Author compiler setup error, this increment | First positive x64/x86 builds returned CS0246 with `/noconfig` and no System.Core reference; second returned CS0012 with System.Core but missing System. Framework reference closure, not SCM behavior. | Explicit System.dll + System.Core.dll in hosted/author compile commands. Preserve failed receipts; rerun both architectures and flag negatives. Compiler results are not executable test results or independent approval. |
| Missing qualified reviews / GOV | Seven independent security decisions and three accepted complete product regressions absent. | 0/7 and 0/3 unchanged. Author self-review is not independent review. REAL-KEY NO-GO / PRODUCTION HOLD. |

Disposition: bounded fake-only source preparation authorized; product,
original P96, P292 mechanism/cleanup and security/release **HOLD**. No open
material issue is downgraded, deferred as low risk, or closed by fake results.

## Decision contract and dependencies

Only the two new C# files compile into the test assembly. They reference
framework types, never product, service or credential libraries. There is no
P/Invoke, unsafe code, native handle acquisition, service creation, account,
process manipulation, network, registry, credential store or file effect in
the model. Its only mutable state is bounded in-memory bookkeeping. The test
entrypoint reads fixed hosted-guard environment fields and writes sanitized
fixed case names/counters to stdout. Host compilation is authorized; local
execution on Kristian is prohibited, even though the model has no OS effects.

`Episode` and `FakeObservation` are sealed immutable data. Every event binds
session, exact service name, boot, generation, source, nonce and expected
name/account/image/principal/restricted-SID subject. An ordinal is consecutive;
fake ticks strictly increase, each gap is at most ten and total span at most
120 synthetic units. These are deterministic fake observation budgets, not a
trusted clock or freshness claim about Windows. Missing data, nulls, unknown
origin/phase, query errors, timeouts, drift, replay and uncertainty refuse.

Episode and nonce reservations are shared across instances within this test
process, never evicted, capped at 4,096 and fail closed on exhaustion. They
cannot establish durable uniqueness, source authenticity or replay protection
across a process restart. A forged fake source can construct coherent claims;
the result still grants zero authority. Nothing accepts an external model
output or deserializes a proof into an effect permission.

The explicit sequence is:

1. Fake native pre-create absence, exactly **1060**.
2. Create response0; uncertain/failed create immediately retains recovery duty.
3. Exact configured name/account/image and restricted service SID.
4. Start response0; 1053, 1069, timeout and all other errors refuse.
5. Fake QueryStatusEx RUNNING with positive PID.
6. Separate fake independent retained process handle and positive birth.
7. Two distinct matching fake kernel token captures, same PID/birth/handle,
   token identity, exact image, virtual principal, restricted service SID and
   no thread impersonation. Duplicate capture or mixed instance refuses.
8. Stop response0, then STOPPED with unused SCM PID0; retained handle/birth
   remain continuous. A STOPPED/PENDING PID never supplies running identity.
9. Delete response0, then all SCM handles closed. Neither is absence.
10. Fake native post-delete absence exactly1060, same retained process handle
    signaled, then exact-image child absence. New process/birth, reopened handle,
    remaining child, CIM-only absence or 1072 refuses.

`InProgress` means incomplete fake data only. `Finish()` on incomplete evidence
is terminal HOLD, or `RecoveryRequired` after create may have occurred. Any
failure is sticky; later coherent data cannot erase it. `RecoveryRequired`
is a label, never an attempted cleanup. Events after coherence invalidate it.
Repeated `Finish()` only reads the completed result; there is no reset/retry.

The only positive name is `FakeDevelopmentSequenceCoherent`. At construction,
each prefix, refusal, completion and replay, **ClientAdmissionAllowed(),
CredentialEffectAllowed(), ApprovedServiceProvenance() and
ProductionReleaseAllowed() always return literal false**. There is no issuer,
authority-bearing object, production approval token or credential effect edge.
Permission -> Policy -> Confirmation -> Execution -> Verification remains a
separate product obligation, with no new route into that chain.

## Windows semantics deliberately not simulated as production proof

[QueryServiceStatusEx](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryservicestatusex)
reports the most recently reported status. Microsoft lists RUNNING and some
pause/continue states as PID-valid; START_PENDING/STOP_PENDING may have invalid
PIDs, and STOPPED never has a valid PID. P293 deliberately accepts only RUNNING
for the fake running evidence. Even RUNNING plus a PID does not prove process
identity, token, code provenance or application authority.

[QueryServiceConfigW](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryserviceconfigw)
may describe the next run after configuration changes during execution.
Configuration does not prove the currently executing image or kernel token.
That is why the separate process/birth/two-token steps cannot be omitted.

[DeleteService](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-deleteservice)
marks deletion. Actual removal requires the service stopped and all service
handles closed. **1072 is deletion-marked, not 1060 absent.** Even a genuine
finite1060/handle-signaled/child-absent sample cannot establish permanent absence
or production execution provenance. No fake test here exercises those APIs.

## Hosted-only evidence and author checks

Both C# files use exactly
`#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P293_FAKE_WITNESS_ONLY && !RELEASE`
with an explicit `#error` otherwise. No unguarded executable or permissive
release/default branch exists. The compiler uses `/noconfig /warn:4
/warnaserror+`, explicit framework references and absolute source paths.
Expected positives are raw exit0; forbidden flag combinations are raw exit1,
only CS1029, and no output executable. Both source guards must fire.

Author checks are compile-only x64/x86, PowerShell AST parse, source/forbidden
API and workflow review, raw Git/disk custody and whitespace checks. No generated
executable, hosted script, original test or Python product regression is run on
Kristian. Compiler failures and any static errors must be retained and reported,
not turned into PASS. Runtime assertions remain unexecuted until publication.

The six disposable `windows-2022` jobs are x64/x86 times three trials, each
bounded to eight minutes. Workflow and script check same repository, draft,
exact base SHA/branches, event head equals checkout, one direct parent, exact
five added paths, 1,194-tree inventory, clean index/disk including ignored
files, and every raw blob. Before/after SHA256 manifests cover **all** sources.
Reparse/link paths refuse. Git and disk drift is HOLD. A skipped/missing job is
missing evidence, not a pass. Frozen checkout/upload action SHAs match P292.

No network download, package restore, external call, service mutation command
or old executable is in the script. The only test program executed is the
new guarded fake-only assembly. Each child has a 15-second deadline, bounded
kill/join and output drain; total work has a 360-second budget within the job
ceiling. Compilation progress is emitted without retries. The five-minute
watchdog requires inspecting a stalled process/log immediately, not extending
the timeout to manufacture a pass.

The script binds exact class names and unique literal case names from the
hashed test source, requires at least40, compares **every** emitted case in
source order, checks raw exit0 and at least1,000 executed assertions. Assertions
check precise HOLD/recovery outcomes, sticky failure, intermediate phase and
all four constant denials; the coherent control must reach completion without
enabling any capability. Missing-step cases cover every sequence prefix.
There are 111 unique literal cases (110 refusal/adversarial cases and one
coherent fake control), with 23 assertion call sites expanded by prefix/denial
helpers. No executed assertion count is claimed by author static review.
Exact case/assertion totals and hashes are delivered in the author report;
hosted counts must come from actual executable output, not source counting.

Only allowlisted text artifacts are uploaded: source SHA256 manifests,
compiler exit/error-code/raw-log-hash receipts, binary before/after hashes,
fixed case labels/counts and summary. Raw compiler logs remain in runner temp;
no binaries, real service names, PID/SID/account observations, exception text,
environment dump or credentials are uploaded. Source path/hash manifests are
repository metadata, not actual Windows identity evidence.

Final author compiler checks: positive x64/x86 raw exits **0/0**, no diagnostics.
All 15 forbidden truth-table combinations of DEBUG/isolated/P293/RELEASE per
architecture (30 total) returned raw exit **1**, CS1029 at both source guards,
and no output executable. This includes no DEBUG, missing isolated, missing
P293, RELEASE, and all flags absent. Final PowerShell AST parse errors **0**;
compiler syntax/type/warning errors **0** in the two allowed builds. Static
action-pin, required workflow literals, four constant-denial bodies, forbidden
C# API scan and additive whitespace checks found no errors. An earlier author
PowerShell diagnostic command had a quoting/parenthesis parse error and was
corrected; this was not a hosted-script or executable test result. No author
static check is represented as independent approval or runtime PASS.

Nayeon must independently review the exact five files and all six future hosted
archives. No fake coherence result closes the original cleanup, revocation,
installation, consent, store, restart, alternate Python route or qualified
review obligations. REAL-KEY NO-GO and PRODUCTION HOLD remain in force.
