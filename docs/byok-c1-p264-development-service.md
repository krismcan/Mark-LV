# P264 development-only successor service executable

17 November 2026. **DEVELOPMENT CANDIDATE; REAL API KEY / PRODUCTION RELEASE HOLD.**

User authorization permits isolated implementation before formal external security
review, deferring the comprehensive retrospective until Nayeon is operational.
This is no security seal, production qualification or approval of the P250
principal/store design. One source writer; no staging, commit, tag, push or Drive
change. No service installation, start, SCM modification, pipe, WinCred, secret,
signing, deployment, policy change or provider call was performed.

Intake: branch `byok-c1-p264-service-runtime-development-20261117`, exact P261 HEAD
`49fe4ae32ed20122c3513798edb4687c0a202b1c`; clean index and worktree before edits;
no tag at HEAD. `.codex/CURRENT_STATE.md` describes older Phase 10.2 work and is
not authoritative for this branch; its bytes remain unchanged. Read dependencies:
AGENTS.md, engineering failure gate, P250 architecture, P261 boundary/observer/
tests, original P99 gate/chassis, candidate chassis, P251 and P258 hold records.

## Implemented boundary

Four additive files only:

* `native_c1_successor/P264DevelopmentCustodyService.cs`: actual EXE `Main` and
  `ServiceBase.Run`, SCM start/stop/shutdown/custom-command overrides and disposal.
* `tests/p264_successor/P264DevelopmentServiceTests.cs`: separate managed test EXE.
* `tests/test_byok_c1_p264_development_service.py`: five focused static test methods,
  including source mutations and frozen-byte witnesses.
* This approval-boundary note and host commands.

There is no default release build. Both `DEBUG` and the explicit
`C1_P264_DEVELOPMENT_ONLY` symbol are required. Default/invalid command lines
return 64 before service construction or SCM dispatch. The sole accepted token,
`--development-only-no-effects`, acknowledges development scope; it grants no
authority. Do not run that entrypoint or register the candidate in this task.

SCM start can establish a **RunningDenied** in-memory lifetime. It does not
establish qualified startup, custody, credentials, a listener or storage. Every
credential, IPC and store request returns immutable denial evidence with all
authority properties false, before start, while running and after termination.
Custom SCM commands are also denial-only. No string/secret request payload,
effect callback, backend interface, transferable permit or external dependency
is accepted by the owner. The private monitor serializes every lifecycle and
denial request. Same-thread reentry faults before the requested mutation. Stop,
revoke, fault and disposal latch; repeated terminal notifications are idempotent;
fault survives stop; disposal dominates the displayed state without clearing
fault evidence. Duplicate/stale start faults and cannot reopen that instance.
A new process starts denial-only: there is no durable recovery claim.

The service name is `NayeonV1ByokCustody`. A source-linked constant projection is
checked against frozen P99 `ServiceGate.ServiceName`, including its raw-byte pin.
This is a test-enforced source linkage, not a C# reference to that obsolete class.
Only the new service source compiles into the candidate: the historical
LocalSystem-only eligibility gate and ProtectedAcl are deliberately absent.
Neither LocalSystem nor a virtual account, ACL, SDDL, store or profile is selected.
Matching a name is not principal, loaded-image or production identity evidence.

## Open Failures & Prior-Issues Review

This bounded review carries prior findings forward; it is not the deferred
comprehensive audit. Independent P264 review and all native execution are pending.

| Prior issue / severity | Cause, affected route and existing evidence | P264 containment / disposition |
| --- | --- | --- |
| P96 / HIGH | Separate final approval/lease probes precede external dispatch; original negative harness reproduces revoke winning before effect. | No effect path exists here; one private owner orders denial/lifecycle. Original coordinator is unchanged and NOT repaired. HOLD. |
| P261 identity / HIGH | P216 virtual-account proposal omits `V1`; frozen service name and original LocalSystem-only gate also conflict with the proposal. | Source name consistency test; no original eligibility calls or compiled legacy dependencies. Qualified principal/startup repair remains HOLD. |
| P251 / P258 / HIGH | Legacy same-user/native routes and original failures; P258 default route containment is bounded, with inherited failures unwaived. | No composition/import of legacy routes; all original files unchanged. No package/OS isolation proof. HOLD. |
| P76 / material | Four original failing methods remain unwaived in prior records. | Frozen tests retained; no full-suite substitute or closure claim. HOLD. |
| P261 host controls / material missing evidence | Prior x64 launch blocked by Application Control; author Python access denied. Compilation is not execution. | No bypass, alternate interpreter or native execution here. Host tests pending. HOLD. |
| SEC-03/04 / HIGH missing evidence | Principal, ACL/store, IPC/consent, loaded-code, durable recovery and cross-process isolation unresolved. | No authority-bearing implementation. Qualified decisions and external review pending. REAL-KEY / RELEASE HOLD. |

