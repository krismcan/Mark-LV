# P272 OS-bound custody admission: executable denial, production HOLD

18 November 2026. Sole writer in
`D:\Nayeon\CODEX_P272_OS_BOUND_CUSTODY_GATE_20261118`, branch
`byok-c1-p272-os-bound-custody-admission-20261118`. Intake HEAD exactly
`bff6895f5f0b4f086f0c4ed97f5f46a44f8d2762`, clean index/worktree, no tag
at HEAD; nearest tag `nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`.
`.codex/CURRENT_STATE.md` is stale Phase 10 history, not BYOK truth. It is
unchanged under the explicit five-addition assignment. No staging, commit,
tag, push, PR, original XLSM, dashboard or historic-source changes.

**GO only for this authorized nondeployable denial increment. Production,
security acceptance, real keys, P96 and P76 remain HOLD.** No qualified
SEC-03/04 account choice or independent rollback authority is manufactured.

## Callable boundary and current P271 connectivity

`OsBoundCustodyAdmission.CreateReadOnly()` creates no bridge, root, file,
listener or service. `AttemptProduction(CustodyOperation)` accepts only the
typed Save/Replace/Delete operation; undefined values return a distinct denial.
It samples real SCM and returns `CustodyAdmissionResult`. All three properties
`ProductionEligible`, `RealKeyEligible`, `MayInvokeWinCred` are literal false
for every outcome. There is no secret, SID, identity, witness, human-consent,
approval boolean, callback or configuration injection port. Exceptions are not
logged by the boundary; native test errors emit fixed case/type labels only.

The result's immutable production-dependency contract explicitly reports
independent monotonic authority and authenticated exact-operation consent as
**NotWired**. Qualified principal, running isolated token/signer, protected
store root and custody freshness are **NotValidated**. This is a requirement
contract, not a fake provider capable of granting acceptance. A future protected
witness must independently authenticate monotonic history across processes,
restarts and rollback, bound to the exact operation and service instance.
A same-user journal/anchor pair, matching digests, enum value or environment
variable supplies neither that witness nor authenticated human consent.

The new owner privately holds the **actual P271 DurableDevelopmentBridge**;
only internal `TestOnlyCreate` can instantiate it, retaining P271's exact
hosted-disposable and non-LocalSystem guards plus the P272 test guard. Its
internal test submission delegates Start/Prepare/Submit to that bridge.
Public production attempts have no call into it, including when the owner
already contains a live synthetic bridge. Tests assert zero fixture effects
before synthetic submission and no additional effects after a denied production
attempt on an already-used owner. P271 remains internal with no public launch
method. No wrapper returns its bridge or tickets. Environment checks are
accident barriers for disposable tests, not authenticated production authority.

The test path remains P271 -> P269 -> P268 -> P270/P95 with the original frozen
P96 interfaces and fixtures. The old `PendingCustodyTransaction` is never
constructed/called by P272; it executes only under its separate preserved
P96 negative-test Main. Source contracts reject a reference to it from the
new boundary. No historical entrypoint is rerouted or repaired incidentally.
This increment supplies a guarded current composition seam, not a deployed
product launcher or universal fence over other existing entrypoints.

## Real OS evidence and deliberate uncertainty

P272 reuses the frozen P261 observer before and after two freshly queried local
`ServiceController.Status` samples. The exact target and derived account come
from `ServiceGate.ServiceName = "NayeonV1ByokCustody"`, hence
`NT SERVICE\NayeonV1ByokCustody`. There is no caller-selected service name.
`ServiceController` supplies the Framework read-only SCM status query; P272
adds no P/Invoke, service control, process opening or image-path logging.

P261 retains its minimum SCM/config rights, bounded 8192-byte size query,
range/alignment/terminator checks, restricted SID policy classification, and
finally cleanup. Missing service is Missing; denied access is Denied; resize,
delete-pending, invalid handle and other query errors are Unverified. No
unbounded retry or malformed-buffer acceptance is added. Its internal parser
rejects restricted-SID values other than 0/1/3 as malformed and rejects 0/1
for restricted configuration. A restricted service SID configuration is **not**
proof of an isolated running token, selected virtual account approval, signed
loaded image or protected storage. No Windows service/account is created.

Changed configuration samples or changed running status yield Changed.
Matching samples remain non-atomic observations: an ABA change, same-name
service replacement, PID reuse, stale configuration versus running token, or
change after observation is not excluded. RunningIdentityProof is always
NotValidated. Missing/denied/malformed/racing evidence cannot promote anything.
Read-only SCM evidence is the strongest honest OS observation available here
without deploying an independently approved service and trusted authority.

## Open Failures & Prior-Issues Review

