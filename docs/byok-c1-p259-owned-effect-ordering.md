# P259 owned integer transaction comparator

17 November 2026. OM v2.1. Sole Codex source writer. **DRAFT / REVIEW-ONLY /
NONDEPLOYABLE / UNSTAGED. P96 HIGH remains OPEN. Production and real-key HOLD.**

## Intake and Open Failures & Prior-Issues Review

Git intake was clean on `byok-c1-p259-p96-owned-effect-ordering-20261117`, exactly
`766ed973f41411799ed78d8504d2ebb89c0c7db5` (P258), with no tag at HEAD. Nearest
ancestor tag is `nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`.
The work root is `D:\Nayeon\CODEX_P259_P96_OWNED_EFFECT_ORDERING_20261117`.
`.codex/CURRENT_STATE.md` describes older Phase 10.2 work. Git governs this
bounded correction comparator. This assignment continues existing BYOK C1
review work. Product phase completion and security sign-off remain pending.

Read the engineering failure gate, relevant P96/P110/P221/P247 source and
P250/P251/P255/P257/P258 review evidence. The dependency boundary is the old
coordinator's separate approval-current, lease-owned and effect-interface
calls, the denial-only candidate host, and alternate Python backend routes.
P258's default UI containment does not establish OS-enforced effect ownership.

| Issue / severity | Cause, affected boundary and evidence | Containment, tests and disposition |
| --- | --- | --- |
| P96 HIGH | Original final approval check precedes a separate lease check and later external fake effect. Completed revoke can interleave before Save/Replace/Delete. | Preserve both original files and assertions. Independent original executable remains a negative comparator. P259 owns its entire integer dispatch. Production repair OPEN/HOLD. |
| P221/P247/P257/P110 scope limits | P221 wraps original fake Save. P247 makes effect-free decisions. P257 owns denial-only host calls. P110 integrates synthetic terminal methods in the candidate host. | P259 links none of these sources. It owns one immutable operation, nonreentrant admission and distinct private Save/Replace/Delete integer mutations. Existing evidence and host boundaries retain their scope. |
| SEC-03/04 HIGH missing evidence | Real service principal/store isolation, genuine consent, authenticated IPC, enforced loaded-image identity and protected durable journal/history remain unqualified. Shared objects across instances/processes/restarts and alternate effect routes remain unproved. | Qualified SEC-03/04 decisions 0, qualified approvals 0/7. P259 restart construction is recovery-only. No production closure or independent approval supplied. HOLD. |
| Original P76 / P251 material failures | Four original P76 FAIL methods and one original P251 FAIL remain unwaived. Current-source evidence cannot replace original acceptance. | Retain original dispositions. Full product Windows regressions 0/3. HOLD. |
| P247 execution / material missing evidence | Script policy and Code Integrity blocks prevented native acceptance. | x64 0/54 and x86 0/54 remain unexecuted. Existing policy remains authoritative. HOLD. |
| P258 inherited failures / material | Prior review HOLD and selected historical failures remain in P258's record. | P259 source and focused cases provide no closure of those issues. HOLD. |
| P259 validation / missing evidence | Host Python access probe returned Access denied. Native C# compiler/runtime and Python tests have not run for P259. | Commands below await host orchestration and independent read-only review. Author source inspection provides no runtime PASS. HOLD. |

Disposition is **GO for this user-authorized additive synthetic comparator only**.
Failure/security/release gates remain **HOLD**. Independent reviewer pending.

## Owned algorithm and authored acceptance cases

Four additions comprise the C# owner, C# driver, Python source contract and this
evidence note. The owner has no dependency on the old coordinator or candidate
host. One private `SemaphoreSlim(1, 1)` protects request consumption, lifecycle
publication, dispatch order, mutation and observations. Owning-thread detection
rejects recursive admission and poisons the request while its gate is held.
Interrupted gate waiters acquire the gate to publish sticky fault/recovery before
returning, so interruption cannot leave their request reusable.

Construction binds one synthetic operation. `Apply()` consumes the request,
latches recovery and invokes only the private fixed integer switch while still
holding the gate. Save sets marker 17, Replace sets 23, Delete sets 0. The initial
marker is 0 for Save and 1 for Replace/Delete. Each route has a separate counter.
These markers record only synthetic integer mutations. The owner accepts fixed
operation and synthetic scenario enums.

