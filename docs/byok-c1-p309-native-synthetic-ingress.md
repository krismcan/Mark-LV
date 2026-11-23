# P309 native synthetic transaction ingress — PRODUCTION HOLD

2026-11-23. Sole source writer: Codex. Worktree:
`D:\Nayeon\CODEX_P309_NATIVE_INGRESS_20261123`. Exact starting branch:
`byok-c1-p309-native-synthetic-request-ingress-20261123`, clean at P308
`d31bd4d129b9ca1599aec7ca495015ca9e85a9eb`. Configured Git author is Kris;
no milestone tag points at that HEAD. Git is authoritative. The existing
`.codex/CURRENT_STATE.md` describes older Phase 10.2 work and is stale for this
task; the explicit six-path scope leaves it unchanged. AGENTS.md and the
mandatory failure review gate were read before implementation.

This is an unsealed source candidate. **Qualified approvals 0/7. Full
regressions 0/3. REAL-KEY NO-GO. PRODUCTION HOLD.** User-reported P308 hosted
x86/x64 Python and Kristian passes are inherited evidence, not rerun or
promoted into P309 acceptance. No stage, commit, push, tag, merge, SCM action,
credential operation, service installation or workbook/dashboard update is
included.

## Purpose and exact trust contract

P304 owns a real C# Windows service and status server. P306/P307 supply a
service-owned metadata transaction owner and typed deny/cancel handlers. P309
connects actual native request IPC to that exact private owner. The only result
is a synthetic refusal. It does not establish authenticated client admission,
consent, a credential store, provider authority or SEC03/04 qualification.

The internal product constructor takes only the exact
`SyntheticTransactionOwner`; the endpoint is fixed to
`NayeonV1ByokCustody.SyntheticDenied.v1`, distinct from P305's status pipe.
There is no public constructor or caller-selected product path. A separate
internal friend-test overload accepts only canonical nonzero UUID names under
`P309.Disposable.`. It uses the identical DACL and implementation. The sole new
friend declaration is `InternalsVisibleTo("P309.ProductService.Tests")` in the
new ingress file. Friend access supports tests; it is not authenticated IPC.

The actual `NamedPipeServerStream` is asynchronous, message mode, duplex,
noninheritable and limited to one instance. Its protected DACL is copied from
P305: process token user SID is owner, NETWORK has FullControl denied, only
that owner SID has ReadWrite allowed. No administrator, interactive-user,
Everyone or authenticated-user allow rule is added. In product composition,
that SID follows both existing restricted service-identity checks. Test
composition uses the ordinary runner's SID without requiring an installed
service. ACL access is an exclusion boundary, not qualified peer admission.

Each service lifetime permits one connection and one request read, with no
reconnect, continuation, retry, queue or dispatcher. The request is exactly
13 bytes in a single complete message:

| Offset | Length | Meaning |
| --- | --- | --- |
| 0 | 4 | ASCII `C1T1` |
| 4 | 8 | Little-endian unsigned RequestId, greater than zero |
| 12 | 1 | Typed operation: 1 Add, 2 Replace, 3 Delete |

The bounded 14-byte read and message-completeness check reject empty, short,
oversized and malformed messages without a second read. Zero IDs and unknown
operations refuse. Empty writes that transfer no message reach the read
deadline; they cannot create a request. No owner token, epoch, secret, target,
endpoint or payload comes from the peer. All owner identity and epoch values
are obtained through `owner.Observe()` inside the service boundary, used to
construct `SyntheticTransactionRequest`, and submitted to `owner.Deny()`.
Only `Allowed == false` and `Disposition == Denied` permit the fixed ASCII
response `C1|DENIED|HOLD|NO_CREDENTIALS`. Replays, cancelled IDs and terminated
owners get no reply. No owner identity/epoch or exception text goes to the
peer. No READY, grant or authorization response exists.

Only the unchanged owner's fixed high-water metadata is retained. There is no
request collection, credential state, pending operation, effect callback,
WinCred, DPAPI, provider, storage or console logging. The operation byte cannot
select code, invoke credential APIs or make the synthetic denial executable.
Model output remains untrusted input; Permission -> Policy -> Confirmation ->
Execution -> Verification is not replaced by successful transport.

## Lifecycle, concurrency and cleanup

`CustodyService.OnStart` creates ingress after both `VerifyExecutingIdentity`
calls and after creating its transaction owner, before `CompleteStart`.
Construction itself does not claim valid SCM dispatch or authorization.
Existing typed P307 handlers and their service-gate behavior remain intact.
The worker calls the owner's independent lock directly; it never calls those
service handlers or acquires the service lifecycle lock. This avoids joining
a worker that is waiting on the same lock held by shutdown.