Read AGENTS.md, the mandatory engineering failure gate, stale state, P261
implementation/tests/review, P268/P269 composition and P270/P271 durable bridge
implementation/latest reviews, original P96 negative driver and workflow,
frozen ServiceGate and native ServiceOwnedAdmissionBoundary. Bounded alternate
route inspection identified `nayeon/brain/local_byok_user_scope.py` and
`nayeon/secrets/windows_credential.py`; they are not imported/executed here.

| Issue / source / severity | Root cause and impacted trust paths | Containment, evidence and disposition |
| --- | --- | --- |
| Account mismatch / P261 and P216 / HIGH OPEN | Frozen service derives `NT SERVICE\NayeonV1ByokCustody`; proposed `NT SERVICE\NayeonByokCustody` is another principal. Candidate service uses the frozen constant. | P272 derives only from the constant. Parser wrong-name negative; qualified SEC-03/04 decision pending. HOLD. |
| LocalSystem conflict / P261, original ServiceGate / HIGH OPEN | Original `EligibleForService` requires LocalSystem; proposed restricted virtual account cannot satisfy that rule. Selecting LocalSystem here would silently contradict the proposed least-privilege architecture. | Neither chosen nor altered. Native LocalSystem/account tests plus frozen P261 source tests reproduce the conflict. HOLD. |
| Independent anti-rollback authority / P270/P271 / HIGH OPEN | CurrentUser DPAPI and two same-user files admit equivocation/replay after handle release. Pair equality cannot establish monotonic epoch or exact-operation authorization across processes/restarts. | Dependency NotWired. New actual DPAPI same-user counterexample rewrites a formerly valid older pair, observes consistency AND recovery-required on reopen, and requires stale bridge enrollment refusal. No fake witness grants authority. HOLD. |
| Human consent/provenance / P96 and P268 / HIGH OPEN | Synthetic ticket identity is not authenticated exact-operation human permission, policy, confirmation or revocation provenance. | Dependency NotWired; no injection port. Environment/parallel-claimant negatives and immutable denial properties. HOLD. |
| Real token/signer and store root / P261/P270 / HIGH OPEN | SCM configuration is not a running service-token, signed loaded-image or protected root ownership/isolation proof. P270 is current-user disposable custody. | Explicit NotValidated dependencies; correct-derived-name/missing-token test. No isolated-token or signer proof claimed. HOLD. |
| Alternate WinCred path / Python local-user routes / HIGH OPEN | New native wrapper cannot protect alternate user-scope credential routes or establish global service ownership across old callers/windows/processes. | No import/call or lower-level effect adapter in this increment. Whole-parent byte boundary preserves old guards; independent end-to-end route review/remediation required before production. HOLD. |
| Original P96 post-check revocation / original 15 negatives / HIGH OPEN | Separate original approval check and later effect permit late revocation. Other callers and old coordinator remain affected. | P272 excludes that coordinator; P268 atomic successor retained. CI separately recompiles/runs original 15-case negative proof, preserving OPEN/HOLD receipts. This does not close the original production defect. |
| P269 APM lifetime, P270 owner and P271 failed-stop cleanup / parent reviews / prior material failures | Disposed wait handle; fresh owner mismatch; releasing witness after failed stop could lose custody. | Parent repairs are immutable. Original P271 38 cases rerun x64/x86 in new CI, including timeout-retains-custody. No earlier source repair or runtime evidence is overwritten. Hosted acceptance and independent review required. |
| P76 and full product / inherited release boundary / HIGH OPEN | P76 remains held; full product has 0/3 accepted current-source regressions. Narrow negatives do not prove architecture/release safety. | P76 untouched; no full-suite, milestone, production or release closure claimed. HOLD. |
| Local validation environment / this increment / verification blocker | Authoritative Python inaccessible; App Control prohibits native execution on Kristian. Initial reduced-input compile also exposed P271 CS0649 under warnings-as-errors. | No interpreter installation/network workaround or native execution. Include unchanged P271 harness to assign its test probe; do not suppress warning. Final builds/guard receipts below. Python and hosted runtime pending. HOLD for acceptance. |

Independent validation/security review is **pending Nayeon** for every new
claim. No unresolved finding is downgraded or waived. User authorized bounded
denial code despite the production HOLD; this is not forward production phase
progress or permission to select an account, install anything or cross a seal.
Permission -> Policy -> Confirmation -> Execution -> Verification remains
required. Model interpretation, SCM evidence and development flags confer no
authority at any step.

## Adversarial validation and CI

The P272 native harness has **17 cases**, including four operation outcomes,
real live missing-service observations before/after, wrong/derived account,
LocalSystem contradiction, malformed buffers and restricted-SID semantics,
denied/resize/deletion/status races, parallel claimants, missing consent and
provenance, environment spoofing, actual P271 ownership and zero-effect denial,
uncertain trust, same-user rollback, stale enrollment, hosted-test refusal and
no-created-service observation. The SCM error/race cases use deterministic
classifiers; malformed config uses allocated parser buffers. They do not claim
to provoke privileged live SCM races on a hosted runner. Only the separate
parameterless observations call real SCM. An unexpected installed service
causes HOLD, never installation, start, deletion or account creation.

