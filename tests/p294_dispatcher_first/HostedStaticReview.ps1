# HOSTED WINDOWS-2022 COMPILE ONLY. Locally parse as data; never run/dot-source.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '4627157965bc978b5e502c85b6bc5eea5485050d'
$headBranch = 'byok-c1-p294-dispatcher-first-service-candidate-20261121'
$baseBranch = 'byok-c1-p293-scm-lifecycle-witness-contract-20261121'
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:RUNNER_OS -cne 'Windows' -or $env:ImageOS -cne 'win22' -or !$IsWindows -or
    ![Environment]::Is64BitProcess -or $env:GITHUB_EVENT_NAME -cne 'pull_request' -or
    $env:P294_COMPILE_ONLY -cne '1' -or $env:GITHUB_REPOSITORY -cne 'krismcan/Mark-LV' -or
    $env:REVIEW_ARCH -cnotin @('x64','x86') -or $env:REVIEW_TRIAL -cnotin @('1','2','3') -or
    $env:REVIEW_FRAMEWORK -cne (@{x64='Framework64';x86='Framework'}[$env:REVIEW_ARCH])) {
    throw 'Hosted compile-only guard HOLD'
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
    throw 'Exact direct-child checkout HOLD'
}
$added = @('tests/p294_dispatcher_first/P294DispatcherFirstDisposableService.cs',
    'tests/p294_dispatcher_first/HostedStaticReview.ps1',
    '.github/workflows/p294-windows-dispatcher-first-static-review.yml',
    'docs/byok-c1-p294-dispatcher-first-security-review.md')
