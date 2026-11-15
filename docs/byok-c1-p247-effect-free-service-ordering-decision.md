# P247 effect-free service ordering decision

15 November 2026. Nayeon v1 / Mark-LII, BYOK C1.

**NONDEPLOYABLE MODEL ONLY. NO production-authority guarantee. Original P96
integrated check-to-effect race remains OPEN. REAL-KEY NO-GO / RELEASE HOLD.**
Qualified approvals **0/7**; unfiltered whole-product Windows regressions **0/3**.
The four historical P76 failures remain authentic, unresolved and unwaived.

## Intake and bounded failure review

Verified workspace `D:\Nayeon\CODEX_P247_EFFECT_FREE_ORDERING_20261115`, branch
`byok-c1-p247-effect-free-service-ordering-20261115`, clean initial HEAD
`e49810c0cc0982f73fb2d7f84ba516ab006f75a5` (P245). No tag points at this HEAD.
The existing `.codex/CURRENT_STATE.md` starts with older Phase 10.2 status;
it is not the Git-authoritative handoff for this branch and remains untouched.
This is the user's explicitly bounded model experiment, not forward product
integration or a security seal. Parent/protected checkouts were not accessed.

| Issue / source | Severity and root cause / impacted route | Evidence, containment, review, disposition |
|---|---|---|
| Original P96 race; P246 independent review reported by user; original P96 source and P221 review read here | High: `StillCurrent`, final `IsOwned`, and `SaveOrReplace`/`DeletePending` are separate calls; approval revoke can win between check and effect | Original deterministic negative harness retains separate-thread revoke injection. Not rerun here. No original source edited. P247 tests describe a different model; original finding HOLD. |
| P221/P230 synthetic owner examples | High integration gap: local monitor does not own alternate service/Python routes or establish durable custody | Both examples reviewed. P221 wraps original fake coordinator; P230 owns fixed integer transitions. P247 imports neither. No integrated remediation or independent P247 approval; HOLD. |
| Candidate `CustodyService` / `ServiceOwnedAdmissionBoundary` | High missing authority: candidate refuses production operations and startup; synthetic methods do not confer authority | Source reviewed, denial-only production behavior unchanged. No service composition, IPC, credential adapter or policy edit. HOLD. |
| Legacy user-scope Python WinCred, P246/user and P221/P222 source review | High alternate authority: interactive-user credential effects are outside native candidate ownership | No Python route modified or claimed repaired. Package exclusion and OS isolation required below. HOLD. |
| Four historical P76 failures, user intake | Material unresolved regression evidence; per-failure root causes/closure not established in this scope | Preserve assertions and failures; no full suite, workaround, waiver or claimed closure. HOLD. |
| SEC-03/SEC-04 and other qualified decisions, P222 response form | High missing independent principal/store/signing/loaded-code/consent evidence | Form reviewed; all approvals remain unissued. No privileged smoke authorised. HOLD. |
| Local validation barriers, this session | Environment: PowerShell scripts disabled; native generated executable refused by Application Control | Compile-only evidence below, no bypass and no test PASS inferred. Host runtime validation pending; HOLD. |

Disposition: bounded effect-free source work only within explicit user scope;
**HOLD** for integration, production phase progression, independent approval or seal.
No subagents or other engineering writers were started. Independent validation
belongs to Nayeon/qualified reviewers; author static inspection is not independence.

## Model and single lock order

`OrderingOwner` is sealed and owns exactly one private `gate`. Every mutation
(`Prepare`, `DispatchDecision`, `Publish`, recovery observation) enters that same
monitor. There are no nested owner locks, waits, I/O, user objects with virtual
behavior, callbacks or terminal-effect ports. Same-thread monitor reentry is
explicitly rejected before mutation. Read returns an immutable snapshot.
No independent approval check result can become a dispatch permit.

The conceptual linearisation point is the assignment of `MayHaveEffect`, one
dispatch-decision increment and sticky recovery under that monitor. This is
metadata only: it does not run an effect, represent completed custody, or return
an executable capability. A trusted lifecycle event is modeled by a closed enum;
calling it here proves no trusted caller identity. Trust is an assumption about
a future private service caller, never supplied by the enum or model output.

