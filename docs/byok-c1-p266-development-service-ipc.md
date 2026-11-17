# P266 development service-owned IPC and synthetic lifecycle

17 November 2026. **DEVELOPMENT ONLY. REAL KEYS NO-GO. PRODUCTION HOLD.**

Intake matched clean branch `byok-c1-p266-service-bound-ipc-synthetic-20261117`
and exact parent `e835f60447f06a9320d3f474d3320f539f847f0a`, with no tag at HEAD.
One source writer, five additive paths; no historical source, P96, legacy path,
current-state file or frozen test edits. No staging, commit, tag, push, service
installation/start, candidate loading/execution, credentials, policy change,
provider call, Drive/workbook or dashboard activity. The user explicitly limits
local validation to static work and native compilation. Hosted execution is pending.

## Implemented boundary

`P266DevelopmentServiceIpc.cs` is a new `ServiceBase` host owning the actual,
unchanged P265 `DevelopmentPipeAdapter`, worker and private synthetic fixture.
P264 and P265 sources compile unchanged into the successor assemblies; `/main`
selects P266, and P266 never constructs or calls the separate P264 owner. P265's
standalone source contract remains untouched; the new composition is here.

Startup takes a fresh `WindowsIdentity.GetCurrent()` inside the lifecycle lock,
rejects thread impersonation, anonymous/system/LocalService/NetworkService and
virtual-service SIDs, then lets P265 check the current SID again and create its
protected current-SID pipe DACL. No P99 account gate, supplied identity, assumed
`NT SERVICE` approval, privilege grant or impersonation callback is introduced.
**Same SID is not application identity**; a same-user process remains untrusted.
This is not qualified service-principal admission or protected custody.

Start, terminal latches, snapshots and synthetic mutations share one lock. A
duplicate/stale start faults and closes the instance. A background worker calls
the same P265 `ServeOnce(2000)` at most 128 times; it never recreates the adapter.
Only completed, thread-restored framed denials may continue. Timeout, malformed
input, disconnect, transport/worker fault and request ceiling fail closed.
Idle timeout is intentionally terminal after two seconds, not a listener restart.
Stop/revoke/fault/dispose latch, delete the marker and dispose the pipe under the
lock, then join outside it for at most 2500 ms. Shutdown uses the stop path.
An unjoined worker produces an explicit timeout/fault, never a success receipt.
Cleanup exceptions remain sticky and are surfaced after the join, preserving the
original exception as the inner cause; cleanup failure cannot skip the join.
As with P265, OS cancellation depends on Windows returning; hosted execution has
an additional hard 35-second process deadline. No thread abort or retry exists.

The private fixture contains only integer marker `266` and stage/replace/delete
counters. Stage creates the marker, replace counts replacement of that same fixed
marker, delete clears it, and revoke/stop/fault/dispose clear it once. Local
no-argument fixture methods require a running, nonterminal owner. No bytes, keys,
tokens, caller data, store, WinCred, file, registry, provider or network backend
exists. The wire loop does not call fixture methods. P265's four operations still
return identical fixed denial bytes; none dispatches a synthetic operation.
All owner permission/production properties are always false, including while a
marker exists. Terminal instances cannot restage, replace, restart or resurrect.

The SCM-compatible entrypoint requires exactly `--development-only-no-effects`
before `ServiceBase.Run`. This token is scope acknowledgement, not authorization.
Do not invoke it, register the service or start SCM on Kristian or the runner.
The separate harness compiles these SAME lifecycle methods into its test process;
it calls them directly and invokes SCM overrides by test reflection, never SCM.
Production source contains no reflection. Invalid service entrypoint arguments
are tested without calling the accepted entrypoint.

## Open Failures & Prior-Issues Review