`Publish()` consumes the same request and publishes revoke/stop/fault under that
gate. Publication-first prevents all dispatches. Dispatch-first publication
returns `TooLatePossibleEffect` with a later publication order, including when
an attempted mutation has uncertain completion. Every dispatch and injected
failure returns `RecoveryRequired`. The result enums provide no stored-success
outcome. A new object represents an independent synthetic scenario. It cannot
establish global one-use across service instances, processes or restarts.

Both C# files contain an explicit `#error` unless **both**
`C1_REVIEW_ISOLATED_ASSEMBLY` and `C1_SYNTHETIC_TEST` are defined. Private event
rendezvous are attached through driver reflection solely to pause the fixed
path. Driver delegates never cross the owner boundary. Reflection is test
instrumentation, with no claim of isolation from a hostile same-process caller.

The driver authors **49 cases per architecture**. Eighteen cover all three
operations, three lifecycle signals and both winner orders. Effect-first pauses
before mutation inside the held gate, starts a publisher, observes its contender
event, releases dispatch and checks publication's return-time dispatch evidence.
The remaining cases cover eight concurrent Apply callers per operation, nine
recursive-entry cases, nine partial-failure cases, three interrupted admissions,
three restart cases and four invalid-input cases. Events determine winner order.
Driver rendezvous waits and joins have failure deadlines. The host process
deadline bounds a stalled gate test. The interruption test observes an actual
blocked Windows thread before interrupting its gate wait.

The Python module authors four source-only tests, including 13 in-memory mutation
negatives with specific rejection reasons. It checks both compile guards, narrow
owner boundaries and frozen hashes. This bounded lexical checker supplies
supplementary evidence. Host compiler guard negatives and C# runtime tests remain
separate acceptance obligations.

Observed preserved raw SHA-256 values are below.

| File | SHA-256 |
| --- | --- |
| `tests/p96_native_transaction_negative/PendingCustodyTransaction.cs` | `D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB` |
| `tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs` | `2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F` |
| `native_c1_candidate/CustodyService.cs` | `876E3006BA26966BE93BA033C97779B6FBB41E8656869A462535B1CF4B12D95E` |
| `native_c1_candidate/ServiceOwnedAdmissionBoundary.cs` | `1FA108C18F228F83FE4BBDE0F682025BD23E864B23DDC24EA4D4F70F27382DD5` |

## Windows host commands awaiting execution

Run in an ordinarily authorized Windows host. Preserve logs, native exits and
source hashes. An Application Control refusal is a blocked run with zero cases
executed. Stop on refusal or failure and retain evidence for review.
The commands create only disposable host evidence artifacts outside source.

