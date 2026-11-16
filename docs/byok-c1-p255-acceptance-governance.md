# P255 source effect boundary and acceptance governance

16 November 2026. Sole implementation writer. **DRAFT, host P255 focused tests
17/17 PASS, source probe OPEN/BLOCKED, original current-descendant P251 failure
on version-root compatibility HOLD. Independent review pending. REAL-KEY NO-GO.
PRODUCTION HOLD. RELEASE HOLD.**

## Source identity and bounded advancement

Intake branch is `byok-c1-p255-p76-governance-effect-boundary-20261116`, HEAD
`4e2a605f6e8a7b079c9430dbf18461c2b2795a77`, tree
`112714c1489ddb6a62b56ed0800ecf334a9ba097`, in
`D:\Nayeon\CODEX_P255_SECURITY_BOUNDARY_20261116`. Intake status was clean,
with no milestone tag at HEAD. Recent commits are P254, P253, P252, P251 and
P250. `.codex/CURRENT_STATE.md` starts with older 3 November Phase 10.2 material.
Git and the explicit P255 assignment govern this bounded diagnostic checkpoint.

Three additive files implement a source probe, synthetic unittest module and
this acceptance record. `tools/byok_c1_p255_effect_boundary.py` reuses P251
`_assess`, its fixed six-source SHA-256 manifest, `_read_source` and scoped
`_ast_records`. It adds six explicit route obligations and an unconditional
BLOCKED exit contract. Production acceptance continues on HOLD. The engineering
failure gate and P250 through P254 were read before implementation.

P251's raw SHA-256 is
`990117324c727662d2909c96b73c135c7278baf69c242f312bdf24782d96330b`.
PowerShell raw hashing matched all six inherited source pins below.

| Inspected source | SHA-256 |
| --- | --- |
| `nayeon/desktop_alpha/local_byok_launch_bridge.py` | `1fb8a889c7dcba0a83c1dbc888bd1d7deb219bcff3fc08cadeb246f61b3c71d5` |
| `nayeon/desktop_alpha/local_byok_window.py` | `8dfdfc587886471f312d39aa53bc049179a7ca2d61bc310f84ac142ba5d103e6` |
| `nayeon/brain/local_byok_user_scope.py` | `1971a3f7f90c840fb6c3dc95128ecb6cf2a5e855204d418d99144eb10f3a17b6` |
| `nayeon/secrets/windows_credential.py` | `e6443853300fb2fb4944b8c8bede2ee953719eaf7544d7338056d81491b46125` |
| `tests/p96_native_transaction_negative/PendingCustodyTransaction.cs` | `d8b8e4c6d5ea5e035b58c6ad73dd758c16640167c804ccf3305969b12bdf81ab` |
| `docs/byok-c1-p250-p96-service-owned-ordering-architecture.md` | `def6c23193a9b26ef0046e76e6d296aa75baf2dfaac603827dc0e7820cbd0b6b` |

## Source exposure and probe contract

| Route / inspected methods | Concrete source evidence | Acceptance disposition |
| --- | --- | --- |
| Direct Python native mutation | `_Advapi32Adapter.write` calls `self._dll.CredWriteW` at `windows_credential.py` 113. `delete` calls `self._dll.CredDeleteW` at 120 | HIGH, OPEN. Production effect-owner exclusivity NOT ESTABLISHED |
| Direct backend wrappers | `WindowsCredentialBackend.put` delegates to `self._adapter().write` at 169, `delete` delegates at 177. `_adapter` lazily constructs `_Advapi32Adapter`, whose setup loads Advapi32 | HIGH, OPEN. Direct backend entry has separate authority from the proposed service |
| Interactive user approval | `LocalByokController.approve` calls backend delete at 175 or put at 181. `compose_user_scope_local_byok` constructs the actual backend at 207 | HIGH, OPEN. Local one-use review/RLock/cooperative mutex does not establish exclusive service custody |
| Source child/UI | Application Connection callback calls `LocalByokLaunchBridge.launch`. Source launch calls `subprocess.Popen` at 98. `local_byok_window.main` composes the controller, and `approve_from_button` calls its approval method at 243 | OPEN. Source CLI and direct module entry remain part of the known inventory |

