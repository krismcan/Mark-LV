# P265 isolated development Windows named-pipe adapter

17 November 2026. **DEVELOPMENT SOURCE CANDIDATE. NATIVE ACCEPTANCE PENDING;
P96, REAL KEYS AND PRODUCTION RELEASE HOLD.** Single source writer; no subagents.

Intake matched the requested clean branch
`byok-c1-p265-authenticated-windows-ipc-20261117` and exact P264 parent
`3a566c544384bc0b961fbf65fa2e987be47b343c`. No tag points at HEAD. The current
state file describes older Phase 10.2 work; Git governs this intake. That file,
all P264 files, historical implementation/tests and milestone tags are unchanged.
Read dependencies were AGENTS.md, the failure gate, P264 source/driver/source
checks/review, and bounded P250 trust/owner/IPC/impersonation/failure sections.
There was no pre-existing P265 architecture file in this checkout; this bounded
implementation follows the user's explicit P265 development authorization.

## Material implementation and authority boundary

Exactly five additive paths:

* `native_c1_successor/P265DevelopmentPipeAdapter.cs`: a standalone library using
  actual Windows `System.IO.Pipes` server handles, security descriptors and
  `RunAsClient` OS-token observation. It is not a synthetic identity comparator.
* `tests/p265_successor/P265DevelopmentPipeTests.cs`: separate native test EXE.
* `tests/test_byok_c1_p265_development_pipe.py`: five independent source test
  methods, including frozen-byte witnesses and negative mutations.
* `.github/workflows/p265-windows-development-pipe.yml`: hosted x64/x86 PR review.
* This boundary/evidence/command record.

Both C# files require `C1_P265_DEVELOPMENT_ONLY` AND `DEBUG`; missing either is a
compiler error. There is no production listener, service entrypoint or default
runtime command. The adapter has no dependency on P264, the candidate/historical
service, Python/backend, WinCred, credential bytes, store, SCM or provider code.
No effect delegate, extensible dispatch interface or transferable permit exists.
The native driver's IL audit examines all candidate methods before construction,
forbids declared native/internal calls and `calli`, and restricts external call
types and assembly references. A narrowly permitted compiler array initializer
does not widen the effect graph. The Python checks independently reject selected
credential, storage, process, reflection and service-forwarding mutations.

Trusted test code supplies a `WindowsIdentity.GetCurrent()` object. The adapter
copies its SID after verifying it equals the current process SID on a thread
without impersonation. Client data never selects this expected SID. Each adapter
creates a random `Nayeon-P265-dev-<32 hex>` endpoint and one native pipe instance;
the handle is not inheritable. Its DACL is protected against inheritance, owned by
that current developer SID, grants that SID only ReadWrite (.NET implicitly
adds Synchronize), and explicitly denies Network SID FullControl. No Everyone,
Authenticated Users, Administrators, LocalSystem or assumed service virtual SID
is granted. The native test reads the actual kernel pipe descriptor, not merely
the pre-creation `PipeSecurity` object. No network test is authorized or performed.

After a complete typed frame has been read, `RunAsClient` captures the actual
thread `WindowsIdentity`, requiring a non-anonymous impersonation token and
comparing its `SecurityIdentifier` with the trusted expected SID. A finally block
requires that no thread impersonation identity remains after `RunAsClient`.
Pre-existing impersonation, capture/revert failure, exceptions and deadlines fail
closed. No protected operation occurs inside or after impersonation.

**Even a matching SID remains UNTRUSTED for privileged requests.** It proves
neither application/image identity nor human consent. Same-SID hostile processes
can connect and interfere with this developer endpoint. This does not implement
server authentication, endpoint-squatting defense, signer/session/integrity
qualification, handle-transfer exclusion or service-to-UI production IPC.
The DACL is developer containment, not an approved service-principal design.

## Fixed wire protocol and bounded lifetime

Windows message-mode pipe, one request and one denial per connection. No client
identity string, PID, secret, candidate, target, approval or extensible payload.

