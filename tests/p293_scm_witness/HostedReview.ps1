# HOSTED ONLY. On Kristian parse as data; NEVER execute or dot-source this script.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '7c1b70c041010a19262e7772d0f4782c20542041'
$headBranch = 'byok-c1-p293-scm-lifecycle-witness-contract-20261121'
$baseBranch = 'byok-c1-p292-readonly-scm-cim-diagnostic-20261120'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:RUNNER_OS -cne 'Windows' -or $env:ImageOS -cne 'win22' -or !$IsWindows -or
    ![Environment]::Is64BitProcess -or $env:GITHUB_EVENT_NAME -cne 'pull_request' -or
    $env:P293_FAKE_WITNESS_ONLY -cne '1' -or $env:GITHUB_REPOSITORY -cne 'krismcan/Mark-LV' -or
    $env:REVIEW_ARCH -cnotin @('x64','x86') -or $env:REVIEW_TRIAL -cnotin @('1','2','3') -or
    $env:REVIEW_FRAMEWORK -cne (@{x64='Framework64';x86='Framework'}[$env:REVIEW_ARCH])) {
    throw 'Hosted fake-only guard HOLD'
}
$event = Get-Content -LiteralPath $env:GITHUB_EVENT_PATH -Raw | ConvertFrom-Json
$pr = $event.pull_request
if ($event.action -cnotin @('opened','synchronize','reopened') -or $pr.draft -isnot [bool] -or !$pr.draft -or
    $event.repository.full_name -cne 'krismcan/Mark-LV' -or
    $pr.base.repo.full_name -cne 'krismcan/Mark-LV' -or $pr.head.repo.full_name -cne 'krismcan/Mark-LV' -or
    $pr.base.sha -cne $parent -or $pr.base.ref -cne $baseBranch -or $pr.head.ref -cne $headBranch -or
    $env:GITHUB_HEAD_REF -cne $headBranch -or $env:GITHUB_BASE_REF -cne $baseBranch -or
    $pr.head.sha -cnotmatch '\A[0-9a-f]{40}\z') { throw 'Exact same-repo draft HOLD' }
function Git-Read([string[]]$Arguments) {
    $lines = @(& git --no-optional-locks @Arguments 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'Git HOLD' }
    return $lines
}
$head = [string](Git-Read @('rev-parse','HEAD'))
if ($head -cne $pr.head.sha -or
    [string](Git-Read @('rev-list','--parents','-n','1',$head)) -cne ($head+' '+$parent) -or
    [string](Git-Read @('rev-parse','--show-toplevel')) -cne $env:GITHUB_WORKSPACE.Replace('\','/')) {
    throw 'Exact child checkout HOLD'
}
$added = @('native_c1_successor/P293NonDeployableScmWitnessGate.cs',
    'tests/p293_scm_witness/P293WitnessTests.cs','tests/p293_scm_witness/HostedReview.ps1',
    '.github/workflows/p293-windows-scm-witness-contract.yml','docs/byok-c1-p293-scm-witness-decision.md')
$delta = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $delta -CaseSensitive).Count) {
    throw 'Five additions HOLD'
}
$inherited = @(Git-Read @('ls-tree','-r',$parent))
$current = @(Git-Read @('ls-tree','-r',$head))
if ($inherited.Count -ne 1189 -or $current.Count -ne 1194 -or
    @($inherited | Where-Object { $_ -cnotin $current }).Count) { throw 'Inherited tree HOLD' }
function Assert-NoLinks([string]$Path) {
    for ($p=[IO.Path]::GetFullPath($Path); $null -ne $p; $p=[IO.Path]::GetDirectoryName($p)) {
        $item=Get-Item -LiteralPath $p -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.LinkType) { throw 'Link HOLD' }
    }
}
function Source-Hashes {
    if (@(Git-Read @('status','--porcelain=v1','--untracked-files=all','--ignored=matching')).Count -or
        @(Git-Read @('diff','--name-only',$head)).Count -or
        @(Git-Read @('diff','--cached','--name-only',$head)).Count) { throw 'Clean source HOLD' }
    if ([string](Git-Read @('rev-parse','HEAD')) -cne $head -or
        @(Compare-Object $current @(Git-Read @('ls-tree','-r','HEAD')) -CaseSensitive).Count) { throw 'Git drift HOLD' }
    foreach ($line in $current) {
        if ($line -cnotmatch '\A100644 blob ([0-9a-f]{40})\t([^\r\n]+)\z') { throw 'Tree mode HOLD' }
        $expected=$Matches[1]; $relative=$Matches[2]
        $path=Join-Path $env:GITHUB_WORKSPACE $relative
        Assert-NoLinks $path
        $bytes=[IO.File]::ReadAllBytes($path)
        $prefix=[Text.Encoding]::ASCII.GetBytes(('blob '+$bytes.Length+[char]0))
        $sha=[Security.Cryptography.SHA1]::Create()
        try {
            $null=$sha.TransformBlock($prefix,0,$prefix.Length,$prefix,0)
            $null=$sha.TransformFinalBlock($bytes,0,$bytes.Length)
            $actual=[Convert]::ToHexString($sha.Hash).ToLowerInvariant()
        } finally { $sha.Dispose() }
        if ($actual -cne $expected) { throw 'Raw disk/blob HOLD' }
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash+'  '+$relative
    }
}
$evidence=Join-Path $env:RUNNER_TEMP ('p293-fake-evidence-'+$env:REVIEW_ARCH)
$build=Join-Path $env:RUNNER_TEMP ('p293-fake-build-'+[Guid]::NewGuid().ToString('N'))
foreach ($directory in @($evidence,$build)) {
    if (Test-Path -LiteralPath $directory) { throw 'Temp collision HOLD' }
    $null=New-Item -ItemType Directory -Path $directory
    Assert-NoLinks $directory
}
foreach ($file in @('source-before.sha256','source-after.sha256','compiler.txt','binary.sha256',
    'cases.txt','summary.txt')) { [IO.File]::WriteAllText((Join-Path $evidence $file),'') }