| Issue / severity | Evidence, cause and affected boundary | P266 disposition |
| --- | --- | --- |
| P265 native lifetime repair / material, closed per user evidence | Async wait handles previously closed before matching End calls. User reports hosted run `44198398563`, x64/x86, 3,024 assertions each passed. Logs were not fetched. | P265 bytes unchanged. Harness keeps End inside handle lifetime; source mutations guard it. GO for development composition only. |
| P264 separate owner / architecture gap | P264 is SCM-compatible but has no pipe owner. P265 was standalone. | New owner composes unchanged adapter; lifecycle, concurrency, real-pipe and cleanup assertions added. Runtime/independent acceptance pending. |
| P96 / HIGH; P76 / material | Prior atomic authorization/effect and regression holds remain unwaived. | No P96/P99/legacy gate or effect call. No repair or closure claim. HOLD. |
| Same-user identity / HIGH missing qualification | Current SID ACL cannot identify an approved application; no approved service account is established. | Fresh OS SID, denial-only protocol, no privileges, synthetic-only owner. Production principal/isolation HOLD. |
| Host validation / missing evidence | Authoritative Python path probe returns Access denied; prior candidate loaders were policy-blocked. | No interpreter or loader workaround, no local native execution. Python/native/full regressions and independent review pending. HOLD acceptance. |
| P266 first compile / source defect, repaired | `TimeoutException` ambiguous between System and ServiceProcess. | Qualified `System.TimeoutException`; repeated warning-as-error builds passed. No runtime claim. |
| P266 duplicate-start observation / material review finding | Fault latch could become visible before marker cleanup when a repeated start released the lock. | Cleanup now precedes lock release. Mutation canary and runtime terminal-snapshot invariants added; static checks pass, hosted confirmation pending. HOLD runtime acceptance. |

**GO only for the explicitly authorized development candidate.** Runtime/security
acceptance, P96/P76, real credentials and production remain HOLD/NO-GO. No prior
failure is waived; no milestone seal is claimed.

## Validation and review paths

Five additions only:

* `native_c1_successor/P266DevelopmentServiceIpc.cs`
* `tests/p266_successor/P266DevelopmentServiceIpcTests.cs`
* `tests/test_byok_c1_p266_development_service_ipc.py`
* `.github/workflows/p266-development-service-ipc.yml`
* `docs/byok-c1-p266-development-service-ipc.md`

The workflow admits only five additions from the exact P265 parent, on a PR to
`byok-c1-p265-authenticated-windows-ipc-20261117`, checks out exact PR HEAD and
verifies branch/base/scope/cleanliness. Pinned checkout/setup-python/upload actions,
read-only permissions, no checkout credentials, x64/x86 and `fail-fast: false`.
It records source hashes before/after; artifacts contain only logs/exits/JSON.
No binaries, secret access, install/start commands or alternate loader are used.

Each architecture compiles the service and harness with `DEBUG`,
`C1_P264_DEVELOPMENT_ONLY`, `C1_P265_DEVELOPMENT_ONLY` and
`C1_P266_DEVELOPMENT_ONLY`. Both artifacts reject no flags and each missing flag,
including Release/no-DEBUG, with exact compiler diagnostics and no output artifact.
Six Python tests check frozen bytes, owner/driver/workflow contracts and mutations.
Every native assertion executes in the hosted harness: actual kernel ACL/current
SID, fixed replies/all operations/replay, synthetic stage/replace/delete/revoke,
wire isolation, held permissions, invalid startup, SCM callbacks, repeated/stale
start, terminal-before-start, concurrent clients and lifecycle races, idle/partial
timeouts, malformed frame, request bound, cancellation, closed handles, joined
workers and no resurrection. This does not test SCM dispatcher operation or
cross-user isolation and does not supply a security seal.

Final local receipts: four x64/x86 warning-as-error service/harness compiler exits
0; all 20 missing-flag builds failed with exact guard diagnostics and no output
artifact. Flags tested: none, no DEBUG (Release), no P264 opt-in, no P265 opt-in,
no P266 opt-in, for each artifact/architecture. Compiler text logs and raw exits:
`%TEMP%\p266-final-compile-abd3d73ef69d42c5b779507c5570642b`.
Five workflow PowerShell blocks parse. Supplemental PowerShell text checks match
47 owner and 57 driver witnesses, reject 27 owner and 13 driver mutations, match
29 workflow witnesses and five frozen hashes. These are source checks, not Python
or native execution receipts. Tracked/index diffs remain empty; five additive
paths and whitespace checks are reviewed separately.

Python execution is blocked by the authoritative host-path denial. No alternate
interpreter, assembled-code inspection or native launch was attempted. Hosted
native x64/x86, Python tests, affected/full regressions, compileall and independent
review remain UNEXECUTED/PENDING. CI receipts are required before runtime acceptance.
