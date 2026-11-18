# P270 disposable Windows durable custody witness — RELEASE HOLD

Date: 2026-11-18. Codex source candidate only; no commit, staging, push,
service installation, credentials, workbook or dashboard changes.
Exact requested parent: `b160244c26dda096e86ec03ca0bd23b10ed29679` (P269).
Branch: `byok-c1-p270-durable-protected-custody-20261118`.
The worktree began clean at that parent with no HEAD milestone tag returned.
`.codex/CURRENT_STATE.md` describes unrelated Phase 10 work and is stale for
this task. Git and the explicit P270 instruction govern this bounded candidate;
the state file is unchanged under the exact five-addition authorization.
P269 PR189 x64/x86 23 cases / 350 assertions is user-supplied historical
evidence, not a P270 runtime result.

## Actual implementation and authority

`native_c1_successor/P270DevelopmentDurableWitness.cs` is a sealed, internal,
DEBUG + C1_P270_DEVELOPMENT_ONLY fixture, Windows only. A trusted test host
provisions one direct OS-temp child named `nayeon-p270-<32 hex GUID>`, with
a verified fixed local drive, an explicit current-SID owner and protected current-SID-only inheritable
FullControl ACL. The constructor takes that root and an explicit fresh flag.
There is no production factory, IPC root argument, credential effect method,
P96 state-interface implementation, or integration into any frozen successor.
"Service-owned" here describes intended fixture ownership by the trusted
host; this process is NOT SCM, a real service principal, or real service acceptance.

Every ancestor is opened with OPEN_REPARSE_POINT + BACKUP_SEMANTICS, checked
by handle and retained without delete sharing. The root owner/ACL are checked
while those handles pin its path. Both fixed files (`journal.dpapi`,
`anchor.dpapi`) are opened with no sharing, OPEN_REPARSE_POINT and
WRITE_THROUGH, checked by handle for reparse/directory attributes, single
hard-link count and current-SID ownership, then wrapped in .NET FileStream.
There are no native credential calls. Kernel32 declarations open/check file
handles only. Unexpected entries and non-file entries fail closed.

Fresh enrollment requires an empty, pre-existing protected test root. It
creates both files with CREATE_NEW; no existing unknown state is overwritten.
The P95 CreateInitial journal and independently protected P95 Anchor use DPAPI
CurrentUser and domain-specific entropy binding SID, root and file role.
Only small nonsecret P95 ledger metadata is accepted; no API-key byte port
exists. Length-prefixed ciphertext is bounded at 65,536 bytes; decoded text
is bounded at 32,768 bytes and strict UTF-8. Exact framing rejects trailing
bytes independently of DPAPI parser behavior. No plaintext fallback exists.
DPAPI failure throws LedgerBlocked and causes hosted verification HOLD.

Each WriteJournal/WriteAnchor compares the caller's exact expected value with
both the decoded disk value and the private current-session snapshot. This
rejects stale expected values, including a same-process return to an earlier
accepted value. Journal updates must be precisely one valid P95 appended
frame, not replacement history. Anchor updates must match the outstanding
journal. The uncertainty latch is set BEFORE the first write. Each write
uses FileStream, Flush(true), and exact decoded per-file readback; layout is
checked again. A failed write/check permanently faults that instance. A
journal awaiting its anchor reports RecoveryRequired and accepts only the
matching anchor continuation in that uninterrupted fresh fixture session.
Inspection never clears a recovery latch. It can identify consistent bytes
without admitting any effects.

This deliberately uses in-place bounded writes, not a claimed atomic file
replacement or atomic pair. A journal-only interruption leaves a mismatched
pair. A torn write leaves invalid framing/DPAPI/codec. Missing, extra, tampered,
or mismatched state is quarantined by refusal (not moved, deleted or repaired).
Opening inconsistent state throws LedgerBlocked: recovery required.
Opening even a valid pair starts permanently recovery-required and refuses
all writes. No independent service-session authenticator exists, and there
is no recovery authorization method, automatic repair or restart reenrollment.
Fresh enrollment is a host-only assertion of disposable provisioning, NOT
proof that a same-SID attacker never erased or replayed a former directory.

## Executable tests and CI

