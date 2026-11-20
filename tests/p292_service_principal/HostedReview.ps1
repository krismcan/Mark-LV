# HOSTED ONLY. Local validation MUST parse this as data, never execute it.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:ImageOS -cne 'win22' -or $env:RUNNER_OS -cne 'Windows' -or
    $env:P292_DISPOSABLE_SCM_WITNESS -cne '1' -or $env:GITHUB_EVENT_NAME -cne 'pull_request' -or
    $env:GITHUB_REPOSITORY -cne 'krismcan/Mark-LV' -or $env:REVIEW_ARCH -cnotin @('x64','x86') -or
    $env:REVIEW_FRAMEWORK -cne (@{x64='Framework64';x86='Framework'}[$env:REVIEW_ARCH])) { throw 'Hosted guard HOLD' }
$event = Get-Content -LiteralPath $env:GITHUB_EVENT_PATH -Raw | ConvertFrom-Json
$pr = $event.pull_request
if ($event.action -cnotin @('opened','synchronize','reopened') -or $pr.draft -isnot [bool] -or !$pr.draft -or
    $event.repository.full_name -cne 'krismcan/Mark-LV' -or $pr.base.repo.full_name -cne 'krismcan/Mark-LV' -or
    $pr.head.repo.full_name -cne 'krismcan/Mark-LV' -or $pr.base.sha -cne $parent -or
    $pr.base.ref -cne 'byok-c1-p291-shared-revocation-effect-owner-20261120' -or
    $pr.head.ref -cne 'byok-c1-p292-ephemeral-scm-service-witness-20261120' -or
    $env:GITHUB_HEAD_REF -cne $pr.head.ref -or $env:GITHUB_BASE_REF -cne $pr.base.ref -or
    $pr.head.sha -cnotmatch '\A[0-9a-f]{40}\z') { throw 'Exact draft HOLD' }
function Git-Read([string[]]$Arguments) {
    $result = @(& git @Arguments)
    if ($LASTEXITCODE -ne 0) { throw 'Git HOLD' }
    return $result
}
function Assert-NoLinks([string]$Path) {
    for ($p = [IO.Path]::GetFullPath($Path); $null -ne $p; $p = [IO.Path]::GetDirectoryName($p)) {
        if ((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse HOLD' }
    }
}
$head = [string](Git-Read @('rev-parse','HEAD'))
if ($head -cne $pr.head.sha -or
    [string](Git-Read @('rev-list','--parents','-n','1',$head)) -cne ($head + ' ' + $parent)) { throw 'Single child HOLD' }
$added = @('tests/p292_service_principal/P292DisposableService.cs','tests/p292_service_principal/P292ServiceIdentityProbe.cs',
    'tests/p292_service_principal/HostedReview.ps1','.github/workflows/p292-windows-disposable-service-review.yml',
    'docs/byok-c1-p292-service-principal-review.md')
$delta = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $delta -CaseSensitive).Count) { throw 'Five additions HOLD' }
$old = @(Git-Read @('ls-tree','-r',$parent))
$tree = @(Git-Read @('ls-tree','-r',$head))
$inherited = @($tree | Where-Object { ($_ -split "`t",2)[1] -cnotin $added })
if ($old.Count -ne 1180 -or $tree.Count -ne 1185 -or
    @(Compare-Object $old $inherited -CaseSensitive).Count) { throw 'Frozen parent HOLD' }
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
        if ((Get-Item -LiteralPath $paths[$i] -Force).PSIsContainer -or $disk[$i] -cne $oids[$i]) { throw 'Raw bytes HOLD' }
        (Get-FileHash -LiteralPath $paths[$i] -Algorithm SHA256).Hash + ' ' + $paths[$i]
    }
}
Assert-NoLinks $env:RUNNER_TEMP
$build = Join-Path $env:RUNNER_TEMP ('p292-build-' + $env:REVIEW_ARCH)
$evidence = Join-Path $env:RUNNER_TEMP ('p292-evidence-' + $env:REVIEW_ARCH)
foreach ($path in @($build,$evidence)) {
    if (Test-Path -LiteralPath $path) { throw 'Output collision HOLD' }
    New-Item -ItemType Directory -Path $path | Out-Null
}
$artifacts = @('source-before.sha256','source-after.sha256','compiler.log','compiler-exits.txt',
    'test-binary.sha256','runtime.exit','runtime.log','scope.log')
