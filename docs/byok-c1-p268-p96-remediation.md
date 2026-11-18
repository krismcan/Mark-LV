# P268: direct isolated repair of the P96 pending-transaction race

Date: 2026-11-18. DEVELOPMENT IMPLEMENTATION; native runtime validation OPEN;
production HOLD. This is an additive repair candidate, not a production seal.
Branch `byok-c1-p268-p96-actual-successor-20261118`, exact parent
`0241b4277b8098c47e4de725bd1425bf0a0e764e`; intended draft PR #187 targets
`byok-c1-p267-service-owned-atomic-ordering-20261118`.

## Actual change

`native_c1_successor/P268ServiceOwnedPendingTransaction.cs` implements the real
P95 ledger algorithm against the unchanged P96 `IProtectedPendingState` methods.
It reads and verifies the existing journal/anchor and enrollment witness, checks
prior presence, appends an InFlight intent, performs both compare/write/readback
steps, dispatches exactly one SaveOrReplace or DeletePending, then appends and
reads back the terminal pair and marks/disposes the continuous custody lease.
Save never initializes lost history. Replace/Delete require stored prior state.
Every exception or ambiguous readback is denied/recovery-required without retry.
The two stores are never represented as one atomic write.

A single private service-owned gate covers approval issuance, identity/operation
binding, one-use admission, Revoke, Stop, Fault, the actual state effect call,
terminal persistence and lease disposal. The effect buffer is a private copy and
is cleared. Only the literal disposable four bytes `31 32 33 34` (or null for
Delete with destructive acknowledgement) are accepted. No actual keys are used.

The caller's P96 Approval fixture is an observation instrument, NEVER approval
authority: neither Consume nor StillCurrent is called. A foreign or constructed
approval object cannot pass the exact service-issued object identity check.
The token binds operation and this sole allowed synthetic value. The original
raw approval interface's independent revocation is deliberately not claimed to
be protected by an outer lock. A successful service revocation publishes under
the gate; the test then revokes the frozen fixture's observation flag.

If Revoke wins, no effect interface submission occurs. Once dispatch wins,
MAY_HAVE_EFFECT and RecoveryRequired stay sticky, including after a successful
terminal pair; Revoke/Stop/Fault return TooLate, never cancellation success.
The verified InFlight journal/anchor pair is the persistent pending marker
contract before any effect. The fake models this contract in memory only.
After an uncertain effect it remains InFlight; partial writes or mismatched
terminal records require recovery. Even a complete terminal record cannot
auto-admit a restarted service: restart defaults to recovery, with no recovery
or clearing API in this successor. `freshSyntheticSession` is explicitly a test
fixture constructor option, not an enrollment or production recovery authority.
The same adapter cannot be claimed twice. Fake fixture objects may be recreated
for tests; they are not a protected cross-process ownership mechanism.

Monitor reentry faults the owning transaction even if an arbitrary fake callback
swallows the exception. A second thread waiting synchronously from a callback
has a bounded 500 ms gate wait: timeout throws, atomically requests fault, and
NEVER reports revocation success. The owner checks this request after callbacks
and before dispatch. A callback after effect entry preserves possible-effect
uncertainty and cannot cause terminal success or replay. No unbounded wait or
join is used in the service gate. A real effect adapter would need its own
reviewed blocking, process, custody and failure contract.

## Production exclusion and dependency boundaries

The constructor is private and the only factory takes the sealed in-memory
DevelopmentPendingState, whose sole backing is the sealed frozen P96StateFixture.
There is no constructor accepting an arbitrary protected-state adapter. The
original P96 transaction is NOT instantiated/referenced by the successor source.
Source guards and red mutation tests reject direct and fixture-mediated original
coordinator references. It is compiled only to supply its frozen interface types
and in the separate historical negative executable. It remains vulnerable.

DEBUG and C1_P268_DEVELOPMENT_ONLY are mandatory compile-time guards. There is
no public IPC route, service launcher, SCM installer, native pending store,
WinCred call, provider call or production factory. ProductionEligible and
TrustedIssuerConnected are literal false. Real managed mutation calls here are
the P96 fixture's actual SaveOrReplace/DeletePending methods under the gate,
not a synthetic counter followed by an unrelated effect.

Trusted service principal/ACL, authenticated IPC and issuer provenance, durable
protected enrollment/journal/anchor, native continuous custody, crash/restart
recovery, audit integration and qualified independent review remain mandatory
before any production composition. A fake TrustVerified value grants none of
those. No protected production adapter is added. The P267 ordering source is
immutable: its private gate and synthetic submission API cannot meaningfully
compose this ledger/effect path. P268 reuses the ordering design, not its counter
as a proxy for a real transaction.

No historical implementation, assertion or workflow changes. No AppControl,
WinCred, Kristian native execution, service launch, real keys, Drive workbook,
commit, staging, tag, push, merge or release.

## Executable validation contract

`tests/p268_successor/P268RemediationTests.cs` contains 33 top-level native cases
with additional per-case assertions. SAVE, REPLACE and DELETE use the SAME
frozen P96 State/Approval fixture types and the same effect methods. Separate
threads establish revoke-first refusal and dispatch-first TooLate semantics for
all three operations and all Revoke/Stop/Fault controls. Event rendezvous holds
actual effect entry under the gate; the revoker cannot complete until release.
The test asserts verified InFlight state before effects, exactly two ledger and
anchor writes, one effect submission, terminal readback, lease cleanup, zero
post-revocation effects and no replay.

