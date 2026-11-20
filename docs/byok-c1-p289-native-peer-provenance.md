# P289 native named-pipe peer provenance diagnostic - 20 November 2026

**NONDEPLOYABLE / DIAGNOSTIC_ONLY / RUNTIME NOT RUN / INDEPENDENT REVIEW OPEN.**
Real-key NO-GO; production HOLD. Qualified external approvals **0/7**;
accepted full Windows product regressions **0/3**. Original P96 HIGH remains
OPEN. This candidate provides source and compilation evidence, not OS runtime
evidence, authenticated client issuance, a product milestone or security closure.

## Custody and bounded authorization

Initial read-only inspection confirmed exactly:

- Branch `byok-c1-p289-native-peer-provenance-20261120`.
- HEAD `2e211ca77cc2810e6d571cb647e0e258240c22e0`, P288.
- Parent `3edf7130daa41c2ac240f9a92d6745ac5a726eaa`, P287.
- Clean working tree/index, no tag at HEAD, 1,167 inherited tracked files.

The stale `.codex/CURRENT_STATE.md` describes November 3 Phase 10.2. Git is
authoritative here. The explicit inherited-path freeze prevents context-file
refresh in this diagnostic candidate; no completed-product status is promoted.
The failure gate and relevant P279/P282/P286/P287/P288/P96 sources/reviews were
read first. OM v2.1 requirements are those supplied in the task; no independent
OM sign-off or absent external document was inferred.

Exactly four additive regular paths are proposed:

| Path | Purpose |
| --- | --- |
| `tests/p289_native_peer/NativePeerDiagnostic.cs` | Standalone native kernel experiment and bounded child mode |
| `tests/p289_native_peer/HostedReview.ps1` | Hosted-only exact-source custody, builds, guard negatives, runtime watchdogs |
| `.github/workflows/p289-windows-native-peer-review.yml` | Same-repository DRAFT Windows-2022 x64/x86 three-trial matrix |
| `docs/byok-c1-p289-native-peer-provenance.md` | Audit, limitations, failure ledger, actual evidence and remaining gates |

There is no new source under `nayeon/`, no production reference to P289 and no
compilation with a service/credential/store implementation. All inherited files,
including P267/P271/P282/P286/P287/P288/P96/P76 sources, tests and workflows,
remain frozen. No original endpoint is exercised. Only this worktree and local
temporary compiler evidence are written. No stage, commit, tag, push, merge,
PR creation, workflow launch or workbook/dashboard update is authorized here.
Nayeon owns independent review and publication.

## Open Failures & Prior-Issues Review

Reviewed 2026-11-20. This author cannot issue independent acceptance. The
explicit diagnostic-only task contains existing architectural gaps through
absence of any production call edge; it does not defer or close those gaps.

