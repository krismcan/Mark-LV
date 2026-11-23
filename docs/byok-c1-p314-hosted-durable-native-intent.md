# P314: disposable durable intent before hosted synthetic native Add

Date: 2026-11-23. SOURCE CANDIDATE; hosted test PENDING; production NO-GO / HOLD.
Operating Model v2.1: Codex sole source writer. CTO independently reviews,
validates and publishes a same-repository DRAFT PR. No staging, commit, push,
tag, merge, SCM, production IPC, real keys, service installation, workbook or
dashboard update is authorized or performed here.

Starting branch: byok-c1-p314-hosted-durable-native-intent-20261123.
Verified clean parent: 4fcf75666f8bd055f940eb5bbee01d154bf43c6b.
The requested parent and branch match Git. No milestone tag points at parent.
The cross-branch .codex/CURRENT_STATE.md describes older unrelated work and is
stale for BYOK; Git and the explicit current scope are authoritative. Its bytes
remain frozen because this task permits exactly seven source/review paths.
P313 hosted run 45248644051, x64/x86 Debug/Release 4/4 PASS, draft PR #232
unmerged, is user-supplied inherited evidence, not a P314 verification result.

## Open Failures & Prior-Issues Review

| Issue / source | Severity, cause and affected boundary | Containment, evidence and disposition |
| --- | --- | --- |
| P96 original revocation/effect flaw; user checkpoint 2026-11-23 | Original HIGH remains OPEN. Earlier control and effect routes did not provide a single sufficient service-owned admission/durable effect boundary. Cross-window/process/restart production closure is unproved. | This candidate covers only the nested hosted synthetic route. Real keys NO-GO. No original finding closure or production repair claimed. HOLD. |
| P313 owner and P312 adapter, frozen parent | Test-only monitor serialization is volatile; a process loss can erase the in-memory possible-effect flag. Hosted user/environment and unsigned friend identity are accident brakes. | P314 adds one disposable DPAPI IN_FLIGHT witness before the existing Add, under that same monitor. Tests cover control winners, queued late controls, pre-native crash, terminal replay and native absence. Hosted results and independent review PENDING. |
| P270 DPAPI durable witness precedent | CurrentUser DPAPI and SID ACLs cannot establish production protected-service custody, same-SID anti-rollback or restart authorization. A consistent file is not effect success. | Reuse only the bounded filesystem/DPAPI/flush/readback pattern. No ledger import, production recovery, retry, READY state or clearing of recovery. HOLD for production. |
| P312 migrated topology | Other product types must neither mention nor directly reference the adapter. Extra native authority in the partial would violate the frozen contract. | New standalone journal has no adapter name/reference. Owner remains nested in existing partial. Original P312/P313 tests frozen; original P312 --readonly required in hosted matrix. Original native adapter is frozen except the readonly P314 bit and gate selection. |
| P292 x86 SCM | UNKNOWN; root cause/evidence not established by this task. | No SCM execution or service inference. Four compile shapes and hosted friend runs cannot close this issue. HOLD. |
| Programme assurance | 0/7 independent approvals; 0/3 whole-product regressions. | Neither local compile nor hosted synthetic tests substitutes for these gates. No seal/signoff. HOLD. |
| Local compile orchestration | First compile-only command compiled x64 Debug service, then failed to resolve a relative friend-source argument. Tool invocation defect, not native evidence or product failure. | Resolved friend paths to absolute paths. Installed Framework CSC subsequently compiled service plus P312/P313/P314 friends in all four shapes, warnings as errors. No EXE executed. |
| Line endings in initial edit | Mixed CRLF/LF made git diff --check flag CR bytes. | Normalize only the seven scoped paths to LF. Recheck exact adapter/project transformation and frozen sources. No historical-test edits. |

Disposition: GO only for the explicitly authorized bounded hosted-test source
candidate and compile/static preparation. Production and milestone/release HOLD.
No independent approval is inferred from this sole-writer source review.

## Composition and ordering

