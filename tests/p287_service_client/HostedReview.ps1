# Hosted only. Locally parse as data; never execute/dot-source this script.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = 'bf96a2a5d6570da7397770445967fa2434dd9008'
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
    $pr.base.ref -cne 'byok-c1-p286-async-pipe-handle-lifetime-20261119' -or
    $pr.head.ref -cne 'byok-c1-p287-service-client-pipe-boundary-20261119' -or
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
$added = @('native_c1_successor/P287ServiceClientPipeBoundary.cs',
    'tests/p287_service_client/ServiceClientBoundaryTests.cs','tests/p287_service_client/HostedReview.ps1',
    '.github/workflows/p287-windows-service-client-boundary-review.yml',
    'docs/byok-c1-p287-service-client-identity-boundary.md')
$history = @(Git-Read @('rev-list','--reverse','--parents',($parent + '..' + $head)))
if ($history.Count -lt 1 -or $history.Count -gt 12) { throw 'Bounded P287 history HOLD' }
$previous = $parent
foreach ($line in $history) {
    if ($line -cnotmatch '\A([0-9a-f]{40}) ([0-9a-f]{40})\z') { throw 'Linear history HOLD' }
    $commit = $Matches[1]
    if ($Matches[2] -cne $previous) { throw 'Exact ancestry HOLD' }
    foreach ($change in @(Git-Read @('diff','--name-status','--no-renames',$previous,$commit))) {
        if ($change -cnotmatch '\A[AM]\t([a-zA-Z0-9_./-]+)\z' -or $Matches[1] -cnotin $added) { throw 'Additive repair scope HOLD' }
    }
    $previous = $commit
}
if ($previous -cne $head) { throw 'History tip HOLD' }
$actual = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $actual -CaseSensitive).Count) { throw 'Five additions required' }
$before = @(Git-Read @('ls-tree','-r',$parent))
$tree = @(Git-Read @('ls-tree','-r',$head))
$inherited = @($tree | Where-Object { ($_ -split "`t",2)[1] -cnotin $added })
if ($before.Count -ne 1157 -or $tree.Count -ne 1162 -or
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
$build = Join-Path $env:RUNNER_TEMP ('p287-build-' + $env:REVIEW_ARCH)
$evidence = Join-Path $env:RUNNER_TEMP ('p287-evidence-' + $env:REVIEW_ARCH)
foreach ($path in @($build,$evidence)) {
    if (Test-Path -LiteralPath $path) { throw 'Output already exists HOLD' }
    New-Item -ItemType Directory -Path $path | Out-Null
}
$initialHashes = @(Source-Hashes)
$initialHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$sources = @('native_c1_successor/P287ServiceClientPipeBoundary.cs','tests/p287_service_client/ServiceClientBoundaryTests.cs',
    'native_c1_successor/P286SafeDevelopmentPipeAdapter.cs','tests/p286_async_pipe/AsyncPipeLifetimeTests.cs')
$flags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P287_SERVICE_CLIENT_REVIEW_ONLY',
    'C1_P265_DEVELOPMENT_ONLY','C1_P286_ASYNC_PIPE_REVIEW_ONLY')
$dir = Join-Path $env:WINDIR ('Microsoft.NET/' + $env:REVIEW_FRAMEWORK + '/v4.0.30319')
$csc = (Resolve-Path -LiteralPath (Join-Path $dir 'csc.exe')).Path
$common = @('/nologo','/noconfig','/warn:4','/warnaserror+','/target:exe','/main:ServiceClientBoundaryTests',('/platform:' + $env:REVIEW_ARCH))
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
    foreach ($p in @($env:GITHUB_WORKSPACE,$env:RUNNER_TEMP,$env:WINDIR)) { $log = $log.Replace($p,'<PATH>') }
    Add-Content -LiteralPath (Join-Path $evidence 'compiler.log') -Value ($Label + " RAW_EXIT=$raw`n" + $log)
    Add-Content -LiteralPath (Join-Path $evidence 'compiler-exits.txt') -Value ($Label + " RAW_EXIT=$raw")
    if ($Guard) {
        if ($raw -ne 1 -or (Test-Path -LiteralPath $output) -or
            $log -notmatch ('error CS1029:.*' + [regex]::Escape($Guard))) { throw 'Compiler negative guard HOLD' }
    } elseif ($raw -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compiler HOLD' }
}
$ok = $false
try {
    Compile 'P287Focused' $flags ''
    foreach ($missing in @('ALL','RELEASE') + $flags) {
        $selected = @($flags | Where-Object { $missing -ne 'ALL' -and $_ -cne $missing })
        if ($missing -eq 'RELEASE') { $selected += 'RELEASE' }
        $guard = 'P287_TEST_ONLY_DEBUG_ISOLATED_AND_OPT_IN_REQUIRED'
        if ($missing -eq 'C1_P265_DEVELOPMENT_ONLY') { $guard = 'P265_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED' }
        if ($missing -eq 'C1_P286_ASYNC_PIPE_REVIEW_ONLY') { $guard = 'P286_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED' }
        Compile ('guard-' + $missing) $selected $guard
    }
    $exe = Join-Path $build 'P287Focused.exe'
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
        $pattern = '\AP286_FOCUSED=PASS\r\nP287_FOCUSED=PASS CASES=([0-9]+) ASSERTIONS=([0-9]+) BITS=' + $bits +
            '\r\nPRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=HIGH_OPEN\r\n\z'
        $match = [regex]::Match($out, $pattern)
        if (!$match.Success -or $err.Length) {
            $safeFailure = '\A(?:P286_FOCUSED=(?:PASS|HOLD)\r\n)?P287_FOCUSED=HOLD CASES=[0-9]+ ASSERTIONS=[0-9]+ ERROR=[A-Za-z][A-Za-z0-9]{0,80}\r\n\z'
            $receipt = if (!$err.Length -and $out -cmatch $safeFailure) { $out } else { 'UNEXPECTED_OUTPUT_REDACTED HOLD' }
            $receipt | Set-Content -LiteralPath (Join-Path $evidence 'runtime.log')
            throw 'Unexpected test output HOLD'
        }
        $out | Set-Content -LiteralPath (Join-Path $evidence 'runtime.log')
        if ($raw -ne 0 -or [int]$match.Groups[1].Value -lt 40 -or [int]$match.Groups[2].Value -lt 1000) { throw 'Focused tests HOLD' }
        if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -cne $binaryHash) { throw 'After-binary drift HOLD' }
    } finally { $process.Dispose() }
    $ok = $true
} finally {
    try {
        $finalHashes = @(Source-Hashes)
        $finalHashes | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initialHashes $finalHashes -CaseSensitive).Count) { throw 'After-source drift HOLD' }
    } catch { $ok = $false; throw } finally {
        'P287_REVIEW=HOLD PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
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
            'P287_REVIEW=PASS PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3' |
                Set-Content -LiteralPath (Join-Path $evidence 'scope.log')
        }
    }
}