| Issue / severity / source | Root cause, affected callers, evidence and containment | Tests / independent review / disposition |
| --- | --- | --- |
| Original P96 revoke/effect race / HIGH OPEN; original negative-proof review | Final check and native effect across old coordinator/ledger and alternate callers lack the same trusted, non-reentrant owner. No P289 code invokes those routes or claims process snapshots fix linearization. | Original adversary untouched, not rerun locally. Service-owned ordering/effect/recovery repair and independent review required. HOLD. |
| Trusted live client/message issuer absent / HIGH architecture gap; P287/P288 | Caller SID, PID, session, primary token and synthetic issuer are not authenticated message context. All older live-admission refusal remains unchanged. P289 observations stay private to a standalone EXE. | Native PID/session/token experiment prepared; message token deliberately UNOBSERVED. Independent runtime/source review OPEN. Production HOLD. |
| Executing-service/vault custody absent / HIGH; P279/P282 | Configured SCM principal, running PID/token and own-process observation cannot establish installed image trust or protected service-owned profile/store. Original LocalSystem versus virtual-account policy contradiction and SEC03/04 remain. | No SCM, DPAPI, WinCred, store or service operations added. Qualified decisions, profile/custody and continuity proof required. HOLD. |
| P265/P285 callback crash / historical HIGH development blocker; P286 | Framework may signal its event after caller-side disposal; connect/read/write share ownership defect. P286 callback-owned End/event cleanup contains the development defect. | Unchanged P288 invokes unchanged P287, which invokes unchanged P286 completion suite. Parent P288 PR #208 six hosted successes are user-supplied, not freshly retrieved. P289 inherited builds pass; fresh hosted evidence/independent review OPEN. No production closure. |
| P282 invalid frozen-source-dependent negative / material historical incident | Earlier negative depended on rejected P270 mutation; narrow repair moved the test to the P282/P271 seam. Whole inherited source must remain unchanged across alternate entrypoints. | All old bytes frozen; raw Git/disk identity review required here. No old test weakened or new repair inferred. Broader closure HOLD. |
| P76/P211/P216 original acceptance / unwaived OPEN | Earlier acceptance failures and original direct native Python effect expectations remain unresolved/unwaived. Root-cause and disposition authority stays with original gates. | Not locally executed, altered, downgraded or counted as passing. Acceptance HOLD. |
| Whole-product / external acceptance missing | Focused hosted diagnostics are not qualified external approval or three complete native product regression runs. | 0/7 approvals, 0/3 full regressions, explicit one-use consent and original acceptance still OPEN. HOLD. |
| Hosted child privilege interpretation / CTO decision received | Ordinary child creation inherits runner context and requests no elevation, new account or privilege change. Runner privilege level is **UNVERIFIED** and may be admin-capable. | CTO explicitly selected no elevation/privilege changes; diagnostic may inherit hosted identity, with no non-admin assurance. No restricted-token creation, extra accounts, privilege changes or extra token queries. Scope clarification resolved; no broader isolation claim. |
| Exit-code-based liveness / independent CTO security finding, material diagnostic correctness defect | Initial candidate accepted GetExitCodeProcess == 259, but an exited process may return 259. This could misclassify a terminated child as live; both initial capture and revalidation shared the helper. Initial compile receipt is not evidence of correct liveness. | Same P289 candidate repaired: retained handle requests only QUERY_LIMITED_INFORMATION plus SYNCHRONIZE; zero-timeout WaitForSingleObject == WAIT_TIMEOUT alone is live. Signaled, failed and other results deny. Actual hosted cases prepare exits 0 and 259, assert signaled handle and observation rejection; invalid wait and closed-query-handle negatives added. Fresh static and positive/negative builds required below. Independent finding supplied by CTO; post-repair independent acceptance/runtime OPEN, HOLD for closure. |
| Initial local compile command / tooling error, contained | `/noconfig` invocation omitted System/System.Core/System.Security references. Raw compiler exit 1: CS0234/CS0246, no EXE. This was an orchestration failure, not a failing runtime test. | Original raw log/exit retained. Corrected explicit reference-array command compiled x64 with raw exit 0, then final x86/x64 matrix below. No test or source guard weakened. |
| Local static-review wrapper / tooling error, contained | A direct read-only wrapper used invalid PowerShell operator `-cjoin` and failed at parse time before checks ran. One report-edit patch also failed its exact-context match and changed no bytes. | Corrected wrapper uses parenthesized `-join` with case-sensitive comparison; actual AST, API allowlist and inherited blob checks returned native shell exit 0. Neither incident ran a diagnostic, masked a failed test or changed inherited sources. |
| Native platform behavior / evidence absent | Unconnected peer query semantics, DACL readback, native interop and reconnect scheduling have not executed on Windows-2022 for these bytes. Static analysis cannot manufacture that evidence. | No retries or green claims. Six hosted jobs and Nayeon's independent inspection required. P289 runtime HOLD. |

**Disposition: GO only for the authorized additive diagnostic implementation,
static review and compiler smoke. HOLD for hosted acceptance until independent
review/publication and real runtime evidence; HOLD for all live production
admission, credentials, seals and finding closure.** No low-risk waiver is used.
Five-minute no-progress watchdog: inspect active process/logs and stop/pivot if
stalled; there was no long-running local diagnostic process. Hosted per-process
60s and job 10m bounds are stricter than that watchdog.

## Actor trust and source map

