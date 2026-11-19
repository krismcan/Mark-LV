# BYOK C1 P282 narrow repair — 19 November 2026

**NO-GO / HOLD. Independent approval OPEN.** Pre-commit candidate only.
Branch: `byok-c1-p282-service-identity-custody-20261119`.
HEAD remains `248ec4d4243aae795387959dcfd9d03a007a3341`; index unchanged.
The November 3 Phase 10.2 handoff in `.codex/CURRENT_STATE.md` describes
another candidate and does not establish this P282 candidate's status.

P282 retains genuine current-process-token read-only observation, isolated
review compile guards, and unconditional protected-store denial. Observation
does not establish profile ownership, DPAPI/store custody, qualified SEC03/04
approval, or production eligibility. Every evidence status denies these grants.
P271's `RequireHosted` route remains a disposable synthetic-only fixture;
environment claims and its additive token binding grant no protected production
authority. `OpenProtectedService` always denies before witness construction.

The invalid `DirectWitnessNegative` depended on a rejected P270 modification.
Its replacement, `SyntheticBridgeBindingNegatives`, rejects missing or false
`RUNNER_OS` claims at the P282 binding and P271 constructor seam, with the older
P271 hosted prerequisites present. Both fresh modes use a null root and require
an unchanged P270 diagnostic stage: reaching P270 path processing would fail
the test. Environment changes are restored in `finally`. This test is compiled,
**not executed**; it supplies no runtime negative evidence yet.

P270 was never edited in this repair. Its raw Git blob equals HEAD:
`dcb5c79a9b47b601463e73fbe77de11297637ed2`.
SHA256: `088104A5F0A073885C4488C2B6C6A8F5CF23A4BE3C7C7DB8C670E6E79B224A45`.
The only tracked source diff is additive P271; original P268/P269/P261/P279/P281
and frozen tests were not modified. No other worktree or Git history was altered.

## Actual validation

Direct PowerShell commands invoked the resolved absolute Framework64 and
Framework `v4.0.30319/csc.exe` paths with resolved absolute C# inputs,
`/warn:4 /warnaserror+ /target:exe /debug+ /optimize- /platform:x64|x86`,
the nine review/development defines and framework references enumerated in
`tests/p282_service_identity/CompileReview.ps1`. That script was not executed,
dot-sourced or evaluated. Host ExecutionPolicy was respected without changes
or bypass. Its PowerShell syntax parser returned **0 errors**.

These are fresh results after P270 restoration, captured immediately from
`$LASTEXITCODE`; the earlier compile claim is not used.

| Test entrypoint (compilation only) | x64 raw exit | x86 raw exit |
| --- | --- | --- |
| ExecutingServiceCustodyTests | 0 | 0 |
| P268RemediationTests | 0 | 0 |
| P270DurableWitnessTests | 0 | 0 |
| P271DurableBridgeTests | 0 | 0 |
| RuntimeServiceTokenTests | 0 | 0 |

| Missing compiler defines (negative compilation) | x64 raw exit | x86 raw exit |
| --- | --- | --- |
| All | 1 | 1 |
| DEBUG | 1 | 1 |
| C1_REVIEW_ISOLATED_ASSEMBLY | 1 | 1 |
| C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY | 1 | 1 |

All ten positive builds emitted assemblies. All eight negative builds emitted
no executable and contained `error CS1029` with
`P282_IDENTITY_CUSTODY_REVIEW_ONLY_NONDEPLOYABLE`.
`git diff --check` raw exit: **0**. Compiler orchestration raw exit: **0**.
No generated executable ran on Kristian. Native token/SCM observation and all
runtime assertions remain unrun. No Python source/mutation test was added or
run: actual C# compilation covered the narrow compile repair; a source-only
Python check would not prove runtime denial. No WindowsApps shim was invoked.

Local evidence directory (compiler logs, per-build raw exits, input hashes):
`C:\Users\krist\AppData\Local\Temp\nayeon-p282-narrow-repair-c425b9a7ec984bc38e1de2b472c2d01d`.
SHA256 `raw-exits.txt`:
`2FBBBB99BBEB151651906EEE1ACFE418D98BE9D8000495FCAA768F8FA75502E6`.
SHA256 `source-sha256.txt`:
`F6F007DAD52DD5D544BB29866A647525F43EA865CF10497195A830C436E55FF7`.

## Bounded open failures and prior issues

| Issue | Evidence / repair / remaining gate | Disposition |
| --- | --- | --- |
| Material frozen P270 mutation | Reviewer restored parent before this run; raw identity checked. Invalid dependent test replaced and compiled. Independent closure OPEN. | HOLD |
| Invalid P282 negative | Root cause was expecting a constructor stage absent from frozen P270. Replacement targets the P282-bound P271 seam; hosted runtime/adversarial evidence OPEN. | HOLD |
| P216: 2 failures | User-reported prior failures; not reproduced, diagnosed, repaired or waived in this bounded run. | OPEN / HOLD |
| P76/P96 and other prior issues | Inherited OPEN; detailed severity/root-cause/affected-route review and independent closure not established by this repair. | OPEN / HOLD |
| Protected-store/service isolation evidence | Current-process identity observation cannot prove store custody. No approved production path. | NO-GO |

Independent approval **OPEN**; hosted evidence **not yet obtained**;
full regressions **0/3**. No full regression, release permission, seal,
credentials, WinCred, privileged operation or service mutation was performed.
No staging, commit, tag, push, workflow, PR or workbook update occurred.
Nayeon must independently review the exact bytes and arrange hosted evidence.

## Exact candidate changed-path set and SHA256

Exactly five paths relative to HEAD (including untracked additions):

| Path | SHA256 (raw bytes) |
| --- | --- |
| `native_c1_successor/P271DurableDevelopmentBridge.cs` (modified) | `D22A93B71435BA364A549518D748A84DD604D70885E695EDF6D3015362E7DE6B` |
| `native_c1_successor/P282ExecutingServiceCustody.cs` (new, preserved by repair) | `C42D2A2F30114B423745808845ED68770FDB018AB78863C7003E09D5089C0AE9` |
| `tests/p282_service_identity/ExecutingServiceCustodyTests.cs` (new) | `6405D7DCD5800F11F38926EA03E9002D0AF09F28BA9DD7AD3801F6B89CB2CF86` |
| `tests/p282_service_identity/CompileReview.ps1` (new) | `8CE4A7F3951387EF023CDD0967E4F0EA817C2FBFD1751691C29FEC437A168187` |
| `docs/byok-c1-p282-narrow-repair-20261119.md` (new) | This report; no self-hash |
