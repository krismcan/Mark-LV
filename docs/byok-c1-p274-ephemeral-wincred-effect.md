# P274: actual ephemeral WinCred effect timing under frozen P268

Nayeon v1 / Mark-LII BYOK C1, OM v2.1. Date: 2026-11-18.
DEVELOPMENT-ONLY CANDIDATE. Hosted execution and independent review PENDING.
Overall disposition: HOLD for verified OS timing, production and release.

Source parent: `9546228e5c726a46a3bf91ba05793f38c23d686f` (P273).
Branch: `byok-c1-p274-real-os-effect-gate-20261118`.
Intended publication: a same-repository DRAFT pull request in
`krismcan/Mark-LV` targeting `byok-c1-p273-current-p76-admission-20261118`,
with that exact base and a single direct child as its head. Nayeon owns
independent review and publication. No staging, commit, tag, push or PR here.

Exactly five additive paths: this report, the P274 workflow, the P274 C#
helper and harness, and `tests/test_byok_c1_p274_ephemeral_effect.py`.
All inherited files, original P96/P268/P273 and existing tests remain unchanged.
The old `.codex/CURRENT_STATE.md` describes historical Phase 10 work; Git is
authoritative for this isolated candidate. That file remains unchanged under
the explicit five-addition scope. This is no new sealed product milestone.

## Bounded native experiment

[P134](byok-c1-p134-ephemeral-native-wincred-interoperability.md) provides the
synthetic-only disposable hosted-profile precedent. P274 goes beyond P268's
fake effect counters: its test-only helper P/Invokes actual Windows
`CredWriteW`, `CredReadW`, `CredDeleteW` and `CredFree`. No other native
entrypoints are imported. It never enumerates credentials. Its only target is
an internally created `Nayeon.P274.Disposable.<GuidN>`; no caller can select a
target or provide arbitrary data. The only payload is literal nonsecret
`0x31 0x32 0x33 0x34`, or null for Delete. Generic credentials use
`CRED_PERSIST_SESSION=1`, in the disposable hosted runner's current-user
logon profile. This is neither a production target nor a service vault.

Before ownership is established the constructor reads only its fresh target
and demands absence. A collision fails without write/delete or cleanup of
that target. Readback checks the exact target, username ownership marker,
generic type, session persistence, four-byte size and fixed bytes. Every
allocated native read buffer is freed in `finally`; the write buffer is
cleared and freed. Read failures other than ERROR_NOT_FOUND fail the test.
There is no logging of blob contents, keys, account names or event JSON.

Replace and Delete require a synthetic seed in that same initially absent,
owned target. Every seed is logged as `P274_SETUP_SEED_NOT_TERMINAL`, checked
through genuine CredReadW, and excluded from gated terminal-effect counts.
Replace deliberately writes the same fixed marker: native success plus
readback proves a bounded call occurred; value inequality is not claimed.

Each owned target has a `using`/`finally` cleanup after success or failure.
Cleanup reads and validates ownership before deleting, and re-reads absence
even if delete fails. A mismatched credential is refused without deletion.
Any cleanup/readback error fails; none is waived. CI checks unique initial
and cleanup target receipts match exactly. A killed/crashed process cannot
guarantee managed finally cleanup; a watchdog timeout is HOLD, never PASS,
and the hosted VM/profile must be discarded. No cleanup retry or real-user
recovery tool is introduced.

## Actual trust-path placement and tests

The assembly compiles unchanged P95 `CustodyLedger`, original P96
`PendingCustodyTransaction`, `P96StateFixture`, `P96GuardFixture`, and P268
`DevelopmentPendingState` / `ServiceOwnedPendingTransaction`. P268's frozen
33-case harness is compiled and run separately without modification.
The original coordinator is compiled for its types/fixtures and its separate
15-case NEGATIVE executable; P274 never constructs the original coordinator.

The OS terminal operation executes synchronously inside the frozen
`DevelopmentPendingState.Inject("effect-enter")` callback. The unchanged
P268 path has already consumed its development ticket, written and verified
both InFlight records, performed its final barrier and latched
`mayHaveEffect=true`, while holding its single private admission gate. The
test reads the exact private gate/latch through reflection solely to assert
ownership and timing; it never changes those fields or acquires that gate.
Native effect and genuine readback finish before the callback returns to
the unchanged fixture mutation. No unrelated native mutation is performed
after `Apply` returns. Post-return observations are readback only.

There are 30 top-level P274 cases per architecture:

- Three negative groups: pure host/event refusals, pure invalid payload/op
  refusals, and five real-P268 admission negatives with zero OS mutations.
- For each SAVE/REPLACE/DELETE and Revoke/Stop/Fault, control-first commits on
  a separate bounded thread before Apply. Zero gated native effects, zero
  fixture effects and zero ledger writes are required. Replace/Delete retain
  only their documented setup seed until cleanup. Frozen P268 Fault-first
  returns `RecoveryRequired`, not `Faulted`; this behavior is preserved.
