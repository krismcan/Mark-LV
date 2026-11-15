# No SDK, packages, product sources, service startup or full regressions.
$ErrorActionPreference = 'Stop'
$sources = @((Join-Path $PSScriptRoot 'EffectFreeServiceOrdering.cs'),
             (Join-Path $PSScriptRoot 'OrderingTests.cs'))
$output = Join-Path ([System.IO.Path]::GetTempPath()) ('nayeon-p247-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $output | Out-Null
Write-Output ('P247_ARTIFACTS=' + $output)
foreach ($arch in @('x64', 'x86')) {
    $framework = if ($arch -eq 'x64') { 'Framework64' } else { 'Framework' }
    $compiler = Join-Path $env:WINDIR ('Microsoft.NET\' + $framework + '\v4.0.30319\csc.exe')
    if (!(Test-Path -LiteralPath $compiler)) { throw ('Compiler unavailable: ' + $compiler) }
    $denied = Join-Path $output ($arch + '-without-flags.exe')
    $guardLog = Join-Path $output ($arch + '-guard.log')
    & $compiler /nologo /target:exe "/platform:$arch" "/out:$denied" @sources > $guardLog
    $guardExit = $LASTEXITCODE
    if ($guardExit -eq 0 -or (Test-Path -LiteralPath $denied) -or
        !(Select-String -LiteralPath $guardLog -SimpleMatch 'P247 NONDEPLOYABLE EFFECT-FREE TEST MODEL')) {
        throw 'Missing explicit no-flags build refusal'
    }
    Write-Output ("P247_$arch" + '_NO_FLAGS_REFUSED=PASS')
    $exe = Join-Path $output ($arch + '-p247.exe')
    & $compiler /nologo /target:exe "/platform:$arch" /define:C1_REVIEW_ISOLATED_ASSEMBLY,C1_SYNTHETIC_TEST "/out:$exe" @sources
    if ($LASTEXITCODE -ne 0) { throw 'P247 compilation failed' }
    $stdout = Join-Path $output ($arch + '-stdout.log')
    $stderr = Join-Path $output ($arch + '-stderr.log')
    $process = Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (!$process.WaitForExit(30000)) { $process.Kill(); throw 'P247 exceeded 30-second bound' }
    $process.WaitForExit()
    Get-Content -LiteralPath $stdout
    Get-Content -LiteralPath $stderr
    if ($process.ExitCode -ne 0) { throw ('P247 native exit ' + $process.ExitCode) }
    Write-Output ("P247_$arch" + '_EXIT=0')
}