On a fully matching snapshot the probe is designed to emit `assessment=OPEN`,
six OPEN route records, `status=BLOCKED`, and
`effect_owner_exclusivity=NOT_ESTABLISHED`. Every route includes exact witnessed
path, scope, call and line. Any drift, missing/duplicate/wrong-scope site,
unreadable/unparseable source or unresolved obligation yields UNKNOWN/BLOCKED.
Safe lexical fixtures and empty inventories also remain UNKNOWN/BLOCKED.
`release_admitted`, `real_key_admitted` and `independently_approved` are false.
The CLI accepts no root, manifest or approval override and returns **3** for
both OPEN and UNKNOWN. The independently executed host probe returned exit 3
with externally verified `assessment=OPEN`, `status=BLOCKED`,
`effect_owner_exclusivity=NOT_ESTABLISHED` and direct Python routes present.
This records the intended admission refusal. Security acceptance remains HOLD.

The probe reads source bytes and parses ASTs. Its project dependency is P251's
diagnostic module. Synthetic tests patch that module's manifest in memory and
use temporary source strings within this workspace, each with an execution-failure
sentinel. Seventeen named test methods cover direct calls and wrappers, aliases,
dynamic lookup, safe reads, comments/strings, duplicate/wrong-scope calls,
unexpected byte drift, empty evidence, missing/invalid/oversized/denied sources,
mocked reparse refusal, fresh restored observations, absence of product imports,
and CLI blocker/root/argument contracts. The independently executed Windows
CPython 3.12.10 host run passed all seventeen tests, native exit 0.

Static inspection supplies incomplete evidence. OPEN describes lexical presence.
Dynamic import/native alias resolution, transitive dependency closure, runtime
reachability, loaded images, installed packages, copied callers, other processes,
actual credential effects and OS exclusion require separate evidence. Trusted
tool/interpreter imports and a quiescent checkout remain prerequisites. P251's
path checks retain hardlink and concurrent-replacement limitations. These tools
grant no OS-level exclusion guarantee or production authority. P250 requires both
signed production package/load exclusion and independent OS isolation of the new
service store. Existing interactive-user data requires GOV-02 disposition.

## Four original P76 failures and authentic historical witnesses

All four P252 current-product executions remain **FAIL, native exit 1, unwaived**.
Their common root cause is successful-positive assertions reaching
`tests/phase8_byok_c1_p76_scope.py.assert_p76_offline_integrity`, which first
requires `byok-c1-p80-sealed-historical-fixture-20261106`. Current B routes through
Phase10, Phase10.2 and Phase10.3. Current 8.34 routes through 8.36, final 8.37
and B. The terminal refusal precedes later causal assertions. P255 reviewed the
actual original methods and the terminal guard as source.

M1-M3 belong to `tests/test_phase8_byok_b_scope_integrity.py`. M4 belongs to
`tests/test_phase_834_scope_integrity.py`. Full method identities within those
modules and the distinct evidence are mapped below.

| Original identity | Current P252 failure / later coverage gap | Authentic historical completed witness | Owner-needed disposition |
| --- | --- | --- | --- |
| M1 `BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay` | Initial live B admission fails before Phase10 `_disk` corruption of both brain targets, causal reach and final restored admission | P254 M1 PASS, exit 0, 67.985s | GOV-01 and REL-06 must preserve the current failure and decide separately versioned current live-admission and original-reader acceptance requirements |
| M2 `BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected` | Initial live admission fails before three historical factories across three states, 18 brain corruptions, causal reach/restoration and final live bracket | P254 M2 PASS, exit 0, 165.750s | GOV-01 and REL-06 must accept historical replay evidence only for its exact source and specify current coverage for all required properties |
| M3 `ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission` | Literal manifest checks precede failed live B admission. Positive A/B state agreement remains unreached | P253 M3 PASS, exit 0, 55.593s | GOV-01 and REL-06 must distinguish literal archival witness credit from separately approved current public-admission/equality obligations |
| M4 `Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route` | Initial 8.34 admission fails before twenty sealed pins, predecessor reader counts, second-read corruption and restoration | P254 M4 PASS, exit 0, 99.687s | GOV-01 and REL-06 must resolve current public-state agreement and actual predecessor reader/error/restoration requirements in explicit approved scope |

