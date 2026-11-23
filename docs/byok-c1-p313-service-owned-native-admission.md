# P313: service-owned admission around actual P312 native Add

Date: 2026-11-23. SOURCE CANDIDATE; hosted evidence PENDING; production HOLD.
Operating Model v2.1: Codex sole source writer; independent Nayeon review and
publication remain external to this task. No staging, commit, push, merge, tag,
workbook or dashboard update.

Exact starting branch: `byok-c1-p313-service-owned-vault-admission-20261123`.
Clean P312 parent: `d980c4ef7de118a685c245e4dd915d1d9fe8ca1a`.
P312 hosted run `45232721811`, draft PR #231, x86/x64 Debug/Release 4/4 PASS
is user-supplied inherited evidence, not a P313 result. The inherited P312
review still says pending; its frozen bytes are intentionally not rewritten.
The cross-branch `.codex/CURRENT_STATE.md` is stale; Git is authoritative and
the explicit six-path scope excludes updating that historical handoff.

## Bounded composition and linearization

The actual service assembly includes a new partial adapter source with nested
`HostedDisposableWinCred.ServiceOwnedAdmission`. The only original adapter
changes are `partial`, a readonly P313 session bit, and the host-gate choice.
P312's four native imports, native write/read/delete/free methods, synthetic
ALPHA/BETA bytes, cleanup, zeroization and original hosted validation are intact.
The project adds exactly one compile entry. No non-adapter product caller or
public factory is introduced; nested owner types retain the frozen P312 IL
inventory's original adapter-family topology.

A private marker constructor validates the canonical nonempty UUID before OS
access, validates the actual P313 host context, binds process SID and disposable
P312-prefixed target, checks native structure layout, and checks absence under
the existing shared Writer lock. Only the nested owner calls this constructor.
The owner also admits actual context before allocating its test event handles.
The friend test cannot select a target prefix, credential type, payload, native
adapter, arbitrary effect delegate, production operation or callback.

One private owner monitor covers Issue, Revoke, Stop, Fault, Dispatch, actual
`vault.Add()`/`vault.Verify()` and Dispose. Approval is a service-created opaque
object identity, usable only once for this owner's single fixed ALPHA Add.
No caller-provided StillCurrent predicate or approval interface is consulted.
The private P313 constructor is not an assertion of trusted user consent.

| First owner-gate winner | Result and subsequent behavior |
| --- | --- |
| Revoke / Stop / Fault before dispatch | Terminal Revoked / Stopped / Faulted; approval removed; Dispatch refuses; no Add and no possible-effect flag |
| Dispatch | Approval consumed; terminal, MayHaveEffect and RecoveryRequired set BEFORE actual Add; native Add and readback remain inside monitor |
| Control after dispatch entry | TooLate, including after success, fault or disposal; never successful cancellation |
| Bounded 2-second gate wait expires | HoldUnknown for a control; atomic fault request; never a cancellation claim |
| Recursive monitor entry | Refusal and sticky fault request; the outer route cannot ignore it and admit a later dispatch |
| Failure or native uncertainty | Terminal, no replay; possible-effect/recovery flags never cleared; Dispose attempts verified native cleanup |

There is no READY, retry, recovery-clear, real-key eligibility or restart admission
API. Invalid/null/foreign approval also terminates this owner. Repeated issuance
is refused without replacing its existing approval. Dispose retries only cleanup,
never Add; an unsuccessful cleanup is an incident and cannot produce PASS.
The original Writer remains nested inside the owner monitor and is never changed.
There is no callback into the owner from the adapter and no inverted lock route.
Native calls are synchronous and are not preempted by the monitor timeout;
the hosted outer process deadline bounds a hung test, with cleanup then unproven.

The fixed test rendezvous is a private ManualResetEvent pair, not an arbitrary
callback. A paused dispatch signals just before Add while holding its monitor;
a separate Windows thread signals attempted control and waits. Normal tests
release after a bounded observation before the gate timeout and demand TooLate.
The separate timeout adversary waits for HoldUnknown, releases dispatch, and
requires its fault latch to refuse Add with conservative sticky uncertainty.
Both paths have bounded joins and a 5-second pause deadline.

## Hosted-only brakes and evidence contract

RequireHostedP313 reads actual process environment and a real event file. The pure
ValidateContextP313 helper accepts synthetic dictionaries/JSON only for read-only
predicate tests; its return is never passed as authorization to a constructor.
Environment requires exact GITHUB_ACTIONS=true, RUNNER_OS=Windows,
RUNNER_ENVIRONMENT=github-hosted, GITHUB_EVENT_NAME=pull_request,
GITHUB_REPOSITORY=krismcan/Mark-LV, fixed P313 head and P312 base branches,
and P313_SYNTHETIC_HOSTED_ONLY=1. The draft PR must bind checkout Git HEAD to
PR head SHA and the fixed P312 base SHA. Root/head/base must all name the exact
repository with ID 1402212689 and equal boolean fork values. The real repository
itself has fork=true; same-repository does not mean fork=false.

The event file must be a regular nonreparse file below RUNNER_TEMP, strictly
smaller than 64 KB, decoded strictly and parsed with bounded JSON recursion.
Process SID must not be LocalSystem and the existing process-token/no-impersonation
checks apply at construction and every adapter effect/cleanup gate. Environment
brakes, unsigned friend names and PR metadata are test restrictions, not principal
or signing authentication. Nonhosted/missing flags refuse. P312's old gate and
constructor caller identity remain unchanged.

