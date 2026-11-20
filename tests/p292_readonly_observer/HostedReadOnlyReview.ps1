# HOSTED ONLY. On Kristian parse this file as data; NEVER execute or dot-source.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '1083919da53f808105522dd8e11dba9fdf844fa0'
$headBranch = 'byok-c1-p292-readonly-scm-cim-diagnostic-20261120'
$baseBranch = 'byok-c1-p292-ephemeral-scm-service-witness-20261120'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:ImageOS -cne 'win22' -or $env:RUNNER_OS -cne 'Windows' -or
    $env:P292_READONLY_DIAG_ONLY -cne '1' -or $env:GITHUB_EVENT_NAME -cne 'pull_request' -or
    $env:GITHUB_REPOSITORY -cne 'krismcan/Mark-LV' -or $env:REVIEW_ARCH -cnotin @('x64','x86') -or
    $env:REVIEW_FRAMEWORK -cne (@{x64='Framework64';x86='Framework'}[$env:REVIEW_ARCH]) -or
    $env:REVIEW_TRIAL -cnotin @('1','2','3') -or !$IsWindows -or ![Environment]::Is64BitProcess) {
    throw 'Hosted guard HOLD'
}
$event = Get-Content -LiteralPath $env:GITHUB_EVENT_PATH -Raw | ConvertFrom-Json
$pr = $event.pull_request
if ($event.action -cnotin @('opened','synchronize','reopened') -or $pr.draft -isnot [bool] -or !$pr.draft -or
    $event.repository.full_name -cne 'krismcan/Mark-LV' -or $pr.base.repo.full_name -cne 'krismcan/Mark-LV' -or
    $pr.head.repo.full_name -cne 'krismcan/Mark-LV' -or $pr.base.sha -cne $parent -or
    $pr.base.ref -cne $baseBranch -or $pr.head.ref -cne $headBranch -or
    $env:GITHUB_HEAD_REF -cne $headBranch -or $env:GITHUB_BASE_REF -cne $baseBranch -or
    $pr.head.sha -cnotmatch '\A[0-9a-f]{40}\z') { throw 'Exact same-repo draft HOLD' }
function Git-Read([string[]]$Arguments) {
    $lines = @(& git --no-optional-locks @Arguments 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'Git HOLD' }
    return $lines
}
$head = [string](Git-Read @('rev-parse','HEAD'))
if ($head -cne $pr.head.sha -or
    [string](Git-Read @('rev-list','--parents','-n','1',$head)) -cne ($head + ' ' + $parent) -or
    [string](Git-Read @('rev-parse','--show-toplevel')) -cne $env:GITHUB_WORKSPACE.Replace('\','/')) {
    throw 'Exact checkout/direct parent HOLD'
}
$added = @('tests/p292_readonly_observer/NativeScmReadOnlyCanary.cs',
    'tests/p292_readonly_observer/HostedReadOnlyReview.ps1',
    '.github/workflows/p292-windows-readonly-scm-cim-diagnostic.yml',
    'docs/byok-c1-p292-scm-cim-readonly-diagnostic.md')
$delta = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $delta -CaseSensitive).Count) {
    throw 'Four additive paths HOLD'
}
$inherited = @(Git-Read @('ls-tree','-r',$parent))
$current = @(Git-Read @('ls-tree','-r',$head))
if ($inherited.Count -ne 1185 -or $current.Count -ne 1189 -or
    @($inherited | Where-Object { $_ -cnotin $current }).Count) { throw 'Inherited tree HOLD' }