function Record([string]$File,[string]$Text) { Add-Content -LiteralPath (Join-Path $evidence $File) -Value $Text }
$initial=@(Source-Hashes)
$initial | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
$clock=[Diagnostics.Stopwatch]::StartNew()
function Child([string]$Exe,[string[]]$Arguments) {
    if ($clock.Elapsed.TotalSeconds -ge 360) { throw 'Total budget HOLD' }
    $info=[Diagnostics.ProcessStartInfo]::new($Exe)
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.WorkingDirectory=$build; $info.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),@('TEMP',$build),@('TMP',$build),
        @('GITHUB_ACTIONS','true'),@('RUNNER_ENVIRONMENT','github-hosted'),@('RUNNER_OS','Windows'),
        @('ImageOS','win22'),@('P293_FAKE_WITNESS_ONLY','1'),@('REVIEW_ARCH',$env:REVIEW_ARCH))) {
        $info.Environment[$pair[0]]=$pair[1]
    }
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process=[Diagnostics.Process]::new(); $process.StartInfo=$info; $started=$false
    try {
        $started=$process.Start()
        if (!$started) { throw 'Child start HOLD' }
        $stdout=$process.StandardOutput.ReadToEndAsync(); $stderr=$process.StandardError.ReadToEndAsync()
        if (!$process.WaitForExit(15000)) { throw 'Child timeout HOLD NO_RETRY' }
        if (![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdout,$stderr),1000)) {
            throw 'Child output timeout HOLD'
        }
        return @{Exit=$process.ExitCode; Out=$stdout.GetAwaiter().GetResult(); Err=$stderr.GetAwaiter().GetResult()}
    } finally {
        try {
            if ($started -and !$process.HasExited) {
                $process.Kill($true)
                if (!$process.WaitForExit(2000)) { throw 'Child unjoined HOLD' }
            }
        } finally { $process.Dispose() }
    }
}
$model=Join-Path $env:GITHUB_WORKSPACE $added[0]
$tests=Join-Path $env:GITHUB_WORKSPACE $added[1]
$framework=Join-Path $env:WINDIR ('Microsoft.NET/'+$env:REVIEW_FRAMEWORK+'/v4.0.30319')
$csc=Join-Path $framework 'csc.exe'
$flags=@('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P293_FAKE_WITNESS_ONLY')
function Compile([string]$Label,[string[]]$Defines,[bool]$Negative) {
    $output=Join-Path $build ($Label+'.exe')
    if (Test-Path -LiteralPath $output) { throw 'Output collision HOLD' }
    $options=@('/nologo','/noconfig','/warn:4','/warnaserror+','/debug-','/optimize-','/target:exe',
        ('/platform:'+$env:REVIEW_ARCH),('/out:'+$output),
        ('/reference:'+(Join-Path $framework 'System.dll')),
        ('/reference:'+(Join-Path $framework 'System.Core.dll')))
    if ($Defines.Count) { $options+='/define:'+($Defines -join ';') }
    $r=Child $csc (@($options)+@($model,$tests))
    $raw=$r.Out+$r.Err
    $rawPath=Join-Path $build ($Label+'.raw.txt'); [IO.File]::WriteAllText($rawPath,$raw)
    $codes=@([regex]::Matches($raw,'\b(?:error|warning) (CS[0-9]{4}):') |
        ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    Record 'compiler.txt' ($Label+' RAW_EXIT='+$r.Exit+' CODES='+($codes -join ',')+
        ' RAW_SHA256='+(Get-FileHash -LiteralPath $rawPath -Algorithm SHA256).Hash)
    Write-Output ('COMPILER='+$Label+' RAW_EXIT='+$r.Exit)
    if ($Negative) {
        if ($r.Exit -ne 1 -or (Test-Path -LiteralPath $output) -or $codes.Count -ne 1 -or
            $codes[0] -cne 'CS1029' -or
            @([regex]::Matches($raw,'error CS1029:.*P293_DEBUG_ISOLATED_FAKE_WITNESS_ONLY_REQUIRED')).Count -ne 2) {
            throw 'Negative compile HOLD'
        }
    } elseif ($r.Exit -ne 0 -or $codes.Count -ne 0 -or !(Test-Path -LiteralPath $output)) {
        throw 'Positive compile HOLD'
    }
}
$hold=$false; $runtimeExit='UNAVAILABLE'; $completed=0
try {
    Record 'summary.txt' ('HEAD='+$head+' PARENT='+$parent+' ARCH='+$env:REVIEW_ARCH+' TRIAL='+$env:REVIEW_TRIAL)
    $text=[IO.File]::ReadAllText($tests)
    $names=@([regex]::Matches($text,'\b(?:Case|Mutation|Missing)\("([A-Z0-9_]+)"') |
        ForEach-Object { $_.Groups[1].Value })
    if ($names.Count -lt 40 -or @($names | Sort-Object -Unique).Count -ne $names.Count -or
        $text -notmatch 'internal static class P293WitnessTests' -or
        [IO.File]::ReadAllText($model) -notmatch 'internal sealed class P293NonDeployableScmWitnessGate') {
        throw 'Exact class/case custody HOLD'
    }
    Compile 'positive' $flags $false
    Compile 'negative-none' @() $true
    foreach ($flag in $flags) { Compile ('negative-'+$flag) @($flags | Where-Object { $_ -cne $flag }) $true }
    Compile 'negative-release' @($flags+'RELEASE') $true
    $exe=Join-Path $build 'positive.exe'
    $binary=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    Record 'binary.sha256' ('BEFORE='+$binary)
    # Only executable invocation in this script: guarded, synthetic, independent of all product code.
    $r=Child $exe @(); $runtimeExit=$r.Exit
    $lines=@($r.Out -split '\r?\n' | Where-Object { $_ -cne '' })
    if ($r.Exit -ne 0 -or $r.Err -cne '' -or $lines.Count -ne $names.Count+1) { throw 'Fake runtime HOLD' }
    for ($i=0;$i -lt $names.Count;$i++) {
        if ($lines[$i] -cne ('CASE='+$names[$i]+' RESULT=PASS')) { throw 'Case order/result HOLD' }
        Record 'cases.txt' $lines[$i]; $completed++
    }
    if ($lines[-1] -cnotmatch '\ASUMMARY CASES=([0-9]+) ASSERTIONS=([0-9]+) FAKE_ONLY=1 PRODUCTION_ALLOWED=0\z' -or
        [int]$Matches[1] -ne $names.Count -or [int]$Matches[2] -lt 1000) { throw 'Assertions HOLD' }
    Record 'cases.txt' $lines[-1]
    $after=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    Record 'binary.sha256' ('AFTER='+$after)
    if ($after -cne $binary) { throw 'Binary drift HOLD' }
    Write-Output ('FAKE_CASES='+$completed+' RAW_EXIT='+$r.Exit)
} catch {
    $hold=$true; Record 'summary.txt' 'EVIDENCE=ERROR_OR_TIMEOUT HOLD NO_RETRY'
} finally {
    try {
        $final=@(Source-Hashes)
        $final | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if (@(Compare-Object $initial $final -CaseSensitive).Count) { throw 'Source drift HOLD' }
        Record 'summary.txt' 'SOURCE=RAW_IDENTICAL_1189_INHERITED_PLUS_5_ADDITIONS'
    } catch { $hold=$true; Record 'summary.txt' 'SOURCE=ERROR HOLD' }
    Record 'summary.txt' ('FAKE_RUNTIME_RAW_EXIT='+$runtimeExit+' COMPLETED_CASES='+$completed)
    Record 'summary.txt' 'REAL_KEY=NO_GO PRODUCTION=HOLD EXTERNAL_APPROVALS=0/7 PRODUCT_REGRESSIONS=0/3 REAL_SCM_CLEANUP=UNVERIFIED'
}
if ($hold) { Record 'summary.txt' 'FAKE_DEVELOPMENT_EVIDENCE=HOLD SCRIPT_RAW_EXIT=1'; exit 1 }
Record 'summary.txt' 'FAKE_DEVELOPMENT_EVIDENCE=COHERENT_ONLY SCRIPT_RAW_EXIT=0'
exit 0