The existing partial gains a private P314 marker constructor and one nested
ServiceOwnedAdmission overload. The P313 constructor remains on its original
host gate; P312 constructor, all four credential imports, fixed synthetic
ALPHA/BETA values, native effect/readback, zeroization and cleanup are unchanged.
The adapter's only other changes are readonly p314Session and gate dispatch.
The project adds the journal compile item and System.Security reference.

The P314 constructor checks canonical nonzero lowercase GUID N before OS access.
RequireHostedP314 then reads the actual environment/event/local Git HEAD and
process SID. It requires GITHUB_ACTIONS=true, RUNNER_OS=Windows,
RUNNER_ENVIRONMENT=github-hosted, event pull_request, P314_SYNTHETIC_HOSTED_ONLY=1,
repository krismcan/Mark-LV ID 1402212689, exact P314 head branch above, exact
P313 base branch byok-c1-p313-service-owned-vault-admission-20261123 and base
SHA 4fcf75666f8bd055f940eb5bbee01d154bf43c6b. Root/head/base must have the
same name/ID and Boolean fork=true metadata. The PR must be draft and actual
local HEAD must match PR head. Event file is bounded below 64 KiB, regular,
nonreparse, under RUNNER_TEMP. LocalSystem and thread impersonation refuse.
ValidateContextP314 is a pure negative-test predicate; its result never grants
constructor or execution authority.

Journal object allocation for a fresh owner is pure. No journal directory/file,
including IDLE, is created before dispatch wins. The original nonreentrant
monitor covers Issue, all controls, Dispatch, native Add/Verify and Dispose.

1. A control winning first terminates approval: no journal and no native effect.
2. Dispatch validates exact opaque approval identity, consumes it, and latches
   terminal, MayHaveEffect and RecoveryRequired before any durable/native work.
3. RecordInFlightAndFlushVerify exclusively creates the fixed root/leaf, writes
   and verifies IDLE, then writes IN_FLIGHT, SetLength, Flush(true), and strict
   readback of the actual exclusive FileStream before returning.
4. The fixed test rendezvous follows durable verification, before native entry.
   Its optional fixed crash simulation throws here; it accepts no callback.
5. Only successful journal completion and clear fault latch permit the unchanged
   vault.Add(), then vault.Verify(), still under the same admission monitor.

A failure/refusal is terminal and recovery-required; no Add retry/replay exists.
Late controls report TooLate (or bounded contention HoldUnknown), never successful
cancellation. A contention fault can prevent native entry while retaining the
already durable conservative IN_FLIGHT witness. Dispose closes journal handles
and performs existing verified fake credential cleanup, retaining journal bytes.
There is no IN_FLIGHT-to-success or recovery-clear transition.

## Disposable journal contract

DurableIntentJournal.cs is independent of the adapter and imports no WinCred API.
Its new native imports are kernel32 CreateDirectoryW, CreateFileW and
GetFileInformationByHandle. CreateDirectoryW performs fail-if-exists root
creation with a protected SID-only DACL installed atomically. Managed
Directory.CreateDirectory would silently adopt a root in a creation race.
The native inventory explicitly allows only these three additional filesystem imports.

The only path is the immediate OS-temp child nayeon-p314-GUID_N/intent.dpapi,
on a fixed local drive. Ancestor/root/leaf reparse points refuse. Ancestors and
root are opened with OPEN_REPARSE_POINT and pinned without delete sharing.
Reopen uses a no-follow exclusive file handle. Handle checks reject reparse,
directory-mode mismatches and hardlinks; readback rechecks volume/file identity,
access mode and exact single-leaf layout. Root and leaf
ownership must match the nonimpersonated ordinary process SID; DACLs are protected,
with exactly one explicit allow FullControl rule for that SID and no inheritance.
Directory child inheritance flags are fixed; the file has no inheritance flags.
FileMode.CreateNew, FileShare.None, write-through and strict ACL/readback checks
are required. Existing roots/files are never adopted or overwritten on dispatch.