```powershell
Set-Location -LiteralPath 'D:\Nayeon\CODEX_P259_P96_OWNED_EFFECT_ORDERING_20261117'
$ErrorActionPreference = 'Stop'
$p259Evidence = Join-Path $env:TEMP ('P259-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $p259Evidence | Out-Null
$p259New = @(
    (Resolve-Path -LiteralPath 'native_c1_g2_review/P259OwnedPendingTransaction.cs').Path
    (Resolve-Path -LiteralPath 'tests/p259_owned_pending_transaction/OwnedPendingTransactionTests.cs').Path
)
$p259Original = @(
    (Resolve-Path -LiteralPath 'tests/p95_native_custody_preflight/CustodyLedger.cs').Path
    (Resolve-Path -LiteralPath 'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs').Path
    (Resolve-Path -LiteralPath 'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs').Path
)
$p259Tracked = @(git ls-files)
if ($LASTEXITCODE -ne 0) { throw 'Source inventory failed' }
$p259Scope = @('native_c1_g2_review/P259OwnedPendingTransaction.cs',
    'tests/p259_owned_pending_transaction/OwnedPendingTransactionTests.cs',
    'tests/test_byok_c1_p259_owned_pending_transaction.py',
    'docs/byok-c1-p259-owned-effect-ordering.md')
$p259Before = @($p259Tracked + $p259Scope | Sort-Object -Unique | ForEach-Object {
    Get-FileHash -LiteralPath $_ -Algorithm SHA256
})
$p259Before | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $p259Evidence 'source-before.csv')
foreach ($p259Arch in @('x64', 'x86')) {
    $p259Compiler = if ($p259Arch -eq 'x64') {
        'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    } else { 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe' }
    foreach ($p259Guard in @('none', 'isolated-only', 'synthetic-only')) {
        $p259Defines = @()
        if ($p259Guard -eq 'isolated-only') { $p259Defines += '/define:C1_REVIEW_ISOLATED_ASSEMBLY' }
        if ($p259Guard -eq 'synthetic-only') { $p259Defines += '/define:C1_SYNTHETIC_TEST' }
        $p259Rejected = Join-Path $p259Evidence ($p259Arch + '-' + $p259Guard + '.dll')
        $p259GuardLog = Join-Path $p259Evidence ($p259Arch + '-' + $p259Guard + '.log')
        & $p259Compiler /nologo /target:library ("/platform:" + $p259Arch) `
            @p259Defines ("/out:" + $p259Rejected) @p259New *> $p259GuardLog
        $p259Exit = $LASTEXITCODE
        $p259GuardText = Get-Content -Raw -LiteralPath $p259GuardLog
        if ($p259Exit -eq 0 -or (Test-Path -LiteralPath $p259Rejected) -or
            ([regex]::Matches($p259GuardText, 'error CS1029')).Count -ne 2 -or
            !$p259GuardText.Contains('P259 requires isolated synthetic review and is NONDEPLOYABLE')) {
            throw 'Explicit two-source compile guard rejection missing'
        }
    }
    foreach ($p259Suite in @('P259', 'P96-original-negative')) {
        $p259Sources = if ($p259Suite -eq 'P259') { $p259New } else { $p259Original }
        $p259Defines = @()
        if ($p259Suite -eq 'P259') {
            $p259Defines += '/define:C1_REVIEW_ISOLATED_ASSEMBLY,C1_SYNTHETIC_TEST'
        }
        $p259Exe = Join-Path $p259Evidence ($p259Suite + '-' + $p259Arch + '.exe')
        & $p259Compiler /nologo /target:exe ("/platform:" + $p259Arch) `
            @p259Defines ("/out:" + $p259Exe) @p259Sources `
            *> (Join-Path $p259Evidence ($p259Suite + '-' + $p259Arch + '-compile.log'))
        if ($LASTEXITCODE -ne 0) { throw 'C# compilation failed' }
        $p259Out = Join-Path $p259Evidence ($p259Suite + '-' + $p259Arch + '-stdout.log')
        $p259Err = Join-Path $p259Evidence ($p259Suite + '-' + $p259Arch + '-stderr.log')
        $p259Process = Start-Process -FilePath $p259Exe -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $p259Out -RedirectStandardError $p259Err
        if (!$p259Process.WaitForExit(60000)) {
            Stop-Process -Id $p259Process.Id
            throw 'Synthetic executable timed out; inspect preserved logs'
        }
        $p259Process.WaitForExit()
        if ($p259Process.ExitCode -ne 0) { throw 'C# runtime failed' }
        $p259Text = Get-Content -Raw -LiteralPath $p259Out
        if ($p259Suite -eq 'P259') {
            $p259Bits = if ($p259Arch -eq 'x64') { 64 } else { 32 }
            if (!$p259Text.Contains('P259_PASSED=49') -or !$p259Text.Contains('P259_FAILED=0') -or
                !$p259Text.Contains('P259_POINTER_BITS=' + $p259Bits)) { throw 'P259 receipt missing' }
        } elseif (!$p259Text.Contains('P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=15') -or
            !$p259Text.Contains('P96_NATIVE_ACTUAL_COORDINATOR_TESTS_FAILED=0') -or
            !$p259Text.Contains('P96_LEGACY_POST_CHECK_REVOCATION_RACE=REPRODUCED_IN_FAKE_ONLY') -or
            !$p259Text.Contains('P96_C1_PRODUCTION_RELEASE=HOLD')) { throw 'Original negative receipt missing' }
    }
}
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B `
    -m unittest discover -s tests -p test_byok_c1_p259_owned_pending_transaction.py -v `
    *> (Join-Path $p259Evidence 'python-source-tests.log')
if ($LASTEXITCODE -ne 0) { throw 'P259 source contract failed' }
foreach ($p259Pin in $p259Before) {
    if ((Get-FileHash -LiteralPath $p259Pin.Path -Algorithm SHA256).Hash -ne $p259Pin.Hash) {
        throw 'Source changed during validation'
    }
}
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Whitespace failure' }
Write-Output $p259Evidence
```

Actual author checks comprise Git identity/status, raw frozen hashes, bounded
source inspection, host-command PowerShell AST parsing and whitespace checks.
P259 C# executions are **0/49 x64 and
0/49 x86**, pending host execution. Python tests are unexecuted. Compilation
results and runtime receipts must be recorded independently. Independent review,
affected/cross-phase tests and full product regressions remain pending. All source
is left untracked for human review. Qualified GOV/SEC approval and production
milestone/seal decisions remain outstanding.
