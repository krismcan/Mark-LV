# P298 current-effect retirement: source-bound decision log

22 November 2026; OM v2.1; Codex is the sole implementation writer.
Bounded implementation 4/4 is documentation only, not a product seal.
**REAL KEY NO-GO. PRODUCTION HOLD. Hosted results PENDING.**
Qualified approvals remain **0/7**; accepted full Windows regressions **0/3**.

## Custody and exact additive scope

The supplied exact clean inherited HEAD is
`d30665e457e3c8b24cb69949caf4d99a2b01304b` (P297).
This turn accepts that supplied custody statement; it does not run Git to verify it.
Three untracked P298 files were already authored and independently inspected,
as supplied by the user; this turn reads them and creates only this fourth file.
No inherited file, consumer source, historical test or historical report is edited.
The exact four additive paths are:

1. `docs/byok-c1-p298-current-effect-retirement.md`
2. `scripts/p298_current_effect_boundary_audit.py`
3. `tests/test_byok_c1_p298_effect_boundary.py`
4. `.github/workflows/p298-windows-current-effect-retirement.yml`

Read scope is the first 100 lines of [P296](byok-c1-p296-launch-custody-diagnostic.md)
and the three current P298 additions above; inherited implementation is not reread.
Current-source statements below describe the contracts encoded by those additions.
Historical results below are supplied evidence, not newly retrieved artifacts.
No local tests/Python execution, SCM, WinCred, keys or network are invoked.
No Git staging, commit, tag or push occurs; no workbook/dashboard update occurs.

## Current retirement decision and limits

`nayeon/secrets/windows_credential.py` has its native mutation route retired.
The real `_Advapi32Adapter` native surface is only `CredReadW`/`CredFree`;
it does not supply native credential write/delete authority.
Default `WindowsCredentialBackend()` get/put/delete operations are denied.
The audit encodes absent injected adapters and fixed `SecretStorageError` denial.
An explicitly supplied fake `_native` object remains a deterministic test seam.
The mutation accessor rejects absent adapters and real `_Advapi32Adapter` objects.
Explicit injection is not a production backend mode or an OS trust boundary.

`nayeon/brain/local_byok_user_scope.py` default composition constructs
`LocalByokController(WindowsCredentialBackend())` with no injected mutation.
Default begin is denied; approval refuses and clears pending review state.
This retires current default effects; it does not repair the original P96 race.
Python provides no OS security against malicious same-SID users able to alter
objects, imports, code or process state. Fake-only checks cannot establish that.
No effect capability is added, no real keys are used, and no consumer source changes.

Current `native_c1_successor/P274EphemeralWinCredEffect.cs` is a guarded,
development-only ephemeral WinCred test, not a production protected store.
The audit requires DEBUG, `C1_P268_DEVELOPMENT_ONLY` and
`C1_P274_EPHEMERAL_WINCRED_ONLY` guards plus an exact decoded-source hash.
**The P274 ephemeral WinCred test is NEVER invoked in this work.**

## Authored evidence, not executed results

The [P298 tests](../tests/test_byok_c1_p298_effect_boundary.py) author 15
fake-only cases with native-loader tripwires during import and test execution.
They target default denial, forged/pending reviews, invalid operations, default
composition and explicit in-memory fake workflow behavior. They have not run here.
Authorship and independent inspection do not establish test passes.

The [P298 audit](../scripts/p298_current_effect_boundary_audit.py) reuses the
P275 product-wide AST inventory, pins decoded source, and checks exact AST
contracts for adapter denial, controller guards and default composition.
It authors three string-only negative mutations: native read-to-write substitution,
adapter-guard removal and controller-guard removal; rejection remains unexecuted.
It checks P274 source guards without importing or executing the native effect.
Source pins bind reviewed text, not deployed binaries or OS custody.