The plaintext is a four-byte little-endian byte-length frame followed by strict
UTF-8 exactly P314|IDLE|ID or P314|IN_FLIGHT|ID. DPAPI CurrentUser protects that
entire frame with entropy bound to canonical root, SID and fixed leaf.
Ciphertext and cleartext are bounded at 16 KiB. Protect/unprotect buffers are
cleared. No user payload, secret, key, target, path or effect delegate is accepted.

Reopen opens the existing file read-only and exclusive, verifies path/ACL/SID,
DPAPI and strict framing, and exposes IN_FLIGHT with RecoveryRequired. Reopened
IDLE is also conservatively recovery-required. Record is denied on every reopened
object. The owner reopen overload is terminal, creates no vault and cannot Issue
or Dispatch. Choosing the fresh constructor against an existing root cannot
overwrite it or perform Add: dispatch fails closed at exclusive root creation.

This proves neither physical power-loss durability nor atomic journal/native
commit. Flush(true) and same-handle readback are OS-level test observations;
simulated crash means a fixed post-flush exception plus handle closure/reopen,
not a killed process, machine restart, VM reset or disk power-cut experiment.
Directory handles pin identity but are not separately flushed for directory durability.
Path checks and ACLs are not a defense against a malicious same-SID owner,
administrator, rollback, copied profiles, deleted journals or tampered binaries.
Deleting the fixture and reusing its ID is outside this disposable experiment.
A fresh GUID is not global production idempotency or a durable authorization.
DPAPI CurrentUser under an ordinary hosted SID is NOT protected service custody.
No production crash/restart trust or original P96 closure is claimed.

## Validation and acceptance

Local allowed work: source review, exact frozen-source comparisons, PowerShell
AST parsing, source hashes, git diff --check, and compile-only using the installed
Framework x64/x86 CSC, Debug/Release switches, /warn:4 /warnaserror+. Service
and unchanged historical friends plus the new friend compile against the real
service binary. Installed .NET Framework references were used; local CSC checks
are not the authoritative hosted .NET 4.8 MSBuild evidence. No downloaded tools.
No local test EXE, DPAPI fixture or credential effect was executed.

Hosted workflow uses Windows-2022 x64/x86 Debug/Release, installed MSBuild
targeting actual v4.8 service with warnings as errors, matching CSC, pinned
checkout action at exact PR head and persist-credentials=false. It verifies
exact seven-path name/status delta from parent, frozen unrelated service and
P312/P313 witnesses, exact adapter/project transformation and native inventory,
PowerShell ASTs, regular source paths, clean worktree and before/after SHA-256
hashes. Original P312 friend runs only --readonly. P313 native friend never runs.
Only P314 friend may write fixed fake values. Processes have bounded deadlines
and 8 KiB stdout/stderr caps; nonzero, unexpected stderr/output, timeout, source
drift or cleanup failure fails the job with cleanup unproven / HOLD.

P314 friend has 15 bounded scenario groups: pure hosted predicate, GUIDs,
three control-first routes, three successful dispatch/late-control routes,
one post-flush/pre-native crash/reopen, root collision, four damaged/foreign/ACL
journal routes and reparse denial. The post-flush rendezvous checks real adapter
Uninitialized state, journal IN_FLIGHT and exclusive handle before releasing
dispatch. Successful Add must reach Saved; crash must remain Uninitialized.
All restart/second effects refuse. Ciphertext/reopen checks follow handle close.
All fixture cleanup first verifies fake credential absence via the unchanged
native constructor preflight, then removes only exact nonreparse leaf/root,
nonrecursively, and verifies filesystem absence. Reparse test deletes only its
own link after checking native absence. A required symbolic-link creation failure
fails the run; it is never skipped. No secret, target or generated fixture ID
is printed. The fixed PASS count is emitted only after all groups and cleanup.

Hosted matrix: PENDING, 0/4 P314 results claimed.
P312 read-only topology at new source: PENDING hosted execution.
Independent review: PENDING; approvals remain 0/7.
Whole-product regressions: 0/3; no milestone verification.
CTO must inspect exact final source, validate all four hosted jobs and cleanup
evidence, and decide the draft publication/review. Any missing evidence is HOLD.
No Drive workbook until BYOK is fully complete.
