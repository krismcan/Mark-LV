# HOSTED DRAFT COMPILE / MEMORY TESTS ONLY. Never run locally or dot-source.
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$parent = '2b4a10b483ca37505d4f0b20c7121bcd0f568c57'
$root = (Get-Location).Path
if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
    $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or $env:ImageOS -cne 'win22' -or
    $env:GITHUB_EVENT_NAME -cne 'pull_request' -or $env:GITHUB_REPOSITORY -cne 'krismcan/Mark-LV' -or
    $env:BUILD_ARCH -cnotin @('x64', 'x86') -or $env:BUILD_CONFIGURATION -cnotin @('Debug', 'Release')) {
  throw 'Hosted draft only HOLD'
}
$eventData = Get-Content -Raw -LiteralPath $env:GITHUB_EVENT_PATH | ConvertFrom-Json
$p = $eventData.pull_request
if ($eventData.action -cnotin @('opened', 'synchronize', 'reopened', 'converted_to_draft') -or
    $eventData.repository.full_name -cne $env:GITHUB_REPOSITORY -or $eventData.repository.id -ne 1402212689 -or
    $p.head.repo.full_name -cne $env:GITHUB_REPOSITORY -or $p.base.repo.full_name -cne $env:GITHUB_REPOSITORY -or
    $p.head.repo.id -ne $eventData.repository.id -or $p.base.repo.id -ne $eventData.repository.id -or
    $p.draft -isnot [bool] -or !$p.draft -or $p.base.sha -cne $parent -or
    $p.head.sha -cnotmatch '\A[0-9a-f]{40}\z' -or
    $p.head.ref -cne 'byok-c1-p96-p292-closure-20261125' -or
    $p.base.ref -cne 'byok-c1-p320-durable-custody-core-20261124' -or
    $env:GITHUB_HEAD_REF -cne $p.head.ref -or $env:GITHUB_BASE_REF -cne $p.base.ref) {
  throw 'Exact same-repository draft HOLD'
}
function Git-Read([string[]]$arguments) {
  $lines = @(& git --no-optional-locks @arguments)
  if ($LASTEXITCODE -ne 0) { throw 'Git HOLD' }
  return $lines
}
$head = [string](Git-Read @('rev-parse', 'HEAD'))
if ($head -cne $p.head.sha -or
    [string](Git-Read @('rev-list', '--parents', '-n', '1', $head)) -cne ($head + ' ' + $parent)) {
  throw 'Exact direct parent HOLD'
}
$scope = @{
  'src/Nayeon.ByokC1.Service/AtomicCustodyPublication.cs' = 'A'
  'src/Nayeon.ByokC1.Service/DenialOnlyRecoveryAdmission.cs' = 'A'
  'src/Nayeon.ByokC1.Service/CustodyService.cs' = 'M'
  'src/Nayeon.ByokC1.Service/CustodyTransactionCore.cs' = 'M'
  'src/Nayeon.ByokC1.Service/SyntheticTransactionOwner.cs' = 'M'
  'src/Nayeon.ByokC1.Service/ServiceRecoveryBoundary.cs' = 'M'
  'src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj' = 'M'
  'tests/p320_transaction_core/P320.Synthetic.csproj' = 'M'
  'tests/held_failure_service_ordering/HeldFailureServiceOrderingTests.cs' = 'A'
  'tests/held_failure_service_ordering/HeldFailure.ServiceOrdering.csproj' = 'A'
  'tests/held_failure_service_ordering/HostedDraftReview.ps1' = 'A'
  '.github/workflows/held-failure-service-ordering.yml' = 'A'
  'docs/byok-c1-held-p96-p292-integration.md' = 'A'
}
$expected = @($scope.Keys | ForEach-Object { $scope[$_] + "`t" + $_ } | Sort-Object)
$actual = @(Git-Read @('diff', '--name-status', '--no-renames', $parent, $head) | Sort-Object)
if ($actual.Count -ne $expected.Count -or (Compare-Object -CaseSensitive $expected $actual)) { throw 'Exact scope HOLD' }
git diff --check $parent $head
if ($LASTEXITCODE -ne 0) { throw 'Whitespace HOLD' }
$tree = @(Git-Read @('ls-tree', '-r', $head))
$paths = @(); $oids = @()
foreach ($entry in $tree) {
  if ($entry -cnotmatch '\A100644 blob ([0-9a-f]{40})\t([a-zA-Z0-9_./-]+)\z') { throw 'Regular source tree HOLD' }
  $oids += $Matches[1]; $paths += $Matches[2]
}
function Source-Manifest {
  if ([string](Git-Read @('rev-parse', 'HEAD')) -cne $head -or
      @(Git-Read @('status', '--porcelain=v1', '--untracked-files=all', '--ignored')).Count) { throw 'Source drift HOLD' }
  foreach ($path in $paths) {
    $item = Get-Item -LiteralPath $path -Force
    while ($null -ne $item) {
      if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Source reparse HOLD' }
      if ($item.FullName -ceq $root) { break }
      if ($item -is [IO.FileInfo]) { $item = $item.Directory } else { $item = $item.Parent }
    }
  }
  $disk = @($paths | & git hash-object --no-filters --stdin-paths)
  if ($LASTEXITCODE -ne 0 -or $disk.Count -ne $oids.Count) { throw 'Raw source custody HOLD' }
  for ($i = 0; $i -lt $paths.Count; $i++) {
    if ($disk[$i] -cne $oids[$i]) { throw 'Raw source bytes HOLD' }
    (Get-FileHash -LiteralPath $paths[$i] -Algorithm SHA256).Hash + ' ' + $paths[$i]
  }
}
function Require-Sources([string]$project, [string[]]$expectedSources) {
  [xml]$xml = Get-Content -Raw -LiteralPath $project
  $includes = @($xml.Project.ItemGroup.Compile | ForEach-Object { $_.Include })
  if ($includes.Count -ne $expectedSources.Count -or
      (Compare-Object -CaseSensitive ($includes | Sort-Object) ($expectedSources | Sort-Object))) { throw 'Compile sources HOLD' }
  if (@($xml.SelectNodes('//*[local-name()="ProjectReference" or local-name()="PackageReference"]')).Count) { throw 'Dependency HOLD' }
}
$serviceProject = 'src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj'
$p320Project = 'tests/p320_transaction_core/P320.Synthetic.csproj'
$sharedProject = 'tests/held_failure_service_ordering/HeldFailure.ServiceOrdering.csproj'
Require-Sources $serviceProject @('CustodyService.cs', 'LifecycleCoordinator.cs', 'ServiceRecoveryBoundary.cs',
  'StatusPipeServer.cs', 'StatusPipeClient.cs', 'SyntheticTransactionOwner.cs', 'SyntheticIngressServer.cs',
  'HostedDisposableWinCred.cs', 'HostedDisposableWinCred.P313Admission.cs', 'DurableIntentJournal.cs',
  'AtomicCustodyPublication.cs', 'DenialOnlyRecoveryAdmission.cs')