- For each operation/control, effect-first rendezvous holds the actual
  callback under the P268 gate. The control thread cannot complete before
  OS mutation/readback, later returns `TooLate`, and possible-effect plus
  recovery uncertainty stay sticky. Terminal ledger/readback and original
  fixture lease disposal are checked, together with no replay/rearm.
- For every operation/control, a successful native call and genuine readback
  are followed by a deliberate exception in the callback. Apply must return
  `RecoveryRequired`, retain InFlight, dispose/fault its original lease,
  never write a terminal pair or retry the native effect. In these cases
  the native mutation has happened while the original fixture counter is
  still zero: fake counters are explicitly not the native-effect evidence.

Expected per successful P274 architecture run: 30 case receipts, 32 unique
initially absent targets with 32 matching cleanup receipts, 18 documented
setup seeds and 18 gated native success/readback receipts. Every approval
observer remains unused as authority. Only P268's development-issued,
object-bound one-use ticket admits this test path. No trusted consent claim.

The source-only Python module has eight tests: frozen SHA-256/source binding,
helper, callback driver and workflow contracts, three causal mutation groups,
and Python syntax/negative syntax checking without execution. It imports only
the standard library and cannot load native APIs or launch executables.
These are bounded lexical/source checks, not semantic proof or independent
review. C# warning-as-error compilation is the actual C# syntax check.

## Execution confinement and residual limits

Both P274 C# files require DEBUG, C1_P268_DEVELOPMENT_ONLY and
C1_P274_EPHEMERAL_WINCRED_ONLY. Every missing flag and the all-missing build
must fail with exactly the expected CS1029 diagnostics and no output exe.
There is no production factory, native service, IPC endpoint or installer.
The frozen P268 production/issuer properties remain literal false.

The workflow uses `pull_request`, never a privileged target event. It admits
only the exact same-repository draft P274 branch, exact P273 base SHA and
direct child PR head, checks actual event JSON, all five additions and
regular-file modes, clean source and frozen parent SHA-256s, before building
with pinned checkout/setup-python/upload-artifact actions. Jobs use
GitHub-hosted `windows-2022`, x64 Framework64 and x86 Framework
`v4.0.30319/csc.exe`, `/noconfig /debug+ /optimize- /warn:4 /warnaserror+`.
Original 15 P96 negatives, 33 P268 fake cases and 30 P274 OS timing cases
have distinct executables, raw exit/logs and receipt requirements.

Native execution additionally checks Windows, `RUNNER_ENVIRONMENT`, Actions
and PR variables, exact repository/branches/base/head, explicit disposable
opt-in and non-LocalSystem/non-impersonated identity. The native helper
independently parses bounded actual GitHub event JSON (262144-byte/character
bound, recursion 32), verifies draft/same-repo endpoints and PR number/ref,
and rejects event symlinks and event paths outside runner temp. It checks
this context before creating targets and again on each exposed operation.
The launcher clears its child environment and supplies only the explicit
Windows/profile/event variables; it supplies no token, provider secret or
credential payload. Runtime has a 60-second watchdog and no retries.

Workflow and environment checks are accidental-misuse controls, NOT
hostile-runner cryptographic attestation. A hostile same-user process can
forge environment/event inputs, alter code, or race Credential Manager.
WinCred offers no create-if-absent atomic reservation here: random fresh
GUID plus absence/ownership checks bounds normal collision risk but cannot
exclude a malicious same-user writer between read and write/delete. P274
claims no OS isolation from that actor, trusted runner attestation, atomic
native cancellation, durable protected journal, crash/rollback resistance,
or cross-account/service-principal safety. Hosted load that exceeds P268's
frozen 500ms gate wait is a failure with sticky uncertainty, not a reason
to widen the gate or retry. Neither environment flags nor synthetic tickets
authorize any production operation.

The code makes no network/provider call. CI infrastructure necessarily
checks out source, sets up Python and uploads TEXT evidence; the native
experiment itself has no network interface. Artifacts allow only `.log`,
`.exit` and `.json`, record SHA-256, and never distribute EXEs/PDBs or secrets.
No WinCred API or newly built native EXE may execute on Kristian.

## Open Failures & Prior-Issues Review

Reviewed AGENTS.md and engineering failure gate before implementation;
P96 original source/15 negatives, P268 source/33 tests/review, P134 actual
synthetic hosted example, P216 owner-decision RFC and P273 current admission
source/workflow/tests. The bounded experiment is explicitly authorized;
no forward production phase, historical repair, seal or external GO is inferred.