$delta = @(Git-Read @('diff','--name-status','--no-renames',$parent,$head) | Sort-Object)
if (@(Compare-Object @($added | ForEach-Object { "A`t$_" } | Sort-Object) $delta -CaseSensitive).Count) {
    throw 'Exactly four additions HOLD'
}
$inherited = @(Git-Read @('ls-tree','-r',$parent))
$current = @(Git-Read @('ls-tree','-r',$head))
if ($inherited.Count -ne 1194 -or $current.Count -ne 1198 -or
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
# Pure text review, never loads a C# assembly or invokes any service entrypoint.
# The separate exact raw SHA pin below also denies any unreviewed extra code.
function Assert-CandidateText([string]$Text,[string]$Original) {
    $code=[regex]::Replace($Text,'(?m)//[^\r\n]*|/\*[\s\S]*?\*/','')
    $start=[regex]::Match($code,'(?s)protected override void OnStart\(string\[\] args\)\s*\{(?<body>.*?)\r?\n    \}\s*protected override void OnStop')
    $main=[regex]::Match($code,'(?s)private static int Main\(string\[\] args\)(?<body>.*)\z')
    if (!$start.Success -or !$main.Success) { throw 'Method structure HOLD' }
    $body=$start.Groups['body'].Value; $entry=$main.Groups['body'].Value
    foreach ($pattern in @('WindowsIdentity\.GetCurrent\(\)','new NTAccount\(', '\.Translate\(typeof\(SecurityIdentifier\)\)')) {
        if ([regex]::Matches($code,$pattern).Count -ne 1 -or [regex]::Matches($body,$pattern).Count -ne 1 -or
            [regex]::IsMatch($entry,$pattern)) { throw 'Identity lookup placement HOLD' }
    }
    $oldGuard=[regex]::Match($Original,'(?s)if \((identity\.ImpersonationLevel.*?)\) return 1;')
    $newGuard=[regex]::Match($body,'(?s)if \((identity\.ImpersonationLevel.*?)\) throw new InvalidOperationException\("P294_START_DENIED"\);')
    if (!$oldGuard.Success -or !$newGuard.Success -or
        ($oldGuard.Groups[1].Value -replace '\s','') -cne ($newGuard.Groups[1].Value -replace '\s','')) {
        throw 'Frozen identity predicate equivalence HOLD'
    }
    if ($body -cnotmatch 'new NTAccount\("NT SERVICE", expectedServiceName\)' -or
        $body -match '\b(return|async|Task|Thread|RequestAdditionalTime)\b' -or
        $body -cnotmatch 'catch \(Exception\)\s*\{\s*throw new InvalidOperationException\("P294_START_DENIED"\);\s*\}' -or
        [regex]::Matches($body,'throw new InvalidOperationException\("P294_START_DENIED"\);').Count -ne 2 -or
        $body.IndexOf('startIdentityVerified = true;') -lt $newGuard.Index+$newGuard.Length -or
        [regex]::Matches($code,'startIdentityVerified = true;').Count -ne 1) { throw 'Synchronous fail-closed OnStart HOLD' }
    if ([regex]::Matches($code,'ServiceBase\.Run\(service\);').Count -ne 1 -or
        [regex]::Matches($entry,'ServiceBase\.Run\(service\);').Count -ne 1 -or
        $entry -cnotmatch 'new P294DispatcherFirstDisposableService\(args\[1\]\)' -or
        $entry.IndexOf('ServiceBase.Run(service);') -lt $entry.IndexOf('new P294DispatcherFirstDisposableService(args[1])') -or
        $entry -cnotmatch 'return service\.startIdentityVerified \? 0 : 1;' -or
        $entry -cnotmatch 'catch \(Exception\)\s*\{ return 1; \}' -or
        $code -cnotmatch 'private readonly string expectedServiceName;' -or
        $code -cnotmatch 'expectedServiceName = name;\s*ServiceName = name;\s*AutoLog = false;' -or
        [regex]::Matches($code,'\bOnStart\(').Count -ne 1) { throw 'Dispatcher-only entry HOLD' }
    foreach ($required in @('args.Length != 4','P292_DISPOSABLE_SCM_WITNESS=1','args[1].Length != 23',
        '\\ANayeonP292_[0-9a-f]{12}\\z','4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f',
        'args[3].Length != 40','\\A[0-9a-f]{40}\\z','Environment.UserInteractive',
        'current.SessionId != 0','Environment.Exit(1);','55000, Timeout.Infinite')) {
        if (!$entry.Contains($required)) { throw 'Frozen mode/deadline HOLD' }
    }
    if ($entry.IndexOf('new Timer(') -gt $entry.IndexOf('ServiceBase.Run(service);') -or
        $code -match 'DllImport|ServiceInstaller|InstallUtil|ServiceController|RequestAdditionalTime|System\.Net|System\.IO|Console\.|EventLog\.|Registry|ProtectedData|Credential|Process\.Start|Environment\.GetEnvironmentVariable') {
        throw 'Authority/logging/timeout surface HOLD'
    }
}
$evidence=Join-Path $env:RUNNER_TEMP ('p294-static-evidence-'+$env:REVIEW_ARCH)
$build=Join-Path $env:RUNNER_TEMP ('p294-static-build-'+[Guid]::NewGuid().ToString('N'))
foreach ($directory in @($evidence,$build)) {
    if (Test-Path -LiteralPath $directory) { throw 'Temp collision HOLD' }
    $null=New-Item -ItemType Directory -Path $directory
    Assert-NoLinks $directory
}
foreach ($file in @('source-before.sha256','source-after.sha256','compiler.txt','binary.sha256','static.txt','summary.txt')) {
    [IO.File]::WriteAllText((Join-Path $evidence $file),'')
}
function Record([string]$File,[string]$Text) { Add-Content -LiteralPath (Join-Path $evidence $File) -Value $Text }
$framework=Join-Path $env:WINDIR ('Microsoft.NET/'+$env:REVIEW_FRAMEWORK+'/v4.0.30319')
$csc=Join-Path $framework 'csc.exe'
$source=Join-Path $env:GITHUB_WORKSPACE $added[0]
$clock=[Diagnostics.Stopwatch]::StartNew()
# No generic child launcher: the executable path is fixed to the framework compiler.
function Invoke-Compiler([string[]]$Arguments) {
    if ($clock.Elapsed.TotalSeconds -ge 360) { throw 'Compile budget HOLD' }
    $info=[Diagnostics.ProcessStartInfo]::new($csc)
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.WorkingDirectory=$build; $info.Environment.Clear()
    foreach ($pair in @(@('SystemRoot',$env:WINDIR),@('WINDIR',$env:WINDIR),
        @('PATH',(Join-Path $env:WINDIR 'System32')),@('TEMP',$build),@('TMP',$build))) {
        $info.Environment[$pair[0]]=$pair[1]
    }
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process=[Diagnostics.Process]::new(); $process.StartInfo=$info; $started=$false
    try {
        $started=$process.Start()
        if (!$started) { throw 'Compiler launch HOLD' }
        $stdout=$process.StandardOutput.ReadToEndAsync(); $stderr=$process.StandardError.ReadToEndAsync()
        if (!$process.WaitForExit(15000)) { throw 'Compiler deadline HOLD NO_RETRY' }
        if (![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdout,$stderr),1000)) { throw 'Compiler output deadline HOLD' }
        return @{Exit=$process.ExitCode; Out=$stdout.GetAwaiter().GetResult(); Err=$stderr.GetAwaiter().GetResult()}
    } finally {
        try {
            if ($started -and !$process.HasExited) {
                $process.Kill($true)
                if (!$process.WaitForExit(2000)) { throw 'Compiler unjoined HOLD' }
            }
        } finally { $process.Dispose() }
    }
}
function Compile([string]$Label,[string[]]$Defines,[bool]$Negative) {
    $output=Join-Path $build ($Label+'.exe')
    if (Test-Path -LiteralPath $output) { throw 'Output collision HOLD' }
    $options=@('/nologo','/noconfig','/nostdlib+','/warn:4','/warnaserror+','/debug-','/optimize-','/target:exe',
        ('/platform:'+$env:REVIEW_ARCH),('/out:'+$output))
    foreach ($reference in @('mscorlib.dll','System.dll','System.Core.dll','System.ServiceProcess.dll')) {
        $options+='/reference:'+(Join-Path $framework $reference)
    }
    if ($Defines.Count) { $options+='/define:'+($Defines -join ';') }
    $r=Invoke-Compiler (@($options)+@($source))
    $raw=$r.Out+$r.Err
    $rawPath=Join-Path $build ($Label+'.raw.txt'); [IO.File]::WriteAllText($rawPath,$raw)
    $codes=@([regex]::Matches($raw,'\b(?:error|warning) (CS[0-9]{4}):') |
        ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    Record 'compiler.txt' ($Label+' RAW_EXIT='+$r.Exit+' CODES='+($codes -join ',')+
        ' RAW_SHA256='+(Get-FileHash -LiteralPath $rawPath -Algorithm SHA256).Hash)
    Write-Output ('COMPILER='+$Label+' RAW_EXIT='+$r.Exit)
    if ($Negative) {
        if ($r.Exit -ne 1 -or (Test-Path -LiteralPath $output) -or $codes.Count -ne 1 -or $codes[0] -cne 'CS1029' -or
            [regex]::Matches($raw,'error CS1029:.*P294_DEBUG_ISOLATED_DISPATCHER_FIRST_ONLY_REQUIRED').Count -ne 1) {
            throw 'Negative compile HOLD'
        }
    } elseif ($r.Exit -ne 0 -or $codes.Count -ne 0 -or !(Test-Path -LiteralPath $output)) {
        throw 'Positive compile HOLD'
    }
}
$hold=$false; $initial=@(); $negatives=0
try {
    $initial=@(Source-Hashes)
    $initial | Set-Content -LiteralPath (Join-Path $evidence 'source-before.sha256')
    Record 'summary.txt' ('HEAD='+$head+' PARENT='+$parent+' ARCH='+$env:REVIEW_ARCH+' TRIAL='+$env:REVIEW_TRIAL)
    $originalPath=Join-Path $env:GITHUB_WORKSPACE 'tests/p292_service_principal/P292DisposableService.cs'
    if ((Get-FileHash -LiteralPath $originalPath -Algorithm SHA256).Hash -cne 'B226DD10506640F90D49E5EE0C27DB3D22DC21B759138469B94A7CC3E520F665' -or
        (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -cne '2B7D87F8770BED1B21C756DE0344D34C5A87584D800AF58A430B9864CB1B81FC') {
        throw 'Frozen original/candidate SHA256 HOLD'
    }
    $text=[IO.File]::ReadAllText($source); $original=[IO.File]::ReadAllText($originalPath)
    Assert-CandidateText $text $original
    $mutations=@($original,
        $text.Replace('.Translate(typeof(SecurityIdentifier))',''),
        $text.Replace('identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid)','false'),
        $text.Replace('startIdentityVerified = true;','startIdentityVerified = false;'),
        $text.Replace('55000','56000'),
        $text.Replace('ServiceBase.Run(service);','OnStart(args);'),
        $text.Replace('throw new InvalidOperationException("P294_START_DENIED");','return;'))
    foreach ($mutation in $mutations) {
        $rejected=$false
        try { Assert-CandidateText $mutation $original } catch { $rejected=$true }
        if (!$rejected) { throw 'Source negative accepted HOLD' }
    }
    $tokens=$null; $parseErrors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile((Join-Path $env:GITHUB_WORKSPACE $added[1]),[ref]$tokens,[ref]$parseErrors)
    if ($parseErrors.Count) { throw 'PowerShell AST HOLD' }
    Record 'static.txt' 'ORDER=DISPATCHER_THEN_SYNCHRONOUS_IDENTITY GUARD=FROZEN_PREDICATE_EQUIVALENT POWERSHELL_AST_ERRORS=0'
    Record 'static.txt' 'SOURCE_DATA_NEGATIVES=7/7 INCLUDING_FROZEN_PRE_DISPATCHER_SOURCE NOT_SERVICE_VALIDATION'
    # Exhaust the four-symbol truth table. Only mask 7 is allowed (DEBUG+isolated+P294).
    $symbols=@('DEBUG','C1_REVIEW_ISOLATED_ASSEMBLY','C1_P294_DISPATCHER_FIRST_ONLY','RELEASE')
    Compile 'positive' $symbols[0..2] $false
    for ($mask=0;$mask -lt 16;$mask++) {
        if ($mask -eq 7) { continue }
        $defines=@(for ($bit=0;$bit -lt 4;$bit++) { if ($mask -band (1 -shl $bit)) { $symbols[$bit] } })
        Compile ('negative-mask-'+$mask) $defines $true
        $negatives++
    }
    # Hash once after all compiler children have exited; never load/run the image.
    Record 'binary.sha256' ((Get-FileHash -LiteralPath (Join-Path $build 'positive.exe') -Algorithm SHA256).Hash+'  positive.exe NOT_EXECUTED')
} catch {
    $hold=$true
    # Preserve failure text privately; publish only its hash, never exception text.
    $failurePath=Join-Path $build 'failure.raw.txt'
    [IO.File]::WriteAllText($failurePath,$_.ToString())
    Record 'summary.txt' ('STATIC_OR_COMPILER=HOLD FAILURE_SHA256='+(Get-FileHash -LiteralPath $failurePath -Algorithm SHA256).Hash)
} finally {
    try {
        $final=@(Source-Hashes)
        $final | Set-Content -LiteralPath (Join-Path $evidence 'source-after.sha256')
        if ($initial.Count -ne 1198 -or $final.Count -ne 1198 -or
            @(Compare-Object $initial $final -CaseSensitive).Count) { throw 'Source drift HOLD' }
        Record 'summary.txt' 'SOURCE=RAW_IDENTICAL_1194_INHERITED_PLUS_4_ADDITIONS'
    } catch { $hold=$true; Record 'summary.txt' 'SOURCE=HOLD' }
    Record 'summary.txt' ('COMPLETED_NEGATIVE_COMPILES='+$negatives+' CANDIDATE_EXE_LAUNCHES=0 SCM_OPERATIONS=0')
    Record 'summary.txt' 'RUNTIME_ACCEPTANCE=NOT_TESTED PRODUCTION_ALLOWED=0 REAL_KEYS_ALLOWED=0 EXTERNAL_APPROVALS=0/7 FULL_REGRESSIONS=0/3 P292_CLEANUP=UNVERIFIED'
}
if ($hold) { Record 'summary.txt' 'COMPILE_STATIC_EVIDENCE=HOLD SCRIPT_RAW_EXIT=1'; exit 1 }
Record 'summary.txt' 'COMPILE_STATIC_EVIDENCE=ONLY SCRIPT_RAW_EXIT=0'
exit 0
