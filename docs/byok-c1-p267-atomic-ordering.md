# P267 development service-owned atomic ordering

18 November 2026. DEVELOPMENT SYNTHETIC PROOF ONLY. Candidate source, unsealed;
independent review and hosted runtime acceptance pending. P96 original finding
OPEN; P76 HOLD; REAL-KEY NO-GO; PRODUCTION RELEASE HOLD.

## Source identity and bounded scope

Writer checkout: `D:\Nayeon\CODEX_P267_ATOMIC_ORDERING_20261118`, branch
`byok-c1-p267-service-owned-atomic-ordering-20261118`, clean initial HEAD
`08c5cc6d3c3f9b25bd0b9f85b1c515af960a0169` (P266). No milestone tag at HEAD.
Git agrees with the requested parent. `.codex/CURRENT_STATE.md` instead starts
with historical 3 November Phase 10.2 material; preserved without editing.
This is an explicitly authorized development successor, not a product seal.
No separate OM v2.1 document was supplied or found in the bounded root inventory;
no uninspected OM compliance or independent approval is claimed.

Exactly five additions: P267 service, C# harness, Python source/mutation tests,
Windows workflow and this document. No historical source, tests, workflows,
release holds, state file or tags changed. No staging, commit, push, SCM, service
installation/start, signing, package publication or workbook/dashboard update.
The new workflow targets the P266 branch and requires an exact single child of
the pinned P266 parent, exact PR head/base/branch and five additions only. Thus
all historical tracked files must remain unchanged, not just selected pins.
Raw SHA-256 pins additionally freeze P264/P265/P266 and the P96 coordinator and
negative harness. CI records source hashes before/after and text evidence only.

## Open Failures & Prior-Issues Review

| Issue / source | Severity, root cause and impacted route | Containment, evidence and disposition |
| --- | --- | --- |
| Original P96 frozen negative / P250 sections 2-3 | HIGH architectural race: separate-thread revoke after final StillCurrent, before old fake effect. Old coordinator, lease and alternate production routes do not share an owner. | Historical negative remains untouched and OPEN. New owner reproduces the required ordering property with integer submissions only; it does not repair the original or exclude alternate OS callers. Production HOLD. |
| P266 reentrant monitor / separate marker ingress | Material gap for this successor's atomic-dispatch claim: P266 does not implement nonreentrant final submission ordering. | P267 composes only unchanged P265, not the P266 host. One private P267 monitor covers admission, dispatch and lifecycle publication. Reentry latches uncertainty for outer exit. Native adversarial acceptance pending; no closure claim. |
| Restart / process loss | HIGH production missing evidence: no durable intent, anchor, custody tenure or recovery. | New recovery-mode owner denies prepare/old attempts. Explicit fresh fixture is an independent synthetic test universe, never evidence of clean restart or persisted history. Production HOLD. |
| Same SID / P265 peer evidence | HIGH if interpreted as app identity or human consent. | Wire remains fixed denial; no wire path enters prepare or dispatch. Same-SID app trust remains UNTRUSTED. |
| P76 / user handoff, P250 record | Existing original regression failures, unwaived. | Unchanged and not rerun here; P76 HOLD. P266 user-reported x64 4611/x86 4619 assertions, run 44204116636 and draft PR186 are historical context, not P267 evidence. |
| Host validation access | Environment limitation: authoritative Python path access denied. | No install, copy, alternate interpreter or network workaround. Python source tests unexecuted locally; hosted CI required. |

Disposition: GO only for the explicitly authorized synthetic source candidate;
HOLD for runtime acceptance, independent security approval, milestones and release.
No broader failure closure, qualified approval or whole-product regression claim.

## Ownership and linearization

`DevelopmentAtomicService` is sealed and derives from ServiceBase, with a distinct
P267 name. Its executable entry always returns 64; there is no ServiceBase.Run,
installer or SCM path. The harness alone constructs and invokes it in-process.
DEBUG, C1_P267_DEVELOPMENT_ONLY and C1_P265_DEVELOPMENT_ONLY are all mandatory.

One private `sync` monitor protects all mutable owner state. `Enter` explicitly
rejects same-thread reentry before nested admission, lifecycle publication or
submission. It sets only a pending-reentry latch; trusted outer `Exit` publishes
fault plus RecoveryRequired and closes the adapter before releasing the gate.
The test uses reflection to acquire this outer lease; production exposes no
callback, delegate or caller-supplied code inside it. Snapshots grant no authority.
Constructor initialization occurs before publication. All subsequent owner reads
and mutations, including worker completion, enter this same gate. P265 retains
its own unchanged transport-only interlocked cancellation/concurrency guards;
these neither authorize nor serialize synthetic dispatch.

