# P271 durable service integration: development candidate, HOLD

2026-11-18. Exact clean starting branch:
`byok-c1-p271-service-owned-durable-custody-20261118`, parent
`1b9c3d56a942930d059065a05b84b127cf671bfb`. Git and the explicit assignment
supersede stale Phase10 `.codex/CURRENT_STATE.md`; that file is unchanged.
Five additive P271 paths only. No commit, tag, push, PR, workbook or dashboard.

## Actual implementation

`DurableDevelopmentBridge` privately owns the actual P269 composed service and
P270 DPAPI witness. P269 owns the repaired P268 transaction. No old P96
coordinator is constructed or called by this path. The historical source is
compiled for its interfaces and legitimate in-memory fixtures; its negative
proofs and all frozen files remain unchanged. There is no Windows Credential
Manager adapter, secret input, production entrypoint or service installation.

Enrollment must be fresh and P270-consistent. The fixture pair is seeded from
the exact durable readback, never its default fake pair. For Replace/Delete,
the owner first writes a valid prior Save intent/journal, its anchor, terminal
journal and terminal anchor through P270, checking consistency after each pair.
It then seeds synthetic prior presence. This is nonsecret fixture provisioning,
not evidence that an actual prior credential exists. P269's fabricated non-Save
constructor bootstrap is avoided by always creating its Save fixture.

The installed `DevelopmentPendingState.Inject` callback runs synchronously
under P268's existing single gate. It compares fake journal/anchor against
private snapshots AND both actual DPAPI reads on every P268 read and other
callback edge, including presence/trust. The after-journal callback mirrors
the newly accepted fake journal synchronously; the after-anchor callback
mirrors its exact matching anchor synchronously. P270 performs CAS, flush and
decoded readback. The bridge also checks exact readbacks. A partial pair is
allowed only for the uninterrupted journal-to-anchor continuation; every
exception permanently faults the bridge. It never repairs or reenrolls.

Immediately before the fixture effect, the callback verifies enrollment,
trust, expected presence, identical snapshots, P270 non-recovery status,
InspectConsistent, InFlight phase and bound operation. P268 invokes the fixture
immediately after that callback, while retaining its gate. No second
check-then-effect admission gate or lower-level effect call is added. Revoke,
Stop and Fault delegate to actual P269/P268 controls. Returned revoke-first
means zero fixture effects; dispatch-first controls return TooLate with sticky
MayHaveEffect/RecoveryRequired. P268 may conservatively set MayHaveEffect even
when the effect-entry callback refuses and the underlying fixture count is zero.

## Open Failures & Prior-Issues Review

| Issue / evidence reviewed | Severity, cause and affected boundary | Containment, tests, disposition |
| --- | --- | --- |
| Historical P96 post-check revocation negative proofs | High production defect: separate consent check and effect admit a late revocation across callers. | P268 gate owns control and actual fixture invocation; P271 routes exclusively through P269. New revoke-first, effect-first, simultaneous controls and replay cases. Original negatives untouched; production HOLD. |
| P268 fake persistence / P270 disconnected witness | High production gap: fake writes did not establish disk persistence. | P271 synchronous callbacks mirror accepted writes and verify actual durable state before fixture invocation. Both journal/anchor write-refusal adversaries require zero fixture effects. Hosted verification and independent review OPEN. |
| P269 hosted ObjectDisposedException, preserved failure and repair | Harness lifetime bug: APM wait handle disposed before EndRead. | Frozen P269 repair retained. This harness does not perform APM reads; actual service still owns denial-only transport. No historical failure relabelled. |
| P270 hosted runs 44267760065 / 44269213492 and parent owner repair | Material blocker: fresh file owner defaulted to Administrators, exact-SID check correctly refused. | Parent uses CREATE_NEW-only handle ownership provisioning and unconditional readback. P271 does not weaken ACL/owner checks. Fresh hosted x64/x86 proof of that repair remains required; no closure inferred from compilation. |
| Partial writes / damaged history / restarts | High production uncertainty: two files are not an atomic pair; trusted restart authority is missing. | Sticky bridge and witness latches; no rebind/recovery route. Torn, corrupt, missing, extra-entry, exclusive-owner, journal-only and consistent-restart refusals. Independent review OPEN. |
| P271 cleanup ordering found during source review | Material candidate defect: unconditional finally-disposal could release witness handles after a P268 stop timeout while its gate was still held. | Replaced with fault-and-retain on stop failure; only successful stopped cleanup releases witness. New dispose-timeout-retains-custody case asserts actual DPAPI inspection still works before releasing the writer, then zero fixture effects. Compiles; hosted reproduction/repair validation and independent review OPEN. |
| Same-user rollback / service identity | High unresolved production boundary: CurrentUser DPAPI and current-user ACL do not prevent same-user replay or supply independent service authority. | Development isolation, unconditional restart refusal, no real effect port. No antirollback or real service acceptance claim; production HOLD. |
| Local validation environment | Authoritative Python access denied in sandbox; native execution prohibited on Kristian. | Respect refusal; compile-only evidence below. Hosted runtime/Python and full regressions remain OPEN. No installation, policy change or network workaround. |

