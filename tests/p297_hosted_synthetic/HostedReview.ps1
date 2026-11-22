# Source review only on Kristian. NEVER invoke this script or its outputs there.
# This script has no command-line parameters, local mode, retry or alternate launcher.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$base = '45010901a7d1bd28fff03c83449c23d596c18bbd'
$olderParent = 'c1bb282f0224b22902cdba7740de71bbeaf07b8a'
$baseBranch = 'byok-c1-p296-launch-custody-diagnostic-20261122'
$headBranch = 'byok-c1-p297-hosted-synthetic-evidence-20261122'
$additions = @(
    '.github/workflows/p297-hosted-synthetic-review.yml',
    'docs/byok-c1-p297-hosted-synthetic-acceptance.md',
    'tests/p297_hosted_synthetic/HostedReview.ps1',
    'tests/p297_hosted_synthetic/P297SyntheticEntry.cs'
)
$sourcePaths = @(
    'tests/p296_launch_custody/P296LaunchCustodyDiagnostic.cs',
    'tests/p296_launch_custody/P296LaunchCustodyDiagnosticTests.cs',
    'tests/p297_hosted_synthetic/P297SyntheticEntry.cs'
)
$pins = @(
    '9EA16EEA4765BD10E7C2C47DB9C8BCD1100F37971DA7F3F2D584735D000BD48D',
    'B3D8FBA3B5A16EBC2BD2FB6AF09C3463E28314583B71D287B38FDB2DA6FE3C01'
)
$git = 'C:\Program Files\Git\cmd\git.exe'
$clock = [Diagnostics.Stopwatch]::StartNew()
$utf8 = [Text.UTF8Encoding]::new($false)

