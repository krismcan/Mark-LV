# P315: hosted cross-process pre-native termination and no replay

2026-11-23. OM v2.1. Source candidate; hosted runtime evidence PENDING.
REAL KEY NO-GO / PRODUCTION RELEASE HOLD.

Codex is the sole source writer. Nayeon independently inspects and publishes a
separate same-repository DRAFT PR. No staging, commit, push, tag, merge, workbook
or dashboard update is performed or authorized in this task. No main Drive
workbook update until BYOK is fully complete.

Verified starting worktree: `D:\Nayeon\CODEX_P315_CRASH_RECOVERY_20261123`.
Branch: `byok-c1-p315-hosted-crash-recovery-20261123`.
Clean exact P314 parent: `8ea85bc2682183a95845c5b14a7986bb7200f5ec`.
No milestone tag points at this parent. `.codex/CURRENT_STATE.md` describes older
unrelated work and does not match the BYOK checkpoint. Git and the explicit
task scope control; that file remains frozen outside the exact six paths.

## Open Failures & Prior-Issues Review

| Issue / source | Severity, root cause, affected boundary | Evidence, containment, review and disposition |
| --- | --- | --- |
| P96 original production race; user checkpoint | HIGH OPEN. Production control/effect ordering and cross-process restart authority remain unproved. | No production entrypoint changes. Only the existing disposable nested owner is extended. Original production closure not claimed. HOLD. |
| P314 same-process interruption; frozen parent/test | A fixed exception and orderly handle disposal do not establish process termination behavior. Volatile admission state cannot survive process loss. | User reports run 45257800865, 4/4 hosted PASS, draft PR #233 unmerged. P315 adds actual child termination after flush/readback; original P314 tests/workflow stay frozen. New runtime results PENDING; independent review PENDING. |
| P313 predecessor; user checkpoint | Monitor serialization is a bounded test route, not production durable admission. | User reports 4/4 hosted PASS. Original monitor/Issue/control/Dispatch/cleanup bodies retained exactly. No inferred production approval. |
| P312 migrated topology; source/test | Adapter authority must not escape into unrelated product types; native bodies/imports must stay fixed. | Only two existing adapter files mention the adapter in service source. Journal has no adapter reference or WinCred call/import. Original P312 friend --readonly required in every hosted job. P313/P314 native tests never execute on P315. |
| DPAPI hosted-user precedent | Ordinary SID CurrentUser DPAPI does not qualify an SCM principal, anti-rollback, or protected service custody. | Same ACL, exclusive handles, entropy, format, identity, Flush(true), readback and sticky RecoveryRequired remain. No production recovery capability. HOLD. |
| P292 x86 SCM teardown | UNKNOWN; cause and production evidence unresolved. | No SCM install, start/stop, or product Main execution. Compile shapes and hosted ordinary-user tests cannot close it. HOLD. |
| Programme assurance | Independent approvals 0/7; whole-product regressions 0/3. | Sole-writer static review and compile checks are not independent security approval. Production/milestone HOLD. |
| Local build tooling | Installed Framework MSBuild rejects /warnaserror and lacks v4.8 reference assemblies (MSB3644). | No tools downloaded or project retargeting. Use installed CSC for compile-only four-shape checks; actual v4.8 MSBuild remains a hosted requirement. No local runtime evidence. |
| Initial P315 constructor copy | Compile caught unassigned p315Session (CS0649); copied constructor assigned predecessor bit. New route would select wrong host gate. | Corrected only P315 assignment. All four service/friend compilations subsequently passed with warnings as errors. Original constructors unchanged. Runtime and independent validation pending. |

Disposition: GO only for the explicitly authorized synthetic source preparation
and compile/static checks. All hosted results and independent review are pending.
Production, security-sensitive seal and milestone remain HOLD. No finding is
downgraded, no risky production deferral approved, no test skipped or weakened.

## Bounded service extension

