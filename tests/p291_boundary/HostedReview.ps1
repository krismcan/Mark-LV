# Hosted only. Locally parse as data; never execute/dot-source this script.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '3451352b57ef50dcc757580b43625af759712b79'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:RUNNER_OS -cne 'Windows' -or $env:ImageOS -cne 'win22' -or
    $env:GITHUB_EVENT_NAME -cne 'pull_request' -or $env:GITHUB_REPOSITORY -cne 'krismcan/Mark-LV' -or
    $env:REVIEW_ARCH -cnotin @('x64','x86') -or
    $env:REVIEW_FRAMEWORK -cne (@{x64='Framework64';x86='Framework'}[$env:REVIEW_ARCH])) { throw 'Hosted review required' }
$event = Get-Content -LiteralPath $env:GITHUB_EVENT_PATH -Raw | ConvertFrom-Json
$pr = $event.pull_request
if ($event.action -cnotin @('opened','synchronize','reopened') -or $pr.draft -isnot [bool] -or !$pr.draft -or
    $event.repository.full_name -cne 'krismcan/Mark-LV' -or $pr.base.repo.full_name -cne 'krismcan/Mark-LV' -or
    $pr.head.repo.full_name -cne 'krismcan/Mark-LV' -or $pr.base.sha -cne $parent -or
    $pr.base.ref -cne 'byok-c1-p290-message-token-observation-20261120' -or
    $pr.head.ref -cne 'byok-c1-p291-shared-revocation-effect-owner-20261120' -or
    $env:GITHUB_HEAD_REF -cne $pr.head.ref -or $env:GITHUB_BASE_REF -cne $pr.base.ref -or
    $pr.head.sha -cnotmatch '\A[0-9a-f]{40}\z') { throw 'Exact same-repository DRAFT required' }
function Git-Read([string[]]$Arguments) {
    $result = @(& git @Arguments)
    if ($LASTEXITCODE -ne 0) { throw 'Git read HOLD' }
    return $result
}
function Assert-NoLinks([string]$Path) {
    for ($p = [IO.Path]::GetFullPath($Path); $null -ne $p; $p = [IO.Path]::GetDirectoryName($p)) {
        if ((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse HOLD' }
    }
}
$head = [string](Git-Read @('rev-parse','HEAD'))
if ($head -cne $pr.head.sha) { throw 'Exact PR tip HOLD' }
$added = @('native_c1_successor/P291DevelopmentAdmissionSeam.cs','tests/p291_boundary/P291BoundaryTests.cs',
    'tests/p291_boundary/HostedReview.ps1','.github/workflows/p291-windows-boundary-review.yml',
    'docs/byok-c1-p291-trusted-owner-boundary.md')
$lineage = @(Git-Read @('rev-list','--parents','-n','1',$head))
if ($lineage.Count -ne 1 -or $lineage[0] -cne ($head + ' ' + $parent)) { throw 'Exact single-child ancestry HOLD' }
$actual = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $actual -CaseSensitive).Count) { throw 'Five additions required' }
$before = @(Git-Read @('ls-tree','-r',$parent))
$tree = @(Git-Read @('ls-tree','-r',$head))
$inherited = @($tree | Where-Object { ($_ -split "`t",2)[1] -cnotin $added })
if ($before.Count -ne 1175 -or $tree.Count -ne 1180 -or
    @(Compare-Object $before $inherited -CaseSensitive).Count) { throw 'Inherited tree HOLD' }
