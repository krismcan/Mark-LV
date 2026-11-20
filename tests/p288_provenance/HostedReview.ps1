# Hosted only. Locally parse as data; never execute/dot-source this script.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '3edf7130daa41c2ac240f9a92d6745ac5a726eaa'
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
    $pr.base.ref -cne 'byok-c1-p287-service-client-pipe-boundary-20261119' -or
    $pr.head.ref -cne 'byok-c1-p288-trusted-role-provenance-20261120' -or
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
$added = @('native_c1_successor/P288SyntheticProvenanceSequence.cs',
    'tests/p288_provenance/ProvenanceSequenceTests.cs','tests/p288_provenance/HostedReview.ps1',
    '.github/workflows/p288-windows-provenance-sequence-review.yml',
    'docs/byok-c1-p288-trusted-role-provenance.md')
$lineage = @(Git-Read @('rev-list','--parents','-n','1',$head))
if ($lineage.Count -ne 1 -or $lineage[0] -cne ($head + ' ' + $parent)) { throw 'Exact single-child ancestry HOLD' }
$actual = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $actual -CaseSensitive).Count) { throw 'Five additions required' }
$before = @(Git-Read @('ls-tree','-r',$parent))
$tree = @(Git-Read @('ls-tree','-r',$head))
$inherited = @($tree | Where-Object { ($_ -split "`t",2)[1] -cnotin $added })
if ($before.Count -ne 1162 -or $tree.Count -ne 1167 -or
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
$build = Join-Path $env:RUNNER_TEMP ('p288-build-' + $env:REVIEW_ARCH)
$evidence = Join-Path $env:RUNNER_TEMP ('p288-evidence-' + $env:REVIEW_ARCH)
foreach ($path in @($build,$evidence)) {
    if (Test-Path -LiteralPath $path) { throw 'Output already exists HOLD' }
    New-Item -ItemType Directory -Path $path | Out-Null
}
$initialHashes = @(Source-Hashes)
$initialHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$sources = @('native_c1_successor/P288SyntheticProvenanceSequence.cs','tests/p288_provenance/ProvenanceSequenceTests.cs',
    'native_c1_successor/P287ServiceClientPipeBoundary.cs','tests/p287_service_client/ServiceClientBoundaryTests.cs',
    'native_c1_successor/P286SafeDevelopmentPipeAdapter.cs','tests/p286_async_pipe/AsyncPipeLifetimeTests.cs')
$flags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P288_SYNTHETIC_PROVENANCE_REVIEW_ONLY','C1_P287_SERVICE_CLIENT_REVIEW_ONLY',
    'C1_P265_DEVELOPMENT_ONLY','C1_P286_ASYNC_PIPE_REVIEW_ONLY')