Authentic historical source is P80 commit
`24da07345c67566d2e79f442aabfba36a1ebddb4`, tree
`1795b59895b7fd52da525d237eb4282d5d10851f`. Its subject identifies a WIP historical
fixture migration and its P76 gate identifies a prototype. P253 reports the direct
historical `EXACT_CHILD` observation, original P76 public/private agreement PASS,
five denial-method PASS witnesses, and a supplementary five-public-route agreement
PASS. P254 reports independent technical GO for its bounded historical evidence.
This scope adds zero qualified product approvals.

P253's original M1/M2/M4 60-second timeout records remain incomplete in that run
window. P254's later completed witnesses address that historical evidence gap.
P252's four current failures retain their original results. P255 reads these
inherited reports and references their receipts. External streams and receipts
were neither reexecuted nor independently rehashed here.

| Inherited receipt | Recorded SHA-256 |
| --- | --- |
| P252 `receipt.json` | `427ccddc4191292926d7986998cdd2651122c5f2c89738cbb5d2c6e0a8238a28` |
| P253 ten-method `receipt.json` | `4a4b947b61cdd4ab5ae4c19a3978b4f75a955345103270a3f2bf5d6aeb996c8c` |
| P253 `second-p76-positive.receipt.json` | `8ad298a79eff4e9cd2ea166efac7275c00aa2c667b2e45890f01a2e82e12e4fd` |
| P254 `completion-receipt.json` | `a989f445b65d6b74afbd50a6d1f5681264f0cb036386d2e46767dc0f7aeda4e9` |

Current raw historical test hashes match the inherited receipts' source pins,
B `65dad89298a587d6bb5dde5455df4d701bb1a1fd9a7a96cecf3e647800e3ae8b`,
8.34 `8dc69ec770ea008dff9cd13e15299a73e38044f1671fd4fe78fbe2a431ccf57a`,
and P76 guard `1c42912d9fc550dea56c9ba9bb70d9568f298223b5514af8d03c1723aaad3327`.
The original assertions and failure records remain authentic witnesses.

## Modern P245/P248 diagnostics and remaining decisions

P245 `complete_source`, `raw_source` and `git_identity` establish their separately
bounded current-source observations. P248 `source_snapshot` adds its own draft
or one-child topology. Its `current_read_pair` composes two P245 complete scans.
P248's C01/C02 test literal B manifests and sealed twenty-file witnesses. C03
corrupts the two current brain targets through P245 `raw_source`. C04 corrupts
the second current conversation-session read. C05 observes unchanged terminal
P76 refusals. The four topology tests exercise synthetic controls.

Original positive public admission, original Phase10 `_disk` error/reach
contracts, historical projection `_raw_frozen_disk` routes and restored public
agreement require their own source-bound acceptance. P253/P254 supply historical
execution witnesses. P245/P248 supply distinct modern diagnostic properties.
Their branch/root/envelope contracts also require applicable validation before
reuse on P255. GOV-01/REL-06 must issue an explicit archival/current inventory
decision and approved current coverage, with REL-05 security review of any
proposed routing migration. Conflicting frozen contracts remain a HOLD for
current acceptance. Historical PASS witnesses cannot convert P252 outcomes or
authorize weakening, rewriting, skipping or waiving the original assertions.

## P96 ownership and race proof obligations

`PendingCustodyTransaction.Apply` checks `ApprovalCurrent`, then `lease.IsOwned`,
then calls `state.DeletePending` or `state.SaveOrReplace` at 210/212. In
`NativeTransactionRaceProof.cs`, `P96LeaseFixture.IsOwned` injects and joins a
separate revoker on check four, after the final current-approval observation.
The fake state counts possible effects after revoke. The original race remains
**HIGH, OPEN**. Its negative harness was inspected as source.