| Offset | Width | Required value |
| --- | --- | --- |
| 0 | 4 | Little-endian body length exactly 24; every other length rejected before payload allocation |
| 4 | 4 | ASCII `C1P5` |
| 8 | 1 | Version 1 |
| 9 | 1 | 1 ObserveDenial, 2 RejectCredential, 3 RejectStore, 4 RejectPrivileged |
| 10 | 2 | Zero reserved flags |
| 12 | 16 | Nonzero request ID; opaque .NET Guid byte layout, not an authority token |

Exactly 28 request bytes must exhaust the current pipe message. Framing, unknown
opcodes/versions/flags, all-zero IDs and attached text/extra bytes close without
a payload. Validly framed denials use only the same eight bytes:
`43 31 44 4E 01 01 00 00` (`C1DN`, v1, denied, zero reserved bytes).
No request ID, observed token, cause detail or data is reflected on the wire.
After reading the reply, the client sends a separate one-byte message `A5` as a
delivery marker. This prevents immediate Disconnect discarding a buffered reply;
the marker conveys no consent. Missing, malformed or second-request markers
fail closed. There is no unbounded `WaitForPipeDrain`.

`ServeOnce` accepts a total 50..2000ms monotonic deadline covering connect, partial
reads, token observation, reply and delivery marker. Every pending I/O wait uses
remaining time. A timeout closes the handle and cancels outstanding native I/O;
disconnect/fault closes the lifetime. Concurrent ingress returns Busy immediately.
Disposal is sticky/idempotent and interrupts pending connection/read work. The
adapter cannot guarantee an OS impersonation/revert call itself returns on time;
the permitted runner must also enforce the process watchdog below. Closing a
handle is not proof that Windows has already completed kernel cancellation.

Valid IDs are reserved once per adapter, including peer refusals, with capacity
128, no eviction and no capacity reset. Reconnect, changed-opcode duplicate and
saturation attempts remain denied. This is bounded in-memory replay detection;
there is no durable replay/consent guarantee across adapter/process restart.
Every operation and every evidence property is denial-only even after restart.
Local evidence reports reason/OS-observed/SID-match/revert/reply booleans, never
a grant. A new connection cannot gain privilege by presenting another ID.

Future integration seam: a separately approved composition phase could own this
adapter's lifetime. There is deliberately no callback or call to P264 rejection
or effect methods today. Such a phase must decide real principals, server/client
authentication, consent, lifecycle ordering, loaded-code exclusion and durable
recovery before adding authority. This development adapter cannot clear P96.

## Open Failures & Prior-Issues Review

The explicit user authorization permits this isolated denial-only development
step. It does not waive the following findings or constitute independent review.