| Actor/source | What is established | What remains untrusted or absent |
| --- | --- | --- |
| P279 `P279RunningServiceTokenReadOnly` | Frozen read-only SCM configuration/status and selected process-token comparison with second SCM observation | SCM snapshots are not a service-execution lease, signed image, protected store or message issuer; all release properties deny |
| P282 `P282ExecutingServiceCustody` | Frozen executing-process primary token, statistics/session and sampled thread-token absence; distinguishes executing process from SCM selection | Diagnostic status and hosted fixture binding never establish service-owned profile/DPAPI/WinCred or production custody |
| P267/P271 development composition | Developer/hosted synthetic actors and development lifetime paths | Environment, current developer SID and synthetic binding cannot become executing-service or authenticated client capabilities |
| P286 `DevelopmentPipeAdapter` and completion tests | Frozen development connect/read/write callback-owned End/event cleanup, deadline/cancellation publication | Lifetime correctness is separate from live role/message trust; no inherited code is replaced here |
| P287 service/client boundary | Frozen separate service/client synthetic issuers, role/SID/SCM/process/token/ACL model; live demand always refuses | No installed executing-service issuer or authenticated live client issuer |
| P288 provenance sequence | Frozen event/ticket/lifetime ordering model; independent service/client/message observations only in private fixture | Synthetic event named peer-authenticated-after-revert is not evidence that any real message token was captured or restored |
| P289 diagnostic parent | Fixed test-owned endpoint handle, ordinary child Process object, minimal query handle, birth time, initial/current primary-token evidence, kernel peer PID/session | Never a service actor; private observations are neither consent nor production admission; host and child deliberately share the disposable account |
| P289 child | Exact same test binary, validated GUID argument, local-only client, fixed one-byte exchanges and own sampled thread-token absence | Parent retains expected process identity; child payload and successful handshake do not authenticate arbitrary clients or messages |
| Model/GUI/wire/environment/caller fixtures | Inputs or accident barriers only | Cannot supply service identity, trusted message token, user-present consent, endpoint bootstrap permission or result verification |
| Nayeon / qualified external reviewers | Independent review and controlled publication remain external gates | Codex source authorship and a hosted green job cannot self-approve production or close 0/7 |

## Endpoint bootstrap and observation sequence

```text
Nayeon review/publication -> actual same-repo DRAFT event, exact parent/head
  -> Windows-2022 disposable job, source/tree/raw-byte proof
  -> separate unchanged P288/P287/P286 focused executable
  -> separate P289 executable (no service/store dependencies)
       own thread: ERROR_NO_TOKEN only; own primary TokenUser/session
       GUID local name + FIRST_PIPE_INSTANCE + max 1 + REJECT_REMOTE_CLIENTS
       create with protected single current-user ACE, explicit owner, noninheritable
       read back actual kernel owner/DACL before any child launch
       create ordinary disposable child of same binary, no elevation request
       retain Process + OpenProcess(QUERY_LIMITED_INFORMATION | SYNCHRONIZE) + birth
       retain primary TOKEN_QUERY handle
       connect exact instance; ready byte from controlled child
       kernel peer PID/session -> expected child PID and process/token session
       process birth/liveness -> managed Process.StartTime + retained birth
       current primary token -> retained token statistics/user/session
       second kernel peer query + birth/liveness + epoch + own thread absence
       fixed ack exchange -> repeat complete observation
       diagnostic cancellation latch -> refusal -> repeat after controlled reset
       command child exit before another snapshot -> liveness refusal
       invalidate epoch -> DisconnectNamedPipe -> no reusable observation
       second child reconnects SAME server instance -> NEW epoch -> stale refusal
       close endpoint -> invalid/closed query checks -> checked handle cleanup
  -> raw exit and bounded identity-free output + source/binary after-hashes
```

Bootstrap is intentionally authorized by this developer diagnostic scope, before
peer evidence exists. This is **not** a production endpoint-creation permission
derived from a peer that has not connected. GUID names are collision avoidance,
not secrets. First-instance creation refuses a pre-existing endpoint. The
current-user-only full-control ACE is disposable object security, not a trusted
service/client-separated ACL; another process under that account is not excluded.
Remote clients are rejected by the pipe mode, and client code accepts only
`\\.\pipe\p289-<32 hex>`; no remote name is accepted. No machine ACL is changed.

The child inherits the hosted account's existing context through ordinary
`Process.Start`; it never requests RunAs, a service/system identity, token
duplication or privilege adjustment. CTO explicitly approved this interpretation
of the bounded child scope. Its privilege level is **UNVERIFIED** and may be
admin-capable. There is no non-admin sandbox or privilege-isolation assurance.