`tests/p270_successor/P270DurableWitnessTests.cs` contains 23 bounded cases (22 original plus the owner-fix ACL negative).
It refuses ordinary execution unless all GitHub-hosted/disposable environment
gates match, rejects LocalSystem, and uses only newly generated OS-temp roots.
These environment gates prevent accidents; they are not authenticated consent
or a production trust boundary. Do not run this executable on Kristian.

Cases cover initial protected enrollment/P95 decode; plaintext-marker absence;
wrong entropy; inspection-only restart; Save/Replace/Delete InFlight and
terminal persistence; journal-only interruption; a deliberately half-written,
flushed journal; stale journal and anchor CAS; fault latching; invalid/oversized
updates; live unexpected entries; deleted anchor/journal; truncated/corrupt/
appended/oversized files; extra files; cross-file and cross-root replay;
repeat enrollment; arbitrary-root rejection; unprotected ACL; and file symlink
rejection if Windows permits unprivileged symlinks. Symlink unavailability is
reported explicitly with the Windows error, never silently asserted PASS
for that subprobe. Wrong-user DPAPI is not tested: no second identity or token
is provisioned. Wrong entropy and cross-root entropy refusal are deterministic.
The same-SID pair replay case demonstrates that consistent protected bytes
still do not permit restarted writes; it does not prove rollback detection.
Cleanup deletes only immediate files (including links themselves) in the exact
new root and deletes that root nonrecursively. No user input or user files.

`tests/test_byok_c1_p270_durable_witness.py` supplies five focused source,
frozen-hash, scope, runner, workflow and red mutation checks. The 27 mutation
probes remove or weaken explicit source protections; these are static guard
checks, not substitutes for Windows execution or independent security review.

`.github/workflows/p270-windows-durable-custody.yml` pins checkout/setup-python
by full SHA; requires a clean third P270 commit with the exact preserved diagnostic/first/P269 ancestry and exactly
five added paths; pins P95/P96/P269 source plus P269 workflow hashes; and thus
freezes all other historical source via the exact-parent delta restriction.
It runs Python checks and x64/x86 .NET Framework C# warning-as-error builds,
with System.Security.dll and explicit cryptography imports. Three compiler
negative probes reject missing guards. Actual DPAPI execution uses only the
ephemeral GitHub-hosted current identity, with a 40-second process watchdog.
DPAPI unavailability, launch refusal, timeout, missing receipts or any test
failure is HOLD; there is no bypass or retry. Raw exits, text logs, source
hashes and SHA-256 of text evidence are emitted to Actions job logs. No binary
or DPAPI-blob artifacts are uploaded. CI has not been triggered by Codex.

## Open Failures & Prior-Issues Review

| Issue / source (2026-11-18) | Severity / cause and boundary | Containment, evidence and disposition |
| --- | --- | --- |
| P95 codec warning / P96 Persist interface | High for production: a hash chain and physically separate anchor are not trusted persistence or an atomic pair. | Actual DPAPI file persistence added only in an isolated fixture. Journal-only and torn-write adversaries added. Production HOLD. |
| P268 bounded fake store | High for production: TrustVerified and enrollment are synthetic; prior service/session and effect boundaries remain unproven. | P268 unchanged; no adapter injection or lower-level credential route. P270 cannot become a P96 effect port. Independent review OPEN; production HOLD. |
| Replacement / crash uncertainty (user warning) | High for production: two writes cannot establish an atomic pair; an interrupted first update leaves uncertainty. | No replacement atomicity claimed. Flush/readback, prewrite fault latch, mismatched-pair denial, no repair and restart denial. Hosted adversarial runtime OPEN. |
| Same-SID replay and impersonation | High unresolved production boundary: DPAPI CurrentUser and current-user ACL do not establish an independent historical witness or service principal. | Reopen always refuses writes. Same-SID pair replay remains indistinguishable at byte inspection. Independent antirollback design/service principal REQUIRED; no risky production deferral approved. |
| Host environment / observed compile preflights | Environment only: authoritative Python access denied; first compiler invocation treated slash paths as options; a /noconfig preflight omitted System.Core; C# definite assignment required initializing handle-info struct. | Absolute paths, explicit System/Core/Security references and initialized struct compile cleanly. No native execution attempted. No installer, credentials or workaround. Python/hosted runtime HOLD. |
| Stale context file | Documentation mismatch, outside five-path scope. | Exact Git parent verified; state preserved. No milestone completion asserted. |