The rollback counterexample uses only nonsecret ledger metadata in a newly
generated, protected current-SID temp root. After closing the original witness,
it uses real CurrentUser DPAPI to encode/replay older valid journal/anchor
content with the same entropy. Reopening accepts consistency while preserving
RecoveryRequired. Thus consistent same-user custody is explicitly demonstrated
insufficient; no independent anti-rollback success is asserted. Every disposable
root uses P270's exact prefix/ACL shape, and cleanup deletes only immediate
generated files and the checked direct-temp root, nonrecursively.

Six new Python tests cover source contracts/red mutations, exact five-addition
scope, **all 1094 historical tracked blobs** against the exact P271 parent,
frozen P271 source/adversaries, runtime inventory and workflow/red mutations.
P271's original topology test remains unchanged and is specific to its own
five-file milestone. P272 invokes its four topology-independent tests verbatim;
the new whole-parent byte check proves the successor boundary instead. This is
not a waiver or an assertion that the old topology test passes on P272.

The PR-only workflow accepts one exact clean P272 child of the exact P271 parent
and only the five additions, same repository and expected head branch. It uses
GitHub-hosted `windows-2022` only, pinned checkout/setup-python action commits,
Python 3.12.8, and installed Framework compilers with SHA-256 receipts. x64/x86
builds use warnings-as-errors. ALL defines missing, DEBUG missing, isolated
assembly missing, and each development flag missing must fail with compiler
guard diagnostics and no executable (10 negatives per architecture).

Four separate Main selections compile/run P272 (17), unchanged P271 (38),
unchanged P261 parser/live denial, and original P96 (15 negatives). Both hosted
environment checks apply before any P272 fixture creation. Internal deadlines
are 55 seconds; each launched process has a 60-second watchdog, preserved raw
exit, text output and SHA-256 receipts. Launch refusal has no native process
exit and is recorded as such. There is no retry or App Control bypass. CI
checks every tracked source hash before/after; receipts remain text-only in
Actions logs. No executable or DPAPI blob is uploaded. Native code is never
executed locally. CI is authored, not dispatched or observed in this task.

## Local evidence and remaining external gate

Compile-only evidence is outside the repository at
`%TEMP%\nayeon-p272-compile-20261118`. Initial reduced-input x64/x86 builds each
returned compiler **1**, CS0649 on frozen P271.TestProbe; corrected source list
includes its unchanged harness. No source warning suppression or old-file edit.
The exact workflow build block then compiled all four Main selections for both
architectures, each raw compiler **0**. All 20 compiler guard negatives returned
raw **1**, required CS1029 guard text and no output executable. A final repeat
after the P272 reflection assertions used fresh
`%TEMP%\nayeon-p272-final-compile-20261118` and again returned eight compiler
**0** exits and twenty guard **1** exits; compile orchestration raw **0**.
An attempted repeat in the original output directory stopped with PowerShell
**1** on existing-directory refusal before compilation; the fresh-root pivot
preserves that checkpoint and avoids accepting pre-existing guard outputs.

Authoritative Python failed before interpreter startup: PowerShell raw **1**,
CommandNotFoundException after the path probe was access-denied. There is **no
Python process exit code**, no claimed six-test PASS, no compileall or full-suite
result. The exact error is retained in `python-launch.log`. No fallback Python,
package download, network workaround, credentials or native launch was used.
Python error-log SHA-256:
`1F4878953DE6A34FCA55DDD5FBF7271C5261A425F6B3555CF114D49FA17EEE43`.
Final `git diff --check`, five-file scope and all 1094 parent-blob comparisons
returned raw **0**. All five workflow PowerShell blocks parsed; 30 required
source literals were independently checked in PowerShell (not a Python PASS).
No-index checks against NUL return raw **1** for the expected new-file delta
with zero whitespace diagnostics; an initial shell check wrongly treated that
normal difference exit as a whitespace error, then explicitly checked both the
raw code and empty diagnostics. No source/test requirement was weakened.
The final evidence directory contains a text `receipts.sha256` manifest for
source, compiler outputs, raw compile/guard exits and the retained Python error.

External acceptance requires independently observed hosted x64/x86 negatives
(including preserved P271 receipts), Python source checks, independent source
and security review, then the qualified principal decision, real deployed
service-token/signer and protected-root evidence, an independent protected
monotonic authority and authenticated exact-operation human consent. Global
alternate-route/P96/P76 closure and 3 accepted full-product regressions remain
separate requirements. **Production cannot be enabled by flipping a P272 flag**:
there is no authority-granting branch or real-key port to enable. This increment
implements the strongest honest executable denial seam within the approved
read-only/nondeployable scope, not original P96 production-security closure.