| Issue / source / date | Severity, root cause and affected paths | Containment, reproduction and evidence | Independent review / disposition |
|---|---|---|---|
| Original P96 check/effect race; P96 frozen proof | HIGH: independent caller approval can revoke in final ownership getter before original SAVE/REPLACE/DELETE | Original source unchanged; separate 15-case expected-vulnerable proof must reproduce. P274 uses actual frozen P268 service gate, never original Apply | Original/prod HOLD; P274 cannot close it |
| P268 fake-only effect evidence; 2026-11-18 | Material evidence gap: real managed fake calls/counters do not establish OS timing | Real WinCred in exact effect-enter callback; verified InFlight, runtime gate/latch observations, control/effect ordering and throw-after-native adversaries | Hosted evidence and separate source review PENDING; timing HOLD |
| Partial journal/anchor, callback, timeout and uncertain native outcome; P268 | HIGH: journal, anchor and WinCred are not one atomic transaction; callback/reentry and delayed control can fault | Frozen P268 barriers/timeouts unchanged; retain 33 original tests, add actual OS then throw cases and no-retry proof. Same objects/gate/lease, no bypass route | No durable store/restart/rollback closure; production HOLD |
| Synthetic target collision or cleanup failure; P134/P274 | HIGH containment requirement: wrong ownership or uncertain process exit could affect state | Fresh random namespace, absence before ownership, no enumeration, fixed payload, exact readback, finally cleanup and final absence. Collision never deleted. Hard kill cleanup is unproved | Successful receipt required per target; any failure HOLD, disposable runner only |
| Service principal/store/IPC/consent; P216 2026-11-14 | HIGH unapproved architecture: existing user-scope routes and new service store are not isolated by a flag or counter | No service account, ACL/security policy, signing, DPAPI adapter or production target changed. P216 source decisions remain unissued; this test user profile proves none of them | Qualified Windows security/policy owner missing; HOLD |
| P76 original four modern FAIL; P273 parent | Material governance failures remain unwaived; current source admission is not old evidence closure | P273 source/workflow/tests frozen, no invented GO, no source test weakening | P76 original FAIL remain OPEN; HOLD |
| Stale context and local Python availability; 2026-11-18 | Environment/handoff mismatch, not a runtime PASS | Exact clean requested branch/parent verified. Inherited state untouched; no Python invocation, override, install, copy or network workaround | Hosted Python tests PENDING; no independent result claimed |
| Local additive whitespace receipt checker; 2026-11-18 | LOW tooling defect: wrapper incorrectly demanded exit 0 from a new-file `git diff --no-index --check`; raw exit was 1 with zero diagnostics | No source defect or change. Corrected checker accepts diff exits 0/1 only with zero diagnostics; ordinary diff still requires 0. Raw reproduction in external `checker-incident.log`; repeated complete static check exited 0 | Local checker incident closed; no native/Python credit or independent GO |

Dependency trace: development ticket -> P268 gate/one-use admission ->
original P95 intent pair -> frozen P268 callback -> P274 private owned-target
native helper -> genuine readback -> original fixture -> P95 terminal pair
-> original lease dispose -> control returns. Failure keeps recovery/no retry.
Legacy P96 and P132/P133 alternate user-scope paths are not made safe or
retired by this test. Cross-process/restart ownership and authenticated IPC
are explicitly outside this disposable single-process experiment.

## Current validation and restart point

Local x64 and x86 C# warning-as-error COMPILE ONLY builds exited 0 using the
approved .NET Framework compilers. No executable was launched. Build logs
and raw exits are outside the checkout in `%TEMP%\P274-compile-only-20261118`.
Separate original P96 and P268 x64/x86 compile-only builds also exited 0.
Eight missing-flag/all-missing builds rejected with exit 1 and only their
expected CS1029 diagnostics (10/4/4/2 per architecture); none produced an EXE.
All five workflow PowerShell blocks parsed with the PowerShell language
parser without execution. Ten frozen SHA-256 pins match. PowerShell checks
matched the source contracts' required helper/driver/workflow witnesses;
these checks are not execution of the eight Python test methods. Tracked
and additive whitespace checks passed. Local raw compile logs/exits have
`evidence-sha256.log` in that same external evidence directory.
All 1,104 inherited files independently matched their raw Git blob SHA-1
framing; index modes/OIDs/stages exactly matched HEAD, every index entry had
ordinary H flags, and the only source delta was the five untracked additions.
`final-static.log` and `final-source-hashes.json` retain the local static
receipt and final five-file SHA-256 inventory outside the checkout.
Authoritative Python is unavailable as specified: no local Python tests,
full product discovery or compileall were attempted. No hosted run occurred
in this authoring session. Hosted test evidence and independent review remain
PENDING. No external reviewer GO is claimed.

P96 original/prod HOLD. P76 original four modern FAIL remain unwaived.
Service principal, authenticated IPC, service-user DPAPI, antirollback and
trusted consent remain unapproved. Qualified owner missing. Full-product
regressions **0/3**. Real keys **NO-GO**. No provider/C2, service installation,
native Kristian execution, security-policy changes or production mutation.
Google master workbook and dashboard unchanged.

Next: Nayeon independently reviews the exact five source additions, publishes
only if appropriate as the bounded draft, and examines both hosted native
architecture receipts and cleanup/source hashes. Failed/missing evidence is
HOLD; there is no fake-only fallback or permission to promote this candidate.