$paths = @(); $oids = @()
foreach ($entry in $tree) {
    if ($entry -cnotmatch '\A100644 blob ([0-9a-f]{40})\t([a-zA-Z0-9_./-]+)\z') { throw 'Tree shape HOLD' }
    $oids += $Matches[1]; $paths += $Matches[2]
}
function Source-Hashes {
    if ([string](Git-Read @('rev-parse','HEAD')) -cne $head -or
        @(Git-Read @('status','--porcelain=v1','--untracked-files=all','--ignored')).Count) { throw 'Source drift HOLD' }
    $disk = @($paths | & git hash-object --no-filters --stdin-paths)
    if ($LASTEXITCODE -ne 0 -or $disk.Count -ne $oids.Count) { throw 'Disk hash HOLD' }
    for ($i = 0; $i -lt $paths.Count; $i++) {
        Assert-NoLinks $paths[$i]
        if ((Get-Item -LiteralPath $paths[$i] -Force).PSIsContainer -or $disk[$i] -cne $oids[$i]) { throw 'Raw blob mismatch HOLD' }
        (Get-FileHash -LiteralPath $paths[$i] -Algorithm SHA256).Hash + ' ' + $paths[$i]
    }
}
Assert-NoLinks $env:RUNNER_TEMP
$build = Join-Path $env:RUNNER_TEMP ('p291-build-' + $env:REVIEW_ARCH)
$evidence = Join-Path $env:RUNNER_TEMP ('p291-evidence-' + $env:REVIEW_ARCH)
foreach ($path in @($build,$evidence)) {
    if (Test-Path -LiteralPath $path) { throw 'Output already exists HOLD' }
    New-Item -ItemType Directory -Path $path | Out-Null
}
$initialHashes = @(Source-Hashes)
$initialHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$original = @('tests/p95_native_custody_preflight/CustodyLedger.cs',
    'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs',
    'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs')
$owner = @($original) + @('native_c1_successor/P268ServiceOwnedPendingTransaction.cs')
$composition = @($owner) + @('native_c1_successor/P265DevelopmentPipeAdapter.cs',
    'native_c1_successor/P267DevelopmentAtomicService.cs','native_c1_successor/P269ComposedDevelopmentService.cs')
$boundary = @($composition) + @('native_c1_successor/P291DevelopmentAdmissionSeam.cs','tests/p291_boundary/P291BoundaryTests.cs')
$flags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P291_BOUNDARY_EXPERIMENT_ONLY',
    'C1_P265_DEVELOPMENT_ONLY','C1_P267_DEVELOPMENT_ONLY','C1_P268_DEVELOPMENT_ONLY','C1_P269_DEVELOPMENT_ONLY')