SEC-03/SEC-04 and REL-05 must accept one actual service-private, nonreentrant
ordering owner across Prepare/Admission, Revoke, Stop, Fault and Dispatch, plus
continuous OS custody and stale-process fencing. Deterministic actual-owner
evidence must cover Save/Replace/Delete with both winner orders, recursive
reentry, duplicate/replay and crash/restart. Lifecycle-first requires zero
submission for that operation. Dispatch-first requires at most one submission,
sticky MAY_HAVE_EFFECT/RecoveryRequired and a too-late response. Durable consumed
intent, protected journal/anchor/independent witness, actual principal/profile,
impersonation reversion and recovery uncertainty need independent proof.
The same acceptance must trace old Python, direct native/backend, legacy native,
multi-process/session and stale-installed routes. Another final check, local
monitor or synthetic model supplies no cross-process exclusion proof.

## Qualified decisions and Open Failures & Prior-Issues Review

These roles require actual named independent owners, authority/conflicts,
source/artifact/environment identities, date/expiry/revocation, evidence and
authenticated GO/HOLD/REJECTED decisions. All seven remain pending, **0/7**.

| Decision owner requested by P250 | Required disposition / current state |
| --- | --- |
| SEC-03 Windows principal/store | Select exact account/SID/token/profile, ACL/SDDL, separate store, durable witness and recovery/retention boundaries. HIGH missing evidence, HOLD |
| SEC-04 signing/CI/IPC/consent | Approve signed loaded graph, enforced CI, authenticated OS peers, human one-use consent and alternate-effect exclusion. HIGH missing evidence, HOLD |
| GOV-01 threat-model/acceptance | Resolve same-user/cross-user/admin/rollback scope and historical/current acceptance inventory above. Material unresolved acceptance, HOLD |
| GOV-02 retention/recovery | Decide existing user-vault retention, migration/deletion authority, privacy and recovery. HIGH missing evidence, HOLD |
| REL-05 independent security | Review exact source/artifacts, actual owner/race repairs and adversarial alternate-route evidence. HIGH OPEN trust boundaries, HOLD |
| REL-06 Windows validation | Accept exact current test inventory and three unfiltered authoritative Windows whole-product regressions in approved pre-stage/staged/immediate-child workflow. **0/3**, HOLD |
| REL-07 production change/rollback | Independently approve install/update/rollback and production scope after prerequisite closure. HOLD |

P247 remains **x64 0/54 and x86 0/54 nonexecuted**. Code Integrity/script-policy
refusals leave runtime evidence missing. P249 requires environment-owner approval
for any later execution chain. P255 runs no such binary. These model cases cannot
close original P96 or OS custody obligations. Qualified approvals stay **0/7**,
full unfiltered Windows regressions **0/3**, **REAL-KEY NO-GO, RELEASE HOLD**.

The bounded repair here addresses diagnostic automation only. Original P76
failures, P96, alternate Python effects and qualified-evidence gaps remain OPEN
with the root causes and impacted routes above. Independent P255 review is
pending. Production progression/seal disposition is **HOLD**.

## P255 validation and review handoff

Authenticated Desktop Commander host orchestration independently ran the stdlib
subprocess runner
`D:\Nayeon\P255_SECURITY_BOUNDARY_EVIDENCE_20261116\run-windows-focused.py`
under actual Windows CPython 3.12.10. The user supplied the resulting evidence
for this documentation-only reconciliation. Its receipt is
`D:\Nayeon\P255_SECURITY_BOUNDARY_EVIDENCE_20261116\windows-focused-receipt.json`,
SHA-256
`55B306D54418F3D873C84C3540AA7BFD659C5FFDD798DEC4420E9052E15AF23F`.
The receipt confirms identical before/after hashes for the five inspected files
(two P255 additions and three tracked reference files). Receipt and raw streams
were externally verified and supplied here. This reconciliation performs no test
rerun or independent receipt rehash.

The native jobs used these exact commands.

```text
python -B -m unittest discover -s tests -p test_byok_c1_p255_effect_boundary.py -v
python -B -m tools.byok_c1_p255_effect_boundary
python -B -m unittest discover -s tests -p test_byok_c1_p251_effect_exposure_gate.py -v
```