Dependency audit was limited to the requested P95 codec, P96 state and pending
transaction interface/write-ahead path, P268 fake successor, and P269 workflow
snippets. Alternate production routes remain unchanged: no UI/IPC/service
entrypoint references this witness. Permission -> Policy -> Confirmation ->
Execution -> Verification is not replaced by DPAPI, a fresh flag, a compiler
define or model output. Synthetic continuation admits metadata writes only.
The existing production failures are contained by isolation and unconditional
restart denial; they are not closed by this prototype. GO for the explicitly
authorized fixture source work only; HOLD for milestone/release acceptance.

## Checks observed in this Codex session

- Exact parent and requested branch verified; initial worktree clean.
- x64 and x86 C# executable compilation: PASS, exit 0, warnings as errors,
  explicit System.dll/System.Core.dll/System.Security.dll, /noconfig.
- Missing DEBUG, missing opt-in, both missing: compile refusal exit 1 with
  the required P270 diagnostic; no native executable was run.
- Authoritative Python: access denied by sandbox. Focused Python, full unittest,
  compileall and actual hosted DPAPI tests NOT RUN here. No runtime PASS claimed.
- Independent source/security review and hosted x64/x86 logs: OPEN.
- Final five-path inventory and whitespace checks are recorded by the final
  implementation response; no frozen source edit is authorized.

Before production: independent rollback-resistant anchor/enrollment witness
and dedicated service principal; authenticated IPC/consent/session provenance;
reviewed real WinCred effect port to repaired P268; real recovery authorization,
crash/power-loss assurance, independent review and all required regressions.
Real keys NO-GO. Production RELEASE HOLD. No OS-enforced antirollback,
production journal, installed service or real service acceptance claim.


## First hosted failure and bounded diagnostic follow-up (2026-11-18)

User-supplied evidence: draft PR #190, first Actions run 44267760065,
immutable first P270 commit 815dda613602ec47ec1e5c539ab31d795b2329ee
(parent P269 b160244c26dda096e86ec03ca0bd23b10ed29679).
Both x64/x86 native runtimes exited 1 at or before the first PASS receipt:
`P270_HOLD LedgerBlocked Pending custody recovery required`.
Python source checks passed 5/5 and positive/negative compiler guards passed.
This is an unclassified native fail-closed refusal, not an accepted negative.

Severity: material verification blocker. Root cause UNKNOWN. Limited source
inspection covered Scope provisioning, constructor ancestor handles/root ACL,
file handles/owner, DPAPI persistence/readback and initial-case expectations.
No source-proven OS API defect was established. No ACL, handle, reparse,
hard-link, framing, restart, CAS or fail-closed check is removed or relaxed.
The affected route is this isolated hosted harness into DurableWitness;
frozen P95/P96/P265-P269 and production entrypoints remain unchanged.

Follow-up adds TEST-ONLY fixed stage state and a literal current case label.
Only the top-level failing catch prints P270_FAIL_CASE and P270_FAIL_STAGE;
it retains the fixed LedgerBlocked HOLD message and never prints exception
messages, paths, SIDs, usernames, ciphertext or sensitive bytes. Expected
LedgerBlocked probes restore stage state and emit no stderr. Stage values
are diagnostic breadcrumbs, not proof of the failed predicate or authority.
The original 22 cases, hosted guards, watchdog and empty-stderr pass gate remain.

CI now requires HEAD^ to equal the preserved first P270 commit and HEAD^^
to equal P269, with depth 3 and the same exact five additive paths from P269.
The Python guard permits that first P270 HEAD during local precommit checks;
a subsequent HEAD must have the exact two-commit ancestry. Frozen hashes remain.
No amend, tag movement, commit, push, CI launch or workbook/dashboard update.

Disposition: diagnostic source candidate only; native root-cause closure,
hosted x64/x86 22-case rerun and independent review OPEN. Production and
milestone HOLD. Nayeon may review/stage/commit and run hosted diagnostics;
use its fixed first failing case/stage to guide a separately reviewed repair.
Authoritative Python is unavailable in this sandbox; no replacement installed.
Local compile-only outcomes are reported in the handoff, never runtime proof.