| Issue / severity / source | Root cause, impacted routes and evidence | Containment, regression and disposition |
| --- | --- | --- |
| Original P96 / HIGH; P250/P264 | Approval/lease checks separated from external effect dispatch; retained original negative harness reproduces the interface race historically. Not rerun here. | No effect call graph; original source pinned unchanged. Original and alternate-route repair NOT attempted. HOLD. |
| Principal/IPC confusion / HIGH; P250 SEC-03/04, P261/P264 | Same-user identity is not trusted app/consent; proposed virtual service name conflicts with historical assumptions. | Only actual current developer SID provisioned; actual OS capture and same-SID denial tests supplied. Real service identity/store/consent/CI remains HOLD. |
| Alternate old effects / HIGH; P251/P258/P264 | Python, raw native and stale-process routes bypass a cooperative service monitor. | No dependency/forwarding; frozen P264/P96/WinCred witnesses plus compiled call audit. No OS credential/store exclusion claimed. HOLD. |
| Historical failures / material; P76/P264 | Four original failing methods remain unwaived; broad regressions are not current acceptance evidence. | Tests untouched; no full-suite PASS claimed. HOLD. |
| Host execution / material missing evidence; P261/P264 and current intake | Application Control previously blocked native execution; authoritative Python path probe currently returns Access denied. Current candidate metadata-only ReflectionOnlyLoadFrom was also blocked, HRESULT 0x800711C7. | Stopped at refusal. No alternate loader/interpreter, download, policy change or target execution. Native execution and Python test execution pending. HOLD. |
| Buffered reply delivery / implementation review | Immediate disconnect after buffered write may discard unread denial bytes. | Bounded delivery marker added before disconnect; malformed frames close without reply. Native marker-timeout/invalid/duplicate cases supplied; runtime proof pending. HOLD for native acceptance. |
| Additional access-right mask / implementation review | .NET Framework rejects ReadPermissions in the constructor's additionalAccessRights argument, although it is already included in the ordinary duplex rights. Confirmed by metadata/IL inspection of the installed framework constructor, not pipe execution. | Additional rights set to zero; a static negative mutation prevents recurrence. The native kernel-ACL test still must prove effective ReadPermissions behavior. HOLD for native acceptance. |
| Excess client ACL right / HIGH; independent review | CreateNewInstance granted same-SID callers server-instance authority. | Removed; exact kernel allow mask must be ReadWrite plus implicit Synchronize. Static mutations reject regrant/broader masks and removal of ACL checks. If .NET requires server-instance rights, construction fails closed with no retry/regrant; hosted runtime proof pending. HOLD. |

Independent source/security review and permitted-runner receipts remain pending.
No new qualification or release seal is claimed. Current runtime acceptance is
HOLD; only authorized source implementation/static checking has progressed.

## Compile and static-check commands

Run from the reviewed worktree root. Use the existing .NET Framework C# compiler;
no restore, download, installation, signing or policy modification. These commands
only compile. Never execute generated artifacts inside the Codex sandbox or on
Kristian. Preserve source/artifact hashes, logs and actual compiler exits.

```powershell
$p265Source = (Resolve-Path -LiteralPath 'native_c1_successor/P265DevelopmentPipeAdapter.cs').Path
$p265Driver = (Resolve-Path -LiteralPath 'tests/p265_successor/P265DevelopmentPipeTests.cs').Path
$p265Out = Join-Path $env:TEMP ('nayeon-p265-review-' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $p265Out
foreach ($p265Target in @(@{Arch='x64'; Framework='Framework64'}, @{Arch='x86'; Framework='Framework'})) {
    $p265Arch = $p265Target.Arch
    $p265Framework = Join-Path $env:WINDIR ('Microsoft.NET\' + $p265Target.Framework + '\v4.0.30319')
    $p265Compiler = Join-Path $p265Framework 'csc.exe'
    $p265Common = @('/noconfig', '/debug+', '/optimize-', '/warn:4', '/warnaserror+',
        ('/platform:' + $p265Arch), ('/reference:' + (Join-Path $p265Framework 'System.dll')),
        ('/reference:' + (Join-Path $p265Framework 'System.Core.dll')))
    foreach ($p265Item in @(@{Name='Adapter'; Source=$p265Source; Target='library'; Ext='.dll'; Required='P265_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED'; Release='P265_NO_RELEASE_BUILD'},
                            @{Name='Tests'; Source=$p265Driver; Target='exe'; Ext='.exe'; Required='P265_TESTS_REQUIRE_DEVELOPMENT_BUILD'; Release='P265_TESTS_NO_RELEASE_BUILD'})) {
        foreach ($p265Guard in @('NONE', 'DEBUG', 'C1_P265_DEVELOPMENT_ONLY')) {
            $p265Stem = $p265Arch + '-' + $p265Item.Name + '-' + $p265Guard
            $p265GuardOutput = Join-Path $p265Out ($p265Stem + $p265Item.Ext)
            $p265GuardLog = Join-Path $p265Out ($p265Stem + '.log')
            $p265Define = @()
            if ($p265Guard -ne 'NONE') { $p265Define = @(('/define:' + $p265Guard)) }
            & $p265Compiler @p265Common @p265Define ('/target:' + $p265Item.Target) ('/out:' + $p265GuardOutput) $p265Item.Source *> $p265GuardLog
            $p265Exit = $LASTEXITCODE
            if ($p265Exit -eq 0 -or (Test-Path -LiteralPath $p265GuardOutput)) { throw 'P265 build guard failed' }
            $p265GuardText = Get-Content -LiteralPath $p265GuardLog -Raw
            if ($p265Guard -ne 'C1_P265_DEVELOPMENT_ONLY' -and $p265GuardText -notmatch ('error CS1029:.*' + $p265Item.Required)) { throw 'Unexpected opt-in failure' }
            if ($p265Guard -ne 'DEBUG' -and $p265GuardText -notmatch ('error CS1029:.*' + $p265Item.Release)) { throw 'Unexpected release failure' }
        }
        $p265Artifact = Join-Path $p265Out ('P265.' + $p265Item.Name + '.' + $p265Arch + $p265Item.Ext)
        $p265Log = Join-Path $p265Out ($p265Arch + '-' + $p265Item.Name + '-compile.log')
        & $p265Compiler @p265Common '/define:DEBUG;C1_P265_DEVELOPMENT_ONLY' ('/target:' + $p265Item.Target) ('/out:' + $p265Artifact) $p265Item.Source *> $p265Log
        if ($LASTEXITCODE -ne 0) { Get-Content -LiteralPath $p265Log; throw 'P265 compile failed' }
        Get-FileHash -LiteralPath $p265Artifact -Algorithm SHA256
    }
}
$p265Out
```