| Native job | Actual result / native exit | Elapsed / timeout | Raw stream SHA-256 |
| --- | --- | --- | --- |
| P255 synthetic tests | **PASS 17/17**, child exit **0**. Stdout empty | 0.344s / none | stderr `422F8A185F3D12E999064013D4F6FE7B72484D29B79493A5F4CF3612DBAA84FC` |
| Current P255 source probe | **OPEN/BLOCKED**, child exit **3**, intended admission refusal. Effect-owner exclusivity **NOT_ESTABLISHED**, direct Python routes present | 0.094s / none | JSON stdout `B437706FC09F7DD19697D26B2E2E09BD03EA53A5E1208906DF2A84284689FB56` |
| Original P251 tests on P255 branch | **26 PASS, 1 FAIL**, original native exit **1** | 0.515s / no timeout | stderr `4BA44ED42F4C52906A1284FF6EC9105E238E8BB845C093FDC6B6AB24BA3C0052` |
| Overall host evidence orchestrator | Exit **1** due to the actual original P251 failure | Preserved overall failure | Receipt SHA-256 recorded above |

The review discrepancy is the original current-descendant failure in
`test_byok_c1_p251_effect_exposure_gate.CheckoutTests.test_report_cli`.
It expected `KNOWN_EFFECT_EXPOSURE` and received `UNKNOWN` because P251's fixed
intended worktree root excludes the new P255 location. This remains an unresolved
**version-root compatibility HOLD** affecting P251's current-checkout CLI
assertion. The original test and failure are preserved. Repair and independent
closure remain pending. The P255 focused pass and expected probe refusal supply
zero full-product regression credit. Qualified reviews/approvals remain **0/7**,
full regressions **0/3**, with **REAL-KEY NO-GO, PRODUCTION HOLD, RELEASE HOLD**.
The source-only probe cannot establish OS exclusion.

Earlier Codex sandbox attempts used the required installed interpreter path.
Each PowerShell invocation exited **1** on
`CommandNotFoundException` before Python startup. A direct metadata check also
reported access denied. No native child exit or test runtime exists for either
local attempt. Measured failed-launch durations were 0.042234s and 0.042651s
respectively. These failed launches remain separate from the later actual host
jobs above.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B -m unittest discover -s tests -p test_byok_c1_p255_effect_boundary.py -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B -m tools.byok_c1_p255_effect_boundary
```

Earlier Codex connected-host orchestration was attempted for workspace/branch/HEAD
and Python version inspection. Automatic tool approval rejected it with
`MCP tool call requires approval, but approval policy is never`. It executed no
host command. The later authenticated Desktop Commander execution supplies the
host version and native results recorded above. The earlier local infrastructure
failures remain historical evidence. Independent P255 review remains pending.

One exploratory unquoted `HEAD^{tree}` was interpreted by PowerShell and failed.
The quoted Git query returned the tree recorded above. An early version attempt
displayed stale Git exit 128 after failing to launch Python. The two dedicated
attempts above separately captured null native exits. `rg` was unavailable,
so bounded Git inventory and PowerShell reads were used.

Raw SHA-256 of the proposed probe is
`f5701e051d1f6c35e5d2261060f2aa1c8f0a3f86dcc92754fe33847f6fec320d`,
and of its tests is
`6dbc629017494c585c00ca6aed081b31ff5168eadc9472fe681adb4ce8a3ba32`.
This document's final hash is supplied in the review handoff to avoid a self-pin.
Focused native tests and probe execution are reconciled to the supplied host
receipt above. Python syntax compilation remains pending. Static source/hash and
whitespace checks carry only their stated scope.
`git diff --check`, tracked diff and staged diff checks exited 0. Each addition's
`git diff --no-index --check -- NUL <path>` exited 1 for added-file differences,
with zero whitespace diagnostics. Separate byte checks found final LF and zero
trailing whitespace in all three additions. Final status contains exactly these
three untracked files, on the requested branch and base HEAD. The worktree is
left uncommitted for independent review.
