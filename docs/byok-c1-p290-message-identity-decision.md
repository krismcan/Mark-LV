# P290 message-token observation and installed-service trust decision

20 November 2026. **NONDEPLOYABLE DISPOSABLE DIAGNOSTIC. RUNTIME NOT RUN.
INDEPENDENT AUDIT OPEN. REAL-KEY NO-GO. PRODUCTION RELEASE HOLD.**
Qualified approvals **0/7**; accepted full-product Windows regressions **0/3**.
Original P96 HIGH OPEN. A hosted diagnostic PASS would change none of these.

## Decision and unresolved engineering question

**Conditional production candidate: authenticated local Windows RPC (`ncalrpc`,
the supported local RPC interface over the local transport), with explicit
per-call authorization and a separately protected installed client/consent
broker.** Use the supported RPC/SSPI security interfaces, not a custom raw ALPC
authentication protocol. This is a decision for qualified external review,
not an implementation approval or claim that RPC authenticates application code.

The missing property is an issuer that can distinguish a trusted installed
client and its one-use user-present approval from a hostile process running as
the same interactive account. Neither P289 connection provenance nor P290's
message token supplies that property. Authentication of a Windows account is
necessary evidence; it is insufficient application authentication. If a supported
protected broker/key/isolation boundary cannot be demonstrated against that
same-user adversary, **this candidate is NO-GO**. Do not substitute a SID match,
signature/path snapshot, random pipe name or developer-created capability.

P290 resolves a smaller, real OS question through an experiment ready for hosted
execution: can an exact successful message read, on a retained local server
handle, yield an actual **identification-level impersonation token**, followed
by checked reversion and no residual thread token? There is no positive local
runtime evidence yet. The source deliberately cannot perform a credential,
provider or service effect and cannot issue a production admission object.

| Alternative | Useful property | Missing property / decision |
| --- | --- | --- |
| Named pipe connection PID/session + primary process token (P289) | Diagnostic link to the retained expected child and sampled process lifetime | Does not observe the writing thread's message security context; PID reuse, delegated handles and later changes remain. Insufficient. |
| Named pipe last-read token (P290) | Windows supplies the context associated with the last message read; identification permits identity inspection | Custom framing, exclusive read-to-capture ownership, per-message capture and cleanup must be correct. Still no executable authenticity, delegation resistance or consent. Retain as bounded diagnostic; not selected alone for production. |
| Supported authenticated local RPC / ALPC transport / SSPI | Runtime-supported call framing and authentication; explicit application authorization remains required | Account authentication is not code identity or user presence. Select conditionally with protected broker, request proof, service custody and qualified review. No raw ALPC implementation proposed. |
| Custom pipe + custom SSPI protocol | Could authenticate a security principal and protect a transcript | Adds protocol, downgrade, sequencing, mutual-authentication and recovery responsibilities without solving same-user application trust. Reject as the default here. |