Other cases cover missing enrollment/history, malformed/mismatched anchor or
prior presence, existing InFlight, restart recovery, trust denial, exceptions
in journal/anchor/readback/effect, acquire/ownership/terminal/dispose failures,
terminal mismatch, drift at initial readback and after intent, operation/foreign
approval binding, malformed candidate, same-thread reentry, synchronized
cross-thread callback and callback reentry inside effect entry.

The workflow builds and runs the unchanged original negative proof separately:
P96 negative PASS = expected reproduction of the old vulnerability (15 cases).
Successor positive PASS = evidence for this new isolated path only (33 cases).
Neither is full production P96 closure. Original assertions stay byte-for-byte
unchanged. Workflow pins actions, verifies the exact source branch, target,
one-parent topology and five added paths; checks frozen source SHA256; executes
six Python source/mutation tests; rejects missing development flags; compiles
warning-as-error for x64/x86; uses a 40-second runtime watchdog for each executable;
and retains nonsecret text logs, raw exits and SHA256 receipts only. No binaries
are uploaded and no policy-refused launch is retried or bypassed.

## Exact compilation commands (PowerShell, no local execution)

Run from the repository root. Absolute source paths and explicit System/System.Core
references are needed by the .NET Framework compiler with /noconfig.

```powershell
$original = @(
  'tests/p95_native_custody_preflight/CustodyLedger.cs',
  'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs',
  'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs'
) | ForEach-Object { (Resolve-Path -LiteralPath $_).Path }
$successor = @($original) + @(
  'native_c1_successor/P268ServiceOwnedPendingTransaction.cs',
  'tests/p268_successor/P268RemediationTests.cs'
) | ForEach-Object { (Resolve-Path -LiteralPath $_).Path }
foreach ($arch in @('x64', 'x86')) {
  $framework = if ($arch -eq 'x64') { 'Framework64' } else { 'Framework' }
  $dir = "C:\Windows\Microsoft.NET\$framework\v4.0.30319"
  $common = @('/nologo', '/noconfig', '/debug+', '/optimize-', '/warn:4',
    '/warnaserror+', '/target:exe', ('/platform:' + $arch),
    ('/reference:' + $dir + '\System.dll'),
    ('/reference:' + $dir + '\System.Core.dll'))
  & "$dir\csc.exe" @common '/define:DEBUG;C1_P268_DEVELOPMENT_ONLY' `
    /main:P268RemediationTests ('/out:' + (Join-Path $env:TEMP "P268.Successor.$arch.exe")) @successor
  if ($LASTEXITCODE -ne 0) { throw 'Successor compile failed' }
  & "$dir\csc.exe" @common /main:Nayeon.ByokC1.P96NegativeProof `
    ('/out:' + (Join-Path $env:TEMP "P268.Original.$arch.exe")) @original
  if ($LASTEXITCODE -ne 0) { throw 'Original compile failed' }
}
```

Do NOT launch these artifacts on Kristian. Native execution belongs solely to
the GitHub-hosted Windows workflow after Nayeon publishes the exact candidate.
Focused source command there:
`python -I -B -m unittest discover -s tests -p test_byok_c1_p268_p96_remediation.py -v`.

## Open Failures & Prior-Issues Review

| Issue / source | Severity / root cause / affected callers | Repair and evidence | Disposition |
|---|---|---|---|
| P96 frozen negative review | High: caller approval can revoke during final lease getter between StillCurrent and effect; all original SAVE/REPLACE/DELETE routes affected | Original expected-vulnerable harness preserved; new service-owned approval/gate/ledger/effect path and adversarial cases added | Original excluded; isolated runtime verification OPEN; production HOLD |
| P267 source and CI | Counter ordering does not prove actual pending transaction mutation safety | No changes to P267; direct P95 algorithm and identical P96 effect interface in P268 | New source candidate only; independent review OPEN |
| Journal/anchor partial write, effect or terminal uncertainty | High: two stores and effect are not atomic; possible effects cannot be cancelled or replayed | InFlight readback before one dispatch; failure latch, terminal verification and cleanup inside gate; sticky recovery and restart default | Fake adversaries written; durable adapter prohibited; production HOLD |
| Reentrant / synchronized callbacks | High: Monitor is reentrant; callback can swallow rejection or wait on gate owner | Reentry latch, bounded gate wait and atomic fault request, checked before dispatch and after callbacks; native cases added | Native execution OPEN; production HOLD |
| Stale `.codex/CURRENT_STATE.md` | Historical Phase 10 checkpoint mismatches this P267 branch/parent | Git exact parent and clean worktree verified before editing; no unrelated context edits | Git authoritative for this repair; no phase/seal claimed |
| Local tool environment | Authoritative Python path denied by sandbox; .NET Framework compiler available | Bounded PowerShell static review and C# builds only; no Python download/copy or alternative native loader | Python/native runtime evidence delegated to configured hosted CI; not claimed PASS locally |

Current validation: local x64/x86 warning-as-error builds succeeded. Initial
invocation failures were command construction (relative slash paths interpreted
as compiler options, then missing explicit framework references under /noconfig),
corrected using absolute paths and both framework references; no frozen edits.
Local results: original and successor x64/x86 builds each exit 0; six missing-flag
builds each reject with exit 1 and only the expected CS1029 diagnostics. Five
workflow PowerShell blocks parse; 27 service witnesses match; frozen hashes and
tracked plus additive whitespace checks pass. Logs and raw exits are in
`%TEMP%\P268-source-validation-20261118` (outside the source envelope). These are
static/build receipts, not execution of the six Python tests or native harness. No
hosted runs are claimed. No full regression, independent review or security seal
is claimed. Overall disposition: GO for the authorized bounded repair candidate;
HOLD for verified race closure, production, deployment and release until evidence
and qualified review exist. Nayeon handles any later exact staging/commit/push.
