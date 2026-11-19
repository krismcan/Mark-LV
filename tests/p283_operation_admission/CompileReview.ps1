# Compilation ONLY. Never execute generated assemblies on Kristian.
# Do not dot-source/evaluate this file or bypass host ExecutionPolicy.
# If execution is refused, issue the direct csc.exe commands separately.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if ($root -cne 'D:\Nayeon\CODEX_P283_OPERATION_BOUND_ADMISSION_20261119') { throw 'Exact worktree required' }
Push-Location -LiteralPath $root
try {
    if ((git rev-parse HEAD).Trim() -cne '0f22089b918f428bca8347eff31c563cf17571d2' -or
        (git branch --show-current).Trim() -cne 'byok-c1-p283-operation-bound-admission-20261119') {
        throw 'Exact P283 parent/branch required'
    }
    git diff --exit-code HEAD -- . ':!docs/byok-c1-p283-synthetic-operation-admission.md'
    if ($LASTEXITCODE -ne 0) { throw 'Frozen tracked parent changed' }
    $build = Join-Path ([IO.Path]::GetTempPath()) ('nayeon-p283-compile-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $build | Out-Null
    Write-Output "P283_COMPILE_EVIDENCE=$build"
    $sources = @(
        'tests/p95_native_custody_preflight/CustodyLedger.cs',
        'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs',
        'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs',
        'native_c1_candidate/ServiceBoundRequestIdentity.cs',
        'native_c1_successor/P265DevelopmentPipeAdapter.cs',
        'native_c1_successor/P267DevelopmentAtomicService.cs',
        'native_c1_successor/P268ServiceOwnedPendingTransaction.cs',
        'native_c1_successor/P269ComposedDevelopmentService.cs',
        'native_c1_successor/P283SyntheticOperationAdmission.cs',
        'tests/p268_successor/P268RemediationTests.cs',
        'tests/p269_successor/P269ComposedServiceTests.cs',
        'tests/p283_operation_admission/SyntheticOperationAdmissionTests.cs')
    $inputs = @($sources | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
    $flags = @('DEBUG', 'C1_REVIEW_ISOLATED_ASSEMBLY', 'C1_P265_DEVELOPMENT_ONLY',
        'C1_P267_DEVELOPMENT_ONLY', 'C1_P268_DEVELOPMENT_ONLY', 'C1_P269_DEVELOPMENT_ONLY',
        'C1_P283_SYNTHETIC_OPERATION_REVIEW_ONLY')
    $results = @()
    foreach ($arch in @('x64', 'x86')) {
        $framework = if ($arch -eq 'x64') { 'Framework64' } else { 'Framework' }
        $dir = Join-Path $env:WINDIR "Microsoft.NET/$framework/v4.0.30319"
        $csc = Join-Path $dir 'csc.exe'
        $common = @('/nologo', '/noconfig', '/warn:4', '/warnaserror+', '/target:exe',
            '/debug+', '/optimize-', "/platform:$arch")
        foreach ($reference in @('System.dll', 'System.Core.dll', 'System.Security.dll', 'System.ServiceProcess.dll')) {
            $common += '/reference:' + (Join-Path $dir $reference)
        }
        foreach ($entry in @('SyntheticOperationAdmissionTests', 'P268RemediationTests', 'P269ComposedServiceTests')) {
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
            if ($null -eq $raw -or $raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compilation HOLD; preserve log' }
        }
        foreach ($missing in @('ALL') + $flags) {
            $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -ne $missing })
            $define = @(); if ($selected.Count) { $define = @('/define:' + ($selected -join ';')) }
            $label = "$arch-guard-$missing"
            $output = Join-Path $build "$label.exe"
            $log = Join-Path $build "$label.log"
            $invokeArgs = @($common) + $define
            $invokeArgs += '/main:SyntheticOperationAdmissionTests'
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
                (Get-Content -LiteralPath $log -Raw) -notmatch 'error CS1029:.*P283_TEST_ONLY_ALL_DEVELOPMENT_FLAGS_REQUIRED') {
                throw 'Guard-negative HOLD; preserve log'
            }
        }
    }
    ($sources + @('tests/p283_operation_admission/CompileReview.ps1')) | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
        Write-Output "$hash $_"
    } | Set-Content -LiteralPath (Join-Path $build 'source-sha256.txt')
    $results | Set-Content -LiteralPath (Join-Path $build 'raw-exits.txt')
    git diff --check
    Write-Output "DIFF_CHECK_RAW_EXIT=$LASTEXITCODE"
    if ($LASTEXITCODE -ne 0) { throw 'Whitespace HOLD' }
    Write-Output 'COMPILE_ONLY=PASS RUNTIME=NOT_RUN ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3'
}
finally { Pop-Location }