foreach ($file in $artifacts) { [IO.File]::WriteAllText((Join-Path $evidence $file), '') }
function Record([string]$File, [string]$Text) { Add-Content -LiteralPath (Join-Path $evidence $File) -Value $Text }
$initial = @(Source-Hashes)
$initial | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$flags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P292_EPHEMERAL_SCM_ONLY')
$dir = Join-Path $env:WINDIR ('Microsoft.NET/' + $env:REVIEW_FRAMEWORK + '/v4.0.30319')
$csc = (Resolve-Path -LiteralPath (Join-Path $dir 'csc.exe')).Path
$common = @('/nologo','/noconfig','/debug+','/optimize-','/warn:4','/warnaserror+','/target:exe',('/platform:' + $env:REVIEW_ARCH))
foreach ($ref in @('System.dll','System.Core.dll','System.ServiceProcess.dll')) { $common += '/reference:' + (Join-Path $dir $ref) }
function Compile([string]$Label, [string]$Source, [string[]]$Defines, [bool]$Negative) {
    $output = Join-Path $build ($Label + '.exe')
    if (Test-Path -LiteralPath $output) { throw 'Binary collision HOLD' }
    $options = @($common) + @('/out:' + $output)
    if ($Defines.Count) { $options += '/define:' + ($Defines -join ';') }
    $absoluteSource = (Resolve-Path -LiteralPath $Source).Path
    $result = Child ('compile-' + $Label) $csc (@($options) + $absoluteSource) 20
    $raw = $result.Exit
    $log = $result.Out + $result.Err
    [IO.File]::WriteAllText((Join-Path $build ($Label + '.raw')), $log)
    $codes = @([regex]::Matches($log, '\b(?:error|warning) (CS[0-9]{4}):') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    Record 'compiler-exits.txt' ($Label + " RAW_EXIT=$raw")
    Record 'compiler.log' ($Label + " RAW_EXIT=$raw CODES=" + ($codes -join ',') + ' RAW_SHA256=' +
        (Get-FileHash -LiteralPath (Join-Path $build ($Label + '.raw')) -Algorithm SHA256).Hash)
    if ($Negative) {
        if ($raw -ne 1 -or (Test-Path -LiteralPath $output) -or $codes.Count -ne 1 -or $codes[0] -cne 'CS1029' -or
            $log -notmatch 'error CS1029:.*P292_DEBUG_ISOLATED_EPHEMERAL_ONLY') { throw 'Compile refusal HOLD' }
    } elseif ($raw -ne 0 -or $codes.Count -ne 0 -or !(Test-Path -LiteralPath $output)) { throw 'Compile HOLD' }
}
# Every native child uses a bounded process, no shell interpolation, no output to CI.
function Child([string]$Label, [string]$Exe, [string[]]$Arguments, [int]$Seconds) {
    $si = [Diagnostics.ProcessStartInfo]::new($Exe)
    $si.UseShellExecute = $false; $si.CreateNoWindow = $true
    $si.RedirectStandardOutput = $true; $si.RedirectStandardError = $true
    $si.WorkingDirectory = $build; $si.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),@('TEMP',$build),@('TMP',$build),
        @('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),@('RUNNER_OS','Windows'),
        @('ImageOS','win22'),@('P292_DISPOSABLE_SCM_WITNESS','1'))) { $si.Environment[$pair[0]] = $pair[1] }
    foreach ($argument in $Arguments) { $si.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $si; $launched = $false
    try {
        $launched = $process.Start()
        if (!$launched) { throw 'Child launch HOLD' }
        $outTask = $process.StandardOutput.ReadToEndAsync(); $errTask = $process.StandardError.ReadToEndAsync()
        if (!$process.WaitForExit($Seconds * 1000)) {
            Record 'runtime.exit' ($Label + ' TIMEOUT RAW_EXIT=UNAVAILABLE NO_RETRY')
            throw 'Child watchdog HOLD'
        }
        $raw = $process.ExitCode
        $stdout = $outTask.GetAwaiter().GetResult(); $stderr = $errTask.GetAwaiter().GetResult()
        [IO.File]::WriteAllText((Join-Path $build ($Label + '.stdout')), $stdout)
        [IO.File]::WriteAllText((Join-Path $build ($Label + '.stderr')), $stderr)
        Record 'runtime.exit' ($Label + " RAW_EXIT=$raw")
        # Return only in memory to caller. sc output may contain the service name.
        return @{ Exit=$raw; Out=$stdout; Err=$stderr }
    } catch {
        Record 'runtime.log' ($Label + ' HOLD')
        throw 'Child HOLD'
    } finally {
        try {
            if ($launched -and !$process.HasExited) {
                $process.Kill($true)
                if (!$process.WaitForExit(5000)) { throw 'Child cleanup HOLD' }
            }
        } finally { $process.Dispose() }
    }
}
$serviceExe = Join-Path $build 'Service.exe'; $probeExe = Join-Path $build 'Probe.exe'
if ($build -match '["\r\n]' -or $build.Contains("'")) { throw 'Temporary path HOLD' }
$name = 'NayeonP292_' + ([Guid]::NewGuid().ToString('N').Substring(0,12))
if ($name -cnotmatch '\ANayeonP292_[0-9a-f]{12}\z') { throw 'Name HOLD' }
$command = '"' + $serviceExe + '" P292_DISPOSABLE_SCM_WITNESS=1 ' + $name + ' ' + $parent + ' ' + $head
$sc = Join-Path $env:WINDIR 'System32/sc.exe'
function Sc([string]$Verb, [string[]]$Tail, [string]$Label) {
    # No generic public name or command input; only this run's random service.
    if ($name -cnotmatch '\ANayeonP292_[0-9a-f]{12}\z' -or $Verb -cnotin @('create','sidtype','start','stop','delete')) { throw 'SCM bound HOLD' }
    Child $Label $sc (@($Verb,$name) + $Tail) 8
}
function Probe([string]$Label, [string[]]$Arguments, [bool]$ExpectedPass) {
    $result = Child $Label $probeExe $Arguments 8
    $expectedExit = if ($ExpectedPass) { 0 } else { 1 }
    $expectedOut = if ($ExpectedPass) { "P292_PROBE=PASS`r`n" } else { "P292_PROBE=HOLD`r`n" }
    if ($result.Exit -ne $expectedExit -or $result.Out -cne $expectedOut -or $result.Err.Length) { throw 'Probe HOLD' }
    Record 'runtime.log' ($Label + ' PASS')
}
function Metadata {
    $rows = @(Get-CimInstance -ClassName Win32_Service -Filter ("Name='" + $name + "'") -OperationTimeoutSec 5)
    if ($rows.Count -ne 1) { throw 'SCM metadata HOLD' }
    $row = $rows[0]
    if ($row.Name -cne $name -or $row.StartName -cne ('NT SERVICE\' + $name) -or
        $row.PathName -cne $command) { throw 'Configuration HOLD' }
    return $row
}
function Find-DisposableChild {
    $escapedImage = $serviceExe.Replace('\','\\')
    $rows = @(Get-CimInstance Win32_Process -Filter ("ExecutablePath='" + $escapedImage + "'") -OperationTimeoutSec 5)
    if ($rows.Count -gt 1) { throw 'Unexpected child count HOLD' }
    if ($rows.Count -eq 0) { return $null }
    $candidate = $null; $transferred = $false
    try {
        $candidate = [Diagnostics.Process]::GetProcessById([int]$rows[0].ProcessId)
        $null = $candidate.Handle
        if ($candidate.MainModule.FileName -ine $serviceExe -or $candidate.HasExited -or
            $candidate.StartTime.ToUniversalTime() -lt $startBoundary) { throw 'Child binding HOLD' }
        $transferred = $true
        return $candidate
    } finally { if (!$transferred -and $null -ne $candidate) { $candidate.Dispose() } }
}
$created = $false; $createAttempted = $false; $startAttempted = $false
$serviceProcess = $null; $processBirth = 0L; $ok = $false; $cleanup = $false
$startBoundary = [DateTime]::MaxValue; $stage = 'COMPILE'; $binaryHashes = @()
try {
    foreach ($item in @(@('Service','tests/p292_service_principal/P292DisposableService.cs'),
        @('Probe','tests/p292_service_principal/P292ServiceIdentityProbe.cs'))) {
        Compile $item[0] $item[1] $flags $false
        foreach ($missing in @('ALL','RELEASE') + $flags) {
            $selected = @($flags | Where-Object { $missing -cne 'ALL' -and $_ -cne $missing })
            if ($missing -ceq 'RELEASE') { $selected += 'RELEASE' }
            Compile ($item[0] + '-guard-' + $missing) $item[1] $selected $true
        }
    }
    $binaryHashes = @($serviceExe,$probeExe | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
    for ($i=0; $i -lt 2; $i++) { Record 'test-binary.sha256' (@('Service','Probe')[$i] + ' ' + $binaryHashes[$i]) }
    $stage = 'RUNNER_ADMIN'
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    try {
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Existing runner admin unavailable HOLD' }
    } finally { $identity.Dispose() }
    # Require exact absence immediately before exclusive creation. No collision retry.
    $outsideMode = Child 'service-mode-refusal' $serviceExe @() 8
    if ($outsideMode.Exit -ne 1 -or $outsideMode.Out.Length -or $outsideMode.Err.Length) { throw 'Service mode guard HOLD' }
    Record 'runtime.log' 'SERVICE_MODE_REFUSAL PASS'
    $stage = 'ABSENCE'
    Probe 'before-absent' @('absent',$name) $true
    $stage = 'CREATE'
    $createAttempted = $true
    # No password argument: virtual service accounts require a NULL password.
    $result = Sc 'create' @('binPath=',$command,'type=','own','start=','demand','error=','normal',
        'obj=',('NT SERVICE\' + $name)) 'sc-create'
    if ($result.Exit -ne 0) { throw 'Virtual account create HOLD' }
    $created = $true
    $null = Metadata
    $stage = 'CONFIGURE_RESTRICTED_SID'
    $result = Sc 'sidtype' @('restricted') 'sc-restricted'
    if ($result.Exit -ne 0) { throw 'Restricted SID configuration HOLD' }
    $startAttempted = $true
    $stage = 'START'; $startBoundary = [DateTime]::UtcNow
    $result = Sc 'start' @() 'sc-start'
    if ($result.Exit -ne 0) { throw 'Virtual account start HOLD' }
    # Poll status only; NEVER retry start/create/configure after failure.
    $stage = 'RUNNING'
    $clock = [Diagnostics.Stopwatch]::StartNew()
    do {
        $row = Metadata
        if ($row.State -ceq 'Running' -and $row.ProcessId -ne 0) { break }
        if ($row.State -ceq 'Stopped' -or $clock.Elapsed.TotalSeconds -ge 8) { throw 'Running deadline HOLD' }
        Start-Sleep -Milliseconds 100
    } while ($true)
    $serviceProcess = [Diagnostics.Process]::GetProcessById([int]$row.ProcessId)
    $null = $serviceProcess.Handle # Retain kernel handle, no PID-only kill/reacquisition.
    $processBirth = $serviceProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
    if ($serviceProcess.MainModule.FileName -ine $serviceExe -or $serviceProcess.HasExited) { throw 'Process binding HOLD' }
    $arguments = @('witness',$name,[string]$row.ProcessId,[string]$processBirth,$serviceExe,$command)
    $stage = 'KERNEL_WITNESS'
    Probe 'kernel-witness' $arguments $true
    # Live negative controls on the actual service: wrong lifetime / PID / image / account name.
    $stage = 'NEGATIVE_CONTROLS'
    $wrong = @($arguments); $wrong[3] = [string]($processBirth + 1)
    Probe 'changed-birth-denied' $wrong $false
    $wrong = @($arguments); $wrong[2] = '0'
    Probe 'wrong-pid-denied' $wrong $false
    $wrong = @($arguments); $wrong[4] = $probeExe
    Probe 'wrong-image-denied' $wrong $false
    $wrong = @($arguments); $wrong[1] = 'NayeonP292_' + ('0' * 12)
    if ($wrong[1] -ceq $name) { throw 'Negative name collision HOLD' }
    Probe 'wrong-name-denied' $wrong $false
    $wrong = @($arguments); $wrong[5] = $command + ' changed'
    Probe 'changed-config-denied' $wrong $false
    $stage = 'RECHECK'
    $rowAfter = Metadata
    if ($rowAfter.State -cne 'Running' -or [int]$rowAfter.ProcessId -ne $serviceProcess.Id -or
        $serviceProcess.HasExited -or $serviceProcess.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $processBirth) { throw 'Lifetime drift HOLD' }
    Probe 'kernel-recheck' $arguments $true
    $ok = $true
} catch {
    # No raw exception/identity/SCM output is published; no retry or fallback.
    Record 'runtime.log' ($stage + ' HOLD')
    $ok = $false
} finally {
    # Cleanup is attempted even on partial create/start failure; never another name.
    $cleanupErrors = 0
    try {
        if ($createAttempted) {
            # If create failed, only metadata matching OUR exact ImagePath/account may be cleaned.
            $rows = @(Get-CimInstance Win32_Service -Filter ("Name='" + $name + "'") -OperationTimeoutSec 5)
            if ($rows.Count -gt 1) { throw 'Cleanup multiplicity HOLD' }
            if ($rows.Count -eq 1) {
                $row = Metadata
                if (!$created) { $created = $true } # Exact random name + command, not a preexisting service.
                if ($startAttempted -and $null -eq $serviceProcess -and $row.ProcessId -ne 0) {
                    $serviceProcess = [Diagnostics.Process]::GetProcessById([int]$row.ProcessId)
                    $null = $serviceProcess.Handle
                    $processBirth = $serviceProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
                    if ($serviceProcess.MainModule.FileName -ine $serviceExe) { throw 'Cleanup binding HOLD' }
                }
            }
        }
    } catch { $cleanupErrors++ }
    try {
        # A metadata failure must never skip STOP for a service we created.
        if ($created) {
            $result = Sc 'stop' @() 'sc-stop'
            if ($result.Exit -notin @(0,1062)) { $cleanupErrors++ }
        }
    } catch { $cleanupErrors++ }
    # Find a process that may have launched just as start/metadata failed. Only this
    # unique build image after our start boundary is eligible; retain its handle.
    try {
        if ($startAttempted -and $null -eq $serviceProcess) {
            $serviceProcess = Find-DisposableChild
            if ($null -ne $serviceProcess) {
                $processBirth = $serviceProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
            }
        }
    } catch { $cleanupErrors++ }
    # Separate finally paths ensure stop/kill failure cannot skip deletion/absence check.
    try {
        if ($null -ne $serviceProcess -and !$serviceProcess.HasExited) {
            if (!$serviceProcess.WaitForExit(3000)) {
                if ($serviceProcess.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $processBirth -or
                    $serviceProcess.MainModule.FileName -ine $serviceExe -or
                    $serviceProcess.StartTime.ToUniversalTime() -lt $startBoundary) { throw 'Kill binding HOLD' }
                $serviceProcess.Kill() # Retained exact process handle; not taskkill /IM or PID wildcard.
                if (!$serviceProcess.WaitForExit(5000)) { throw 'Service termination HOLD' }
                # Forced termination is a failed witness, never a clean PASS.
                $ok = $false
                Record 'runtime.log' 'FORCED_TERMINATION HOLD'
            }
        }
    } catch { $cleanupErrors++ }
    try {
        if ($created) {
            $result = Sc 'delete' @() 'sc-delete'
            if ($result.Exit -notin @(0,1060)) { throw 'Delete HOLD' }
        }
    } catch { $cleanupErrors++ }
    try {
        # Catch a launch that became visible only during stop/delete. This is
        # teardown, not a second start or a retry of the failed mechanism.
        if ($startAttempted) {
            $lateChild = Find-DisposableChild
            if ($null -ne $lateChild) {
                try {
                    $ok = $false
                    $lateChild.Kill() # Already bound to exact image + start boundary + handle.
                    if (!$lateChild.WaitForExit(5000)) { throw 'Late child termination HOLD' }
                    Record 'runtime.log' 'LATE_CHILD_TERMINATION HOLD'
                } finally { $lateChild.Dispose() }
            }
        }
    } catch { $cleanupErrors++ }
    try {
        if ($null -ne $serviceProcess -and !$serviceProcess.HasExited) { throw 'Live child HOLD' }
        Probe 'after-absent' @('absent',$name) $true
        # Independent enumeration rejects a late/marked-for-delete service.
        if (@(Get-CimInstance Win32_Service -Filter ("Name='" + $name + "'") -OperationTimeoutSec 5).Count) { throw 'Service remains HOLD' }
        $escapedImage = $serviceExe.Replace('\','\\')
        if (@(Get-CimInstance Win32_Process -Filter ("ExecutablePath='" + $escapedImage + "'") -OperationTimeoutSec 5).Count) { throw 'Orphan child HOLD' }
        $cleanup = $cleanupErrors -eq 0
    } catch { $cleanup = $false }
    finally { if ($null -ne $serviceProcess) { $serviceProcess.Dispose(); $serviceProcess = $null } }
    Record 'runtime.log' $(if ($cleanup) { 'CLEANUP PASS' } else { 'CLEANUP HOLD' })
    try {
        $final = @(Source-Hashes)
        $final | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initial $final -CaseSensitive).Count) { throw 'Source drift HOLD' }
        for ($i=0; $i -lt 2; $i++) {
            if ((Get-FileHash -LiteralPath @($serviceExe,$probeExe)[$i] -Algorithm SHA256).Hash -cne $binaryHashes[$i]) { throw 'Binary drift HOLD' }
        }
    } catch { $ok = $false; Record 'scope.log' 'SOURCE_OR_BINARY HOLD' }
    if (@(Get-ChildItem -LiteralPath $evidence -Force).Count -ne 8 -or
        @(Get-ChildItem -LiteralPath $evidence -Force | Where-Object { $_.PSIsContainer -or $_.Name -cnotin $artifacts -or
            ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) }).Count) { $ok = $false }
    Record 'scope.log' $(if ($ok -and $cleanup) { 'MECHANISM PASS' } else { 'MECHANISM HOLD' })
    Record 'scope.log' 'CLIENT_ADMISSION HOLD CREDENTIAL_EFFECT HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 PRODUCTION HOLD'
}
if (!$ok -or !$cleanup) { throw 'P292 HOLD; no retry, no account/ACL/policy workaround' }