The [authored workflow](../.github/workflows/p298-windows-current-effect-retirement.yml)
targets GitHub-hosted `windows-2022`, two trials, and an admitted draft PR only.
It requires the exact inherited base and one-parent lineage with four additions,
1,208 inherited blobs and 1,212 regular current files; these are planned checks.
It plans only the audit and focused test entries, with raw exits and bounded waits.
Before/after SHA256 manifests and clean-source checks cover source custody.
Receipt initialization retains unavailable/not-run states; artifacts retain HOLD.
Workflow PASS strings are conditional authored output, not actual hosted results.
**Actual P298 hosted results: PENDING; no PASS or regression acceptance claimed.**
Even successful focused receipts would not prove whole-system isolation or release.

## Open Failures & Prior-Issues Review

No issue below is waived, downgraded, repaired or closed by this document.
Independent closure evidence and cross-phase reconciliation remain required.

| Open issue / severity | Evidence, cause and impacted boundary | Repair, tests, independent review / disposition |
| --- | --- | --- |
| Frozen original P96 / HIGH | Approval `StillCurrent` and final `IsOwned` are not atomic with SAVE/REPLACE/DELETE effect; older callers, shared state and restart remain relevant. | Default retirement contains a route, not the race. Atomic effect-boundary repair and adversarial cross-route proof remain open; HOLD. |
| P268 successor / qualification gap | Isolated successor run `44211248673` reports 33 cases, 341 assertions per architecture; it is not the production service. | Preserve historical evidence without transferring its authority to production. Independent integration review pending; HOLD. |
| P275 historical RED / material | Run `44398320658`: original WindowsCredentialBackend tests 2 fails + 5 errors; P211 14 failed obsolete source expectations; P216 2 failed. | All unwaived pending reconciliation. No historical edits, skips or inferred replacement baseline; independent closure pending; HOLD. |
| P292 third run / HIGH | Overall 3/6; original x64 metadata error and timeout remain distinct unknown causes; x86 postdelete absence unverified. | Delete success does not prove absence. Retained-process launch/teardown evidence and causal review required; HOLD. |
| P294 / material missing evidence | Reported 6/6 is static evidence; prior binary-sharing ambiguity is unresolved. | Static results cannot establish service startup, custody or cleanup. Independent runtime evidence pending; HOLD. |
| Local Application Control refusal / HIGH | Independent launch refusal conflicts with author launch reporting; launch custody and root cause unresolved. | Preserve both observations; no bypass, alternate launcher or invented successful retry. Qualified review pending; HOLD. |
| Production authority / HIGH missing evidence | Principal, SCM, protected store, IPC, consent and restart are not validated. | No production service/store integration inferred from fakes or source hashes. OS-bound adversarial evidence and independent review required; HOLD. |
| P298 focused evidence / pending | 15 cases, AST negatives and two-trial workflow are authored; no actual hosted receipts are available here. | Review exact source and raw hosted receipts before any focused-evidence conclusion; no invented passes; HOLD. |
| Governance / release gate | Qualified approvals 0/7; full accepted Windows regressions 0/3. | Independent qualified approvals and accepted regressions remain absent; REAL KEY NO-GO, PRODUCTION HOLD. |

**Failure gate disposition: HOLD.** Unknown causes and material missing evidence
prevent forward production qualification; source-only retirement evidence is bounded.

## Next security work and stop boundary

Obtain separately authorized exact-source hosted receipts for both P298 trials;
inspect raw exits, complete test output, negative-audit behavior and source manifests.
Reconcile P275 RED against current contracts without rewriting historical evidence,
then independently validate affected older routes and full Windows regressions.
Resolve P292 metadata/timeout and x86 teardown custody plus Application Control
refusal before authorizing further OS experiments; preserve original observations.
Review production principal/SCM, protected-store ownership, authenticated IPC,
one-use consent and restart custody with atomic owner/effect enforcement.
Retain Permission -> Policy -> Confirmation -> Execution -> Verification;
model output and receipt labels confer neither authority nor proof.
No workbook/dashboard update until BYOK C1 is complete; no seal is asserted.
Stop immediately after creating this document; perform no subsequent command.