Microsoft documents RPC authentication as a runtime facility and documents
`ncalrpc` as always using packet privacy; that does not imply executable or
consent authenticity. This candidate still requires explicit authentication
service/principal verification, interface security, locality, per-call checks
and qualified validation of the chosen runtime configuration.
[RPC security](https://learn.microsoft.com/en-us/windows/win32/rpc/security),
[authentication levels](https://learn.microsoft.com/en-us/windows/win32/rpc/authentication-level-constants),
[protocol sequences](https://learn.microsoft.com/en-us/windows/win32/rpc/protocol-sequence-constants).
The choice and required broker protections are architectural inferences, not
guarantees asserted by those pages.

## Custody, scope and restart mismatch

Read-only initial Git evidence: clean index/worktree; branch
`byok-c1-p290-message-token-observation-20261120`; exact HEAD
`c3bb2f16303cfc9bcaa04539dffbc8c7a971e958`; no tag at HEAD; **1,171** inherited
regular blobs. User reports P289 DRAFT PR #209 and six hosted successes. Those
are inherited reports, not independently retrieved or rerun P290 evidence.

`.codex/CURRENT_STATE.md` still starts with the November 3 Phase 10.2 candidate.
Git is authoritative for this isolated worktree. The explicit inherited freeze
precludes refreshing that file. This is an engineering diagnostic increment,
not a completed product phase or a promoted regression baseline. Exactly four
additions are maintained; no scope deviation:

- `tests/p290_message_identity/MessageTokenDiagnostic.cs`
- `tests/p290_message_identity/HostedReview.ps1`
- `.github/workflows/p290-windows-message-identity-review.yml`
- `docs/byok-c1-p290-message-identity-decision.md`

Codex is the sole implementation writer. Nayeon independently audits, commits,
publishes the draft and reviews evidence. No delegated agents, stage, commit,
tag, push, PR, hosted launch or workbook/dashboard mutation was performed.
OM v2.1 constraints applied are the instructions supplied with this task;
no absent external manual or independent sign-off is inferred.

## Open Failures & Prior-Issues Review

Reviewed 2026-11-20 before implementation: the failure gate, P289 source/harness
and review, P288/P287 boundaries, P281 principal/store decision, P216 store RFC,
and P96 original race report/source. Evidence below is historical unless marked
as current compile/static evidence. No original security failure is waived.

| Issue / severity / source | Cause, evidence and affected paths/callers | Containment / owner / review / disposition |
| --- | --- | --- |
| Original P96 revoke/effect race / HIGH OPEN; original P96 review | `PendingCustodyTransaction.Apply` checks `StillCurrent`, then `lease.IsOwned`, then SAVE/REPLACE/DELETE effect interfaces without the same trusted revocation/effect owner. Historical deterministic fourth lease probe lets another thread revoke before the fake effect still runs. | Original coordinator, ledger, alternate dispatch/recovery callers remain frozen; no P290 call edge to them. Service owner must prove common non-reentrant ordering, journal and actual effect ownership. Original adversary not rerun here; independent closure OPEN. Production HOLD. |
| Live authenticated application/message issuer / HIGH OPEN; P287-P289 | Connection PID/session and primary-token snapshots do not bind the current writer's message context or trusted code. P287 live admission refuses. P288's synthetic issuer cannot authorize live work. | P290 private token snapshots are identity diagnostics only. No production constructor/admission consumer. Qualified IPC/broker owner and independent security review required. HOLD. |
| Service principal and SEC03/04 custody / HIGH OPEN; P281/P216 | Frozen service name is `NayeonV1ByokCustody` and original gate requires LocalSystem; P216 proposed a different name and virtual principal. Installed image, ACL, profile, store and monotonic recovery custody are unproved. | No SCM/profile/store/DPAPI/WinCred calls or startup gate change. Security/install owner must resolve principal contract and protected execution/custody. External SEC03/04 OPEN. HOLD. |
| P76/P211/P216 historical acceptance / unwaived OPEN | P281 records original P76 four failures, P211 test02 and P216 test02/test06; retired direct Python native-credential expectations are unresolved acceptance debt, not permission to weaken tests. Broader root-cause/closure evidence is not established here. | Frozen source unchanged, not executed locally and not represented as passing. Original acceptance owners retain disposition; independent qualified acceptance required. HOLD. |
| P265/P285 completion/event disposal incident / historical HIGH | Caller disposal could precede Framework event signaling on connect/read/write. P286 callback owns End/event cleanup. Shared async paths matter even though P290 intentionally has no async server path. | Unchanged P288 -> P287 -> P286 suite remains in hosted review. No old fix is recopied or downgraded. Fresh runtime evidence OPEN, owner Nayeon. Diagnostic compile only. |
| P282 frozen negative dependency incident / material historical finding | Negative previously depended on rejected P270 mutation; narrow repair moved it to the P282/P271 seam. Frozen-source assumptions can hide alternate routes. | All 1,171 inherited blobs/raw disk files must match before/after; no old assertion or entrypoint changed. Independent broader closure not inferred. |
| P289 exit-259 liveness / material prior diagnostic defect | `GetExitCodeProcess == 259` could classify an exited child as live. P289 repaired shared capture/revalidation to use zero-timeout wait on a retained SYNCHRONIZE handle. | P289 source/executable unchanged; hosted exact output must include original EXIT_259 refusal and actual raw zero exit. P290 child identity uses the retained Process plus pipe PID only diagnostically. Nayeon reviews new hosted result; not a P96 repair. |
| Last-read/stale token and failed-impersonation fallback / HIGH if admitted | Cached connection/message context can outlive a request. On impersonation failure server identity persists; continuing a protected request would be confused-deputy behavior. | Fresh exact read, exclusive synchronous owner, bounded read expiry, one attempt, one-use observations, sequence/epoch invalidation; invalid native handle must fail impersonation itself. Failed observation terminates request. No effect route exists. Hosted evidence and independent audit OPEN. |
| Failed reversion / fatal security condition | Continuing after failed `RevertToSelf` could leak client identity into later work. A green normal path cannot prove the fatal branch actually executed. | Nested finally closes token then always reverts; false reversion calls `Environment.FailFast` immediately. No injected reversion failure or real-key test authorized. Static branch checked; qualified external fault-injection/review still required. |
| Same-user child / privilege assumption | Host and child deliberately share account and logon. Ordinary child creation can inherit an administrator-capable runner. SID/AuthId agreement is not separation. | PRIVILEGE LEVEL UNVERIFIED. No elevation/account/token adjustment. Never claim non-admin sandbox, different-user denial, trusted client code or consent. |
| Local compiler orchestration / contained tooling failure | First compiler invocation passed relative slash-separated source paths: raw exit 1, CS1504, no EXE. Corrected invocation resolves source paths, as hosted harness does. | Failure receipt preserved in local temp directory ending `084529`; subsequent matrix ending `084601`: 6 positive exit0, 36 expected guard exit1/CS1029. No test ran. Later source edits require final new-source compilation below. |
| Pre-runtime author static corrections / contained source defects | Workflow transformation accidentally changed its base-branch filter; output-flag edit was initially placed before its local declaration. Final review also required the preparatory reversion call to use FailFast on false, exactly like the capture finally. Caught by source inspection before final builds or publication. | Corrected only new paths. Exact branch comparisons and final compile repeated below. No hosted success inferred; Nayeon independent audit OPEN. |
| Static wrapper classification / contained tooling errors | A forbidden-word scan matched `async` in a comment, not an API; a whitespace wrapper initially treated no-index diff exit1 (added-file differences) as a whitespace failure despite zero diagnostics. | Read-only wrappers corrected to scan code excluding comments and require zero whitespace diagnostics with the documented difference exit. No source prohibition weakened or native test executed. Final static checks below; independent audit OPEN. |
| External/product acceptance / HIGH missing evidence | Focused hosted diagnostics cannot replace GOV01/02, SEC03/04, REL05/06/07 approvals or three complete native Windows product regressions. | Approval **0/7**, full product regression **0/3**. Owner: qualified external reviewers and Nayeon. REAL-KEY NO-GO / PRODUCTION RELEASE HOLD. |

**GO only for authorized isolated source, static/AST review and compiler smoke.
HOLD for runtime acceptance, architecture admission, security closure and any
product seal.** No low-risk deferral or independent author self-approval is used.
Five-minute meaningful-progress watchdog applies; local compiler invocations
complete within seconds, with failures inspected immediately. Hosted limits are
60 seconds per EXE and 10 minutes per job; no retries to bend OS behavior green.

## Windows contracts and precise limits

The server API takes its context from the **last message read**, not a supplied
PID, payload identity or the current primary process token. A false return leaves
the process identity in use. Therefore a failed attempt ends that request,
regardless of what the server's own token could do.
[ImpersonateNamedPipeClient](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-impersonatenamedpipeclient).

Identification-level SQOS permits inspecting the client's security information;
it does not grant the ability to use other services as that client. The child
passes `SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION` (`0x00110000`) when
opening the local pipe. The captured token must independently report
`TokenType=TokenImpersonation` and `TokenImpersonationLevel=SecurityIdentification`,
also agreeing with TokenStatistics. Anonymous, impersonation and delegation
levels are rejected; no privilege or protected-effect attempt tests these limits.
[Impersonation levels](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-security_impersonation_level),
[CreateFile SQOS](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

If reversion fails, execution under the client context is unsafe. The mandatory
response here is immediate `Environment.FailFast`, never catch-and-continue.
[RevertToSelf](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-reverttoself).
This source contains the fatal branch; P290 does not claim runtime fault-injection
coverage for a reversion failure.

The pipe uses message type/read mode, nonblocking bounded polling, remote-client
rejection, first-instance guard and one instance. NOWAIT is a disposable diagnostic
choice, not a replacement for P286 async ownership. An explicit protected
current-user-only FullControl ACE and owner are set at object creation and
read back on the retained handle; no machine ACL changes. FullControl here is
not a production least-rights or service-separated DACL.
[Pipe creation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea).

## Actual hosted experiment and last-read ownership

One GUID-named local pipe instance is reused through **two sequential
connections**, each with one short-lived child of this same standalone EXE.
There is never more than one child or server reader in this experiment. The
GUID is collision avoidance, not a secret. The retained child Process and
kernel client PID are compared before and after positive capture, but this
comparison is diagnostic only; it is not delegated-handle or application proof.

```text
own synchronous main thread: ERROR_NO_TOKEN -> own primary-token baseline
  -> explicit private pipe creation and kernel owner/DACL readback
  -> ordinary same-EXE Process.Start, no elevation/account/privilege change
  -> connect expected retained child; no-read observation DENIED
  -> queued bytes peeked but not consumed: observation DENIED
  -> read exact one-byte complete message on exact retained server handle
  -> bytes alone: no diagnostic acceptance without a token observation
  -> consume fresh-read slot BEFORE attempting capture (no reentrant caller)
  -> narrow native window on SAME thread / SAME handle / LAST READ:
       ImpersonateNamedPipeClient -> OpenThreadToken(TOKEN_QUERY, OpenAsSelf)
       -> TokenUser, TokenStatistics/AuthId, Session, Type, ImpersonationLevel
       -> CloseHandle(token) in finally -> RevertToSelf in nested finally
       -> false revert: immediate FailFast; no later code
  -> own ERROR_NO_TOKEN -> parse bounded buffers -> strict type/level checks
  -> expiry + retained-child/PID recheck -> private DIAGNOSTIC observation only
  -> consume once; missing new read cannot capture cached context
  -> repeat for messages 2/3; sequence, expiry, cancellation negatives
  -> message 4: real read expiry (round 1), invalid native handle (round 2)
  -> terminal denial; own no-thread-token assertion; fixed teardown ACK only
  -> child exit/cleanup -> invalidate epoch BEFORE DisconnectNamedPipe
  -> reconnect gives new epoch; prior policy fixture rejected
```

Every native positive capture follows a new exact message read. Payloads are
fixed test bytes, not credentials, claimed identities or commands. Reads request
two bytes in message mode and accept exactly one with successful completion;
partial/oversize/incorrect/error frames fail closed. No further read, concurrent
server callback, await, thread-pool scheduling or protected action occurs between
read and capture. The read slot expires in two seconds, checked before and after
capture; consuming evidence also checks its epoch, sequence and both deadlines.
Immediate second capture without a fresh read returns no observation; the test
deliberately does not depend on undocumented unconnected/cached-context behavior.

Buffers are stack-allocated and pointers prepared before impersonation. The
window contains only primitive branches/assignments and native impersonation,
token-query, close and reversion calls. No managed parsing, allocation, framework
helper, logging, file access, service/provider callout or callback runs there.
Native query/close/thread-token entrypoints are used beforehand; reversion is
also resolved under the original identity before the first attempt. The CLR and
P/Invoke remain runtime dependencies; this is not a general CLR isolation proof.
An exception still crosses the nested finally; no token-query/close failure can
skip reversion. Parsing and all managed output follow successful reversion.

Interop asserts SECURITY_ATTRIBUTES 24/12 bytes and TOKEN_STATISTICS 56 bytes,
ModifiedId offset 48. TokenUser SID pointer/offset/length/revision are bounded
inside the returned live buffer before copying. No SID, PID, GUID, username or
authentication LUID is logged. Snapshot token handles close before parsing and
never escape capture. All native failures or unknown layouts yield HOLD.

Six real successful token captures are expected, each identification-level.
They compare SID, session and AuthId with the host baseline **only diagnostically**.
An invalid `-1` handle is separately tested and again substituted into a fresh
request; the actual impersonation return must be false, not merely a later
query failure. A terminal request cannot use the server's primary token as a
fallback. The only post-denial pipe write is a fixed teardown ACK, after checked
reversion, with no application request/effect dispatch reachable.

Expiry and cancellation are policy tests, not OS token mutation claims. Expiry
at the observation deadline burns that observation even if a later fixture
supplies an earlier clock value. Clearing a cancellation fixture cannot unburn
it. Two explicit copies of real diagnostic evidence test stale sequence and
reconnect epoch predicates in isolation; these are **policy fixtures**, not
additional native identity captures or proof of changed users. A real 2.1-second
own-identity wait tests stale-read denial before native capture.

The experiment cannot establish a different user, independent trusted process
issuer, code integrity, elevation distinction, non-admin isolation, user-present
consent or a production service identity. Same-user hostile apps, injected or
borrowed handles, deliberate delegation, alternate writing threads, PID reuse,
restart/ABA and arbitrary application payload binding remain beyond this proof.
Same-account AuthId agreement demonstrates no independent application authenticity.
Because every writer here shares the account/logon, the experiment cannot
distinguish a changed writer security context from a cached identical context.
`LAST_READ=ORDERED` describes strict API/read ordering; it does not claim an
experimentally observed cross-identity token transition. Last-read semantics
remain the cited Windows contract, not an invented stronger OS guarantee.

## Production candidate: required issuer, bootstrap and effect ownership

These are acceptance obligations, not new production code or permission to
install anything in this task.

1. **Bootstrap A: establish the service independently of any client.** A signed,
   versioned installer and qualified administrator-controlled policy must bind
   the canonical SCM service name to the approved principal, own-process image,
   publisher/version and protected install path. Verify actual executing process
   token, SCM configuration/status, service SID, process-handle/birth continuity,
   restricted rights, service-object security and protected binary/config/update
   ACL ownership. Neither the model, caller-supplied SID, environment nor a client
   handshake can authorize service bootstrap. Resolve P281's LocalSystem versus
   `NT SERVICE\NayeonV1ByokCustody` conflict through SEC03; do not flip the old gate.
2. **Bootstrap B: bind a fixed trusted client issuer.** Provision an independently
   protected consent broker with a fixed approved principal/package, installed
   image/publisher/version and supported isolation/process-access policy. Its
   request-signing key must be inaccessible to unrelated same-user apps and the
   untrusted UI/model. A user-writable executable plus Authenticode check is
   insufficient against replacement, injection or reuse. Do not use an ordinary
   user-profile key accessible to the same-user adversary as application proof.
   If the OS cannot supply the required isolation/attestation, reject the design.
3. **Mutual endpoint and per-request binding.** Client independently verifies the
   installed executing service; service verifies the fixed client issuer and
   account/logon/session/role. Use an explicitly configured local-only RPC
   interface, authenticated principal and authorization per call. Bind both
   endpoint identities, service boot epoch, connection/channel transcript,
   immutable request ID, operation/target, candidate digest/version and nonce in
   a broker-signed proof and service-signed, short-lived one-use receipt. A
   service signature alone does not turn a caller assertion into consent.
4. **Preserve binding on every message/call.** For any retained pipe alternative,
   the trusted exclusive owner must complete exact framing then capture the
   last-read token on that same handle/thread before another read or reentrancy;
   verify actual level, close, revert and assert no residual token every time.
   RPC requires equivalent verified call-context checks, not a connection-only
   allowlist or cached callback approval. Reject anonymous/wrong identity/level,
   downgrade, cancellation, timeout, epoch drift and observation reuse. Do not
   impersonate for provider or custody effects. Service executes only as its own
   separately verified custodian under explicit policy.
5. **Borrowed handles and same-user hostility.** Treat endpoint acquisition and
   token identity as insufficient if an unrelated process receives a handle.
   Request proof must require the isolated broker key and immutable transcript;
   the broker must not expose an arbitrary signing oracle. Test handle transfer,
   injection and proxying. A compromised trusted broker able to sign or delegate
   approvals is outside the claimed guarantee and must be explicit in the threat
   model; if protection against that actor is required, this design stays HOLD.
   Admin/kernel compromise is likewise not defeated by IPC account authentication.
6. **One-use user presence, separate from model output.** A qualified supported
   trusted UI/OS ceremony must display and bind exact operation, account, target,
   candidate version/digest, request ID and expiry. Untrusted UI clicks, replayed
   confirmations, wake/display names or text claiming approval have no authority.
   The consent broker must attest user presence through an externally accepted
   mechanism. Service verifies it, reserves immutable ID once and signs the
   bound receipt. Transport authentication cannot substitute for this ceremony.
7. **Custody and recovery.** Service-signed journal/receipts require protected
   service-owned signing-key custody, not just signed binaries. Under the
   approved service principal prove profile load/unload, user-scoped DPAPI,
   WinCred target/persistence ownership, restart and cross-principal denial.
   No implicit migration from interactive-user credentials. Machine DPAPI is
   not service isolation. Prove independently protected monotonic journal/anchor,
   service boot epoch, pending generation and rollback/ABA/replay resistance;
   service signatures alone do not prevent rollback of a signed old state.
8. **P96 common owner and actual effect.** Authenticate and consume the request,
   journal IN_FLIGHT durably, serialize revocation/fault publication and the
   final effect dispatch under the same trusted non-reentrant service owner.
   Retain the reviewed thread-owned OS custody lock through terminal verification
   and cleanup. No untrusted property/callback after the last check. Revoke wins
   before dispatch => zero effects. Dispatch wins => possible-effect uncertainty
   on failure/crash, deny retries pending verified recovery. Trace SAVE, REPLACE,
   DELETE, cancellation, restart, worker, legacy and alternate entrypoints.
   P290 snapshots do not close the original race.

Service-account DPAPI and WinCred persistence are separate dependencies; account
context/profile and storage ACLs must be proven on the installed service, not a
developer runner. Microsoft describes same-logon protection and machine-scope
exceptions for DPAPI, and same-user persistence for Credential Manager.
[CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata),
[CREDENTIALW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw).

## Required acceptance tests and independent disposition

No item below is satisfied merely by this source or by a green focused run.
Tests involving installation, identities or effects require separately approved
disposable external infrastructure and qualified owners, never Kristian here.

| Gate | Exact required adversarial evidence |
| --- | --- |
| P290 hosted evidence | Three x64 + three x86 windows-2022 jobs on audited exact DRAFT tip; exact native type/level, six captures, all denial cases, checked reversion, zero raw exits; unchanged P289 EXIT_259 refusal and P288/P287/P286 suite; no retry masking. |
| Cleanup/failure semantics | Qualified static review of every token-window exit; externally controlled native open/query/close failure and fatal-revert-failure tests prove no post-failure request/effect continuation, no leaked child/token/pipe authority. Crash behavior is process termination, not a permissive handler. |
| Installed service issuer / SEC03 | Wrong service name/principal, substituted SCM config/image, unsigned/changed installed binary, writable parent directory, swapped/restarted service, token replacement, wrong SID/session/logon and sampled ABA all refuse. Capture actual approved install/ACL/process/code-integrity evidence. |
| Fixed client and mutual authentication | Hostile same-user signed/unsigned apps, spoofed publisher/path/PID, cross-user/logon/session, borrowed/duplicated handles, proxy messages, injected writer and downgrade cannot obtain an accepted application request. Prove broker key/process isolation; test equivalent client rejection of a fake service endpoint. |
| Token/call binding | Anonymous, identification/impersonation/delegation mismatches, no read, malformed/oversize/partial frame, concurrent or reentrant read, stale last-read, reconnect, expiry and cancellation deny. Identification is the required observation level for this design; stronger level is not silently accepted. A successful account-token query never upgrades code trust. |
| Consent and immutable request | No UI ceremony, fake model approval, altered target/digest/operation/ID, replay from another channel/epoch/account, duplicate and concurrently consumed approval all produce zero effects. Trusted user ceremony and service/broker signatures must bind the same immutable transcript. |
| Profile/store / SEC04 | Actual approved service profile startup/restart/unload, separate-principal read/write/decrypt denials, same-user hostile app denial, WinCred target isolation, interrupted custody and protected journal/anchor recovery. No real key until qualified acceptance. |
| P96 original HIGH | Original negative stays intact; reviewed repair reproduces original fourth-probe revoke on all SAVE/REPLACE/DELETE routes and proves zero effect when revoke wins. Actual effect ownership, cross-thread/process contention, abandoned custody, crash after journal/dispatch and restart/ABA/replay require independent proof. Synthetic integers do not establish actual effect safety. |
| Release governance | Unwaived P76/P211/P216 disposition, GOV01/02 SEC03/04 REL05/06/07 reviewer-signed exact-source acceptance, three complete native product regressions and approved seal workflow. Until then REAL-KEY NO-GO / PRODUCTION RELEASE HOLD. |

Qualified external Windows security review must assess the threat model,
supported RPC/SSPI and trusted-UI contracts, install/Code Integrity assumptions,
broker isolation/delegation limits, service privilege/profile/store model and
original P96 effect-owner proof. Nayeon's independent source/hosted audit is
also required. Neither role is performed by this implementation report.

## Hosted custody and local evidence

The workflow accepts only the same-repository DRAFT pull_request, parent
`c3bb2f16303cfc9bcaa04539dffbc8c7a971e958`, base branch
`byok-c1-p289-native-peer-provenance-20261120`, head branch
`byok-c1-p290-message-token-observation-20261120`, and actual event head SHA.
The script proves a sole direct parent, exactly the four additions, all **1,171**
inherited blobs unchanged, and all **1,175** source disk blobs equal to Git with
no untracked/ignored/reparse drift before/after. Checkout and upload pins match
P289; contents permission is read-only, checkout persists no auth. No provider
call, download, package restore or remote review-trigger API is used.

P289 native and P288/P287/P286 executables compile from unchanged inherited
sources and run only hosted. Raw exit and exact anchored output are mandatory;
the original P289 numeric-259 exit refusal is preserved. Each child test process
has a 60-second watchdog and tree kill/checked wait; P290's own child has bounded
polling and deterministic teardown. A 10-minute job timeout is the outer limit.
Timeout, unexpected output, undocumented behavior or native error means HOLD.

Artifacts are eight allowlisted text files only: source SHA256 manifests,
compiler codes/hashes and raw exits, binary hashes, runtime exits, bounded
literal runtime output and scope disposition. Raw compiler output remains in
disposable build storage; unknown stdout/stderr is redacted. No binary, actual
SID, PID, GUID, username, auth LUID, raw exception or endpoint is uploaded.
Environment/username checks are accident barriers, never authentication.

Local validation is compile/source/AST only. The final warning-as-error matrix
includes six x64/x86 positive builds and 36 expected negative exit1/CS1029
builds, with the final receipt below. Both review scripts parsed with
**0 AST errors**. Read-only raw Git/disk
checks found **1,171/1,171** inherited blobs unchanged; no local EXE execution,
impersonation, pipe, child/service, ACL mutation, privilege, profile, DPAPI,
WinCred or provider operation occurred. Product runtime regressions/compileall
were not run under this explicit local execution prohibition; **0/3 remains**.

Final exact-source local Windows compile receipt:
`%TEMP%\p290-final-matrix-20261120-085527\compile-report.txt`;
SHA256 `179887451B149EE3549C9F337F151BA268C91D9F09F8ADF58E6111E5949C8A2E`.
Each invocation retains its raw compiler log and exit. No generated EXE was run.

| Architecture | Positive / raw exit | Negative / raw exit | Diagnostics |
| --- | --- | --- | --- |
| x64 | P290, unchanged P289, unchanged P288/P287/P286: 3/3, exit0 | 18/18, exit1 | Positives: zero warnings/errors; negatives: expected CS1029 guard and no output EXE |
| x86 | P290, unchanged P289, unchanged P288/P287/P286: 3/3, exit0 | 18/18, exit1 | Same strict checks |

The negative matrix covers no defines, RELEASE plus otherwise-positive defines,
and each required define missing individually. `/warn:4 /warnaserror+ /noconfig`
and explicit Framework references are used. Only P290 adds `/unsafe+` for native
stack buffers; inherited builds retain the original P289 compiler options.

Exact non-document source SHA256 at that receipt:

| New source | SHA256 |
| --- | --- |
| MessageTokenDiagnostic.cs | `77C473CF757B8DC6C312F2F8F97FEC23EDCCBF6F1B5024127845EDB8726AB544` |
| HostedReview.ps1 | `DF5B815A2ECEBB2963266ECDD644E89BF3663BA16F28800522287FE791E7F211` |
| p290-windows-message-identity-review.yml | `0095E5A8FA1E64BCA6A2416F11BB49A7E38730FB47100AD7504DD0599CEECABF` |

Author static checks: six intended narrow-window callee names only
(`ImpersonateNamedPipeClient`, `OpenThreadToken`, `GetTokenInformation`,
`CloseHandle`, `RevertToSelf`, mandatory fatal `FailFast`); no forbidden effect,
privilege, async or scheduling API in code. Workflow exact base/head literals,
action pins, architecture/trial matrix and host/time guards checked. Git diff
whitespace checks produce zero diagnostics, including all four untracked
additions via no-index comparison; its raw exit1 denotes added-file differences.
These checks are source evidence, not formal verification, runtime results or
independent acceptance. Hosted runtime remains **NOT RUN / HOLD**.

The read-only inherited SHA256 manifest is retained at
`%TEMP%\p290-final-matrix-20261120-085347\inherited-1171.sha256`, SHA256
`D8C63F66BC5D380CE6576B2A78FD352BA185DA696F3A95FC455822CC53580010`.
Each raw disk blob was compared with the exact P289 Git blob, **1,171/1,171**.
HEAD/branch and index remained unchanged; only the four additive paths are
untracked. Existing milestone tags were inspected and not changed.

**P291 target:** qualified review and separately approved disposable proof of
the actual installed service issuer, fixed protected client/consent issuer and
privilege-separated endpoint, together with original P96 effect ownership.
Do not advance through another synthetic-only identity iteration. Master Google
Drive workbook/dashboard remain untouched until full BYOK C1 completion.
