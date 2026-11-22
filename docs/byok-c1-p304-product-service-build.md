# P304 product service composition — BUILD FIRST, release HOLD

2026-11-22; OM v2.1; Codex sole source writer. Parent P303:
`f181a030c7a122bab8767203e7dccd78ca1d6e1c`; working branch
`byok-c1-p304-product-service-composition-20261122`. Six new files only.
Inherited tracked sources, P301/P282/P268/P269/P292, tests and context stay unchanged.
Git matches the requested checkpoint; `.codex/CURRENT_STATE.md` is stale and
describes a different historical checkpoint. No staging, commit or publication.

## Actual composition and limits

Conventional MSBuild executable project, .NET Framework 4.8, Debug/Release,
x64/x86. No NuGet or historical fixture dependencies. `CustodyService` derives
from `ServiceBase`; one `ServiceBase.Run` instance supplies own-process dispatch
shape. No installer or SCM configuration is supplied or inspected. The P99
product literal is `NayeonV1ByokCustody`; SEC03 principal remains proposed/unknown.

Main rejects arguments, non-Windows, interactive and nonzero-session contexts.
OnStart requires the dispatcher service handle, then independently opens the
actual process token twice before domain transitions. Each verification checks
Session 0, primary TokenType, TokenSessionId, translated
`NT SERVICE\NayeonV1ByokCustody` against TokenUser, exclusion of LocalSystem,
IsTokenRestricted and absence of thread impersonation before/after inspection.
Only ERROR_NO_TOKEN permits absence; identity lookup/native failures deny.
No supplied SID, flag, environment value or mutable grant is accepted.
No live validation of this startup path has occurred. Token sampling is not
continuous token custody, proof of installation, code integrity or store safety.
Restricted-token presence does not establish a reviewed restriction profile.

The internal coordinator is actual product domain source, separately owned by
the service. A private lock serializes lifecycle and all operation denials.
Created → Starting → ActiveDenied is lifecycle observation only; wrong order
faults active states. Stop/fault are terminal, disposal is idempotent and restart
is refused. The host lock serializes OnStart/OnStop/OnShutdown/Dispose; no workers
or asynchronous cleanup exist. AutoLog is off. Startup exit status is successful
only after the SCM callback and identity checks; it grants no credential readiness.
Main returning never signals release approval.

Every immutable readiness snapshot says **NOT AUTHORIZED**, **HOLD**, and why it
is not safe. Client admission and credential operations always deny. There are
no secret-bearing methods/data, injected effect ports, callbacks, credential
adapters, IPC, providers, protected store, journal, anchor or logger. The unsigned
friend test assembly permits direct tests of the actual built internal domain
types; internal visibility is not a security boundary or admission grant.

## Open Failures & Prior-Issues Review

Disposition: GO only for this user-authorized denial-only source build;
HOLD for release, deployment and credential integration. BUILD FIRST does not
waive any qualified SEC03/04 finding or seal gate.

| Issue / source | Root cause, scope and evidence | Containment / review |
| --- | --- | --- |
| Original P96 HIGH; P268/P269 reviews | Post-check revocation/effect race; historical fixture repair evidence does not qualify product custody. Not reproduced here: no effect path exists. | No dependency on P96 or synthetic adapters. HIGH remains open; independent approval pending. |
| Original P292 HIGH; inherited P301/P303 boundary | P303 records x86 teardown/deletion-absence evidence UNKNOWN. Dispatcher/token observations also do not establish approved principal, protected-store ownership or qualified SEC03/04. No new reproduction or closure claimed. | No SCM or native resource creation here; pinned OS-only identity prerequisites and unconditional operation denial. HIGH remains open. |
| P303 packaging failures and historical assumptions | Original first/second P303 RED runs 45043952896 and 45044567307 remain preserved: relative compiler paths, then a PowerShell extended-property assumption in checkout validation caused failures before runtime. P303 final hosted run 45045114008 PASSED x64/x86. | New standalone project uses explicit compile items and an explicit child working directory. No historical guard weakened. P304 hosted evidence is pending. |

Reviewed paths: P301 dispatcher → P269 transport/P268 synthetic transaction;
P282 process-token/impersonation observations; P303 nonSCM refusal/workflow and
latest review. P304 has no route to any of those runtime owners, alternate
credential entrypoints, stores, cross-process windows or restart recovery.
No material issue is marked repaired by this build. Full regression **0/3**;
independent approval **0/7**; original HIGH findings remain. No release acceptance.

## Commands and evidence

First hosted run `45060850055` reported **4/4 PASS**, 209 checks per job,
but checkout used synthetic merge HEAD
`7632522d93a2c21541ff80a3396bea309c5b87cf`, rather than P304 source HEAD
`83cee134ed2089f9dc4af3c8fdf46cf458c511d5`. This is **not final
head-authenticated evidence**. The narrow source-custody repair pins checkout
to `${{ github.event.pull_request.head.sha }}` and refuses non-PR, non-draft,
fork, wrong P303 base ref/SHA, wrong P304 branch or mismatched local HEAD
before source build. Four matrix jobs and denial tests are preserved;
no auth, privilege or network changes. A new run on the exact repaired PR
HEAD is **pending**; release remains HOLD.

With installed VS MSBuild and .NET Framework 4.8 targeting pack, compile only:

```powershell
MSBuild.exe src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj /t:Build /p:Configuration=Debug /p:Platform=x64
MSBuild.exe src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj /t:Build /p:Configuration=Release /p:Platform=x64
MSBuild.exe src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj /t:Build /p:Configuration=Debug /p:Platform=x86
MSBuild.exe src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj /t:Build /p:Configuration=Release /p:Platform=x86
git diff --check
```

No compiled binary was run on Kristian. The conventional local v4.8 reference
assembly directory is absent; local MSBuild/targeting-pack validation is not
claimed. Installed Framework64 `v4.0.30319/csc.exe` compiled product and separate
referencing test executable successfully with warnings as errors, for all four
x64/x86 Debug/Release combinations (eight successful compilations). Outputs are
outside the checkout in Windows Temp `nayeon-p304-compile-3d7ca42db75c42e2b85881194e2eb8f5`.
This is syntax/reference compile evidence against installed runtime assemblies,
not proof of the project build or runtime behavior. Initial CS1504 occurred
before source reading because legacy csc misinterpreted forward-slash relative
paths; resolved absolute Windows paths repaired the invocation. The hosted test
compile uses that same correction. No product-source defect was inferred.
XML parsing, workflow PowerShell AST parsing and new-file whitespace checks passed.
No package/tool installation or network workaround. Hosted workflow uses installed tools only,
read-only checkout with credential persistence disabled, logs checkout SHA and
SHA256 compiler inputs, and runs all four builds. Each test process has a
30-second deadline; entire job eight minutes. No service binary is launched.
The sole independent test source references the separately built product and
tests direct lifecycle/denial, wrong-order/replay, immutable reports and concurrent
denial/stop/fault/disposal. Negative Main reflection is permitted only after
actual OS interactive/nonzero-session observation, so no dispatcher is entered.
An unsuitable runner fails rather than weakening the guard. These tests neither
start a service nor mutate platform state. No secrets, even synthetic, are used.

Passing means **compile + isolated runtime denial only**. Hosted execution,
independent source/security review, affected/full regression and genuine service
dispatch are not proven locally. Next step: Nayeon reviews and publishes the
candidate for hosted evidence, then qualified audit/SEC03/04 design review before
any separately approved integration adapters or controlled service witness.
Real keys, provider/protected-store operations, privileged SCM and Code Integrity
changes remain disabled. No installation commands are supplied.