Prepare reserves one process-local object identity and performs no effect. Dispatch
accepts only that exact private reservation once, while started, nonterminal and
not recovering. Within one gate tenure it marks used, MAY_HAVE_EFFECT and
RecoveryRequired BEFORE incrementing the sole hard-coded integer submission
counter. The fixed failure variant throws after increment and keeps fault plus
uncertainty. There are zero sensitive bytes, arbitrary payloads or effect callbacks.
The returned Attempt object is identity evidence only, with no execution method;
a fabricated/cross-owner reference cannot match the owner's reservation.

Revoke, stop, fault and disposal close admission and invalidate the reservation
under the same gate. If a terminal event wins first, dispatch submits zero. If
dispatch wins first, subsequent terminal results remain TOO_LATE/MAY_HAVE_EFFECT
with exactly one synthetic submission and sticky recovery; no clean-cancellation
receipt is issued. No success/verification of a real effect is represented.
Worker faults and cleanup failures also close admission and require recovery.
Transport cancellation happens under the gate; thread join happens outside it,
allowing worker cleanup to acquire the gate. Join has a bounded timeout and throws
on failure. The unchanged P265 ServeOnce runs outside the owner gate because it
blocks on denial traffic and has no route to the synthetic fixture. Capturing its
reference and publishing evidence happen inside the owner gate. Termination
closes/cancels the owned adapter, then joins; endpoint observation becomes null.

No service actual WinCred effect and no durable recovery. No credential API,
provider, journal IO, file/registry store, DPAPI, network client, secret material,
production policy changes or human consent claim. Fixed local named pipes are
the only IPC. This gate cannot police old Python/native routes, another process,
or other owners. New recovery-mode construction retains uncertainty in memory
only; independent fresh fixture construction is explicitly test bootstrap, not
a recovery algorithm or a way to reauthorize the old Attempt.

## Tests and evidence

The native harness uses real unchanged P265 local named-pipe denial traffic for
all four wire opcodes and replay, before and after synthetic dispatch. It checks
fixed denial bytes, no wire submissions, partial-client cancellation for revoke,
stop and fault, malformed-frame fault, idle timeout, lifecycle callbacks and
worker exit. Other cases cover both ordered winners for each terminal event,
actual gate contention, stale/fabricated/cross-owner attempt rejection, replay,
fixed submission exception, nested ingress rejection and recovery-mode restart.
All later terminal attempts remain denied; no release hold is bypassed.

Deterministic winner tests use external events and complete the first operation
on a separate thread before invoking the second: these are state-phase tests,
not a forced preemption inside final submission. Reflection-held gate stress
queues both contenders, confirms both are blocked on the actual monitor, then
releases them. Either winner is valid; the terminal result must agree with the
final count and uncertainty. Monitor fairness is unspecified, so the harness
does not claim deterministic concurrent winner selection. No controlled callback
is inserted into production code. Threads are background with bounded events,
joins and client operations. CI imposes a 40-second whole-process watchdog,
terminates on timeout and treats launch refusal as STOP without another loader.

Local Windows compilation only: x64 and x86 service plus harness compile with
/warn:4 /warnaserror+. For each artifact/architecture all-flags-missing and each
single-flag-missing builds fail with exactly the expected CS1029 diagnostics and
no executable output. These checks use the actual new workflow compile block.
Final compile logs/exit receipts: `C:\Users\krist\AppData\Local\Temp\p267-reviewed-compile-bac6e4d85d6b4422931c51199e514d37` (outside the checkout). No native
executable or test was run on Kristian. The eight Python source/mutation tests
are pending hosted execution because the authoritative interpreter was denied.
Source tests are bounded syntactic canaries, not a semantic/security proof.

The pinned checkout/setup-python/upload-artifact workflow runs both Windows
architectures, repeats compilation and exact negative checks, runs source tests,
and launches only the native test Main with /main selection. It checks exact
native receipt/bitness, raw exit, empty stderr, source hashes and a clean checkout.
Only logs, exit text and JSON hashes are uploaded; no executable or private data.
Hosted runtime results, independent Nayeon review, focused/affected/full product
regressions and any seal remain OPEN. No milestone verification is claimed.