**GO only for this user-authorized development source candidate.** Engineering
runtime acceptance, security and production remain HOLD. No prior failure is
waived. Formal independent approvals and whole-product regressions are not
advanced by these additions.

## Exact host review commands (not executed here)

Run from `D:\Nayeon\CODEX_P264_SERVICE_RUNTIME_20261117` using ordinary Windows
PowerShell on Nayeon's authorized host. Never weaken policy or use another loader
after a refusal. These commands compile x64/x86 review artifacts only; they never
install or run the service entrypoint. Preserve raw compiler exits. No download,
restore, package installation or signing is needed (.NET Framework compiler and
`System.ServiceProcess.dll` must already exist).

```powershell
$p264ServiceSource = (Resolve-Path -LiteralPath 'native_c1_successor/P264DevelopmentCustodyService.cs').Path
$p264TestSource = (Resolve-Path -LiteralPath 'tests/p264_successor/P264DevelopmentServiceTests.cs').Path
$p264Out = Join-Path $env:TEMP ('nayeon-p264-review-' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $p264Out
$p264Targets = @(
    @{ Arch = 'x64'; Framework = 'Framework64' },
    @{ Arch = 'x86'; Framework = 'Framework' }
)
foreach ($p264Target in $p264Targets) {
    $p264Arch = $p264Target.Arch
    $p264Framework = Join-Path $env:WINDIR ('Microsoft.NET\' + $p264Target.Framework + '\v4.0.30319')
    $p264Compiler = Join-Path $p264Framework 'csc.exe'
    $p264Common = @('/noconfig', '/target:exe', '/debug+', '/optimize-', '/warn:4', '/warnaserror+',
        ('/platform:' + $p264Arch), ('/reference:' + (Join-Path $p264Framework 'System.dll')),
        ('/reference:' + (Join-Path $p264Framework 'System.ServiceProcess.dll')))
    # Each incomplete opt-in MUST fail compilation, with the named #error(s).
    foreach ($p264Guard in @('NONE', 'DEBUG', 'C1_P264_DEVELOPMENT_ONLY')) {
        $p264GuardExe = Join-Path $p264Out ($p264Arch + '-' + $p264Guard + '-MUST-NOT-EXIST.exe')
        $p264GuardLog = Join-Path $p264Out ($p264Arch + '-' + $p264Guard + '-guard.log')
        $p264Define = @()
        if ($p264Guard -ne 'NONE') { $p264Define = @(('/define:' + $p264Guard)) }
        & $p264Compiler @p264Common @p264Define ('/out:' + $p264GuardExe) $p264ServiceSource *> $p264GuardLog
        $p264Exit = $LASTEXITCODE
        if ($p264Exit -eq 0 -or (Test-Path -LiteralPath $p264GuardExe)) { throw 'P264 guard failed' }
        $p264GuardText = Get-Content -LiteralPath $p264GuardLog -Raw
        if ($p264Guard -ne 'C1_P264_DEVELOPMENT_ONLY' -and $p264GuardText -notmatch 'error CS1029:.*P264_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED') { throw 'Wrong guard failure' }
        if ($p264Guard -ne 'DEBUG' -and $p264GuardText -notmatch 'error CS1029:.*P264_NO_RELEASE_BUILD') { throw 'Wrong release guard failure' }
    }
    $p264ServiceExe = Join-Path $p264Out ('P264.DevelopmentCustody.' + $p264Arch + '.exe')
    $p264TestExe = Join-Path $p264Out ('P264.DevelopmentTests.' + $p264Arch + '.exe')
    & $p264Compiler @p264Common '/define:DEBUG;C1_P264_DEVELOPMENT_ONLY' ('/out:' + $p264ServiceExe) $p264ServiceSource
    if ($LASTEXITCODE -ne 0) { throw 'P264 candidate compile failed' }
    & $p264Compiler @p264Common '/define:DEBUG;C1_P264_DEVELOPMENT_ONLY' ('/out:' + $p264TestExe) $p264TestSource
    if ($LASTEXITCODE -ne 0) { throw 'P264 test compile failed' }
}
# Retain this value for the separate test step below.
$p264Out
```