The Windows-2022 hosted workflow uses pinned checkout of exact PR head, an exact
six-path delta, regular-file/source SHA256 receipts, frozen P312 source/test
witnesses, exact allowed adapter/project transformations, and clean Git before
and after execution. Installed MSBuild builds actual .NET 4.8 product with
warnings as errors for x64/x86 Debug/Release. Matching installed CSC compiles
both friends against that product; no source-copy substitute assembly is used.
There are no downloads, service installation, production pipe commands, provider
requests, real keys, user credentials or AppControl bypass.

Each native friend run is capped at 90 seconds with 8192-byte per-stream capture.
Nonzero exit, unexpected stderr/output, timeout, dirty source or changed binaries
fails. P312.ProductVault.Tests.exe --readonly runs unmodified without any P312
hosted flag and must pass its original topology. Only the P313 friend performs
new native effects. Neither friend nor service Main is executed locally.

The P313 friend covers environment/event/ID/repository negatives; all three
control-first outcomes; null, fabricated and foreign approvals; replay;
nonreentry; all three dispatch-first controls; bounded lock timeout; successful
actual Add collision/readback; and a controlled cleanup-gate withdrawal/restoration
incident. Every operated UUID is checked absent by a fresh nested owner invoking
the real outer constructor after disposal. Control-first zero-effect evidence
combines the guarded source path, false possible-effect state and fresh absence;
absence alone is not a historical native-call trace. No targets, values or SIDs
are printed. PASS requires cleanup/absence assertions and a bounded counter.

Hard kill, runner loss or identity loss may prevent cleanup. A failed run is not
proof of deletion: retain source/binary hashes and bounded nonsecret logs, mark
the cleanup incident, retire the disposable runner/session and request review.
No automatic retry converts that incident into PASS.

## Open Failures & Prior-Issues Review

| Issue / source | Severity, root cause and affected boundary | Repair / evidence / independent review | Disposition |
| --- | --- | --- | --- |
| Original P96 negative | HIGH: last StillCurrent check races independent revocation before original Save/Replace/Delete interface dispatch | Frozen expected-vulnerable original unchanged; P313 composes a new monitor directly around actual hosted Add only; adversarial hosted evidence pending; independent review pending | P96 HIGH OPEN; production HOLD |
| P268 architecture | Gate must cover service-issued approval and effect, no arbitrary callback beyond barrier; uncertainty forbids replay | Same-gate native Add, sticky flags, bounded timeout and explicit recursion refusal; no fake counter substituted for effect | Bounded source candidate only; no cross-process/durable closure |
| P312 first event guard | Same-repository fork incorrectly assumed fork=false; original hosted attempt failed before checkout | Frozen P312 correction inherited; P313 checks exact ID/name and matching boolean flags; user reports corrected P312 4/4 PASS | Contained inherited guard error; P313 runtime pending |
| P313 initial local compile | Duplicate private RegularPath definition from partial extraction, compile error CS0111; no native execution | Removed duplicate, reused original helper; subsequent four combinations compiled; final source rebuild recorded below | Compile defect repaired; no runtime inference |
| P292 x86 SCM teardown | UNKNOWN root cause/evidence; ordinary hosted process cannot establish SCM lifecycle safety | No SCM launch, install or teardown route added; original lifecycle sources frozen | UNKNOWN; production HOLD |
| Crash / restart / authority | HIGH missing durable protected IN_FLIGHT journal, authenticated human consent, service principal/ACL and code integrity/signing | Explicitly excluded; no durable journal or production authority claimed; no restarted-session safety proof | OPEN; real key NO-GO |
| Qualification / full regression | SEC03/04 approvals 0/7; whole-product regressions 0/3 | No hosted synthetic result substitutes for qualified review or full product runs | HOLD |

GO applies only to the explicitly authorized synthetic source implementation and
compile-only handoff. Hosted behavior, independent source review, production
integration, security closure and release remain HOLD. Original P96 after-revoke
effect flaw is frozen and remains OPEN. No policy/confirmation/audit/undo gate is
bypassed or represented as supplied by an LLM, host flag or synthetic approval.

## Local validation and restart point

Local CSC warning-as-error compile-only validation uses the actual project
source/reference list and builds service plus both friends for x64/x86
Debug/Release. No EXE was launched. Workflow PowerShell blocks receive AST parse
checks only; this is not YAML-engine or GitHub runtime proof. Final receipts and
bounded static results are recorded after the final source build below.

Next: independent Nayeon reviews the six final paths and compile/static receipts,
then publishes the exact draft through its separately authorized process.
Hosted P313 matrix and original P312 --readonly result remain PENDING.
No security closure, milestone seal, full-product regression or workbook update.

Final local receipts (compile-only, 2026-11-23):
- x64 Debug/Release and x86 Debug/Release: actual service source list plus frozen
  P312 friend and new P313 friend all compile with /warn:4 /warnaserror+, exit 0.
- Logs and binary SHA256 receipts:
  `C:\Users\krist\AppData\Local\Temp\P313-final-compile-58b4b22d00e94984a0009840aab4dcc1`.
- Exact adapter three-change transformation and single project compile addition
  match the P312 Git witness. Nine remaining frozen P312/service witnesses match.
- Exactly six paths, empty index, tracked and additive whitespace checks pass.
- Both workflow PowerShell blocks parse; no native test, Python suite, full
  regression, local service launch or GitHub workflow was executed by Codex.
- The first duplicate-helper compile failure remains disclosed above; no test or
  P312 validation was weakened to repair it. All final C# combinations rebuilt.