| Prior state | Input under gate | Result / next state |
|---|---|---|
| Fresh synthetic Unprepared | First valid operation | Prepared, reserve positive numeric ID and immutable category |
| Any | Repeated reserved ID, including another category | Replay; no new dispatch |
| Prepared | First dispatch with wrong category | Denied; attempt consumed, no retry |
| Prepared | Revoke / stop before dispatch | Cancelled; zero dispatch decisions; stop also revokes |
| Prepared or Unprepared | Fault, torn journal, in-flight, abandoned, crash, unknown | RecoveryRequired, no admission; no claim that historical effects are absent |
| Prepared, no lifecycle barrier | Matching one-use dispatch | MayHaveEffect + RecoveryRequired; one synthetic decision only |
| MayHaveEffect | Any lifecycle event | TooLateMayHaveEffect; preserve phase and sticky recovery |
| Cancelled by revoke/stop | First matching dispatch | ZeroEffectDecision, consumed; subsequent call Replay |
| Any recovery state | New operation or recovery inspection | Refusal / RecoveryRequired; never rearm |
| Restart, including claimed clean or invalid history | Any admission | RecoveryRequired; no initialisation from caller history |

One owner models one service lifetime with at most one dispatch decision. ID
reservations include refused well-formed attempts, are category-independent,
bounded to 128 and never evicted. IDs are neither random nonces nor durable replay
protection. `FreshSyntheticScenario` is only test construction, not enrollment or
a restart escape. Multiple test objects are separate hypothetical worlds; no
process singleton, cross-process exclusion or actual terminal ownership is proved.
There is no success completion, retry, reset, recovery-clear or recovery authority.
Recovery inspection deliberately stays held. Actual recovery is a future design.

## Future durable pre-effect custody and minimum integration boundary

Do not insert a real effect after returning `MayHaveEffect`: that recreates a
check-to-effect gap. A separately approved native service successor must privately
own actual consent consumption, revoke/stop/fault publication, one final pending
effect and physical verification across the same ordering mechanism and continuous
OS custody tenure. It must exclude every older/alternate effect entrypoint, not
wrap the old `StillCurrent` callbacks. There must be no generic injected effect.

Before any native effect, persist and verify source/session/operation/target/
candidate/version-bound one-use consumption and IN_FLIGHT intent in the protected
journal and physically distinct protected anchor, with independent historical
rollback/enrollment witness. Two writes are not atomic. Torn write/readback,
abandoned custody, crash, unknown effect or lost history require sticky recovery
across processes and restart; no replay, automatic retry or ordinary re-enrollment.
Terminal metadata alone proves neither storage durability nor the credential result.
This prototype has no storage interface and fakes none of those guarantees.

Minimum next boundary: independent source-bound review of this model plus explicit
SEC-03/SEC-04 decisions defining the real private owner, durable custody protocol,
all ingress/alternate-route exclusions and recovery authority. Only a separately
approved successor scope may compose anything into the native service, followed by
approved disposable-VM synthetic experiments. No production integration authorised
by P247; no real-key, service, store, principal or signing experiment here.

## Exact unresolved SEC-03 and SEC-04 decisions

SEC-03 must name the SCM logon account, restricted service SID type and literal
installed identity; least privileges, impersonation policy, logon/profile/reboot
behavior; exact service-only store/target (actual service-principal WinCred versus
DPAPI CurrentUser protected file or approved alternative); exact ACL/SDDL for
secret, journal, independent anchor, history witness and installation. None is
selected or proved by this model. LocalSystem is not the default. Machine-scope
DPAPI is rejected as cross-user confidentiality. Prove CurrentUser DPAPI/profile
availability under the actual principal, and OS denial of ordinary interactive-user
legacy read/write/delete attempts against the new store. Decide backup, profile
loss, uninstall, restart, rollback and controlled recovery/re-enrollment. No silent
read, migration or deletion of existing user vault targets.