function Assert-NoLinks([string]$Path) {
    for ($p = [IO.Path]::GetFullPath($Path); $null -ne $p; $p = [IO.Path]::GetDirectoryName($p)) {
        $item = Get-Item -LiteralPath $p -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.LinkType) { throw 'Link HOLD' }
    }
}
function Source-Hashes {
    if (@(Git-Read @('status','--porcelain=v1','--untracked-files=all','--ignored=matching')).Count -or
        @(Git-Read @('diff','--name-only',$head)).Count -or
        @(Git-Read @('diff','--cached','--name-only',$head)).Count) { throw 'Clean source HOLD' }
    foreach ($line in $current) {
        if ($line -cnotmatch '\A100644 blob ([0-9a-f]{40})\t([^\r\n]+)\z') { throw 'Tree mode HOLD' }
        $expected = $Matches[1]; $relative = $Matches[2]
        $path = Join-Path $env:GITHUB_WORKSPACE $relative
        Assert-NoLinks $path
        $bytes = [IO.File]::ReadAllBytes($path)
        $prefix = [Text.Encoding]::ASCII.GetBytes(('blob ' + $bytes.Length + [char]0))
        $hash = [Security.Cryptography.SHA1]::Create()
        try {
            $null = $hash.TransformBlock($prefix,0,$prefix.Length,$prefix,0)
            $null = $hash.TransformFinalBlock($bytes,0,$bytes.Length)
            $actual = [Convert]::ToHexString($hash.Hash).ToLowerInvariant()
        } finally { $hash.Dispose() }
        if ($actual -cne $expected) { throw 'Raw disk/blob HOLD' }
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash + '  ' + $relative
    }
}
$evidence = Join-Path $env:RUNNER_TEMP ('p292-readonly-evidence-' + $env:REVIEW_ARCH)
$build = Join-Path $env:RUNNER_TEMP ('p292-readonly-build-' + [Guid]::NewGuid().ToString('N'))
foreach ($directory in @($evidence,$build)) {
    if (Test-Path -LiteralPath $directory) { throw 'Temp collision HOLD' }
    $null = New-Item -ItemType Directory -Path $directory
    Assert-NoLinks $directory
}
$artifacts = @('source-before.sha256','source-after.sha256','compiler.txt','binary.sha256','controls.txt','summary.txt')
foreach ($file in $artifacts) { [IO.File]::WriteAllText((Join-Path $evidence $file),'') }
function Record([string]$File, [string]$Text) { Add-Content -LiteralPath (Join-Path $evidence $File) -Value $Text }
$initial = @(Source-Hashes)
$initial | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$clock = [Diagnostics.Stopwatch]::StartNew()
# At most 390 seconds of script work, within the eight-minute job ceiling.
# Every child has <=15s wait, <=2s kill/join, <=1s output drain. Each completion emits safe progress;
# no operation may silently stall for the OM v2.1 five-minute watchdog.
function Child([string]$Exe, [string[]]$Arguments, [int]$Seconds) {
    if ($Seconds -lt 1 -or $Seconds -gt 15 -or $clock.Elapsed.TotalSeconds -ge 390) { throw 'Budget HOLD' }
    $info = [Diagnostics.ProcessStartInfo]::new($Exe)
    $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    $info.WorkingDirectory = $build; $info.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),@('TEMP',$build),@('TMP',$build),
        @('PSModulePath',(Join-Path $PSHOME 'Modules')),
        @('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),@('RUNNER_OS','Windows'),
        @('ImageOS','win22'),@('P292_READONLY_DIAG_ONLY','1'),@('POWERSHELL_TELEMETRY_OPTOUT','1'),
        @('POWERSHELL_UPDATECHECK','Off'))) { $info.Environment[$pair[0]] = $pair[1] }
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $info; $started = $false; $killAttempted = $false
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try {
        try { $started = $process.Start() }
        catch { return @{Kind='ERROR';Exit='UNAVAILABLE';Out='';Err='';Lat=(Bucket $watch.ElapsedMilliseconds)} }
        if (!$started) { return @{Kind='ERROR';Exit='UNAVAILABLE';Out='';Err='';Lat='LT100MS'} }
        $stdout = $process.StandardOutput.ReadToEndAsync(); $stderr = $process.StandardError.ReadToEndAsync()
        if (!$process.WaitForExit($Seconds * 1000)) {
            $killAttempted = $true
            $process.Kill($true)
            if (!$process.WaitForExit(2000)) { throw 'Child join HOLD' }
            if (![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdout,$stderr),1000)) {
                Record 'summary.txt' 'CHILD_OUTPUT_DRAIN=ERROR RAW_EXIT=UNAVAILABLE TIMED_OUT=1'
                throw 'Output drain HOLD'
            }
            return @{Kind='TIMEOUT';Exit='UNAVAILABLE';Out=$stdout.GetAwaiter().GetResult();
                Err=$stderr.GetAwaiter().GetResult();Lat=(Bucket $watch.ElapsedMilliseconds)}
        }
        if (![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdout,$stderr),1000)) {
            Record 'summary.txt' ('CHILD_OUTPUT_DRAIN=ERROR RAW_EXIT=' + $process.ExitCode)
            throw 'Output drain HOLD'
        }
        return @{Kind='RETURNED';Exit=$process.ExitCode;Out=$stdout.GetAwaiter().GetResult();
            Err=$stderr.GetAwaiter().GetResult();Lat=(Bucket $watch.ElapsedMilliseconds)}
    } finally {
        try {
            if ($started -and !$process.HasExited) {
                if ($killAttempted) { throw 'Unjoined child HOLD' }
                $killAttempted = $true
                $process.Kill($true)
                if (!$process.WaitForExit(2000)) { throw 'Child join HOLD' }
            }
        } finally { $process.Dispose() }
    }
}
function Bucket([long]$Milliseconds) {
    if ($Milliseconds -lt 100) { return 'LT100MS' }
    if ($Milliseconds -lt 1000) { return 'LT1S' }
    if ($Milliseconds -lt 5000) { return 'LT5S' }
    if ($Milliseconds -lt 12000) { return 'LT12S' }
    return 'GE12S'
}
$source = Join-Path $env:GITHUB_WORKSPACE 'tests/p292_readonly_observer/NativeScmReadOnlyCanary.cs'
$framework = Join-Path $env:WINDIR ('Microsoft.NET/' + $env:REVIEW_FRAMEWORK + '/v4.0.30319')
$csc = Join-Path $framework 'csc.exe'
$flags = @('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P292_READONLY_DIAG_ONLY')
function Compile([string]$Label, [string]$Architecture, [string[]]$Defines, [bool]$Negative) {
    $output = Join-Path $build ($Label + '.exe')
    if (Test-Path -LiteralPath $output) { throw 'Binary collision HOLD' }
    $options = @('/nologo','/noconfig','/debug-','/optimize-','/warn:4','/warnaserror+','/target:exe',
        ('/platform:' + $Architecture),('/out:' + $output),('/reference:' + (Join-Path $framework 'System.dll')))
    if ($Defines.Count) { $options += '/define:' + ($Defines -join ';') }
    $result = Child $csc (@($options) + $source) 15
    $raw = $result.Out + $result.Err
    $rawPath = Join-Path $build ($Label + '.compiler-raw.txt')
    [IO.File]::WriteAllText($rawPath,$raw)
    $codes = @([regex]::Matches($raw,'\b(?:error|warning) (CS[0-9]{4}):') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    Record 'compiler.txt' ($Label + ' RAW_EXIT=' + $result.Exit + ' STATUS=' + $result.Kind +
        ' CODES=' + ($codes -join ',') + ' RAW_SHA256=' + (Get-FileHash -LiteralPath $rawPath -Algorithm SHA256).Hash)
    Write-Output ('COMPILER ' + $Label + ' RAW_EXIT=' + $result.Exit)
    if ($Negative) {
        if ($result.Kind -cne 'RETURNED' -or $result.Exit -ne 1 -or (Test-Path -LiteralPath $output) -or
            $codes.Count -ne 1 -or $codes[0] -cne 'CS1029' -or $raw -notmatch 'error CS1029:.*P292_DEBUG_ISOLATED_READONLY_DIAG_ONLY') {
            throw 'Negative compilation HOLD'
        }
    } elseif ($result.Kind -cne 'RETURNED' -or $result.Exit -ne 0 -or $codes.Count -ne 0 -or
        !(Test-Path -LiteralPath $output)) { throw 'Compilation HOLD' }
}
# The paired CIM process is x64 pwsh on both matrix architectures. The AnyCPU
# bridge is the SAME source compiled independently, loaded in-process so raw
# account/path data never cross a process boundary. Standalone native x86 is
# still executed in every x86 job. Do not label the CIM process itself x86.
$cimChild = @'
param([string]$Label,[string]$Absent,[string]$Bridge)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:ImageOS -cne 'win22' -or $env:RUNNER_OS -cne 'Windows' -or
    $env:P292_READONLY_DIAG_ONLY -cne '1' -or !$IsWindows -or ![Environment]::Is64BitProcess) { exit 9 }
