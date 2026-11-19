# Hosted orchestration only. Local review must parse this file as data and use
# direct csc commands, never execute/dot-source/evaluate this manifest locally.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '52ff1f041afc06a48c41c92aac8ef404d71cc0cb'
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
    $pr.base.ref -cne 'byok-c1-p285-durable-hosted-test-boundary-20261119' -or
    $pr.head.ref -cne 'byok-c1-p286-async-pipe-handle-lifetime-20261119' -or
    $env:GITHUB_HEAD_REF -cne $pr.head.ref -or $env:GITHUB_BASE_REF -cne $pr.base.ref -or
    $pr.head.sha -cnotmatch '\A[0-9a-f]{40}\z') { throw 'Exact same-repository draft required' }
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
if ($head -cne $pr.head.sha) { throw 'Exact PR head HOLD' }
$added = @('native_c1_successor/P286SafeDevelopmentPipeAdapter.cs',
    'tests/p286_async_pipe/AsyncPipeLifetimeTests.cs',
    'tests/p286_async_pipe/HostedReview.ps1',
    '.github/workflows/p286-windows-async-pipe-lifetime-review.yml',
    'docs/byok-c1-p286-async-pipe-handle-lifetime.md')
# Bounded linear review history. Every commit must remain additive versus P285;
# no inherited-file edits, merges, deletes or renames are admitted.
$history = @(Git-Read @('rev-list','--reverse','--parents',($parent + '..' + $head)))
if ($history.Count -lt 1 -or $history.Count -gt 12) { throw 'Bounded P286 history HOLD' }
$previous = $parent
foreach ($line in $history) {
    if ($line -cnotmatch '\A([0-9a-f]{40}) ([0-9a-f]{40})\z') { throw 'Linear P286 history HOLD' }
    $commit = $Matches[1]
    if ($Matches[2] -cne $previous) { throw 'P286 ancestry HOLD' }
    foreach ($change in @(Git-Read @('diff','--name-status','--no-renames',$previous,$commit))) {
        if ($change -cnotmatch '\A[AM]\t([a-zA-Z0-9_./-]+)\z' -or
            $Matches[1] -cnotin $added) { throw 'P286 repair scope HOLD' }
    }
    $previous = $commit
}
if ($previous -cne $head) { throw 'Exact P286 tip HOLD' }
$actual = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $actual -CaseSensitive).Count) { throw 'Additive scope HOLD' }
$before = @(Git-Read @('ls-tree','-r',$parent))
$tree = @(Git-Read @('ls-tree','-r',$head))
$inherited = @($tree | Where-Object { ($_ -split "`t",2)[1] -cnotin $added })
if ($before.Count -ne 1152 -or $tree.Count -ne 1157 -or
    @(Compare-Object $before $inherited -CaseSensitive).Count) { throw 'Inherited blobs HOLD' }