Exact scope: three modified service sources and three added test/workflow/review
files. No project, historical test/workflow, production command, pipe, credential,
SCM, provider, settings or legacy source changes.

The original adapter gains only a private readonly p315Session bit and first
Gate selection. Native CredWriteW body, all four credential imports, fixed
synthetic ALPHA/BETA, preflight, zeroization and cleanup stay exact.

The existing partial gains private P315Marker construction, a pure predicate,
RequireHostedP315, friend access for P315.CrashRecovery.Tests, and a nested owner
overload with fixed HostedCrashOnly mode. Both pause=true and crash=true are
mandatory for that overload, including parent preflight/recovery/collision
fixtures. It cannot become a successful Add path, even if ReleaseNative were
called. No effect callback, payload delegate or arbitrary executor exists.

Canonical nonempty lowercase GuidN validation precedes OS calls. Full actual
environment/event/Git/process identity validation precedes journal or vault
operations. The pure caller-supplied context predicate never grants effects.
The original P312/P313/P314 constructors and gates retain their original branch
contracts. Original Issue, revoke/stop/fault, dispatch and disposal use the same
nonreentrant monitor and original ordering.

RequireHostedP315 demands Windows, GITHUB_ACTIONS=true, RUNNER_OS=Windows,
RUNNER_ENVIRONMENT=github-hosted, GITHUB_EVENT_NAME=pull_request,
P315_SYNTHETIC_HOSTED_ONLY=1 and absent P312/P313/P314 flags. Exact head is the
branch above; exact base is
`byok-c1-p314-hosted-durable-native-intent-20261123`, at the exact parent above.
Root/head/base repository must all be `krismcan/Mark-LV`, ID 1402212689, with
Boolean fork=true. PR must be draft. The regular nonreparse event file is
strictly below 65536 bytes under RUNNER_TEMP. Local Git HEAD must equal event PR
head SHA. LocalSystem and thread impersonation refuse before native preflight.

DurableIntentJournal.Locate accepts mutually exclusive P314/P315 flags. The P315
alternative requires the exact cheap head/base/repository and hosted environment.
The journal has no effect capability and does not itself authorize an owner.
Original P314 marker behavior remains available with P315 absent. Only this host
predicate changes; path/ACL/DPAPI/identity/flush code stays frozen. P315 deliberately
retains the original `nayeon-p314-GuidN/intent.dpapi` namespace and P314 frame,
avoiding a new journal format or changed entropy contract.

## Process-kill proof contract

The friend accepts exactly two modes: no arguments for PARENT, or exactly
`--child-before-native` and one canonical fresh GuidN for CHILD. Unknown arguments
fail. Both modes require the full actual hosted gate. Parent generates the ID;
child refuses an existing root and the journal uses atomic fail-if-exists creation.

1. Child constructs the fixed crash-only owner, obtains its opaque one-add
   approval and starts one background Dispatch thread.
2. Dispatch consumes approval and latches terminal/possible-effect/recovery under
   the original monitor. Journal creation writes DPAPI IDLE, then IN_FLIGHT,
   Flush(true), and verifies strict readback on the exclusive handle.
3. Only after that operation returns does the original beforeNative event signal.
   Child waits on it, checks journal InFlight AND RecoveryRequired and the vault's
   Uninitialized state, then prints exactly P315_CHILD_READY and flushes stdout.
   No generated ID, SID, target, path or secret is printed.
4. Dispatch receives no release. Its existing five-second pause timeout refuses;
   crash=true separately refuses Add even if the pause were released. Child waits
   only fifteen seconds, then fails if it survives. No hidden survivor success.
5. Parent uses Process.Start of its currently running EXE, with no shell and fixed
   arguments. One-character async reads enforce exact stdout and empty stderr,
   with a ten-second readiness watchdog. Parent requires the child still running,
   calls Kill only on that returned Process object and waits at most five seconds
   for exit. It never looks up a PID or kills by process name.