$messageSources = @('tests/p290_message_identity/MessageTokenDiagnostic.cs')
$messageFlags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P290_MESSAGE_TOKEN_DIAGNOSTIC_ONLY')
$dir = Join-Path $env:WINDIR ('Microsoft.NET/' + $env:REVIEW_FRAMEWORK + '/v4.0.30319')
$csc = (Resolve-Path -LiteralPath (Join-Path $dir 'csc.exe')).Path
$common = @('/nologo','/noconfig','/debug+','/optimize-','/warn:4','/warnaserror+','/target:exe',('/platform:' + $env:REVIEW_ARCH))
foreach ($r in @('System.dll','System.Core.dll','System.Security.dll','System.ServiceProcess.dll')) { $common += '/reference:' + (Join-Path $dir $r) }
function Compile([string]$Label, [string[]]$Sources, [string[]]$Defines, [string]$Main, [string]$Guard) {
    $output = Join-Path $build ($Label + '.exe')
    if (Test-Path -LiteralPath $output) { throw 'Binary exists HOLD' }
    $invokeArgs = @($common) + @('/main:' + $Main)
    if ($Main -ceq 'MessageTokenDiagnostic') { $invokeArgs += '/unsafe+' } # Only P290 needs native stack buffers.
    if ($Defines.Count) { $invokeArgs += '/define:' + ($Defines -join ';') }
    $invokeArgs += '/out:' + $output
    $invokeArgs += @($Sources | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
    & $csc @invokeArgs *> (Join-Path $build ($Label + '.raw'))
    $raw = $LASTEXITCODE
    $log = [IO.File]::ReadAllText((Join-Path $build ($Label + '.raw')))
    $codes = @([regex]::Matches($log, '\b(?:error|warning) (CS[0-9]{4}):') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    $rawHash = (Get-FileHash -LiteralPath (Join-Path $build ($Label + '.raw')) -Algorithm SHA256).Hash
    # Raw output retained in build dir; artifacts contain only literal labels, raw exits, codes/hashes.
    Add-Content -LiteralPath (Join-Path $evidence 'compiler.log') -Value ($Label + " RAW_EXIT=$raw CODES=" + ($codes -join ',') + ' RAW_SHA256=' + $rawHash)
    Add-Content -LiteralPath (Join-Path $evidence 'compiler-exits.txt') -Value ($Label + " RAW_EXIT=$raw")
    if ($Guard) {
        if ($raw -ne 1 -or (Test-Path -LiteralPath $output) -or $codes.Count -ne 1 -or $codes[0] -cne 'CS1029' -or
            $log -notmatch ('error CS1029:.*' + [regex]::Escape($Guard))) { throw 'Negative compiler guard HOLD' }
        Add-Content -LiteralPath (Join-Path $evidence 'compiler.log') -Value ($Label + ' GUARD_CHECK=PASS EXPECTED=' + $Guard)
    } elseif ($raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Positive compiler HOLD' }
}
function Run-Review([string]$Label, [string]$Pattern, [string]$CountGroup, [int]$Floor, [string]$Argument) {
    $exe = Join-Path $build ($Label + '.exe')
    $hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    Add-Content -LiteralPath (Join-Path $evidence 'test-binary.sha256') -Value ($Label + ' ' + $hash)
    $si = [Diagnostics.ProcessStartInfo]::new($exe)
    if ($Argument) { $si.ArgumentList.Add($Argument) }
    $si.UseShellExecute = $false; $si.CreateNoWindow = $true
    $si.RedirectStandardOutput = $true; $si.RedirectStandardError = $true
    $si.WorkingDirectory = $env:GITHUB_WORKSPACE; $si.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),
        @('TEMP',[IO.Path]::GetTempPath()),@('TMP',[IO.Path]::GetTempPath()),
        @('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),@('RUNNER_OS','Windows'),@('ImageOS','win22'))) {
        $si.Environment[$pair[0]] = $pair[1]
    }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $si; $launched = $false
    try {
        if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -cne $hash) { throw 'Binary drift HOLD' }
        try { $launched = $process.Start(); if (!$launched) { throw 'Launch HOLD' } }
        catch {
            Add-Content -LiteralPath (Join-Path $evidence 'runtime.exit') -Value ($Label + ' LAUNCH_FAILED RAW_EXIT=UNAVAILABLE NO_RETRY')
            throw
        }
        $stdout = $process.StandardOutput.ReadToEndAsync(); $stderr = $process.StandardError.ReadToEndAsync()
        if (!$process.WaitForExit(60000)) {
            # PowerShell 7 hosted API: terminate ONLY this disposable test process tree.
            $process.Kill($true)
            $stopped = $process.WaitForExit(5000)
            $rawText = if ($stopped) { [string]$process.ExitCode } else { 'UNAVAILABLE' }
            Add-Content -LiteralPath (Join-Path $evidence 'runtime.exit') -Value ($Label + ' TIMEOUT RAW_EXIT=' + $rawText)
            throw '60s watchdog HOLD; disposable teardown required'
        }
        $raw = $process.ExitCode
        Add-Content -LiteralPath (Join-Path $evidence 'runtime.exit') -Value ($Label + " RAW_EXIT=$raw")
        $out = $stdout.GetAwaiter().GetResult(); $err = $stderr.GetAwaiter().GetResult()
        $match = [regex]::Match($out, $Pattern)
        if (!$match.Success -or $err.Length) {
            # Keep raw failures in disposable build custody; upload no exception/identity data.
            [IO.File]::WriteAllText((Join-Path $build ($Label + '.stdout')), $out)
            [IO.File]::WriteAllText((Join-Path $build ($Label + '.stderr')), $err)
            $outHash = (Get-FileHash -LiteralPath (Join-Path $build ($Label + '.stdout')) -Algorithm SHA256).Hash
            $errHash = (Get-FileHash -LiteralPath (Join-Path $build ($Label + '.stderr')) -Algorithm SHA256).Hash
            Add-Content -LiteralPath (Join-Path $evidence 'runtime.log') -Value ($Label + ' UNEXPECTED_OUTPUT_REDACTED HOLD STDOUT_SHA256=' + $outHash + ' STDERR_SHA256=' + $errHash)
            throw 'Runtime output HOLD'
        }
        Add-Content -LiteralPath (Join-Path $evidence 'runtime.log') -Value $out
        if ($raw -ne 0 -or [int]$match.Groups[$CountGroup].Value -lt $Floor) { throw 'Runtime assertions HOLD' }
        if ($Label -ceq 'Message') {
            [IO.File]::WriteAllText((Join-Path $build 'p290-receipt.txt'), $out)
            Add-Content -LiteralPath (Join-Path $evidence 'runtime.log') -Value ('MESSAGE_RECEIPT_SHA256=' +
                (Get-FileHash -LiteralPath (Join-Path $build 'p290-receipt.txt') -Algorithm SHA256).Hash)
        }
        if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -cne $hash) { throw 'Binary drift HOLD' }
    } finally {
        try { if ($launched -and !$process.HasExited) { $process.Kill($true); if (!$process.WaitForExit(5000)) { throw 'Cleanup HOLD' } } }
        finally { $process.Dispose() }
    }
}
$ok = $false
try {
    Compile 'Original' $original @() 'Nayeon.ByokC1.P96NegativeProof' ''
    Compile 'Owner' (@($owner) + 'tests/p268_successor/P268RemediationTests.cs') $flags 'P268RemediationTests' ''
    Compile 'Composition' (@($composition) + 'tests/p269_successor/P269ComposedServiceTests.cs') $flags 'P269ComposedServiceTests' ''
    Compile 'Message' $messageSources $messageFlags 'MessageTokenDiagnostic' ''
    Compile 'Boundary' $boundary $flags 'Nayeon.ByokC1.P291Development.P291DevelopmentAdmissionSeam' ''
    foreach ($missing in @('ALL','RELEASE') + $flags) {
        $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -cne $missing })
        if ($missing -eq 'RELEASE') { $selected += 'RELEASE' }
        Compile ('boundary-guard-' + $missing) $boundary $selected 'Nayeon.ByokC1.P291Development.P291DevelopmentAdmissionSeam' 'P291_TEST_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED'
    }
    foreach ($missing in @('ALL','RELEASE') + $messageFlags) {
        $selected = @($messageFlags | Where-Object { $missing -ne 'ALL' -and $_ -cne $missing })
        if ($missing -eq 'RELEASE') { $selected += 'RELEASE' }
        Compile ('message-guard-' + $missing) $messageSources $selected 'MessageTokenDiagnostic' 'P290_DIAGNOSTIC_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED'
    }
    $bits = if ($env:REVIEW_ARCH -eq 'x64') { 64 } else { 32 }
    $originalPattern = '\A(?:PASS [a-z0-9-]+\r\n){15}' +
        'P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=(?<cases>15)\r\nP96_NATIVE_ACTUAL_COORDINATOR_TESTS_FAILED=0\r\n' +
        'P96_LEGACY_POST_CHECK_REVOCATION_RACE=REPRODUCED_IN_FAKE_ONLY\r\nP96_REAL_NATIVE_EFFECTS=NONE\r\n' +
        'P96_SECURITY_FINDING=OPEN\r\nP96_C1_PRODUCTION_RELEASE=HOLD\r\n\z'
    Run-Review 'Original' $originalPattern 'cases' 15 ''
    $ownerPattern = '\A(?:PASS [a-zA-Z0-9-]+\r\n){33}P268_SUCCESSOR=PASS CASES=(?<cases>33) ASSERTIONS=[1-9][0-9]* BITS=' + $bits +
        '\r\nP268_FIXED_PATH=ISOLATED_FAKE_ONLY PRODUCTION=HOLD TRUSTED_ISSUER=NOT_CONNECTED\r\n\z'
    Run-Review 'Owner' $ownerPattern 'cases' 33 ''
    $compositionPattern = '\A(?:PASS order (?:Save|Replace|Delete) [012] (?:False|True)\r\n){18}' +
        'P269_COMPOSITION=PASS CASES=(?<cases>23) ASSERTIONS=[1-9][0-9]* BITS=' + $bits +
        '\r\nP269_SCOPE=DEVELOPMENT_ONLY DENIAL_ONLY PRODUCTION=HOLD\r\n\z'
    Run-Review 'Composition' $compositionPattern 'cases' 23 ''
    $messagePattern = '\AP290_DIAGNOSTIC=PASS CAPTURES=6 DENIALS=(?<denials>[0-9]+) CHECKS=[1-9][0-9]* BITS=' + $bits +
        '\r\nP290_TOKEN=IDENTIFICATION LAST_READ=ORDERED REVERT=CHECKED INVALID_HANDLE=DENIED FALLBACK=DENIED\r\n' +
        'P290_AUTHORITY=NONE PRIVILEGE=UNVERIFIED REAL_KEY=NO_GO PRODUCTION=HOLD P96_ORIGINAL=HIGH_OPEN APPROVALS=0/7 FULL_REGRESSIONS=0/3\r\n\z'
    Run-Review 'Message' $messagePattern 'denials' 24 ''
    $boundaryPattern = '\AP291_BOUNDARY=PASS CASES=(?<cases>11) ASSERTIONS=[1-9][0-9]* BITS=' + $bits +
        '\r\nP291_NATIVE_RECEIPT=UNTRUSTED PEER=DENIED PREPARE_ROUTE=NONE POSITIVE=TEST_ONLY\r\n' +
        'P291_ISSUER=ABSENT REAL_CONSENT=ABSENT NONDEPLOYABLE PRODUCTION=HOLD P96_ORIGINAL=STILL_VULNERABLE APPROVALS=0/7 FULL_REGRESSIONS=0/3\r\n\z'
    Run-Review 'Boundary' $boundaryPattern 'cases' 11 (Join-Path $build 'p290-receipt.txt')
    $ok = $true
} finally {
    try {
        $finalHashes = @(Source-Hashes)
        $finalHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initialHashes $finalHashes -CaseSensitive).Count) { throw 'After-source drift HOLD' }
    } catch { $ok = $false; throw } finally {
        'P291_REVIEW=HOLD NONDEPLOYABLE_BOUNDARY PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
            Set-Content -LiteralPath (Join-Path $evidence 'scope.log')
        $allowed = @('source-before.sha256','source-after.sha256','compiler.log','compiler-exits.txt',
            'test-binary.sha256','runtime.exit','runtime.log','scope.log')
        foreach ($file in Get-ChildItem -LiteralPath $evidence -Force) {
            if ($file.Name -cnotin $allowed -or $file.PSIsContainer -or
                ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Text evidence allowlist HOLD' }
        }
        if ($ok -and @(Compare-Object @($allowed | Sort-Object) @(Get-ChildItem -LiteralPath $evidence -Name | Sort-Object) -CaseSensitive).Count) {
            throw 'Missing evidence HOLD'
        }
        if ($ok) {
            'P291_REVIEW=PASS NONDEPLOYABLE_BOUNDARY PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
                Set-Content -LiteralPath (Join-Path $evidence 'scope.log')
        }
    }
}
