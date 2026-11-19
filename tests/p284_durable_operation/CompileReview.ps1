# COMPILE ONLY. No generated executable, Python, ACL provisioning or policy bypass.
# Do not dot-source/evaluate this file. Respect host ExecutionPolicy; use the
# equivalent direct compiler commands when script execution is unavailable.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if ($root -cne 'D:\Nayeon\CODEX_P284_DURABLE_OPERATION_BOUND_ADMISSION_20261119') { throw 'Wrong worktree' }
Push-Location -LiteralPath $root
try {
    if ((git rev-parse HEAD).Trim() -cne '9730d810670023909aa1fc3213a4c1130ad6ffb0' -or
        (git branch --show-current).Trim() -cne 'byok-c1-p284-durable-operation-bound-admission-20261119') { throw 'Wrong parent/branch' }
    git diff --exit-code HEAD -- .
    if ($LASTEXITCODE -ne 0) { throw 'Frozen tracked source changed' }
    $build = Join-Path ([IO.Path]::GetTempPath()) ('nayeon-p284-compile-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $build | Out-Null
    Write-Output "P284_COMPILE_EVIDENCE=$build"
    $sources = @(
        'tests/p95_native_custody_preflight/CustodyLedger.cs',
        'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs',
        'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs',
        'tests/p99_original_native_c1_denial/ServiceGate.cs',
        'tests/p99_original_native_c1_denial/ProtectedAcl.cs',
        'native_c1_candidate/P261ScmReadOnlyAdmission.cs',
        'native_c1_candidate/P279RunningServiceTokenReadOnly.cs',
        'native_c1_candidate/ServiceBoundRequestIdentity.cs',
        'native_c1_successor/P265DevelopmentPipeAdapter.cs',
        'native_c1_successor/P267DevelopmentAtomicService.cs',
        'native_c1_successor/P268ServiceOwnedPendingTransaction.cs',
        'native_c1_successor/P269ComposedDevelopmentService.cs',
        'native_c1_successor/P270DevelopmentDurableWitness.cs',
        'native_c1_successor/P271DurableDevelopmentBridge.cs',
        'native_c1_successor/P282ExecutingServiceCustody.cs',
        'native_c1_successor/P283SyntheticOperationAdmission.cs',
        'native_c1_successor/P284DurableOperationAdmission.cs',
        'tests/p268_successor/P268RemediationTests.cs',
        'tests/p269_successor/P269ComposedServiceTests.cs',
        'tests/p270_successor/P270DurableWitnessTests.cs',
        'tests/p271_successor/P271DurableBridgeTests.cs',
        'tests/p282_service_identity/ExecutingServiceCustodyTests.cs',
        'tests/p283_operation_admission/SyntheticOperationAdmissionTests.cs',
        'tests/p284_durable_operation/DurableOperationAdmissionTests.cs')
    $inputs = @($sources | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
    $required = @('DEBUG', 'C1_REVIEW_ISOLATED_ASSEMBLY', 'C1_P265_DEVELOPMENT_ONLY',
        'C1_P267_DEVELOPMENT_ONLY', 'C1_P268_DEVELOPMENT_ONLY', 'C1_P269_DEVELOPMENT_ONLY',
        'C1_P270_DEVELOPMENT_ONLY', 'C1_P271_DEVELOPMENT_ONLY',
        'C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY', 'C1_P284_DURABLE_OPERATION_REVIEW_ONLY')
    $flags = @($required) + @('C1_P283_SYNTHETIC_OPERATION_REVIEW_ONLY')
    $results = @()
    foreach ($arch in @('x64', 'x86')) {
        $framework = if ($arch -eq 'x64') { 'Framework64' } else { 'Framework' }
        $dir = Join-Path $env:WINDIR "Microsoft.NET/$framework/v4.0.30319"
        $csc = (Resolve-Path -LiteralPath (Join-Path $dir 'csc.exe')).Path
        $common = @('/nologo', '/noconfig', '/warn:4', '/warnaserror+', '/target:exe',
            '/debug+', '/optimize-', "/platform:$arch")
        foreach ($reference in @('System.dll', 'System.Core.dll', 'System.Security.dll', 'System.ServiceProcess.dll')) {
            $common += '/reference:' + (Join-Path $dir $reference)
        }
        foreach ($entry in @('DurableOperationAdmissionTests', 'P284ReadOnlyNegativeTests',
            'SyntheticOperationAdmissionTests', 'P268RemediationTests', 'P269ComposedServiceTests',
            'P270DurableWitnessTests', 'P271DurableBridgeTests', 'ExecutingServiceCustodyTests')) {
            $label = "$arch-$entry"
            $output = Join-Path $build "$label.exe"
            $log = Join-Path $build "$label.log"
            $invokeArgs = @($common)
            $invokeArgs += '/define:' + ($flags -join ';')
            $invokeArgs += "/main:$entry"
            $invokeArgs += "/out:$output"
            $invokeArgs += $inputs
            @{ compiler = $csc; arguments = $invokeArgs } | ConvertTo-Json -Depth 3 |
                Set-Content -LiteralPath (Join-Path $build "$label.command.json")
            & $csc @invokeArgs *> $log
            $raw = $LASTEXITCODE
            Set-Content -LiteralPath (Join-Path $build "$label.exit") -Value $raw
            $results += "$label RAW_EXIT=$raw"
            Write-Output $results[-1]
            if ($null -eq $raw -or $raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compile HOLD; preserve evidence' }
        }
        foreach ($missing in @('ALL', 'RELEASE') + $required) {
            $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -ne $missing })
            if ($missing -eq 'RELEASE') { $selected += 'RELEASE' } # even DEBUG+RELEASE must reject
            $invokeArgs = @($common)
            if ($selected.Count) { $invokeArgs += '/define:' + ($selected -join ';') }
            $label = "$arch-guard-$missing"
            $output = Join-Path $build "$label.exe"
            $log = Join-Path $build "$label.log"
            $invokeArgs += '/main:DurableOperationAdmissionTests'
            $invokeArgs += "/out:$output"
            $invokeArgs += $inputs
            @{ compiler = $csc; arguments = $invokeArgs } | ConvertTo-Json -Depth 3 |
                Set-Content -LiteralPath (Join-Path $build "$label.command.json")
            & $csc @invokeArgs *> $log
            $raw = $LASTEXITCODE
            Set-Content -LiteralPath (Join-Path $build "$label.exit") -Value $raw
            $results += "$label RAW_EXIT=$raw"
            Write-Output $results[-1]
            if ($null -eq $raw -or $raw -ne 1 -or (Test-Path -LiteralPath $output) -or
                (Get-Content -LiteralPath $log -Raw) -notmatch 'error CS1029:.*P284_TEST_ONLY_ALL_DURABLE_FLAGS_REQUIRED') {
                throw 'Guard HOLD; preserve evidence'
            }
        }
    }
    ($sources + @('tests/p284_durable_operation/CompileReview.ps1')) | ForEach-Object {
        (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash + ' ' + $_
    } | Set-Content -LiteralPath (Join-Path $build 'source-sha256.txt')
    $results | Set-Content -LiteralPath (Join-Path $build 'raw-exits.txt')
    git diff --check
    if ($LASTEXITCODE -ne 0) { throw 'Whitespace HOLD' }
    Write-Output 'COMPILE_ONLY=PASS RUNTIME=NOT_RUN ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3'
}
finally { Pop-Location }