if ($Label -ceq 'A' -and $Absent -ceq '') { $name='EventLog' }
elseif ($Label -ceq 'B' -and $Absent -ceq '') { $name='Schedule' }
elseif ($Label -ceq 'X' -and $Absent -cmatch '\ANayeonP292_[0-9a-f]{12}\z') { $name=$Absent }
else { exit 9 }
try {
    $null=[Reflection.Assembly]::LoadFrom($Bridge)
    $before=[NativeScmReadOnlyCanary]::Begin($Label,$Absent)
    $before.Report()
    $rows=@(); $cimOk=$false; $hresult=0; $cimStatus=0; $detail='OBSERVED'
    $watch=[Diagnostics.Stopwatch]::StartNew()
    try {
        $rows=@(Get-CimInstance -Namespace root/cimv2 -ClassName Win32_Service -Filter ("Name='"+$name+"'") `
            -Property Name,StartName,PathName,State -OperationTimeoutSec 5 -ErrorAction Stop)
        $cimOk=$true
    } catch {
        $ex=$_.Exception; $hresult=$ex.HResult; $cimStatus=-1; $detail='QUERY_ERROR'
        for ($i=0;$i -lt 5 -and $null -ne $ex;$i++) {
            if ($ex.HResult -eq -2147024891) { $detail='ACCESS_DENIED'; $hresult=$ex.HResult }
            if ($ex -is [Microsoft.Management.Infrastructure.CimException]) {
                $cimStatus=[int]$ex.NativeErrorCode; $hresult=$ex.HResult
                if ($cimStatus -eq 2 -or $hresult -eq -2147024891) { $detail='ACCESS_DENIED' }
                break
            }
            $ex=$ex.InnerException
        }
    }
    $lat=[NativeScmReadOnlyCanary]::Bucket($watch.ElapsedMilliseconds)
    $after=[NativeScmReadOnlyCanary]::Begin($Label,$Absent)
    $after.Report()
    if ($cimOk) {
        'CIM=PASS;DETAIL=OBSERVED;LAT='+$lat+';HRESULT=0;CIMSTATUS=0'
        if ($rows.Count -eq 1) {
            $comparison=$before.Compare($after,1,$rows[0].Name,$rows[0].StartName,$rows[0].PathName,$rows[0].State)
        } else { $comparison=$before.Compare($after,$rows.Count,$null,$null,$null,$null) }
    } else {
        'CIM=ERROR;DETAIL='+$detail+';LAT='+$lat+';HRESULT='+$hresult+';CIMSTATUS='+$cimStatus
        $comparison='COMPARE=ERROR;DETAIL=CIM'
    }
    $comparison
    if ($cimOk -and $comparison -cmatch '\ACOMPARE=PASS;' -and $before.Passed() -and $after.Passed()) { exit 0 }
    exit 3
} catch { exit 9 }
'@
$latPattern = '(?:LT100MS|LT1S|LT5S|LT12S|GE12S)'
$nativePattern = '\ANATIVE=(?:PASS|ERROR|MISMATCH);DETAIL=(?:INTERNAL|GUARD|INPUT|MANAGER|ACCESS_DENIED|ABSENT_1060|OPEN|UNEXPECTED_PRESENT|CONFIG_SIZE|LAYOUT|CONFIG|EMPTY_CONFIG|STATUS|CLOSE|EXISTS);WIN32=[0-9]+;LAT=' + $latPattern + ';ARCH=(?:x64|x86)\z'
$cimPattern = '\ACIM=(?:PASS|ERROR);DETAIL=(?:OBSERVED|QUERY_ERROR|ACCESS_DENIED);LAT=' + $latPattern + ';HRESULT=-?[0-9]+;CIMSTATUS=-?[0-9]+\z'
$comparePattern = '\ACOMPARE=(?:PASS|ERROR|MISMATCH);DETAIL=(?:NATIVE|INPUT|ABSENT|PRESENCE|NAME|NATIVE_DRIFT|ACCOUNT_FORMAT|PATH_FORMAT|STATE|EXACT|CIM)\z'
$hold = $false; $completed = 0; $passed = 0
$counts = @{ERROR=0;TIMEOUT=0;MISMATCH=0;ACCESS_DENIED=0;CIM_ERROR=0;NATIVE_ERROR=0}
try {
    Record 'summary.txt' ('HEAD=' + $head + ' PARENT=' + $parent + ' TRIAL=' + $env:REVIEW_TRIAL +
        ' NATIVE_ARCH=' + $env:REVIEW_ARCH + ' CIM_PROCESS_ARCH=x64 SAMPLES=4 CONTROLS=3')
    Compile 'native' $env:REVIEW_ARCH $flags $false
    Compile 'bridge' 'anycpu' $flags $false
    Compile 'negative-none' $env:REVIEW_ARCH @() $true
    foreach ($flag in $flags) { Compile ('negative-' + $flag) $env:REVIEW_ARCH @($flags | Where-Object { $_ -cne $flag }) $true }
    Compile 'negative-release' $env:REVIEW_ARCH @($flags + 'RELEASE') $true
    $nativeExe = Join-Path $build 'native.exe'; $bridge = Join-Path $build 'bridge.exe'
    $binaryBefore = @($nativeExe,$bridge | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
    for ($i=0;$i -lt 2;$i++) { Record 'binary.sha256' ((@('native','bridge')[$i]) + ' BEFORE=' + $binaryBefore[$i]) }
    $childPath = Join-Path $build 'cim-child.ps1'
    [IO.File]::WriteAllText($childPath,$cimChild)
    $pwsh = Join-Path $PSHOME 'pwsh.exe'
    $absentName = 'NayeonP292_' + [Guid]::NewGuid().ToString('N').Substring(0,12)
    # Fixed planned samples, no read retry after empty/error/mismatch, no red-to-green acceptance.
    for ($sample=1;$sample -le 4;$sample++) {
        foreach ($label in @('A','B','X')) {
            $absent = if ($label -ceq 'X') { $absentName } else { '' }
            foreach ($transport in @('SCM','CIM_PAIR')) {
                $prefix = 'SAMPLE=' + $sample + ' LABEL=' + $label + ' TRANSPORT=' + $transport
                if ($transport -ceq 'SCM') { $result = Child $nativeExe @($label,$absent) 4 }
                else { $result = Child $pwsh @('-NoLogo','-NoProfile','-NonInteractive','-File',$childPath,
                    '-Label',$label,'-Absent',$absent,'-Bridge',$bridge) 12 }
                $status = 'ERROR'; $valid = $false
                # Preserve every complete sanitized receipt even if a later
                # child stage fails, times out, or violates the full protocol.
                foreach ($observed in @($result.Out -split '\r?\n')) {
                    if ($observed -cmatch $nativePattern -or $observed -cmatch $cimPattern -or $observed -cmatch $comparePattern) {
                        Record 'controls.txt' ($prefix + ' RECEIPT ' + $observed)
                        if ($observed -cmatch 'DETAIL=ACCESS_DENIED;') { $counts.ACCESS_DENIED++ }
                        if ($observed -cmatch '\ANATIVE=ERROR;') { $counts.NATIVE_ERROR++ }
                        if ($observed -cmatch '\ACIM=ERROR;') { $counts.CIM_ERROR++ }
                    }
                }
                if ($result.Kind -ceq 'TIMEOUT') {
                    $status = 'TIMEOUT'
                }
                elseif ($result.Kind -ceq 'RETURNED' -and $result.Err.Length -eq 0) {
                    $lines = @($result.Out -split '\r?\n' | Where-Object { $_.Length })
                    if ($transport -ceq 'SCM') {
                        $valid = $lines.Count -eq 1 -and $lines[0] -cmatch $nativePattern -and
                            $lines[0].EndsWith(';ARCH=' + $env:REVIEW_ARCH,[StringComparison]::Ordinal)
                    } else {
                        $valid = $lines.Count -eq 4 -and $lines[0] -cmatch $nativePattern -and $lines[1] -cmatch $nativePattern -and
                            $lines[0].EndsWith(';ARCH=x64',[StringComparison]::Ordinal) -and
                            $lines[1].EndsWith(';ARCH=x64',[StringComparison]::Ordinal) -and
                            $lines[2] -cmatch $cimPattern -and $lines[3] -cmatch $comparePattern
                    }
                    if ($valid) {
                        if (@($lines | Where-Object { $_ -cmatch '\A(?:NATIVE|CIM|COMPARE)=ERROR;' }).Count) { $status='ERROR' }
                        elseif (@($lines | Where-Object { $_ -cmatch '\A(?:NATIVE|COMPARE)=MISMATCH;' }).Count) { $status='MISMATCH' }
                        elseif ($result.Exit -eq 0) { $status='PASS' }
                        if (($status -ceq 'PASS' -and $result.Exit -ne 0) -or
                            ($status -cne 'PASS' -and $result.Exit -ne $(if ($transport -ceq 'SCM') { 1 } else { 3 }))) {
                            $status='ERROR'; $valid=$false
                        }
                    }
                }
                if ($status -ceq 'PASS') { $passed++ } else { $hold=$true; $counts[$status]++ }
                $completed++
                $receipt = $prefix + ' CONTROL=' + $status + ' RAW_EXIT=' + $result.Exit +
                    ' CHILD=' + $result.Kind + ' LAT=' + $result.Lat + ' PROTOCOL=' + $(if ($valid) { 'VALID' } else { 'UNVERIFIED' })
                Record 'controls.txt' $receipt
                Write-Output $receipt
            }
        }
    }
    $binaryAfter = @($nativeExe,$bridge | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
    for ($i=0;$i -lt 2;$i++) {
        Record 'binary.sha256' ((@('native','bridge')[$i]) + ' AFTER=' + $binaryAfter[$i])
        if ($binaryBefore[$i] -cne $binaryAfter[$i]) { throw 'Binary drift HOLD' }
    }
} catch {
    $hold=$true
    Record 'summary.txt' 'INFRASTRUCTURE=ERROR HOLD NO_RETRY'
} finally {
    try {
        $final = @(Source-Hashes)
        $final | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initial $final -CaseSensitive).Count) { throw 'Source drift HOLD' }
        Record 'summary.txt' 'SOURCE=RAW_IDENTICAL_1185_INHERITED_PLUS_4_ADDITIONS'
    } catch { $hold=$true; Record 'summary.txt' 'SOURCE=ERROR HOLD' }
    Record 'summary.txt' ('COMPLETED=' + $completed + '/24 PASS=' + $passed + ' ERROR=' + $counts.ERROR +
        ' TIMEOUT=' + $counts.TIMEOUT + ' MISMATCH=' + $counts.MISMATCH + ' ACCESS_DENIED=' + $counts.ACCESS_DENIED +
        ' CIM_ERROR=' + $counts.CIM_ERROR + ' NATIVE_ERROR=' + $counts.NATIVE_ERROR)
    Record 'summary.txt' 'P292_MECHANISM=NOT_ACCEPTED CLEANUP=NOT_TESTED PRODUCTION=HOLD EXTERNAL_APPROVALS=0/7 PRODUCT_REGRESSIONS=0/3'
}
if ($hold -or $completed -ne 24 -or $passed -ne 24) {
    Record 'summary.txt' 'DIAGNOSTIC=HOLD RAW_EXIT=1'
    exit 1
}
Record 'summary.txt' 'DIAGNOSTIC=CONCLUSIVE_STABLE_CONTROLS_ONLY RAW_EXIT=0 P292=HOLD'
exit 0