$dir = Join-Path $env:WINDIR ('Microsoft.NET/' + $env:REVIEW_FRAMEWORK + '/v4.0.30319')
$csc = (Resolve-Path -LiteralPath (Join-Path $dir 'csc.exe')).Path
$common = @('/nologo','/noconfig','/warn:4','/warnaserror+','/target:exe','/main:ProvenanceSequenceTests',('/platform:' + $env:REVIEW_ARCH))
foreach ($r in @('System.dll','System.Core.dll','System.Security.dll')) { $common += '/reference:' + (Join-Path $dir $r) }
function Compile([string]$Label, [string[]]$Defines, [string]$Guard) {
    $output = Join-Path $build ($Label + '.exe')
    if (Test-Path -LiteralPath $output) { throw 'Binary exists HOLD' }
    $invokeArgs = @($common)
    if ($Defines.Count) { $invokeArgs += '/define:' + ($Defines -join ';') }
    $invokeArgs += '/out:' + $output
    $invokeArgs += @($sources | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
    & $csc @invokeArgs *> (Join-Path $build ($Label + '.raw'))
    $raw = $LASTEXITCODE
    $log = [IO.File]::ReadAllText((Join-Path $build ($Label + '.raw')))
    # Raw diagnostics stay in the disposable build directory. Publish only bounded
    # codes/hashes, never source lines, user paths, raw stderr or identity values.
    $codes = @([regex]::Matches($log, '\b(?:error|warning) (CS[0-9]{4}):') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    $rawHash = (Get-FileHash -LiteralPath (Join-Path $build ($Label + '.raw')) -Algorithm SHA256).Hash
    Add-Content -LiteralPath (Join-Path $evidence 'compiler.log') -Value ($Label + " RAW_EXIT=$raw CODES=" + ($codes -join ',') + ' RAW_SHA256=' + $rawHash)
    Add-Content -LiteralPath (Join-Path $evidence 'compiler-exits.txt') -Value ($Label + " RAW_EXIT=$raw")
    if ($Guard) {
        if ($raw -ne 1 -or (Test-Path -LiteralPath $output) -or
            $log -notmatch ('error CS1029:.*' + [regex]::Escape($Guard))) { throw 'Compiler negative guard HOLD' }
        Add-Content -LiteralPath (Join-Path $evidence 'compiler.log') -Value ($Label + ' GUARD_CHECK=PASS EXPECTED=' + $Guard)
    } elseif ($raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compiler HOLD' }
}
$ok = $false
try {
    Compile 'P288Focused' $flags ''
    foreach ($missing in @('ALL','RELEASE') + $flags) {
        $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -cne $missing })
        if ($missing -eq 'RELEASE') { $selected += 'RELEASE' }
        $guard = 'P288_SYNTHETIC_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED'
        if ($missing -eq 'C1_P287_SERVICE_CLIENT_REVIEW_ONLY') { $guard = 'P287_TEST_ONLY_DEBUG_ISOLATED_AND_OPT_IN_REQUIRED' }
        if ($missing -eq 'C1_P265_DEVELOPMENT_ONLY') { $guard = 'P265_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED' }
        if ($missing -eq 'C1_P286_ASYNC_PIPE_REVIEW_ONLY') { $guard = 'P286_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED' }
        Compile ('guard-' + $missing) $selected $guard
    }
    $exe = Join-Path $build 'P288Focused.exe'
    $binaryHash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    $binaryHash | Set-Content -LiteralPath (Join-Path $evidence 'test-binary.sha256')
    $si = [Diagnostics.ProcessStartInfo]::new($exe)
    $si.UseShellExecute = $false; $si.CreateNoWindow = $true
    $si.RedirectStandardOutput = $true; $si.RedirectStandardError = $true
    $si.WorkingDirectory = $env:GITHUB_WORKSPACE; $si.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),
        @('TEMP',[IO.Path]::GetTempPath()),@('TMP',[IO.Path]::GetTempPath()),
        @('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),@('RUNNER_OS','Windows'),@('ImageOS','win22'))) {
        $si.Environment[$pair[0]] = $pair[1]
    }
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -cne $binaryHash) { throw 'Binary drift HOLD' }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $si
    try {
        if (!$process.Start()) { throw 'Test launch HOLD' }
        $stdout = $process.StandardOutput.ReadToEndAsync(); $stderr = $process.StandardError.ReadToEndAsync()
        if (!$process.WaitForExit(60000)) {
            $process.Kill($true)
            $stopped = $process.WaitForExit(5000)
            $rawText = if ($stopped) { [string]$process.ExitCode } else { 'UNAVAILABLE' }
            $rawText | Set-Content -LiteralPath (Join-Path $evidence 'runtime.exit')
            throw 'Test watchdog HOLD; disposable teardown required'
        }
        $raw = $process.ExitCode
        $raw | Set-Content -LiteralPath (Join-Path $evidence 'runtime.exit')
        $out = $stdout.GetAwaiter().GetResult(); $err = $stderr.GetAwaiter().GetResult()
        $bits = if ($env:REVIEW_ARCH -eq 'x64') { 64 } else { 32 }
        $pattern = '\AP286_FOCUSED=PASS\r\nP287_FOCUSED=PASS CASES=[0-9]+ ASSERTIONS=[0-9]+ BITS=' + $bits +
            '\r\nPRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=HIGH_OPEN\r\n' +
            'P288_FOCUSED=PASS CASES=([0-9]+) ASSERTIONS=([0-9]+) BITS=' + $bits +
            '\r\nP288_LIVE=HOLD PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=HIGH_OPEN\r\n\z'
        $match = [regex]::Match($out, $pattern)
        if (!$match.Success -or $err.Length) {
            $receipt = 'UNEXPECTED_OUTPUT_REDACTED HOLD'
            $safeFailure = [regex]::Match($out, '(?:\A|\r\n)(P288_FOCUSED=HOLD GROUP=(?:INHERITED|LIVE_DENIAL|FAULTS|EVENT_ORDER|TICKETS|CALLBACK_CANCEL) CASES=[0-9]{1,10} ASSERTIONS=[0-9]{1,10} ERROR=[A-Za-z][A-Za-z0-9]{0,80})\r\n\z')
            if (!$err.Length -and $safeFailure.Success) { $receipt = $safeFailure.Groups[1].Value }
            $receipt | Set-Content -LiteralPath (Join-Path $evidence 'runtime.log')
            throw 'Unexpected test output HOLD'
        }
        $out | Set-Content -LiteralPath (Join-Path $evidence 'runtime.log')
        if ($raw -ne 0 -or [int]$match.Groups[1].Value -lt 400 -or [int]$match.Groups[2].Value -lt 4000) { throw 'Focused tests HOLD' }
        if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -cne $binaryHash) { throw 'After-binary drift HOLD' }
    } finally { $process.Dispose() }
    $ok = $true
} finally {
    try {
        $finalHashes = @(Source-Hashes)
        $finalHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initialHashes $finalHashes -CaseSensitive).Count) { throw 'After-source drift HOLD' }
    } catch { $ok = $false; throw } finally {
        'P288_REVIEW=HOLD PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
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
            'P288_REVIEW=PASS PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
                Set-Content -LiteralPath (Join-Path $evidence 'scope.log')
        }
    }
}