## P270-HOSTED-FRESH-OWNER: bounded repair candidate (2026-11-18)

This section supersedes the diagnostic-only unknown-cause disposition above;
both failures remain failures. User-supplied run 44267760065 failed x64/x86
with LedgerBlocked. Diagnostic run 44269213492 also failed BOTH architectures,
exit 1, at `P270_FAIL_CASE=initial-dpapi-codec-and-restart-denial` and
`P270_FAIL_STAGE=file-owner`. Its Python 5/5, two positive builds and six
negative compiler guards passed; none establishes native runtime acceptance.
First commit `815dda613602ec47ec1e5c539ab31d795b2329ee` and diagnostic commit
`17cd9774045aaee5ddf97e6c6f3ba89985516fed` are preserved unchanged; PR #190
remains draft. No amend, commit, push or external run was performed here.

Severity: material security/verification blocker; release HOLD. Root cause:
an elevated hosted token may default a newly created file's owner to
BUILTIN\Administrators, although its parent has the current-user owner and
inheritable ACL. The original immediate exact-user owner check therefore
correctly refused the fresh journal. Administrators is never an accepted
substitute owner. Affected callers are fresh enrollment and existing-file
reopen in this fixture only; frozen P95/P96/P265-P269 and production routes
are untouched.

Repair: CREATE_NEW alone adds WRITE_OWNER (0x00080000) to the native access
mask. After exclusive opening, native attribute/link verification and stream
wrapping, `fresh-owner-provision` reads FileSecurity from that same handle,
calls SetOwner(current SID), and persists it through FileStream.SetAccessControl.
The unconditional subsequent FileStream.GetAccessControl rereads the actual
owner and requires exact SID equality on BOTH fresh creation and reopen.
Existing files never receive WRITE_OWNER or owner repair. No path-based
ownership update, retry or fallback exists. Any provisioning failure disposes
the stream/handle, propagates into constructor fail-closed cleanup and retains
the fixed stage diagnostic. Root ACL, reparse/hardlink checks, filenames,
entropy, bounds, DPAPI, dual-store protocol and source identity are unchanged.

The existing Python mutation test now includes six additional red probes:
remove SetOwner, remove handle-based persistence, remove WRITE_OWNER, grant
WRITE_OWNER on reopen, remove fresh-only provisioning, or remove the final
exact owner assertion. A contiguous source contract binds fresh gating to
provisioning and the unconditional reread/return. Five focused test methods
are retained. Static probes do not prove Windows security semantics.

Native runner assertions reopen BOTH disposed files with read-only handles
and require actual current-user ownership. One additional case removes file
ACL inheritance and grants current-user Read only, requiring reopen refusal;
its original ACL is restored in finally for bounded cleanup. This mutates
only its generated disposable fixture. It requires no second account or
privilege enablement. Unauthorized replacement-owner runtime coverage is
not claimed: assigning another SID would depend on token ownership/privileges.
The unconditional exact-owner source guard covers rejection without adding
an OS privilege dependency. The original unprotected-root-ACL case remains.
The workflow now requires the exact 23-case runtime receipt.

Third-commit CI requires HEAD^ = diagnostic commit, HEAD^^ = first P270,
HEAD^^^ = P269, fetch-depth 4, a single-parent HEAD and exactly the same FIVE
additive paths against P269. Python permits the diagnostic HEAD for local
precommit checks, or that exact third-commit topology. No other source scope
is admitted. The diagnostic-only earlier depth-3 description is historical.

Local repair checks: x64/x86 .NET Framework compile-only PASS, exit 0,
/warnaserror+ with System.dll, System.Core.dll and System.Security.dll;
all six missing-define compiler negatives PASS, exit 1, expected diagnostic
and no output executable. No executable launched on Kristian. Authoritative
Python command could not resolve the configured executable in this sandbox;
five focused tests, full regression and compileall remain NOT RUN here.
Independent external security review and fresh hosted x64/x86 execution are
PENDING. Source repair is a candidate, not verified incident closure or a
milestone seal. Production WinCred, rollback protection, installed service,
real keys, workbook/dashboard updates and policy changes are not claimed.
Disposition: HOLD pending independent validation and hosted runtime evidence.