## Native API contracts and their limits

The following are Microsoft API contracts, used as engineering dependencies;
the conclusions about production insufficiency are architectural inferences
from those contracts and the frozen sources, not observed P289 runtime results.

| API/data | Narrow observation | Limit and race |
| --- | --- | --- |
| [GetNamedPipeClientProcessId](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid) / [SessionId](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientsessionid) | Client PID and session from the retained server instance handle | Not an effective thread token, per-message authentication, process image trust or consent; no text supplied by a peer is accepted as this observation |
| [OpenProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess) / [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) | Retained handle with only `0x101000` (PROCESS_QUERY_LIMITED_INFORMATION plus SYNCHRONIZE); creation FILETIME compared with independently obtained managed `Process.StartTime` and repeated while handle retained | Opening a peer PID later alone permits a PID-reuse gap; here expected child Process is already retained. Birth/handle reduce ambiguity, do not atomically bind a message/effect; managed/native views share OS truth and are not independent authorities |
| [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject) | Retained process handle, timeout exactly zero, **only WAIT_TIMEOUT** accepted as live; SYNCHRONIZE is necessary for this query | WAIT_OBJECT_0 means terminated; WAIT_FAILED or any other result denies. No direct GetExitCodeProcess liveness path remains. An exited process returning 259 must still be rejected. No guarantee of liveness after sample |
| [OpenProcessToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocesstoken) / [GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation) | `TOKEN_QUERY=8` only. Actual TokenUser, TokenSessionId, TokenStatistics and independent TokenType; initial token retained, current process token reopened every observation | Primary process token is not connecting/writing thread's effective token; original token handle alone would miss primary-token replacement, so compare current and retained views plus earlier immutable snapshots |
| [TOKEN_STATISTICS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_statistics) | Primary type, TokenId, AuthenticationId, ModifiedId continuity; no identity values leave memory | Statistics are snapshots; sampled equality cannot rule out unsampled ABA or later change, nor prove integrity/image/user intent |
| [OpenThreadToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openthreadtoken) | Own executing parent/child thread queried, TOKEN_QUERY, only ERROR_NO_TOKEN accepted | Access denied, anonymous or other error fails; no fallback to primary identity. Only those sampled test threads, not arbitrary client threads or all times, are covered |
| [Pipe creation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea) / [security](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights) | Fixed max instance, flags, current-user descriptor at creation and actual handle DACL readback | Current-user ACL is not separation from other same-user actors or privileged OS actors; no unauthorized second-user/remote connection is attempted |
| [ConnectNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-connectnamedpipe) | Nonblocking poll accepts connection only on ERROR_PIPE_CONNECTED; explicit disconnect before reuse | NOWAIT is legacy compatibility mode, used only to keep this tiny diagnostic polling bounded. It is not proposed as a production async transport or P286 replacement |

Interop: DWORD/BOOL use 32-bit storage; handles/SID pointer use IntPtr; BOOL
parameters/returns marshal explicitly. SECURITY_ATTRIBUTES is 24 bytes x64,
12 x86. FILETIME combines two DWORDs. TOKEN_STATISTICS is 56 bytes on both,
ModifiedId offset 48; runtime asserts layout. TokenUser has a pointer-sized
SID_AND_ATTRIBUTES header (16/8) with bounded in-buffer SID offset, revision,
subauthority length and 68-byte maximum before conversion. Native variable
buffers are sized by ERROR_INSUFFICIENT_BUFFER, bounded to 4..4096 bytes and
freed in finally. No native identity pointer escapes its live buffer.

Native handles are SafeHandle-owned, checked on explicit disposal via a
cleanup-failure latch; process/token/pipe wrappers, temporary descriptor pin,
query buffers and Process objects have deterministic cleanup. A managed DACL
view uses a non-owning wrapper so it cannot close the retained native pipe.
No OVERLAPPED structures/events/APM callbacks are introduced in P289.

## Adversarial coverage and honest classification

Prepared native/lifecycle cases have a floor of 21 and 50 checks, plus nine
clearly labeled simulated mismatch cases. These numbers are expected source
counts, **not executed results**. Receipt parser refuses wrong architecture,
wrong shape, stderr, nonzero raw exit or missing counts/HOLD statements.