Dependency audit: P95 codec -> frozen P96 interfaces/fixtures -> repaired P268
gate -> P269 lifecycle -> new P271 callback -> P270 verified stores. Public UI,
legacy MARK, production services, IPC consent and real WinCred remain outside
this route. P269 transport remains denial-only and cannot prepare this ticket.
Permission -> Policy -> Confirmation -> Execution -> Verification remains the
production contract; compiler/environment gates and model output confer none
of those authorities. GO only for explicitly authorized development source
work; acceptance/seal HOLD until independent review and hosted evidence.

## Tests and instructions

The new harness defines **38 cases** across Save/Replace/Delete, control-first
and effect-first, simultaneous revokes, duplicate submissions, write refusal,
injected read/effect failure, snapshot skew, trust/recovery refusal, strict root
ownership/ACL, disk damage and crash/restart. Write-failure cases dispose the
actual witness at after-journal/after-anchor so its actual WriteJournal or
WriteAnchor refuses before P268 invokes the underlying fixture. This proves
propagation of durable API failure, not simulation of a physical disk flush
failure. Fixture write counters may advance before a mirror refusal; the
underlying fixture effect counter must remain zero.

P270 holds both files exclusively. Disk damage cases explicitly release the
witness to model crash, damage journal/anchor, then require both the original
prepared dispatch and a new owner to refuse. They do not claim that Windows
permitted corruption through live exclusive handles. Live extra entries and
snapshot skew exercise checks without releasing handles.

The five Python tests check source contract, red mutations, exact additive
scope/frozen history, runner and pinned workflow. They are static guard tests,
not proof of Windows runtime semantics. Run on an approved host Python:
`python -I -B -m unittest discover -s tests -p test_byok_c1_p271_durable_integration.py -v`.
Do not weaken historical scope guards for this successor or count source
checks as full-product accepted regressions.

The pinned Actions workflow requires one clean P271 child of the exact parent,
only these five additions and the exact branch/base. It builds x64/x86 with
warnings-as-errors and rejects ALL/missing each of seven development guards.
It runs only on GitHub-hosted Windows, with raw exits/text hashes and exact
38-case receipts. No binaries or DPAPI blobs are uploaded. Native code refuses
manual execution absent GITHUB_ACTIONS=true, RUNNER_ENVIRONMENT=github-hosted,
P271_HOSTED_DISPOSABLE=1 and refuses LocalSystem. These are accident barriers,
not authenticated production authority. Never run P271.exe on Kristian.

Every root is a new direct temp child with a random GUID and P270's protected
single current-SID owner/FullControl ACL. Normal cleanup closes service/gate
before witness handles, then deletes only immediate generated files and the
exact root nonrecursively. Failed stop retains durable handles and faults the
bridge; cleanup can retry after the pending gate exits. Threads have bounded waits; the native deadline is
55 seconds and outer watchdog 60 seconds. A hung process exits/kills with HOLD;
the disposable hosted VM handles leftovers after abnormal termination.
Receipts contain fixed case/stage labels and exception type only, no paths,
SIDs, key data, exception messages or ciphertext.

## Validation and remaining acceptance

Local final-source x64 and x86 builds passed, each raw compiler exit **0**,
warnings-as-errors. The exact workflow compile block was also exercised
locally without its runtime block. All **16** negative builds (ALL and each
of seven missing defines, both architectures) returned raw exit **1**, required
guard diagnostics and no executable. No P271 executable was run locally.
Authoritative Python launch failed before interpreter startup (PowerShell
command exit **1**; earlier path probe access denied). Thus **5 Python tests /
50 static mutation probes and 38 native cases are authored, not runtime PASS**.
Python discovery/compileall and full regressions remain unrun. No fallback
interpreter was installed or routed around the sandbox.
Independent source/security review must check callback coverage, partial-pair
continuation, immutable dependency assumptions, lifecycle races and cleanup;
Nayeon owns independent validation/publishing. Hosted x64/x86 execution and
P270 owner-repair evidence remain required. No milestone seal is claimed.

**REAL-KEY NO-GO / P76 HOLD / P96 production HOLD /
0-of-3 full-product accepted regressions.**