function Demand([bool]$Condition, [string]$Code) {
    if (-not $Condition) { throw [InvalidOperationException]::new($Code) }
}
function Failure-Code($Failure) {
    # Only our fixed all-uppercase categories may be disclosed. System errors are opaque.
    $message = $Failure.Exception.Message
    if ($Failure.Exception -is [InvalidOperationException] -and $message -cmatch '^[A-Z][A-Z0-9_]{0,63}$') {
        return $message
    }
    return 'UNCLASSIFIED_EXCEPTION'
}
function Budget {
    Demand ($clock.ElapsedMilliseconds -lt 360000) 'TOTAL_DEADLINE'
}
function Git-Lines([string[]]$Arguments) {
    Budget
    $answer = @(& $git --no-optional-locks -c core.fsmonitor=false -C $root @Arguments 2>$null)
    Demand ($LASTEXITCODE -eq 0) 'GIT_RECEIPT'
    return $answer
}
function No-Reparse([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    Demand (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'REPARSE'
}
function Source-File([string]$Relative) {
    Demand ($Relative -cmatch '^[A-Za-z0-9_. /-]+$' -and
        $Relative -notmatch '(^|/)\.\.(/|$)' -and -not $Relative.StartsWith('/')) 'SOURCE_PATH'
    $full = [IO.Path]::GetFullPath((Join-Path $root $Relative))
    Demand ($full.StartsWith($root + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) 'SOURCE_ESCAPE'
    Demand ([IO.File]::Exists($full)) 'SOURCE_MISSING'
    $walk = $full
    while ($walk.Length -gt $root.Length) {
        No-Reparse $walk
        $walk = [IO.Path]::GetDirectoryName($walk)
    }
    return $full
}
function Raw-File([string]$Path) {
    # Exclusive read: sharing/access failure is terminal, never retried.
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
    try {
        Demand ($stream.Length -le 16777216) 'SOURCE_SIZE'
        $data = [byte[]]::new([int]$stream.Length)
        $offset = 0
        while ($offset -lt $data.Length) {
            $read = $stream.Read($data, $offset, $data.Length - $offset)
            Demand ($read -gt 0) 'SOURCE_SHORT_READ'
            $offset += $read
        }
        return ,$data
    } finally { $stream.Dispose() }
}
function Digest([byte[]]$Bytes) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($hasher.ComputeHash($Bytes)).Replace('-', '') }
    finally { $hasher.Dispose() }
}
function Blob-Oid([byte[]]$Bytes) {
    $hasher = [Security.Cryptography.SHA1]::Create()
    try {
        $header = [Text.Encoding]::ASCII.GetBytes('blob ' + $Bytes.Length + [char]0)
        $null = $hasher.TransformBlock($header, 0, $header.Length, $header, 0)
        $null = $hasher.TransformFinalBlock($Bytes, 0, $Bytes.Length)
        return [BitConverter]::ToString($hasher.Hash).Replace('-', '').ToLowerInvariant()
    } finally { $hasher.Dispose() }
}
function Tree([string]$Revision, [int]$Count) {
    $rows = @(Git-Lines @('-c', 'core.quotepath=false', 'ls-tree', '-r', '--full-tree', $Revision))
    Demand ($rows.Count -eq $Count) 'TREE_COUNT'
    $map = [Collections.Generic.SortedDictionary[string,string]]::new([StringComparer]::Ordinal)
    foreach ($line in $rows) {
        Demand ($line -cmatch '^100644 blob ([0-9a-f]{40})\t(.+)$') 'TREE_RECORD'
        $oid = $Matches[1]; $relative = $Matches[2]
        Demand (-not $map.ContainsKey($relative)) 'TREE_DUPLICATE'
        $map.Add($relative, $oid)
    }
    return ,$map
}
function Snapshot {
    $currentHead = @(Git-Lines @('rev-parse', '--verify', 'HEAD'))
    Demand ($currentHead.Count -eq 1 -and $currentHead[0] -ceq $pr.head.sha) 'HEAD_DRIFT'
    $lines = [Collections.Generic.List[string]]::new()
    foreach ($pair in $headTree.GetEnumerator()) {
        Budget
        $bytes = Raw-File (Source-File $pair.Key)
        Demand ((Blob-Oid $bytes) -ceq $pair.Value) 'RAW_BLOB_DRIFT'
        $lines.Add((Digest $bytes) + '  ' + $pair.Key)
    }
    Demand (@(Git-Lines @('status', '--porcelain=v1', '--untracked-files=all', '--ignored')).Count -eq 0) 'DIRTY_TREE'
    return ,$lines.ToArray()
}

# Independent read-only admission: no compiler, candidate, output directory or edit yet.
# Environment checks are defense in depth, not proof of authorization on a local PC.
try {
    Demand ($env:GITHUB_ACTIONS -ceq 'true' -and $env:RUNNER_ENVIRONMENT -ceq 'github-hosted' -and
        $env:RUNNER_OS -ceq 'Windows' -and $env:ImageOS -ceq 'win22' -and $IsWindows -and
        [Environment]::Is64BitProcess -and $env:GITHUB_EVENT_NAME -ceq 'pull_request' -and
        $env:GITHUB_REPOSITORY -ceq 'krismcan/Mark-LV' -and $env:GITHUB_REPOSITORY_OWNER -ceq 'krismcan') 'HOSTED_ONLY'
    Demand ($args.Count -eq 0) 'NO_ARGUMENTS'
    Demand ($env:P297_ARCH -cin @('x64', 'x86') -and $env:P297_TRIAL -cin @('1', '2')) 'MATRIX'
    Demand ([IO.Directory]::Exists($env:GITHUB_WORKSPACE) -and
        [IO.Directory]::Exists($env:RUNNER_TEMP) -and [IO.File]::Exists($git)) 'HOST_PATHS'
    $root = [IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
    $tempRoot = [IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
    No-Reparse $root; No-Reparse $tempRoot
    Demand ([IO.Path]::GetFullPath($PSScriptRoot) -ieq
        (Join-Path $root 'tests\p297_hosted_synthetic')) 'SCRIPT_LOCATION'
    Demand ((Get-Location).Path -ieq $root) 'WORKING_DIRECTORY'
    $gitRoot = @(Git-Lines @('rev-parse', '--show-toplevel'))
    Demand ($gitRoot.Count -eq 1 -and [IO.Path]::GetFullPath($gitRoot[0]) -ieq $root) 'GIT_ROOT'
    Demand ([IO.File]::Exists($env:GITHUB_EVENT_PATH) -and
        (Get-Item -LiteralPath $env:GITHUB_EVENT_PATH).Length -le 1048576) 'EVENT_FILE'
    $event = [IO.File]::ReadAllText($env:GITHUB_EVENT_PATH) | ConvertFrom-Json
    $pr = $event.pull_request
    Demand ($event.action -cin @('opened', 'synchronize', 'reopened', 'converted_to_draft') -and
        $pr.draft -is [bool] -and $pr.draft -eq $true -and
        $env:GITHUB_HEAD_REF -ceq $headBranch -and $env:GITHUB_BASE_REF -ceq $baseBranch -and
        $event.repository.full_name -ceq 'krismcan/Mark-LV' -and
        $event.repository.owner.login -ceq 'krismcan' -and
        $pr.base.repo.full_name -ceq 'krismcan/Mark-LV' -and
        $pr.head.repo.full_name -ceq 'krismcan/Mark-LV' -and
        $pr.head.repo.owner.login -ceq 'krismcan' -and $pr.base.ref -ceq $baseBranch -and
        $pr.head.ref -ceq $headBranch -and $pr.base.sha -ceq $base -and
        $pr.head.sha -cmatch '^[0-9a-f]{40}$') 'EVENT_SCOPE'
    $head = @(Git-Lines @('rev-parse', '--verify', 'HEAD'))
    Demand ($head.Count -eq 1 -and $head[0] -ceq $pr.head.sha) 'HEAD_EVENT'
    $parent = @(Git-Lines @('rev-list', '--parents', '-n', '1', 'HEAD'))
    Demand ($parent.Count -eq 1 -and $parent[0] -ceq ($pr.head.sha + ' ' + $base)) 'DIRECT_CHILD'
    $parent = @(Git-Lines @('rev-list', '--parents', '-n', '1', $base))
    Demand ($parent.Count -eq 1 -and $parent[0] -ceq ($base + ' ' + $olderParent)) 'P296_PARENT'
    $delta = @(Git-Lines @('diff-tree', '--no-commit-id', '--name-status', '-r', 'HEAD'))
    $expected = @($additions | ForEach-Object { 'A' + "`t" + $_ })
    Demand (($delta -join "`n") -ceq ($expected -join "`n")) 'FOUR_ADDITIONS_ONLY'
    $baseTree = Tree $base 1204
    $headTree = Tree HEAD 1208
    foreach ($pair in $baseTree.GetEnumerator()) {
        Demand ($headTree.ContainsKey($pair.Key) -and $headTree[$pair.Key] -ceq $pair.Value) 'INHERITED_TREE_DRIFT'
    }
    $before = Snapshot
    for ($index = 0; $index -lt 2; $index++) {
        Demand ((Digest (Raw-File (Source-File $sourcePaths[$index]))) -ceq $pins[$index]) 'P296_PIN'
    }
    $entry = [IO.File]::ReadAllText((Source-File $sourcePaths[2]))
    Demand ((Digest (Raw-File (Source-File $sourcePaths[2]))) -ceq
        '9165BCEFDBA965421D3560B5442D9C85C65092F3FC6160EB088D0D2CC04F8E12') 'P297_ENTRY_PIN'
    Demand ($entry.StartsWith('#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P296_SOURCE_ONLY && C1_P297_HOSTED_SYNTHETIC_ONLY && !RELEASE') -and
        $entry.Contains('#error P297_DEBUG_ISOLATED_HOSTED_SYNTHETIC_ONLY_REQUIRED')) 'ENTRY_GUARD'
    $framework = if ($env:P297_ARCH -ceq 'x64') { 'Framework64' } else { 'Framework' }
    $frameworkRoot = 'C:\Windows\Microsoft.NET\' + $framework + '\v4.0.30319'
    $csc = Join-Path $frameworkRoot 'csc.exe'
    foreach ($file in @('csc.exe', 'mscorlib.dll', 'System.dll', 'System.Core.dll')) {
        Demand ([IO.File]::Exists((Join-Path $frameworkRoot $file))) 'EXISTING_FRAMEWORK_ONLY'
    }
} catch {
    Write-Output ('P297 HOSTED REVIEW HOLD PREFLIGHT=' + (Failure-Code $_))
    exit 1
}

$evidence = Join-Path $tempRoot ('p297-evidence-' + $env:P297_ARCH + '-' + $env:P297_TRIAL)
$build = Join-Path $tempRoot ('p297-private-' + $env:P297_ARCH + '-' + $env:P297_TRIAL)
$summary = [Collections.Generic.List[string]]::new()
$success = $false
$ownsEvidence = $false
$binaryBefore = $null
$exe = Join-Path $build 'P297Synthetic.exe'

function Record([string]$Line) {
    $summary.Add($Line)
    [IO.File]::WriteAllLines((Join-Path $evidence 'summary.txt'), $summary, $utf8)
    Write-Output $Line
}

function Fixed-Child([string]$Mode, [string[]]$CompilerArguments) {
    Budget
    Demand ($Mode -cin @('COMPILE', 'SYNTHETIC')) 'CHILD_MODE'
    $process = [Diagnostics.Process]::new()
    $state = [hashtable]::Synchronized(@{ Out=''; Err=''; OutEof=$false; ErrEof=$false; Overflow=$false })
    $jobs = [Collections.Generic.List[object]]::new()
    $started = $false; $cleanup = $true; $timeout = $false; $custody = $false
    $raw = 'UNAVAILABLE'; $cleanupRaw = 'UNAVAILABLE'; $fault = $false
    $pidReceipt = 0; $birth = 0; $handle = [IntPtr]::Zero
    $outId = 'P297-' + [Guid]::NewGuid().ToString('N')
    $errId = 'P297-' + [Guid]::NewGuid().ToString('N')
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $limit = if ($Mode -ceq 'COMPILE') { 15000 } else { 8000 }
    try {
        $process.StartInfo.FileName = if ($Mode -ceq 'COMPILE') { $csc } else { $exe }
        $process.StartInfo.WorkingDirectory = $build
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.CreateNoWindow = $true
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        # No token, profiler, runtime override, credentials or ambient input to either child.
        $process.StartInfo.Environment.Clear()
        foreach ($name in @('SystemRoot', 'WINDIR')) { $process.StartInfo.Environment[$name] = 'C:\Windows' }
        foreach ($name in @('TEMP', 'TMP')) { $process.StartInfo.Environment[$name] = $build }
        if ($Mode -ceq 'COMPILE') {
            foreach ($argument in $CompilerArguments) { $process.StartInfo.ArgumentList.Add($argument) }
        } else { Demand ($CompilerArguments.Count -eq 0) 'SYNTHETIC_NO_ARGUMENTS' }
        # Asynchronous output/error event handlers; never ReadToEnd/GetResult/WaitForExit().
        # Retain <=4096 characters per stream. The reviewed entry emits one short line;
        # Framework's line reader is not an adversarial arbitrary-binary stream sandbox.
        $jobs.Add((Register-ObjectEvent $process OutputDataReceived -SourceIdentifier $outId -MessageData $state -Action {
            $s = $Event.MessageData; $d = $Event.SourceEventArgs.Data
            if ($null -eq $d) { $s.OutEof = $true; return }
            $line = $d + "`n"; $room = 4096 - $s.Out.Length
            if ($line.Length -gt $room) { $s.Overflow = $true }
            $s.Out += $line.Substring(0, [Math]::Min($line.Length, $room))
        }))
        $jobs.Add((Register-ObjectEvent $process ErrorDataReceived -SourceIdentifier $errId -MessageData $state -Action {
            $s = $Event.MessageData; $d = $Event.SourceEventArgs.Data
            if ($null -eq $d) { $s.ErrEof = $true; return }
            $line = $d + "`n"; $room = 4096 - $s.Err.Length
            if ($line.Length -gt $room) { $s.Overflow = $true }
            $s.Err += $line.Substring(0, [Math]::Min($line.Length, $room))
        }))
        # Parent watchdog is separate from the tested child and both stream handlers.
        # It starts before Start(), polls without waiting on pipe completion, never retries.
        Demand ($process.Start()) 'START_UNAVAILABLE'
        $started = $true
        $handle = $process.Handle; $pidReceipt = $process.Id; $birth = $process.StartTime.ToUniversalTime().Ticks
        Demand ($handle -ne [IntPtr]::Zero -and $pidReceipt -gt 0 -and $birth -gt 0) 'HANDLE_CUSTODY'
        $process.BeginOutputReadLine(); $process.BeginErrorReadLine()
        while ($true) {
            if ($watch.ElapsedMilliseconds -ge $limit) { $timeout = $true; break }
            if ($state.Overflow) { $fault = $true; break }
            if ($process.WaitForExit(10)) {
                $raw = [string]$process.ExitCode
                $custody = $process.Handle -eq $handle -and $process.Id -eq $pidReceipt -and
                    $process.StartTime.ToUniversalTime().Ticks -eq $birth
                break
            }
            Start-Sleep -Milliseconds 10
        }
        # Separate 2s EOF deadline; do not wait for stream tasks or parameterless exit wait.
        if (-not $timeout -and -not $fault) {
            $drain = [Diagnostics.Stopwatch]::StartNew()
            while (-not ($state.OutEof -and $state.ErrEof) -and $drain.ElapsedMilliseconds -lt 2000) {
                Start-Sleep -Milliseconds 10
            }
            if (-not ($state.OutEof -and $state.ErrEof)) { $fault = $true; $cleanup = $false }
        }
    } catch { $fault = $true }
    finally {
        if ($started) {
            try {
                if (-not $process.HasExited) {
                    # Exact retained process object only. No PID lookup, tree or wildcard kill.
                    $process.Kill()
                    if (-not $process.WaitForExit(2000)) { $cleanup = $false }
                }
                # Teardown exit is separate; it cannot replace a missing natural exit receipt.
                if ($process.HasExited) { $cleanupRaw = [string]$process.ExitCode }
                if (-not $process.HasExited) { $cleanup = $false }
            } catch { $cleanup = $false }
            try { $process.CancelOutputRead() } catch { $cleanup = $false }
            try { $process.CancelErrorRead() } catch { $cleanup = $false }
        }
        foreach ($id in @($outId, $errId)) {
            try { Unregister-Event -SourceIdentifier $id -ErrorAction Stop } catch { $cleanup = $false }
        }
        foreach ($job in $jobs) {
            try {
                if ($job.State -eq 'Failed' -or $job.Error.Count -ne 0) { $fault = $true }
                Remove-Job -Job $job -Force -ErrorAction Stop
            } catch { $cleanup = $false }
        }
        try { $process.Dispose() } catch { $cleanup = $false }
    }
    return [pscustomobject]@{
        Raw=$raw; CleanupRaw=$cleanupRaw; Timeout=$timeout; Cleanup=$cleanup; Custody=$custody
        Fault=($fault -or $state.Overflow -or -not $state.OutEof -or -not $state.ErrEof)
        Out=$state.Out; Err=$state.Err
    }
}

try {
    Demand (-not [IO.Directory]::Exists($evidence) -and -not [IO.Directory]::Exists($build)) 'NO_RETRY_DIRECTORIES'
    $null = [IO.Directory]::CreateDirectory($evidence)
    $ownsEvidence = $true
    $null = [IO.Directory]::CreateDirectory($build)
    [IO.File]::WriteAllLines((Join-Path $evidence 'source-before.sha256'), $before, $utf8)
    Record ('P297 HEAD=' + $pr.head.sha + ' BASE=' + $base + ' ARCH=' + $env:P297_ARCH + ' TRIAL=' + $env:P297_TRIAL)
    Record 'SCOPE=HOSTED_IN_MEMORY_ONLY APPROVALS=0/7 FULL_PRODUCT_REGRESSIONS=0/3 P96=HIGH_OPEN OVERALL=HOLD'
    $positive = 'DEBUG;C1_REVIEW_ISOLATED_ASSEMBLY;C1_P296_SOURCE_ONLY;C1_P297_HOSTED_SYNTHETIC_ONLY'
    # Minimal guard negatives: all absent, each required symbol absent, RELEASE added.
    $modes = @(
        @{ Name='positive'; Defines=$positive; Good=$true },
        @{ Name='none'; Defines=''; Good=$false },
        @{ Name='no-debug'; Defines='C1_REVIEW_ISOLATED_ASSEMBLY;C1_P296_SOURCE_ONLY;C1_P297_HOSTED_SYNTHETIC_ONLY'; Good=$false },
        @{ Name='no-isolated'; Defines='DEBUG;C1_P296_SOURCE_ONLY;C1_P297_HOSTED_SYNTHETIC_ONLY'; Good=$false },
        @{ Name='no-p296'; Defines='DEBUG;C1_REVIEW_ISOLATED_ASSEMBLY;C1_P297_HOSTED_SYNTHETIC_ONLY'; Good=$false },
        @{ Name='no-p297'; Defines='DEBUG;C1_REVIEW_ISOLATED_ASSEMBLY;C1_P296_SOURCE_ONLY'; Good=$false },
        @{ Name='release'; Defines=($positive + ';RELEASE'); Good=$false }
    )
    foreach ($mode in $modes) {
        $output = if ($mode.Good) { $exe } else { Join-Path $build ($mode.Name + '.exe') }
        Demand (-not [IO.File]::Exists($output)) 'OUTPUT_PREEXISTS'
        $compilerArgs = @('/nologo', '/noconfig', '/nostdlib+', '/langversion:5', '/warn:4', '/warnaserror+',
            '/target:exe', ('/platform:' + $env:P297_ARCH), ('/out:' + $output),
            ('/reference:' + (Join-Path $frameworkRoot 'mscorlib.dll')),
            ('/reference:' + (Join-Path $frameworkRoot 'System.dll')),
            ('/reference:' + (Join-Path $frameworkRoot 'System.Core.dll')))
        if ($mode.Defines.Length -gt 0) { $compilerArgs += '/define:' + $mode.Defines }
        foreach ($source in $sourcePaths) { $compilerArgs += Source-File $source }
        $result = Fixed-Child COMPILE $compilerArgs
        Record ('COMPILE=' + $mode.Name + ' RAW_EXIT=' + $result.Raw + ' TIMEOUT=' + $result.Timeout +
            ' CLEANUP_RAW_EXIT=' + $result.CleanupRaw + ' CLEANUP=' + $result.Cleanup +
            ' CUSTODY=' + $result.Custody + ' IO_FAULT=' + $result.Fault)
        Demand (-not $result.Timeout -and $result.Cleanup -and $result.Custody -and -not $result.Fault) 'COMPILER_CUSTODY'
        if ($mode.Good) {
            Demand ($result.Raw -ceq '0' -and $result.Out.Length -eq 0 -and $result.Err.Length -eq 0 -and
                [IO.File]::Exists($output)) 'POSITIVE_COMPILE'
            $binaryBefore = Digest (Raw-File $exe)
            Record ('BINARY_BEFORE_SHA256=' + $binaryBefore)
        } else {
            $diagnostics = @((($result.Out + $result.Err) -split "`n") | Where-Object { $_.Length -gt 0 })
            $expectedErrors = if ($mode.Name -ceq 'no-p297') { 1 } else { 3 }
            Demand ($result.Raw -ceq '1' -and -not [IO.File]::Exists($output) -and
                $diagnostics.Count -eq $expectedErrors) 'GUARD_EXIT_OUTPUT'
            foreach ($line in $diagnostics) {
                Demand ($line -cmatch "^[^\r\n]+\([0-9]+,[0-9]+\): error CS1029: #error: '(P296_DEBUG_ISOLATED_SOURCE_ONLY_REQUIRED|P297_DEBUG_ISOLATED_HOSTED_SYNTHETIC_ONLY_REQUIRED)'$") 'GUARD_DIAGNOSTIC'
            }
            Record ('GUARD=' + $mode.Name + ' EXPECTED_CS1029=' + $expectedErrors + ' OUTPUT=ABSENT')
        }
    }
    Demand ((Digest (Raw-File $exe)) -ceq $binaryBefore) 'PRELAUNCH_BINARY_DRIFT'
    $result = Fixed-Child SYNTHETIC @()
    Record ('SYNTHETIC RAW_EXIT=' + $result.Raw + ' TIMEOUT=' + $result.Timeout + ' CLEANUP=' + $result.Cleanup +
        ' CLEANUP_RAW_EXIT=' + $result.CleanupRaw + ' CUSTODY=' + $result.Custody + ' IO_FAULT=' + $result.Fault)
    Demand (-not $result.Timeout -and $result.Cleanup -and $result.Custody -and -not $result.Fault -and
        $result.Raw -ceq '0' -and $result.Out -ceq "P297 SYNTHETIC PASS COUNT=56`n" -and $result.Err.Length -eq 0) 'SYNTHETIC_RECEIPT'
    Record 'SYNTHETIC_MARKER=EXACT COUNT_RETURNED=56'
    $success = $true
} catch {
    $success = $false
    # Fixed category only. Raw exception/user paths/contents never enter logs or artifacts.
    if ($ownsEvidence) { Record ('FAILURE=HOLD_NO_RETRY CODE=' + (Failure-Code $_)) }
    else { Write-Output ('P297 HOSTED REVIEW HOLD CODE=' + (Failure-Code $_)) }
} finally {
    if ($ownsEvidence) {
        try {
            # All child handles/stream subscriptions disposed before output hash sampling.
            if ([IO.File]::Exists($exe)) {
                $binaryAfter = Digest (Raw-File $exe)
                Record ('BINARY_AFTER_SHA256=' + $binaryAfter)
                Demand ($null -ne $binaryBefore -and $binaryBefore -ceq $binaryAfter) 'BINARY_AFTER_DRIFT'
            } else { $success = $false; Record 'BINARY_AFTER_SHA256=UNAVAILABLE' }
        } catch { $success = $false; Record 'BINARY_HASH=HOLD' }
        try {
            $after = Snapshot
            [IO.File]::WriteAllLines((Join-Path $evidence 'source-after.sha256'), $after, $utf8)
            Demand (($before -join "`n") -ceq ($after -join "`n")) 'SOURCE_AFTER_DRIFT'
            Record 'SOURCE_CUSTODY=1204_INHERITED_UNCHANGED_1208_TOTAL'
        } catch { $success = $false; Record 'SOURCE_CUSTODY=HOLD' }
        Record ('HOSTED_SYNTHETIC_REVIEW=' + $(if ($success) { 'PASS' } else { 'HOLD' }) + ' PRODUCT_RELEASE=HOLD')
    }
}
if ($success) { exit 0 }
exit 1