- Actual invalid handle and just-closed handle peer queries must fail. Invalid
  wait returns WAIT_FAILED and fails closed; a closed retained child query
  handle also refuses observation before further process queries.
- Actual newly unconnected handle peer calls are sampled. Receipt reports
  REJECTED or VALUE_WITHOUT_AUTHORITY. No API assumption is invented: application
  evidence is unusable before connected state/epoch even if Windows returns data.
- Two real child processes, each with different PID from the parent, connect
  sequentially to the exact same retained server instance. Stable observations
  run before/after the controlled byte exchange, with native query comparisons.
- Deliberately wrong expected peer PID/session are compared against a fresh
  real kernel query. The kernel is never modified to manufacture this negative.
- Each child exits on the controlled command before the next observation, one
  with exit 0, the other deliberately with **exit 259**. Managed WaitForExit and
  exact exit code must agree, native retained handle must be **signaled**, and
  nonblocking liveness/diagnostic observation must reject both. This is a real
  exit-before-observation case, not an externally killed midway-through-snapshot
  schedule. Native exit failure stays red.
- Diagnostic cancellation latch rejects while connected; controlled reset is
  only for subsequent observations. No claim of CancelIoEx or pending I/O
  cancellation is made. Existing P286 cancellation/callback tests run separately.
- Disconnect invalidates connection epoch before native disconnect. The second
  real connection cannot match the first immutable snapshot. Closed/stale
  snapshots confer no authority. No intentional PID recycling is attempted.
- Pure copied-value mutations: peer PID, peer session, process birth, token
  ModifiedId, TokenId, AuthenticationId, type, token session and epoch. These
  **simulate** mismatches; they do not establish an observed kernel token swap,
  process restart/PID reuse, session transition or impersonation rejection.

Receive/connect/open polling has a four-second operation bound, a forty-second
process elapsed check and 5ms polling pauses. Writes are one byte on nonblocking
64-byte buffers, checked for exact count; no flush/drain can wait for a peer.
The tiny fixed protocol has no credential/provider payload. WaitForExit calls
are bounded (4s normal, 3s teardown). Parent kills only its retained disposable
child on exception/timeout; the child independently times out its own waits.
Hosted PowerShell kills the whole owned test process tree after 60 seconds and
waits 5 seconds; each job has a 10-minute runner teardown bound. There is no
claim that in-process cleanup defeats arbitrary OS hangs or runner failure.

## Primary token versus effective message token

A connected process can have a primary token different from a particular
thread's effective security context. Primary TokenUser/session/statistics plus
peer PID/session cannot identify the security context of a specific write, nor
prove that the account owner consented. Parent and controlled child query their
own thread-token absence only at sampled points. That says nothing about an
untrusted client, another thread, handle transfer, or a later write.