SEC-04 must name the signed native broker/service/installer, publisher chain and
complete dependency manifests; actual enforced loaded-image Code Integrity/UMCI
policy and EXE/DLL/.NET/script scope, loaded identity and file-ID/rename-race
resistance. A source hash, successful build or compile guard is not loaded CI.
Define authenticated IPC server/client OS tokens, session/integrity level, signed
UI broker and genuine user presence. Define durable one-use human consent bound to
operation, exact target, candidate, session, expiry/version and replay identity;
no caller boolean, model text or digest alone authorises effects. Define the one
actual owner, OS custody lock order, stop/watchdog/crash semantics and uncertain
outcome handling. The signed package must exclude legacy Python P132/P133 direct
WinCred effects, with separate OS store isolation evidence. This model changes
none of these routes and proves no principal, ACL, DPAPI, IPC or signing property.

## Focused verification and host handoff

54 cases authored: 18 forced winner-order cases (3 categories x 3 lifecycle
signals x 2 orders), 15 before/after uncertainty cases, 9 category/replay cases,
7 restart cases, concurrent duplicate preparation/dispatch, reentrancy across all
mutations, invalid/bounded ID retention, invalid signals/startup, and structural
no-effect-port inspection. Winner orders use completed native threads, not sleep
inference. The concurrent duplicate test has a start barrier. Thread waits are
bounded to 2/2.5 seconds; runner bounds each executable to 30 seconds. Test-driver
delegates/reflection are not accepted by or called from the model. These are not
original-source P96 race tests or genuine crash/storage/Windows custody tests.

Actual sandbox results:

- `dotnet --info`: host 10.0.11, no SDK installed. No installation attempted.
- `& ./tests/p247_effect_free_service_ordering/Run-Isolated.ps1`: blocked,
  `PSSecurityException`, running scripts disabled. Policy left unchanged.
- First direct x64 compiler command with relative slash-separated source paths:
  CS1504, sources resolved at checkout root by compiler. Corrected to absolute
  `Resolve-Path` source arguments; no source repair or test weakening.
- Direct .NET Framework x64 and x86 compilation with both defines: exit 0 each.
- Direct x64 compile without defines: exit 1, CS1029 for both explicit `#error`
  guards. x86 no-flags guard remains host-run pending.
- `& ./tests/p247_effect_free_service_ordering/P247-check.exe`: blocked by
  Application Control, `ApplicationFailedException`. **0 runtime cases executed;
  no runtime PASS claimed.** No alternative loading/execution route attempted.
- Generated check binaries removed. No full product regressions or host Python run.
- PowerShell AST parse of runner: no errors. `git diff --check` and per-added-file
  `git diff --no-index --check -- NUL <path>`: no whitespace errors. Final status
  contains exactly these four untracked additions, no tracked/index changes;
  branch and HEAD remain the verified intake identity.

Exact successful direct compilation shape (substitute x86 Framework/compiler and
platform for the second architecture):

```powershell
$p247Model = (Resolve-Path -LiteralPath tests/p247_effect_free_service_ordering/EffectFreeServiceOrdering.cs).Path
$p247Tests = (Resolve-Path -LiteralPath tests/p247_effect_free_service_ordering/OrderingTests.cs).Path
$p247Exe = Join-Path (Get-Location) 'tests\p247_effect_free_service_ordering\P247-check.exe'
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:exe /platform:x64 /define:C1_REVIEW_ISOLATED_ASSEMBLY,C1_SYNTHETIC_TEST "/out:$p247Exe" $p247Model $p247Tests
```

Nayeon should run, in a normally authorised host environment, from this checkout:

```powershell
& ./tests/p247_effect_free_service_ordering/Run-Isolated.ps1
```

Runner uses installed .NET Framework compilers, isolated sources only, x64/x86
explicit no-flags rejection, temporary artifacts/logs and bounded executable runs.
It changes no policy and downloads nothing. Preserve raw logs/exits as genuine
host evidence. Do not relax Application Control to make this sandbox pass.

No preexisting files changed, frozen P76 assertions changed, product Git writes,
staging, commit, tag, push, workflow, workbook or dashboard operations authorised.
Author static scope/diff checks do not substitute for independent review.