6. After termination, parent snapshots the bounded durable ciphertext and opens
   a separate read-only DurableIntentJournal. It requires IN_FLIGHT and
   RecoveryRequired. It checks unchanged bytes, independently checks native target
   absence through the P315 constructor preflight, and closes the read-only owner.
7. Same-ID service reopen is terminal/recovery-required: Issue and Dispatch refuse.
   Selecting a fresh owner with the same ID cannot adopt the existing root;
   dispatch refuses at root collision before native Add. Repeated replay and Issue
   refuse. Every attempt preserves the original ciphertext. Final read-only
   reopen still sees IN_FLIGHT with RecoveryRequired.
8. Cleanup checks target absence, canonical generated root/leaf, regular nonreparse
   ancestors, exact leaf inventory, then deletes only the leaf and empty root
   nonrecursively. Target absence is checked again. Any child, timeout, kill, output,
   replay, witness or cleanup failure emits fixed stderr HOLD and a nonzero exit.
   The fixed PASS line appears only after every fixture cleanup succeeds.

Additional hosted groups exercise pure-context environment and event mutations
(draft, repository names/IDs/fork types, refs, SHA and JSON bounds), malformed IDs,
absent/mixed marker refusal, all three control-first routes with no journal, and
corrupt/foreign-ID witnesses. Damaged-witness reopen and fresh dispatch refuse
without rewriting the damaged bytes. No historical native test is invoked.

This is process termination evidence only. It is not wall-plug power-loss,
machine restart, filesystem-directory durability, post-native crash atomicity,
exactly-once execution, rollback resistance, protection against malicious same-SID
actors/admins, or production recovery authority. No native Add succeeds in P315.
Deleting witnesses and reusing IDs is outside the experiment. Ordinary hosted
CurrentUser DPAPI is not a qualified SCM/service identity. P96 remains HIGH OPEN.

## Validation and publication contract

Local: compile only, installed Framework CSC /warn:4 /warnaserror+, actual service
source plus standalone friend referencing the service, x64/x86 Debug/Release.
No local friend EXE, DPAPI, WinCred or process-kill execution on Kristian. Local
MSBuild v4.8 qualification is unavailable as recorded above; no install/download.
PowerShell AST 2/2, exact six-path scope, UTF-8 LF, frozen-source checks and
git diff --check are required before handoff.

Hosted workflow: Windows-2022 four-shape matrix, draft same-repo exact refs/SHA,
pinned checkout action at PR head, persist-credentials=false, strict six-path Git
delta, frozen P312/P313/P314 friends/workflows and unrelated product. Adapter
transformation is exact; old partial ordering is compared after removing only
P315 additions; journal outside the host predicate is exact. Native inventories
are checked. Regular source paths, clean checkout and before/after SHA-256 source
and binary witnesses are required. Installed MSBuild builds the actual v4.8
service with warnings as errors; CSC compiles the friends. Only original P312
--readonly and P315 execute. Each process has a 90-second watchdog and capped
8 KiB stdout/stderr; fixed stage labels distinguish build, topology and runtime.
No network downloads, SCM, production pipe, real keys or native P313/P314 runs.

P315 hosted matrix: PENDING, 0/4 results claimed. Original P312 readonly runtime:
PENDING. Independent security approvals: 0/7. Whole-product regressions: 0/3.
No production crash assurance, original race closure, milestone seal or release.

Local source-preparation results on 2026-11-23: installed Framework CSC compiled
the actual service project source inventory and P312/P313/P314/P315 friends in
all four x64/x86 Debug/Release shapes, warnings as errors, without executing any
resulting EXE. PowerShell AST passed 2/2; exact native-adapter transformation,
retained partial ordering and journal outside Locate's host predicate passed
parent comparisons. Exact six-path unstaged scope, UTF-8 LF and diff whitespace
checks passed. Historical tests/workflows, project and unrelated sources remain
unchanged. These are compile/static results only; hosted runtime is authority.