Authoritative Python source tests on the authorized host (not attempted again
after the sandbox path denial):

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B -m unittest discover -s tests -p test_byok_c1_p265_development_pipe.py -v
if ($LASTEXITCODE -ne 0) { throw 'P265 source tests failed' }
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B -m unittest discover -s tests -p test_byok_c1_p264_development_service.py -v
if ($LASTEXITCODE -ne 0) { throw 'P264 affected source tests failed' }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Whitespace check failed' }
```

## Native execution: permitted disposable Windows runner ONLY

The user permits GitHub-hosted `windows-latest` x64/x86 for this step through
the P265 PR workflow; Kristian remains excluded. The command-line flag records
scope and cannot bypass policy. Rebuild the exact reviewed source on that runner
and retain `$p265Out` from compilation. Both test EXE and
adapter DLL must be admitted normally. On any policy/loader refusal, STOP; do
not retry through reflection, another interpreter, loader or changed policy.
The driver's ordinary managed assembly loading is not a bypass permission.

```powershell
foreach ($p265Arch in @('x64', 'x86')) {
    $p265Exe = Join-Path $p265Out ('P265.Tests.' + $p265Arch + '.exe')
    $p265Dll = Join-Path $p265Out ('P265.Adapter.' + $p265Arch + '.dll')
    $p265Log = Join-Path $p265Out ($p265Arch + '-native.log')
    $p265ErrorLog = Join-Path $p265Out ($p265Arch + '-native.stderr.log')
    $p265Process = Start-Process -FilePath $p265Exe -ArgumentList ('--permitted-disposable-runner "{0}"' -f $p265Dll) -WindowStyle Hidden -PassThru -ErrorAction Stop -RedirectStandardOutput $p265Log -RedirectStandardError $p265ErrorLog
    $null = $p265Process.Handle
    if (-not $p265Process.WaitForExit(35000)) {
        Stop-Process -Id $p265Process.Id -ErrorAction Stop
        throw 'P265 exact test process timed out; stop review'
    }
    $p265Exit = $p265Process.ExitCode
    Set-Content -LiteralPath (Join-Path $p265Out ($p265Arch + '-native.exit')) -Value $p265Exit -Encoding Ascii
    Get-Content -LiteralPath $p265Log
    if ($null -eq $p265Exit -or $p265Exit -ne 0) { throw 'P265 native tests failed; stop review' }
}
```

The native driver checks real OS peer capture/SID match/restoration, current-SID
kernel ACL/owner, all four denial operations, reconnect replay/altered operation,
capacity without eviction, malformed fields/oversize/spoofed text/extra frames,
idle/partial-header/partial-body timeouts, disconnect, insufficient impersonation
level, pre-existing thread impersonation, concurrent ingress, disposal during
connect, unique endpoints and malformed/missing/second-request delivery markers.
No cross-user account/token is provisioned. Mismatched/null SID comparison is an
additional unit negative, not evidence of actual cross-user execution or OS
store isolation. Every receipt has all authority properties false.

## Author evidence and remaining work

Bounded sandbox builds produced x64/x86 adapter DLLs and test EXEs, all four
positive compiler exits 0 with warnings as errors. All twelve incomplete-flag
builds failed with P265 guard errors. No generated candidate DLL method or EXE
was executed. An initial relative-path compiler invocation failed CS1504 because
the legacy compiler did not resolve forward-slash source paths; commands were
corrected to absolute `Resolve-Path` results, with no compiler/policy workaround.

Authoritative Python path probing returned Access denied; no interpreter fallback
was used. After final successful x64/x86 builds and guard checks, a metadata-only
`Assembly.ReflectionOnlyLoadFrom` inspection of the compiled x64 DLL was refused
by Application Control, HRESULT `0x800711C7`. No candidate method was invoked.
STOP: no retry or alternative inspection/loading route was attempted. PowerShell
continued after that load error, emitted null-value errors and a zero-call
`ALLOWLIST=PASS` line; that line is INVALID and is explicitly excluded as evidence.
The compiled call audit is NOT verified. The refusal is an environment blocker,
not evidence that the adapter passed or failed native behavior.

Python tests, native cases, affected/full regressions and independent review
are **UNEXECUTED/PENDING**. Earlier PowerShell checks matched 51 adapter and 44
driver witnesses, eight frozen pins and twenty adapter mutations; later source
repairs were compiled but those text-check counts are not final-source runtime
or independent acceptance evidence. Three documented PowerShell blocks parsed;
tracked/index diffs and whitespace checks were clean before the final blocker
record. No deployment, service installation,
SCM start, credentials, keys, network, policy change, commit, push, current-state
edit or Drive/dashboard update occurred. Runtime and security claims require
fresh receipts on the permitted disposable runner plus independent review.

## Focused correction and hosted CI

The ACL correction preserves NetworkSid denial, protected DACL, total adapter
deadline, denial-only protocol and isolated effect graph. The new PR workflow
targets base `byok-c1-p264-service-runtime-development-20261117`, checks out exact
PR HEAD against the fixed P264 parent and admits only these five additive paths.
It uses P261's pinned actions, read-only contents permission and disabled checkout
credentials; no secrets, WinCred, service installation or policy changes.
It runs five Python source tests, all twelve incomplete-flag compiler negatives,
four positive x64/x86 builds, then actual native drivers with a hard 35-second
process deadline and raw exit capture. AppControl refusal stops execution without
an alternate loader. Only nonsecret text logs, exits and computed source hashes
are retained; binaries are excluded. GitHub may skip newly introduced workflows;
CI/native acceptance cannot be claimed until actual x64/x86 runs provide evidence.
Correction-session sandbox checks: four warning-as-error builds passed; twelve
incomplete-flag builds rejected with exact guard diagnostics. Five workflow
PowerShell blocks parsed; bounded ACL/workflow text checks and additive whitespace
checks passed. `git diff --name-only` and its staged equivalent were empty;
exactly these five paths remain untracked. Historical P264 files are preserved.
Python execution remains pending under the recorded host-path denial; no retry,
candidate loading or native execution occurred in this correction session.
P96, real keys and production remain HOLD. No commit, tag, push or release.
