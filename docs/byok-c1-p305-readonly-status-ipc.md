# P305 genuine nonsecret read-only status IPC — BUILD FIRST / HOLD

2026-11-22; OM v2.1; Codex sole source writer. Exact clean P304 parent:
`afda79970bd217d8375c45a639faf559f63e1337`; branch
`byok-c1-p305-readonly-status-ipc-20261122`. Eight authorized paths only.
Git matches the requested parent; CURRENT_STATE is stale and remains untouched.
User reports P304 exact-head hosted run 45061138148: 4/4, 209 checks per job.

## Implementation and dependency boundary

Actual .NET Framework 4.8 product types own real Windows named-pipe handles.
Host OnStart retains both P304 executing-identity verifications before creating
StatusPipeServer; startup fault, Stop, Shutdown and Dispose close its lifetime.
No SCM, store, credential, provider, native credential effect or policy changes.
Lifecycle readiness and all operation denials remain unchanged.

Fixed product endpoint: `NayeonV1ByokCustody.Status.v1`. One connection and one
query per server lifetime; no automatic restart or re-listen. Request is exactly
one four-byte message `C1S1`. Reply is the fixed ASCII literal
`C1|NOT_AUTHORIZED|HOLD|NO_CREDENTIALS`. Wrong, partial, overlong, disconnected
or timed-out input terminates the instance without a reply or operation dispatch.
No credential fields, arbitrary payload API, operation callbacks or grants exist.
An idle connection wait lasts until owner disposal; connected I/O has 1s bounds.
Successful instance retains its buffered reply/handle until owner disposal;
there is no second read or worker after completion. Re-query requires a separately
owned new lifetime, not an approved production monitoring/recovery policy.

PipeSecurity is protected against inheritance; owner is the exact process SID.
Only that SID receives ReadWrite (Windows adds Synchronize); Network SID is denied
FullControl. Handle inheritance is disabled. No Everyone/Authenticated Users grant.
SID comes from an opened process token; thread-token absence is required before
identity capture and before/after processing. No impersonation API is invoked.
A distinct interactive client is intentionally not admitted to the service pipe.
Restricted service-token ACL sufficiency still needs qualified production review.

The client sends only C1S1, uses anonymous impersonation level, bounded connection
and I/O deadlines, and checks exact reply bytes and message completion. Even an
exact reply produces UNTRUSTED_HOLD: endpoint bytes are not peer attestation.
Internal unique-name overloads and the P305 friend assembly enable isolated tests;
internal visibility grants no OS rights. No production peer is approved.
Disposal closes the handle, then joins at most 3s; no host lock is needed by
the async worker. A join failure throws HOLD rather than claiming cleanup.

## Open Failures & Prior-Issues Review

GO: user-authorized bounded nonsecret source build only. Release remains HOLD.
P96/P292 original HIGH custody/revocation/teardown findings remain unclosed;
this path has no route to those credential owners and claims no repair evidence.
P304 review's historical merge-HEAD evidence defect is contained by exact PR-head
checkout, same-repo draft/base/branch guards and before/after SHA checks.
Historical packaging path issues are contained by absolute compiler input paths.
Independent review is pending; no new runtime result is inferred from old evidence.
Full product regressions 0/3; qualified independent approvals 0/7; SEC03/04 later.

## Validation / handoff

Hosted workflow builds x86/x64 Debug/Release with installed tools, no downloads.
Each test executable references the actual separately compiled product assembly;
each has a 30s process deadline. No product executable or SCM dispatch is launched;
inherited P304 tests invoke Main in-process only in a proven refusal context.
P305 tests use ordinary disposable runner identity, random endpoint names, kernel
ACL readback, exact exchange, malformed/partial/oversized input, closure/replay,
absent server, connected timeout/disconnect, concurrent disposal while waiting,
and fabricated exact/invalid replies that cannot grant trusted status.
Unchanged P304 denial tests remain an affected baseline, not full regression proof.
Source hashes, exact checkout HEAD and empty tracked worktree/index are checked.
Local compile-only/static evidence is recorded in the source-writer handoff;
no binaries are run on Kristian. Hosted execution and independent CTO validation
remain pending. No staging, commit, tag, push, real key or production RELEASE.