Microsoft distinguishes these contexts in [Impersonation Tokens](https://learn.microsoft.com/en-us/windows/win32/secauthz/impersonation-tokens).
A future named-pipe design could separately propose post-read impersonation
and read-only effective-token capture bound to exact message/connection, then
verified restoration on the same dedicated thread, with strict failure/expiry/
reconnect semantics. Such a design changes thread identity and requires new
approval and privilege/threat review; it is expressly absent and prohibited in
P289. Capture/revert failure must never fall back to service authority or permit
a store/effect. P289 calls no impersonation, RunAsClient, RevertToSelf or token
duplication API.

Alternatively, a separately approved authenticated local protocol/broker could
issue bounded one-use message/operation/connection-bound proof under a reviewed
key/OS custody scheme. It would still need distinct trusted executing-service
and client issuers, framing/replay bounds and user-present consent; choosing a
different transport is not an automatic security fix. Neither option exists
in P289. Repeated observations leave a final observation/use gap and cannot
repair the original P96 revoke/effect linearization defect.

## Hosted custody and execution contract

Only `pull_request` opened/synchronize/reopened, DRAFT, repository/base/head
`krismcan/Mark-LV`, exact P288 base SHA and base branch above, exact P289 head
branch are eligible. Checkout uses **actual event `head.sha`**, never an
invented candidate SHA or the merge ref. Script independently validates event,
runner/image/architecture and HEAD. It requires exactly one commit above P288,
four regular 100644 additions, 1,167 byte-identical inherited tree entries,
1,171 total files, raw disk blob matches and a completely clean checkout.
Do not publish an arbitrary multi-commit or modified-inherited candidate.

Pinned checkout `11bd71901bbe5b1630ceea73d27597364c9af683` and upload
`ea165f8d65b6e75b540449e92b4886f43607fa02`; contents:read only; credentials
not persisted; no submodules/LFS. No package restore/download, external package,
SDK acquisition, provider call or surprise network step is included. The two
pinned Actions and GitHub's checkout/artifact transport are the explicit
publication infrastructure, not test-provider traffic. Compiler is runner's
installed Framework/Framework64 v4.0.30319. Matrix is x64/x86 times three trials;
no retries, fail-fast false. No old workflow is edited or invoked as a script.

Each job builds two EXEs: unchanged P288/P287/P286 test source set with its
unchanged six flags, and standalone P289 with its three flags. All new C# is
guarded by DEBUG, no RELEASE, C1_REVIEW_ISOLATED_ASSEMBLY and
C1_P289_NATIVE_PEER_DIAGNOSTIC_ONLY. Native guard negatives: ALL, RELEASE with
DEBUG, and each missing flag (five); inherited guard negatives retain the eight
P288 cases. Require native raw exit **1**, named CS1029 and no output binary for
each negative, raw **0** plus output file for positive. Compiling with DEBUG
does not itself prevent execution; opt-in flags/environment are accident
barriers, while isolation and lack of integration enforce this scope.

Inherited focused EXE runs first and must retain P286/P287/P288 success receipts,
P288 >=400 cases/>=4000 assertions and all HOLD statements. Failure prevents the
native experiment and leaves the job red. Native EXE then must report only the
bounded diagnostic receipt with no production authority, including the exact
`EXIT_259=REJECTED` liveness line emitted only after the actual exit checks.
Separate raw exit
receipts are mandatory. Source and binary SHA256 are captured and checked after
execution, including failure cleanup. No compiler or runtime failure becomes
success through output redaction.

Only eight explicitly named text artifacts are uploaded: source-before.sha256,
source-after.sha256, compiler.log, compiler-exits.txt, test-binary.sha256,
runtime.exit, runtime.log, scope.log. Compiler artifacts contain literal labels,
raw exits/codes and raw-log hashes; full raw diagnostics stay in the disposable
build directory. Native stdout has only fixed statuses, counts and bitness.
Unexpected output/stderr is not published as raw text. No SID, PID, user name,
LUID, token, endpoint GUID, credential or binary artifact is logged/uploaded.
The source itself is already subject to same-repository draft review, and these
accident barriers do not sandbox a malicious workflow author.

## Actual local evidence and unavailable runtime evidence

Only local Git reads, PowerShell AST/static review, C# compiler smoke and receipt
writes were performed. No generated executable or hosted review script was
executed/dot-sourced/evaluated. No Python/full-product tests were executed;
the task's explicit local prohibition controls the ordinary milestone workflow.
No Windows service, pipe, account, credential, policy, machine ACL or privilege
setting was created/changed locally.

Initial failed orchestration evidence:
`C:\Users\krist\AppData\Local\Temp\nayeon-p289-compile-69f25025ee0c41ba8aeef3e62ae179bb`.
`first.exit`: RAW_EXIT=1, compiler CS0234/CS0246; `references-fixed.exit`:
RAW_EXIT=0. Both raw compiler logs retained; no EXE launched.

Post-CTO-repair warning-as-error compiler matrix (Framework64 x64 / Framework x86):

| Compile entry/guard | x64 raw exit | x86 raw exit |
| --- | --- | --- |
| P289 NativePeerDiagnostic positive | 0 | 0 |
| Inherited ProvenanceSequenceTests positive, includes unchanged P287/P286 | 0 | 0 |
| P289 ALL / RELEASE+DEBUG / missing DEBUG / missing isolated / missing P289 opt-in | 1 each | 1 each |
| Inherited ALL / RELEASE+DEBUG / each of six missing inherited flags | 1 each | 1 each |

Four positive assemblies, 26 expected negative compiler exits 1, named guard
CS1029 diagnostics and no negative output binaries. Compiler inputs SHA256
match before/after. These are **compile results, not test passes**.
Final **post-repair** compiler receipts:
`C:\Users\krist\AppData\Local\Temp\nayeon-p289-repaired-final-f4e3f7f05fbc46d593609c865697d395`.
The earlier pre-CTO-repair compilation directory
`nayeon-p289-final-f23be0997ff443e6a3c06f05c72b1014` remains preserved in the
same Temp parent but is superseded; it must not be used as final source proof.

| Receipt | SHA256 |
| --- | --- |
| raw-exits.txt | BF47966A330B64E04764983401987BB877674730B95C2146ACB031CD03DF2D64 |
| inputs-before.sha256 | FA10B0C83D3F540870D0075492FBEF5B60CD98966BCF1F7C4F13757333E0FD38 |
| binaries.sha256 | DAA03C8A736A0AC54009E4F412F17DAF0BD8381F6D69191DEF1EC22EF8B022EE |

Hosted OS runtime: **NOT_RUN, no raw runtime exit exists, 0/6 trials**. The task
forbids Codex commit/push/PR creation and assigns publication to Nayeon; this
unpublished source has not reached a hosted runner. Do not copy the expected
receipt shape into a purported runtime result. Independent source/runtime
review remains OPEN. Raw final source manifest, inherited-disk proof and AST/
whitespace receipts accompany the final local static review evidence.

Final local static results: hosted PowerShell AST **0 parse errors**; AST literal
comparison confirms inherited six-source/six-flag arrays exactly equal frozen
P288's; exact 19-import P289 native allowlist, no forbidden impersonation/store/
privilege API, all three explicit native waits use zero timeout, no direct
GetExitCodeProcess in C#. All **1,167/1,167** inherited raw disk blobs equal
HEAD. These are bounded static observations, not a security scan or runtime
substitute. Final receipt files are in the post-repair evidence directory above:
`static-review.txt`, `source-final.sha256` (all four additions including this
report), and `inherited-final.sha256` (all inherited paths). The report has no
self-hash; its exact final raw digest is in that external manifest.

## Acceptance before a secure production endpoint / P96 closure

All items remain independent gates; P289 compilation closes none of them.

- Nayeon reviews exact four-path source, interop/layout/cleanup and native API
  scope, verifies the no-elevation/UNVERIFIED privilege contract, publishes the exact same-repo draft;
  all six hosted jobs return genuine source-bound native/inherited receipts,
  including failure/negative evidence. Independently inspect/download artifacts.
- Approve endpoint bootstrap under a distinct installed executing-service
  identity with actual owner/protected DACL, exact installed image/signer/SCM
  policy and retained execution continuity; resolve LocalSystem/virtual-account
  contradiction and SEC03/04. Current disposable-user ACL is not reusable.
- Approve effective client/message identity mechanism and trusted issuer;
  constrain exact connection/message/framing, thread ownership, capture/restoration
  and failure behavior, replay/epoch/expiry, process restart/PID reuse, handle
  transfer, cancellation, reconnect and same-user attacker cases. No primary-
  token-only fallback. Demonstrate adversarial real OS failures under approval.
- Bind trusted user-present one-use consent to exact operation/candidate/session
  and trusted owner, never model/caller booleans. Revalidate at the effect boundary.
- Prove protected service DPAPI/profile/WinCred custody, ACL/handle ownership,
  secret separation, antirollback, crash/restart journal/recovery, no retries
  after possible effects and explicit denial of legacy alternate entrypoints.
- Repair original P96 with common non-reentrant service-owned revoke/final-dispatch
  linearization and required native custody for complete write/terminal lifecycle;
  reproduce original race and prove both orderings across alternate callers,
  callbacks, windows, processes and restarts. No arbitrary callback in final barrier.
- Resolve unwaived original P76/P211/P216 acceptance under qualified authority,
  preserve prior tests/tags, satisfy 0/7 qualified decisions and all three full
  native Windows product regression gates, then separate human release/seal review.
  Real keys, service/store effects and workbook/dashboard remain forbidden until
  the whole BYOK C1 is complete and separately authorized.

Preferred P290: review actual P289 hosted evidence first, then a narrowly approved
effective-message-token/transport RFC with explicit thread/connection ownership
and failure semantics, alongside a distinct executing-service issuer design.
Do not add another synthetic issuer or promote P289 peer evidence to production.
If a required native observation or safe child context is unavailable, retain
HOLD and report the real failure before considering that next scope.