$shared = @('..\..\src\Nayeon.ByokC1.Service\AtomicCustodyPublication.cs',
  '..\..\src\Nayeon.ByokC1.Service\DenialOnlyRecoveryAdmission.cs',
  '..\..\src\Nayeon.ByokC1.Service\SyntheticTransactionOwner.cs')
Require-Sources $p320Project (@('P320TransactionCoreTests.cs',
  '..\..\src\Nayeon.ByokC1.Service\CustodyTransactionCore.cs', '..\p95_native_custody_preflight\CustodyLedger.cs') + $shared)
Require-Sources $sharedProject (@('HeldFailureServiceOrderingTests.cs') + $shared)
$before = @(Source-Manifest)
Write-Output "INPUT_HEAD=$head EXACT_PARENT=$parent ARCH=$env:BUILD_ARCH CONFIGURATION=$env:BUILD_CONFIGURATION"
$before | Write-Output
function Invoke-Bounded([string]$program, [string[]]$arguments, [int]$deadline) {
  if ($program -cnotin $allowedPrograms) { throw 'Fixed compiler/test program HOLD' }
  $start = [Diagnostics.ProcessStartInfo]::new()
  $start.FileName = $program
  $start.UseShellExecute = $false
  $start.CreateNoWindow = $true
  $start.WorkingDirectory = $root
  $start.RedirectStandardOutput = $true
  $start.RedirectStandardError = $true
  foreach ($argument in $arguments) { $start.ArgumentList.Add($argument) }
  $limit = 24 * 1024
  $captures = @()
  $process = $null
  $elapsed = [Diagnostics.Stopwatch]::StartNew()
  try {
    foreach ($name in @('STDOUT', 'STDERR')) {
      $path = Join-Path $env:RUNNER_TEMP ("held-ordering-{0}-{1}.log" -f [Guid]::NewGuid().ToString('N'), $name)
      $file = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
      $captures += @{ Name = $name; Path = $path; File = $file; Buffer = [byte[]]::new(4096);
        Saved = 0; Truncated = $false; Source = $null; Pending = $null }
    }
    $process = [Diagnostics.Process]::Start($start)
    $captures[0].Source = $process.StandardOutput.BaseStream
    $captures[1].Source = $process.StandardError.BaseStream
    foreach ($capture in $captures) {
      $capture.Pending = $capture.Source.ReadAsync($capture.Buffer, 0, $capture.Buffer.Length)
    }
    $timedOut = $false
    $drain = $null
    while ($true) {
      foreach ($capture in $captures) {
        if ($null -ne $capture.Pending -and $capture.Pending.IsCompleted) {
          $count = $capture.Pending.GetAwaiter().GetResult()
          $capture.Pending = $null
          if ($count -gt 0) {
            $keep = [Math]::Min($count, $limit - $capture.Saved)
            if ($keep -gt 0) { $capture.File.Write($capture.Buffer, 0, $keep); $capture.Saved += $keep }
            if ($keep -lt $count) { $capture.Truncated = $true }
            $capture.Pending = $capture.Source.ReadAsync($capture.Buffer, 0, $capture.Buffer.Length)
          }
        }
      }
      if (!$process.HasExited -and $elapsed.ElapsedMilliseconds -ge $deadline) {
        $timedOut = $true
        $process.Kill($true)
        if (!$process.WaitForExit(5000)) { throw 'Process cleanup incomplete; HOLD' }
      }
      if ($process.HasExited) {
        if ($null -eq $captures[0].Pending -and $null -eq $captures[1].Pending) { break }
        if ($null -eq $drain) { $drain = [Diagnostics.Stopwatch]::StartNew() }
        if ($drain.ElapsedMilliseconds -ge 5000) { throw 'Process output cleanup incomplete; HOLD' }
        [Threading.Thread]::Sleep(10)
      } else { [void]$process.WaitForExit(10) }
    }
    Write-Output "PROGRAM=$program EXIT=$($process.ExitCode) ELAPSED_MS=$($elapsed.ElapsedMilliseconds) ARCH=$env:BUILD_ARCH CONFIGURATION=$env:BUILD_CONFIGURATION"
    if ($timedOut) { throw 'Process deadline exceeded; HOLD' }
    if ($process.ExitCode -ne 0) { throw 'Build/test failed; HOLD' }
    if (@($captures | Where-Object { $_.Truncated }).Count -ne 0) { throw 'Diagnostic cap exceeded; HOLD' }
  } finally {
    try {
      if ($null -ne $process -and !$process.HasExited) {
        $process.Kill($true)
        if (!$process.WaitForExit(5000)) { throw 'Process cleanup incomplete; HOLD' }
      }
    } finally {
      try {
        foreach ($capture in $captures) {
          $capture.File.Dispose()
          $diagnostic = [Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($capture.Path))
          $diagnostic = $diagnostic -replace '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '?' -replace '::', ': :'
          Write-Output "PROGRAM=$program STREAM=$($capture.Name) BYTES=$($capture.Saved) TRUNCATED=$($capture.Truncated)"
          foreach ($line in ($diagnostic -split '\r\n|\n|\r')) { Write-Output "[$($capture.Name)] $line" }
        }
      } finally {
        foreach ($capture in $captures) {
          if ($null -ne $capture.Source) { $capture.Source.Dispose() }
          $capture.File.Dispose()
          Remove-Item -LiteralPath $capture.Path -Force -ErrorAction Stop
        }
        if ($null -ne $process) { $process.Dispose() }
      }
    }
  }
}
try {
  $out = Join-Path $env:RUNNER_TEMP ('held-ordering-' + [Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $out -ErrorAction Stop | Out-Null
  $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
  if (!(Test-Path -LiteralPath $vswhere -PathType Leaf)) { throw 'Installed vswhere required; no download' }
  $msbuild = & $vswhere -latest -products '*' -requires Microsoft.Component.MSBuild -find 'MSBuild\**\Bin\MSBuild.exe' | Select-Object -First 1
  if ($LASTEXITCODE -ne 0 -or !$msbuild) { throw 'Installed MSBuild required; no download' }
  $p320Exe = Join-Path $out 'p320/P320.TransactionCore.Tests.exe'
  $sharedExe = Join-Path $out 'shared/HeldFailure.ServiceOrdering.Tests.exe'
  $allowedPrograms = @($msbuild, $p320Exe, $sharedExe)
  foreach ($build in @(@{ Project = $serviceProject; Folder = 'service' },
      @{ Project = $p320Project; Folder = 'p320' }, @{ Project = $sharedProject; Folder = 'shared' })) {
    $buildOut = Join-Path $out $build.Folder
    Invoke-Bounded $msbuild @($build.Project, '/nologo', '/verbosity:minimal', '/t:Build',
      '/warnaserror', '/p:TreatWarningsAsErrors=true', '/nodeReuse:false',
      "/p:Configuration=$env:BUILD_CONFIGURATION", "/p:Platform=$env:BUILD_ARCH",
      "/p:OutputPath=$buildOut\", "/p:IntermediateOutputPath=$buildOut\obj\") 90000
  }
  $artifacts = @((Join-Path $out 'service/Nayeon.ByokC1.Service.exe'), $p320Exe, $sharedExe)
  $artifactBefore = @($artifacts | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
  Write-Output "COMPILE_ONLY_SERVICE_SHA256=$($artifactBefore[0])"
  Invoke-Bounded $p320Exe @() 120000
  Invoke-Bounded $sharedExe @() 45000
  $artifactAfter = @($artifacts | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
  if (($artifactBefore -join ',') -cne ($artifactAfter -join ',')) { throw 'Artifact drift HOLD' }
} finally {
  $after = @(Source-Manifest)
  if (($before -join "`n") -cne ($after -join "`n")) { throw 'Source manifest drift HOLD' }
}
Write-Output 'DRAFT ONLY; P320 142 + SHARED DENIAL 47 PER SHAPE; P96/P292 OPEN; APPROVALS 0/7; FULL REGRESSIONS 0/3; REAL-KEY NO-GO; PRODUCTION HOLD'