There is **no idle no-client timeout**. The single asynchronous connection
wait remains pending through quiet startup until a client connects or service
Stop/Shutdown/Fault/Dispose closes ingress. Absence of a client must never
fault the owner or consume the request lifetime. A dedicated cancellation
token is passed to `WaitForConnectionAsync`; close cancels the kernel
overlapped accept and disposes the actual pipe handle before the bounded join.
This uses the framework's cancellation support for asynchronous pipes
([Microsoft API contract](https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.namedpipeserverstream.waitforconnectionasync?view=netframework-4.8)).
Only connected-peer read/write waits have 1000/1000 ms deadlines. On
such a deadline, the owner faults before the actual pipe handle is disposed; the
outstanding OS I/O is awaited to observe cancellation/completion before its
buffer can be released. Delay cancellation runs in `finally`. There is no
abandoned Task.Run or pipe-drain call. A successful denial keeps the connected
handle until owner disposal to preserve buffered reply delivery, but its
worker has finished and never reads another message. There is no background
relistening or second connection.

STOP, SHUTDOWN, startup FAULT and both disposal paths retire the owner first.
Nested try/finally then closes/joins ingress before closing the status pipe,
attempting status cleanup even if ingress cleanup fails. Disposal is
concurrent-safe and repeated calls join the same worker. Join has a 3000 ms
limit; failure propagates as HOLD. Startup and service cleanup exceptions set
`ExitCode = 1`. A worker framing/I/O/identity refusal faults the transaction
owner directly, without an asynchronous SCM-control callback; it cannot
revive a service or authorize an operation. Existing successful startup exit
semantics are retained. The non-managed disposal route now also closes pipe
workers while retaining its existing terminal owner semantics.

Process token SID discovery and no-impersonation checks fail closed, including
an inaccessible/anonymous thread token. Checks repeat after asynchronous
boundaries, before denial output and after writing. P309 does not impersonate
the peer. Termination and denial serialize under the P306 owner lock. If
termination wins, there is no denial reply. If denial wins immediately before
termination, an already buffered fixed HOLD frame may be observed; this
contains no authorization, and closure may discard it. P309 makes no stronger
revocation/effect or peer-authentication claim. OS cancellation behavior and
timing remain subject to the hosted tests and independent review; a deadline
failure is never a passing cleanup result.

## Open Failures & Prior-Issues Review

Dependency review was bounded to the actual service lifecycle, identity
helpers, P305 message pipe/ACL, P306 owner, P307 handlers and inherited tests,
and the latest relevant reviews/workflow. No broad repository scan, live
credential inspection or P308 runtime retread occurred.

| Issue / source / date | Severity, root cause and affected boundary | Reproduced evidence / containment / tests | Independent review / disposition |
| --- | --- | --- | --- |
| P96, inherited task security blocker, 2026-11-23 | HIGH: unrepaired revocation/effect race; original full caller/restart closure not established here | No repair or runtime reproduction claimed. Ingress has no credential/effect port; cancellation/stop tests cover only synthetic owner metadata | No closure or qualification. HOLD |
| P292, inherited task security blocker, 2026-11-23 | UNKNOWN: x86 SCM cleanup root cause unresolved | No SCM install/start/stop permitted; ordinary-user test pipe cleanup cannot resolve SCM cleanup | No downgrade, repair or independent closure. HOLD |
| Missing request ingress, P304–P308 source inspection, 2026-11-23 | Functional ownership gap: no actual request IPC reached the private P306 owner | New server uses the supplied exact owner; actual pipe/denial/high-water tests and post-identity IL checks prepared | Compile-only candidate. Native assertions and independent review pending. HOLD |
| Lifecycle join risk, P309 dependency review, 2026-11-23 | Potential deadlock if a joined worker reentered the service lifecycle lock | Worker uses only owner lock; forced processing under held host lock plus all five retirement routes are covered in new test source | Not a runtime pass. Independent review pending. HOLD |
| Idle accept expiration, CTO corrective review, 2026-11-23 | Material FUNCTIONAL BUG: a fixed 3s connection deadline faulted the owner during normal quiet startup; the absent-peer negative incorrectly required that failure | Original source called `WithDeadline(pipe.WaitForConnectionAsync(), 3000)` and mode 2 expected completion/refusal. Removed idle deadline; explicit cancellable accept preserves single connection, DACL and connected 1s deadlines. Random nonsecret pipe test waits 3600ms, requires ActiveDenied/pending, then exact late-client HOLD. Separate no-client disposal and all service retirement routes require completed cleanup within 3s, closed handle and terminal owner | Local compilation alone cannot close runtime behavior. Hosted adversarial tests and independent review pending. Publication HOLD |
| Targeting-pack absence, local compile inspection, 2026-11-23 | Validation limitation: local v4.8 reference-assembly directory absent | Installed v4 compilers/references used for compile-only checks; hosted workflow builds actual v4.8 project | No substitution for v4.8 build/runtime acceptance. HOLD |
| Admission/consent/store/SEC03/04, inherited design boundary | Required qualified authority and approvals not established | Fixed denial only, service-owner ACL unchanged; no credential path | 0/7 approvals, 0/3 full regressions. PRODUCTION HOLD |