Only the focused source test runs Python; it never imports Nayeon or executes C#:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B -m unittest discover -s tests -p test_byok_c1_p264_development_service.py -v
if ($LASTEXITCODE -ne 0) { throw 'P264 source checks failed' }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Whitespace failure' }
```

For independently authorized host tests, keep `$p264Out` from the compile step.
The harness loads the review candidate as a managed assembly, checks its actual
entrypoint/IL and invokes denial-only lifecycle methods in-process. It does not
call `ServiceBase.Run`. Never use this harness to execute a policy-blocked image;
stop at any compiler, loader or execution refusal, without trying another route.

```powershell
foreach ($p264Arch in @('x64', 'x86')) {
    $p264TestExe = Join-Path $p264Out ('P264.DevelopmentTests.' + $p264Arch + '.exe')
    $p264ServiceExe = Join-Path $p264Out ('P264.DevelopmentCustody.' + $p264Arch + '.exe')
    $p264Log = Join-Path $p264Out ($p264Arch + '-tests.log')
    $p264ErrorLog = Join-Path $p264Out ($p264Arch + '-tests.stderr.log')
    $p264Process = Start-Process -FilePath $p264TestExe -ArgumentList ('"{0}"' -f $p264ServiceExe) -WindowStyle Hidden -PassThru -ErrorAction Stop -RedirectStandardOutput $p264Log -RedirectStandardError $p264ErrorLog
    $null = $p264Process.Handle
    if (-not $p264Process.WaitForExit(30000)) {
        Stop-Process -Id $p264Process.Id -ErrorAction Stop
        throw 'P264 exact test process timed out; stop review'
    }
    $p264Exit = $p264Process.ExitCode
    Set-Content -LiteralPath (Join-Path $p264Out ($p264Arch + '-tests.exit')) -Value $p264Exit -Encoding Ascii
    Get-Content -LiteralPath $p264Log
    if ($null -eq $p264Exit -or $p264Exit -ne 0) { throw 'P264 native tests failed; stop review' }
}
```

Native tests cover immutable denial in every state, idempotent terminal events,
stale/duplicate start, fault retention, custom-command denial, explicit reentry,
and 24 forced terminal/admission winner orders (four terminals, three admissions,
both orders), plus contended stop/revoke/fault gate checks. Assembly checks require a real EXE entrypoint, default invocation
exit 64, one `ServiceBase.Run` call confined to Main, no declared P/Invoke/calli,
and a bounded dependency/call inventory. This proves none of SCM installation,
dispatcher execution, effective token/ACL, WinCred isolation or physical custody.

## Author evidence and limitations

Authoritative Python path probing returned Access denied. That validation route
was stopped; no interpreter workaround or native execution was attempted.
Compilation, Python test execution, native x64/x86 tests and actual SCM lifecycle
execution are **UNEXECUTED**. Author validation is limited to PowerShell source/
manifest/command parsing and Git checks; it cannot establish C# compilation or
runtime behavior. No expensive full-suite regression was launched.

Static author receipts: 47 selected historical raw Git blobs match the clean
P261 index; 16 SHA-256 witnesses match; all tracked/index diffs are empty.
Three documented PowerShell blocks parse successfully; additive whitespace and
C# delimiter checks pass. A PowerShell text-check mirror finds all 55 required
C# witnesses and rejects all 22 selected text mutations. An initial overbroad
`Cred*` source matcher incorrectly
rejected `CredentialAllowed`; the matcher was narrowed to native credential API
families. These are text checks, not executed Python/native tests or independent
review.

Future qualified work must decide principal/ACL/store, authenticated IPC and
human consent, protected durability/recovery, loaded-code isolation and exclusion
of every older effect route. None is implemented here. The executable candidate
is useful SCM lifecycle and denial infrastructure, not installed production
security, P96 repair, an operational credential service or permission to use keys.
