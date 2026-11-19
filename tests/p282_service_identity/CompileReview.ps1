# Compile/source checks ONLY. Never launches any generated executable or Python.
# Respect host ExecutionPolicy. If script execution is refused, use direct csc.exe
# commands with resolved absolute inputs; do not bypass policy or evaluate this file.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location -LiteralPath $root
try {
    if ((git rev-parse HEAD).Trim() -cne '248ec4d4243aae795387959dcfd9d03a007a3341') {
        throw 'P282 exact immutable parent required'
    }
    $build = Join-Path ([IO.Path]::GetTempPath()) ('nayeon-p282-compile-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $build | Out-Null
    Write-Output "P282_COMPILE_EVIDENCE=$build"
    $sources = @(
        'tests/p95_native_custody_preflight/CustodyLedger.cs',
        'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs',
        'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs',
        'tests/p99_original_native_c1_denial/ServiceGate.cs',
        'tests/p99_original_native_c1_denial/ProtectedAcl.cs',
        'native_c1_candidate/P261ScmReadOnlyAdmission.cs',
        'native_c1_candidate/P279RunningServiceTokenReadOnly.cs',
        'native_c1_successor/P265DevelopmentPipeAdapter.cs',
        'native_c1_successor/P267DevelopmentAtomicService.cs',
        'native_c1_successor/P268ServiceOwnedPendingTransaction.cs',
        'native_c1_successor/P269ComposedDevelopmentService.cs',
        'native_c1_successor/P270DevelopmentDurableWitness.cs',
        'native_c1_successor/P271DurableDevelopmentBridge.cs',
        'native_c1_successor/P282ExecutingServiceCustody.cs',
        'tests/p282_service_identity/ExecutingServiceCustodyTests.cs',
        'tests/p268_successor/P268RemediationTests.cs',
        'tests/p270_successor/P270DurableWitnessTests.cs',
        'tests/p271_successor/P271DurableBridgeTests.cs',
        'tests/p279_service_runtime/RuntimeServiceTokenTests.cs')
    $inputs = @($sources | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
    $flags = @('DEBUG', 'C1_REVIEW_ISOLATED_ASSEMBLY', 'C1_P265_DEVELOPMENT_ONLY',
        'C1_P267_DEVELOPMENT_ONLY', 'C1_P268_DEVELOPMENT_ONLY', 'C1_P269_DEVELOPMENT_ONLY',
        'C1_P270_DEVELOPMENT_ONLY', 'C1_P271_DEVELOPMENT_ONLY', 'C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY')
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
        foreach ($entry in @('ExecutingServiceCustodyTests', 'P268RemediationTests',
            'P270DurableWitnessTests', 'P271DurableBridgeTests', 'RuntimeServiceTokenTests')) {
            $label = "$arch-$entry"
            $output = Join-Path $build "$label.exe"
            $log = Join-Path $build "$label.log"
            & $csc @common ('/define:' + ($flags -join ';')) "/main:$entry" "/out:$output" @inputs *> $log
            $raw = $LASTEXITCODE
            Set-Content -LiteralPath (Join-Path $build "$label.exit") -Value $raw
            Get-Content -LiteralPath $log
            $results += "$label RAW_EXIT=$raw"
            Write-Output $results[-1]
            if ($null -eq $raw -or $raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compilation HOLD' }
        }
        foreach ($missing in @('ALL', 'DEBUG', 'C1_REVIEW_ISOLATED_ASSEMBLY', 'C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY')) {
            $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -ne $missing })
            $define = @(); if ($selected.Count) { $define = @('/define:' + ($selected -join ';')) }
            $label = "$arch-guard-$missing"
            $output = Join-Path $build "$label.exe"
            $log = Join-Path $build "$label.log"
            & $csc @common @define '/main:ExecutingServiceCustodyTests' "/out:$output" @inputs *> $log
            $raw = $LASTEXITCODE
            Set-Content -LiteralPath (Join-Path $build "$label.exit") -Value $raw
            $results += "$label RAW_EXIT=$raw"
            Write-Output $results[-1]
            if ($null -eq $raw -or $raw -ne 1 -or (Test-Path -LiteralPath $output) -or
                (Get-Content -LiteralPath $log -Raw) -notmatch 'error CS1029:.*P282_IDENTITY_CUSTODY_REVIEW_ONLY_NONDEPLOYABLE') {
                throw 'Guard-negative HOLD'
            }
        }
    }
    $sources + @('tests/p282_service_identity/CompileReview.ps1') | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
        Write-Output "$hash $_"
    } | Set-Content -LiteralPath (Join-Path $build 'source-sha256.txt')
    $results | Set-Content -LiteralPath (Join-Path $build 'raw-exits.txt')
    git diff --check
    Write-Output "DIFF_CHECK_RAW_EXIT=$LASTEXITCODE"
    if ($LASTEXITCODE -ne 0) { throw 'Whitespace HOLD' }
    Write-Output 'P282_COMPILE_ONLY=PASS; NATIVE_EXECUTION=NOT_RUN; PRODUCTION=HOLD'
}
finally { Pop-Location }