$paths = @(); $oids = @()
foreach ($entry in $tree) {
    if ($entry -cnotmatch '\A100644 blob ([0-9a-f]{40})\t([a-zA-Z0-9_./-]+)\z') { throw 'Tree shape HOLD' }
    $oids += $Matches[1]; $paths += $Matches[2]
}
function Source-Hashes {
    if ([string](Git-Read @('rev-parse','HEAD')) -cne $head -or
        @(Git-Read @('status','--porcelain=v1','--untracked-files=all','--ignored')).Count) { throw 'Source drift HOLD' }
    $disk = @($paths | & git hash-object --no-filters --stdin-paths)
    if ($LASTEXITCODE -ne 0 -or $disk.Count -ne $oids.Count) { throw 'Disk hashes HOLD' }
    for ($i = 0; $i -lt $paths.Count; $i++) {
        Assert-NoLinks $paths[$i]
        if ((Get-Item -LiteralPath $paths[$i] -Force).PSIsContainer -or $disk[$i] -cne $oids[$i]) { throw 'Disk blob HOLD' }
        (Get-FileHash -LiteralPath $paths[$i] -Algorithm SHA256).Hash + ' ' + $paths[$i]
    }
}
Assert-NoLinks $env:RUNNER_TEMP
$build = Join-Path $env:RUNNER_TEMP ('p285-build-' + $env:REVIEW_ARCH)
$evidence = Join-Path $env:RUNNER_TEMP ('p285-evidence-' + $env:REVIEW_ARCH)
foreach ($path in @($build,$evidence)) {
    if (Test-Path -LiteralPath $path) { throw 'Output exists HOLD' }
    New-Item -ItemType Directory -Path $path | Out-Null
}
$initialHashes = @(Source-Hashes)
$initialHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$sources = @('tests/p95_native_custody_preflight/CustodyLedger.cs',
    'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs',
    'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs',
    'tests/p99_original_native_c1_denial/ServiceGate.cs', 'tests/p99_original_native_c1_denial/ProtectedAcl.cs',
    'native_c1_candidate/P261ScmReadOnlyAdmission.cs', 'native_c1_candidate/P279RunningServiceTokenReadOnly.cs',
    'native_c1_candidate/ServiceBoundRequestIdentity.cs', 'native_c1_successor/P286SafeDevelopmentPipeAdapter.cs',
    'native_c1_successor/P267DevelopmentAtomicService.cs', 'native_c1_successor/P268ServiceOwnedPendingTransaction.cs',
    'native_c1_successor/P269ComposedDevelopmentService.cs', 'native_c1_successor/P270DevelopmentDurableWitness.cs',
    'native_c1_successor/P271DurableDevelopmentBridge.cs', 'native_c1_successor/P282ExecutingServiceCustody.cs',
    'native_c1_successor/P284DurableOperationAdmission.cs', 'tests/p284_durable_operation/DurableOperationAdmissionTests.cs')
$flags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P265_DEVELOPMENT_ONLY','C1_P267_DEVELOPMENT_ONLY',
    'C1_P268_DEVELOPMENT_ONLY','C1_P269_DEVELOPMENT_ONLY','C1_P270_DEVELOPMENT_ONLY',
    'C1_P271_DEVELOPMENT_ONLY','C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY','C1_P284_DURABLE_OPERATION_REVIEW_ONLY')