The user authorized this bounded synthetic-only implementation while retaining
these blockers. That authorization closes no finding and supplies no security
seal, regression waiver or real-key approval. Cross-entrypoint, shared-object,
process/restart and historical effect closure remains required for the open
security issues before production progression.

## Tests, workflow and evidence ledger

`P309.ProductService.Tests` compiles against the actual product executable,
never a copied service/owner implementation. It creates only UUID test pipes
under the runner SID. Cases include all three typed operations, little-endian
IDs through UInt64.MaxValue, exact HOLD bytes, OS DACL readback, owner high-water
and replay, wrong magic/operation/size, partial/zero/empty/disconnected peers,
connected silent-peer deadlines, quiet startup beyond 3.5s with a successful
late denial, separate bounded no-client Stop/Dispose, stopped owner, stop-before-start, invalid endpoint
names and same-user thread impersonation refusal. It checks repeat-client and
second-frame refusal, immediate endpoint reuse, closed handles, cancel races,
concurrent stop/disposal, and stop/shutdown/managed disposal/non-managed
disposal/early startup fault in an UNSTARTED reflected service fixture.
Holding the real host lock while processing proves the worker must not
reenter it. No fixture is evidence of valid SCM startup.

Reflection decodes actual product IL to check post-identity construction and
retirement ordering, private ownership, distinct fixed endpoint and absence
of public construction. Project XML must contain exactly six known compile
entries, target v4.8 and warnings-as-errors. An exact allowlist of the existing
seven identity/handle PInvokes rejects added native imports, including secret
APIs. Assertions are prepared source, not executed evidence.

The new Windows-2022 workflow has only a pull_request event, requires a
same-repository DRAFT PR from the exact P309 head branch to the exact P308
base branch and SHA, and checks out the exact PR head SHA using pinned
checkout without persisted credentials. It proves the exact four-add/two-modify
six-path regular-file delta and P308 ancestry. Before/after HEAD, index,
worktree and source/test/AGENTS hashes must match, including on failures.
All output/intermediate artifacts are under RUNNER_TEMP.

The x64/x86 × Debug/Release matrix uses installed MSBuild for the actual
.NET Framework 4.8 project with build/compiler warnings as errors, without
downloads, restores or SDK installation. New P309 plus unchanged P307, P306,
P305 and P304 test assemblies are compiled against that product and all five
are invoked. Each test has a 60-second process deadline, tree kill and bounded
5-second termination confirmation; build and compiler processes are also
bounded. Only test executables run. Inherited P304's negative-context Main
refusal remains unchanged. Product bytes, source SHA, input hashes, test
exits, architecture/configuration and elapsed milliseconds are recorded.
There is no production deployment/mutation event or SCM installation.

| Evidence | Result |
| --- | --- |
| Initial compile-only candidate: product + five test assemblies, four configurations | 24/24 exit 0, zero diagnostics, 4262 ms aggregate; tests subsequently strengthened, final-source compilation recorded below |
| CTO-corrected source local compile-only matrix | 24/24 exit 0, zero diagnostics, 4246 ms aggregate; x64/x86 x Debug/Release, actual product + all five test assemblies; source hashes unchanged during compilation |
| Workflow PowerShell AST / whitespace | Both run blocks parsed, zero errors; tracked and all four added paths passed diff whitespace checks |
| Hosted v4.8 MSBuild / native P309 and inherited runtime matrix | NOT RUN in this task |
| Local generated product/test execution | ZERO; prohibited on Kristian for this task |
| Independent approval / full regressions | 0/7 / 0/3, unchanged |

Local compilation uses the installed architecture-specific
`C:\Windows\Microsoft.NET\Framework[64]\v4.0.30319\csc.exe`, warning level 4,
warnings as errors, exact project source entries, and explicit Debug/Release
symbols, constants and optimization. It checks reference/API shape only;
compiling a test does not verify its assertions. No Python/packages were
installed or invoked and no secret/native credential API was exercised.

Corrective compile log (outside the source worktree):
`C:\Users\krist\AppData\Local\Temp\p309-cto-compile-245d8e5cf9224a87859fb03e9d78a029\compile-only.log`.
SHA-256: `B9D2F891C890A90FF8FF58310BFD2399906C0A51D4BC26A24838A10E026E4ED6`.
Compiled ingress SHA-256:
`D75CD0206F2D4D86F993FB86C730BE68E51DAD283C6E0F67D5109E21B6CE3C9C`;
compiled P309 test source SHA-256:
`A770FE534AE29A73ABB8F4504BD27F3473D3A3344E27B27A1AC0133530C07A15`.
The log pins the document before this evidence-only update; compiled source
bytes are unchanged. No generated executable was run. Hosted CI and
independent corrective review remain pending before publication; this is
source remediation with compile evidence, not a runtime-qualified repair.

Next work, under a separately qualified and approved design, is **actually
enabling authenticated client admission** with explicit consent and lifecycle/
revocation reasoning. It is outside P309 and must retain the outstanding
security HOLDs and SEC03/04 gates. P309 is not permission to connect the desktop
to credential execution or to accept real keys.