$flags += 'C1_P286_ASYNC_PIPE_REVIEW_ONLY'
$hostFlags = @('DEBUG','C1_P285_HOSTED_ROOT_REVIEW_ONLY')
$dir = Join-Path $env:WINDIR ('Microsoft.NET/' + $env:REVIEW_FRAMEWORK + '/v4.0.30319')
$csc = (Resolve-Path -LiteralPath (Join-Path $dir 'csc.exe')).Path
$common = @('/nologo','/noconfig','/warn:4','/warnaserror+','/target:exe','/debug+','/optimize-',('/platform:' + $env:REVIEW_ARCH))
foreach ($r in @('System.dll','System.Core.dll','System.Security.dll','System.ServiceProcess.dll')) { $common += '/reference:' + (Join-Path $dir $r) }
function Compile([string]$Label, [string[]]$Inputs, [string[]]$Defines, [string]$Main, [string]$Guard) {
    $output = Join-Path $build ($Label + '.exe')
    if (Test-Path -LiteralPath $output) { throw 'Binary exists HOLD' }
    $invokeArgs = @($common)
    if ($Defines.Count) { $invokeArgs += '/define:' + ($Defines -join ';') }
    $invokeArgs += '/main:' + $Main
    $invokeArgs += '/out:' + $output
    $invokeArgs += @($Inputs | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
    & $csc @invokeArgs *> (Join-Path $build ($Label + '.raw'))
    $raw = $LASTEXITCODE
    $log = [IO.File]::ReadAllText((Join-Path $build ($Label + '.raw')))
    foreach ($p in @($env:GITHUB_WORKSPACE,$env:RUNNER_TEMP,$env:WINDIR)) { $log = $log.Replace($p,'<PATH>') }
    Add-Content -LiteralPath (Join-Path $evidence 'compiler.log') -Value ($Label + " RAW_EXIT=$raw`n" + $log)
    Add-Content -LiteralPath (Join-Path $evidence 'compiler-exits.txt') -Value ($Label + " RAW_EXIT=$raw")
    if ($Guard) {
        if ($raw -ne 1 -or (Test-Path -LiteralPath $output) -or $log -notmatch ('error CS1029:.*' + [regex]::Escape($Guard))) { throw 'Compiler guard HOLD' }
    } elseif ($raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compiler HOLD' }
}
$ok = $false
try {
    Compile 'P284Durable' $sources $flags 'DurableOperationAdmissionTests' ''
    $hostSource = @('tests/p285_durable_hosted/P285HostedDurableRunner.cs')
    Compile 'P285Host' $hostSource $hostFlags 'P285HostedDurableRunner' ''
    Compile 'P286Focused' @('native_c1_successor/P286SafeDevelopmentPipeAdapter.cs','tests/p286_async_pipe/AsyncPipeLifetimeTests.cs') @('DEBUG','C1_P265_DEVELOPMENT_ONLY','C1_P286_ASYNC_PIPE_REVIEW_ONLY') 'AsyncPipeLifetimeTests' ''
    foreach ($missing in @('ALL','RELEASE') + $flags) {
        $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -cne $missing })
        if ($missing -eq 'RELEASE') { $selected += 'RELEASE' }
        Compile ('p284-guard-' + $missing) $sources $selected 'DurableOperationAdmissionTests' $(if ($missing -ceq 'C1_P286_ASYNC_PIPE_REVIEW_ONLY') { 'P286_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED' } else { 'P284_TEST_ONLY_ALL_DURABLE_FLAGS_REQUIRED' })
        if ($missing -cin @('ALL','RELEASE','DEBUG')) {
            $guardLog = [IO.File]::ReadAllText((Join-Path $build ('p284-guard-' + $missing + '.raw')))
            if ($guardLog -notmatch 'error CS1029:.*P286_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED') { throw 'P286 release/debug guard HOLD' }
        }
    }
    foreach ($missing in @('ALL','RELEASE') + $hostFlags) {
        $selected = @($hostFlags | Where-Object { $missing -ne 'ALL' -and $_ -cne $missing })
        if ($missing -eq 'RELEASE') { $selected += 'RELEASE' }
        Compile ('p285-guard-' + $missing) $hostSource $selected 'P285HostedDurableRunner' 'P285_HOSTED_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED'
    }
    # Focused tests use managed fakes only. No native pipe, ACL, root or credential work.
    $focused = [Diagnostics.ProcessStartInfo]::new((Join-Path $build 'P286Focused.exe'))
    $focused.UseShellExecute = $false; $focused.CreateNoWindow = $true
    $focused.RedirectStandardOutput = $true; $focused.RedirectStandardError = $true
    $focused.WorkingDirectory = $env:GITHUB_WORKSPACE
    $focused.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),
        @('TEMP',[IO.Path]::GetTempPath()),@('TMP',[IO.Path]::GetTempPath()),
        @('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),@('RUNNER_OS','Windows'))) {
        $focused.Environment[$pair[0]] = $pair[1]
    }
    $fp = [Diagnostics.Process]::new(); $fp.StartInfo = $focused
    try {
        if (!$fp.Start()) { throw 'Focused launch HOLD' }
        $fo = $fp.StandardOutput.ReadToEndAsync(); $fe = $fp.StandardError.ReadToEndAsync()
        if (!$fp.WaitForExit(30000)) {
            $fp.Kill($true)
            $stopped = $fp.WaitForExit(5000)
            $exitText = if ($stopped) { [string]$fp.ExitCode } else { 'UNAVAILABLE' }
            Set-Content -LiteralPath (Join-Path $evidence 'focused.exit') -Value $exitText
            throw 'Focused watchdog HOLD'
        }
        $raw = $fp.ExitCode
        Set-Content -LiteralPath (Join-Path $evidence 'focused.exit') -Value $raw
        if ($raw -ne 0 -or $fo.GetAwaiter().GetResult() -cne "P286_FOCUSED=PASS`r`n" -or $fe.GetAwaiter().GetResult().Length) {
            'P286_FOCUSED=HOLD' | Set-Content -LiteralPath (Join-Path $evidence 'focused.log')
            throw 'Focused tests HOLD'
        }
        'P286_FOCUSED=PASS' | Set-Content -LiteralPath (Join-Path $evidence 'focused.log')
    } finally { $fp.Dispose() }
    $exe = Join-Path $build 'P284Durable.exe'
    $pin = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    $pin | Set-Content -LiteralPath (Join-Path $evidence 'durable-binary.sha256')
    $si = [Diagnostics.ProcessStartInfo]::new((Join-Path $build 'P285Host.exe'))
    $si.UseShellExecute = $false; $si.CreateNoWindow = $true
    $si.RedirectStandardOutput = $true; $si.RedirectStandardError = $true
    $si.WorkingDirectory = $build; $si.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),
        @('TEMP',[IO.Path]::GetTempPath()),@('TMP',[IO.Path]::GetTempPath()),
        @('RUNNER_TEMP',$env:RUNNER_TEMP),@('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),
        @('RUNNER_OS','Windows'),@('ImageOS','win22'),@('P285_HOSTED_ROOTS_REVIEW_ONLY','1'),
        @('P285_DURABLE_EXE',$exe),@('P285_DURABLE_SHA256',$pin))) { $si.Environment[$pair[0]] = $pair[1] }
    $p = [Diagnostics.Process]::new(); $p.StartInfo = $si
    try {
        if (!$p.Start()) { throw 'Host launch HOLD' }
        $stdout = $p.StandardOutput.ReadToEndAsync(); $stderr = $p.StandardError.ReadToEndAsync()
        if (!$p.WaitForExit(190000)) {
            $p.Kill($true)
            $stopped = $p.WaitForExit(5000)
            $exitText = if ($stopped) { [string]$p.ExitCode } else { 'UNAVAILABLE' }
            Set-Content -LiteralPath (Join-Path $evidence 'host.exit') -Value $exitText
            throw 'Host timeout HOLD; disposable runner teardown required'
        }
        $raw = $p.ExitCode
        Set-Content -LiteralPath (Join-Path $evidence 'host.exit') -Value $raw
        $out = $stdout.GetAwaiter().GetResult(); $err = $stderr.GetAwaiter().GetResult()
        # Success requires these exact lines. Unexpected text is never published.
        $bits = if ($env:REVIEW_ARCH -eq 'x64') { 64 } else { 32 }
        $expected = "P285_HOST=PASS BITS=$bits`r`nALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=OPEN P76_P216=UNWAIVED`r`n"
        if ($raw -ne 0 -or $out -cne $expected -or $err.Length) {
            $stage = 'unknown'
            $stageMatch = [regex]::Match($out, '(?m)^P285_HOST_HOLD_STAGE=(host-claims|process-identity|temp-shape|temp-owner|runner-temp|build-path|exe-identity|exe-sha|evidence-root|root-create|child-launch|child-completion|cleanup|evidence-write)\r?$')
            if ($stageMatch.Success) { $stage = $stageMatch.Groups[1].Value }
            Write-Output ('P285_HOST_HOLD_STAGE=' + $stage)
            throw 'Durable hosted runtime HOLD'
        }
    } finally { $p.Dispose() }
    $ok = $true
} finally {
    try {
        $finalHashes = @(Source-Hashes)
        $finalHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initialHashes $finalHashes -CaseSensitive).Count) { throw 'After-source HOLD' }
    } catch { $ok = $false; throw } finally {
        # Publish PASS only after the complete evidence inventory has passed.
        'P286_REVIEW=HOLD ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
            Set-Content -LiteralPath (Join-Path $evidence 'scope.log')
        $allowed = @('focused.exit','focused.log','source-before.sha256','source-after.sha256','compiler.log','compiler-exits.txt','durable-binary.sha256',
            'runtime.stdout.log','runtime.stderr.log','runtime.exit','host.log','host.exit','scope.log')
        foreach ($file in Get-ChildItem -LiteralPath $evidence -Force) {
            if ($file.Name -cnotin $allowed -or $file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Evidence allowlist HOLD' }
        }
        if ($ok -and @(Compare-Object @($allowed | Sort-Object) @(Get-ChildItem -LiteralPath $evidence -Name | Sort-Object) -CaseSensitive).Count) { throw 'Missing evidence HOLD' }
        if ($ok) {
            'P286_REVIEW=PASS ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
                Set-Content -LiteralPath (Join-Path $evidence 'scope.log')
        }
    }
}
