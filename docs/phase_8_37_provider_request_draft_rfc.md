# Phase 8.37 — In-memory provider request draft

Status: **UNSEALED SOURCE CANDIDATE — Increments A + B; B runtime/review HOLD.**
Date: 2026-10-23

Phase 8, "Secure Secrets & BYOK Onboarding", remains IN PROGRESS. The original
master roadmap did not predefine subphase 8.37. This document adapts the approved
`D:\Nayeon\Phase_8_37\phase_837_rfc_proposal.md` and independently obtained
DESIGN_GO in `D:\Nayeon\Phase_8_37\design_review_20261023.log`. Design approval
does not constitute source, regression, integration, seal or release approval.

## Exact Increment A scope

The following sections retain Increment A's original scope and evidence.
The separately authorized Increment B implementation is recorded below.

Only these three new files are authorized:

- `nayeon/desktop_alpha/offline_request_draft.py`
- `tests/test_phase_837_offline_request_draft.py`
- `docs/phase_8_37_provider_request_draft_rfc.md`

No existing tracked files, UI/Tk wiring, review owner, application, scope guards,
failure ledger, context handoff, index, branch, commits or tags are changed.
No credentials, provider calls, storage, process execution, network, actions,
workers, approval operations, external services or protected checkout edits.

## Pure data contract

`OfflineRequestDraft(provider, model, prompt)` accepts only exact built-in strings.
Provider must be exactly `openai`. The model has 1–80 ASCII characters from
`A-Z a-z 0-9 . _ -` (spaces are not part of the allowlist); it is never stripped,
normalized, resolved or checked for availability. Slash, whitespace, controls,
Unicode lookalikes and bidi characters are refused. Prompt validation reuses the
existing pure `validate_offline_text`: 1–512 NFC code points, at most 2048 UTF-8
bytes, nonblank and without prohibited controls/format characters/line breaks.
Accepted prompt contents are preserved literally.

The frozen slotted draft has exactly provider, model and prompt fields. Its pure
`to_json()` returns deterministic ASCII-escaped JSON with precisely this key
order and cardinality:

```json
{"model":"example-model","input":[{"role":"user","content":"current prompt"}]}
```

Provider metadata stays outside the payload. No transcript, assistant identity,
hidden instructions, tool, credential, token, header or future permission is
included. Serialization checks the exact source type before attribute access,
rejects subclasses and arbitrary conversion hooks, and revalidates the fields.
There is no dispatch function. Frozen Python records are an ordinary data
contract, not a security sandbox against hostile arbitrary Python execution.

Disclosure: **LOCAL REQUEST DRAFT — MODEL AVAILABILITY UNCHECKED — NOTHING SENT**.
`OfflineDraftReceipt` retains the exact draft, fixed `NO REQUEST WAS SENT` status,
disclosure and immutable false network/action/persistence permissions. It is
local data only, not proof of a human confirmation, an approval ticket or future
consent. Increment A creates no confirmation workflow.

## Open Failures & Prior-Issues Review

Git preflight: clean `nayeon-v1`, exact parent
`a12565b9be070684e1d7d801ded4833d13121f94`; 8.36 annotated tag
`nayeon-v1-phase-8-36-offline-request-review-01`, object
`aca0de5a873cf41454fe1fa144d12f34d44418a4`, peels to that parent.
No historical tag is changed.

Reviewed `.codex/CURRENT_STATE.md`, `docs/engineering_failure_review_gate.md`,
`docs/phase_8_36_offline_request_review_review.md`, the recent failure ledger,
the external proposal/review, and the pure text validator dependency.

| Issue / source | Severity / cause and affected boundary | Evidence, containment and disposition |
| --- | --- | --- |
| Stale handoff and 8.36 review | Missing phase-closure evidence; handoff still describes 8.34, review says candidate despite Git 8.36 tag | Reproduced by reading files and Git refs. No reconciliation authorized here. Broader phase HOLD; no claimed regression baseline or independent source GO. |
| 8.36 worker ingress / stale cleanup success | Prior P2 findings in UI/owner admission and publication | Existing review records fixes and fault tests on `606f3ce1`; no new independent reproduction. No caller/UI integration in A. Integration HOLD pending evidence reconciliation. |
| 8.36 first-operation thread guards | Prior material cross-phase thread-contract regression | Ledger records 18 failures in 2,867 tests, three guard repairs and two causal passes; full closure not independently established here. A imports no Tk/thread/worker route. Integration HOLD. |
| 831-TK-ASYNCDELETE | Historical native availability failure from worker GC of retired Tk cycles | Ledger records main-thread fixture retirement and bounded reviewed closure. A creates no Tk objects. No broader Tk safety claim. |
| Ignored bytecode / successor topology | Historical isolated `-I` child wrote 24 pyc files; topology tests expected only unstaged state | Ledger records causal reproduction and proposed ordering/topology repairs. No guard migration or subprocess tests here. Use `-B` for focused tests; full successor admission and seal HOLD. |

Dependency path is draft → existing pure validator → standard data utilities;
encoding uses standard `json` only. There are no existing callers, alternate
entrypoints, window/session ownership changes or service imports. These
containments limit A's reach; they do not close historical integration issues.
The user's explicit three-file authorization bounds this implementation.

## Validation and deferred gates

New unittest coverage checks exact types, ASCII/model/provider refusal, prompt
bounds and literal preservation, payload shape/order, immutability, hostile
serialization sources, nonauthorizing receipt and strict import surface. No real
provider is used. Runtime results must be reported from actual execution; this
RFC asserts no passing count or full regression result.

Sandbox attempt on 2026-10-23:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe -B -m unittest tests.test_phase_837_offline_request_draft -v`
could not start: PowerShell `CommandNotFoundException` for the authoritative
interpreter (command exit 1, no tests executed). No retry, fallback shell,
interpreter install or network workaround. Host orchestration must execute the
new tests; runtime validation remains HOLD.

The original proposal's UI controls, one-use confirmation, exact context and
revision binding, 30-second expiry, reentrancy/cleanup/worker invalidation and
final Tcl seam are deferred, not implemented. They require separately approved
scope and failure-gate clearance. Historical 8.30–8.36 guards remain unchanged;
new files may correctly cause current-checkout inventory refusal until an
independently reviewed exact successor migration is approved.

**HOLD for full phase/integration/seal:** host runtime validation as available,
independent source review, historical failure-evidence reconciliation, future
successor guards, affected/adversarial/full Windows suites and compileall remain
required at their appropriate gates. No staging, commit, tag, push, workbook or
dashboard update is part of Increment A.

## Increment B — bounded Conversation UI (23 October 2026)

Explicit user authorization permits this source-only integration on isolated
`D:\Nayeon\Phase_8_37\candidate`, branch `nayeon-v1`, unchanged protected HEAD
`a12565b9be070684e1d7d801ded4833d13121f94`. Git preflight found exactly the three
untracked A files. The user reports independent A SOURCE_GO and signed-host
11/11 PASS; this session does not independently reproduce that evidence.
The stale state/review documents noted above still disagree with Git's 8.36
milestone tag. No context reconciliation or claim of historical gate closure
is made by B. The original protected checkout is outside B's write scope.

Exact B paths (no historical guard or Increment A Python edits):

- `nayeon/desktop_alpha/workspace_window.py` — Conversation controls/controller.
- `nayeon/desktop_alpha/application.py` — only the existing read-only snapshot
  callback, with pure admission/identity checks before and after reentrant Tcl.
- `nayeon/desktop_alpha/offline_draft_consent.py` — new pure composition owner.
- `tests/test_phase_837_draft_consent.py` — new pure adversarial tests.
- `tests/test_phase_837_draft_tk.py` — new owned fake-Tk/controller tests.
- `tests/test_phase_837_draft_application.py` — new app/worker-fake tests.
- `docs/phase_8_37_provider_request_draft_rfc.md` — this update.

The user explicitly types provider `openai` and a bounded model, then selects
**Prepare offline draft**. The same live Conversation prompt supplies the only
input. The exact deterministic JSON appears in a read-only, fixed-height,
scrollable field with A's exact disclosure. No model availability is checked.
**Confirm offline draft** consumes a one-use draft ticket before Tk cleanup or
receipt publication. Only successful final display checks retain the frozen
`OfflineDraftReceipt` and show **NO REQUEST WAS SENT**. Cancel drops all draft,
ticket and receipt references. No transcript entry is added or saved.

The composition privately owns a fresh `OfflineRequestReviewOwner`; it never
borrows the 8.36 owner/ticket. Exact draft identity binds provider, model and
prompt to exact context identity and a 30-second monotonic lifetime starting
at offer. UI binding adds exact immutable snapshot identity. Model, provider
and prompt edits revoke before cleanup, including edit-and-restore attempts.
The app's existing cancellation seam revokes drafts before simulation-worker
admission, Save, reset and render. Prompt-only review still has its own controls,
owner, tickets, receipt and return contract; a draft fault does not poison it.
Navigation/pane/root retirement and draft-widget teardown revoke Python state.
Destroy event handlers perform no Tcl calls.

The controller checks fresh fields, disclosure, exact read-only JSON, current
view/snapshot and owner state, then brackets its final button `instate` with
pure context/generation/deadline checks before arming or consuming. Receipt
publication repeats live checks and a final disabled-button observation. Busy
callbacks revoke rather than recursively publish. Each registered Confirm
callback captures its draft generation; a captured stale callback cancels
instead of confirming a successor. At most one known draft Tcl command is
retained; cancellation retires it. Any publication/cleanup exception revokes
the proposal; Tk/cleanup faults latch that pane against draft reuse. Cleanup
clears success first and independently attempts to hide a failed surface.
If Tcl refuses both clear and hide, visibility cannot be guaranteed; the fault
latch and revoked ticket still prevent any later draft success or authority.

### Open Failures & Prior-Issues Review — B

| Issue | Severity / root cause / affected path | Repair, evidence and disposition |
| --- | --- | --- |
| 8.36 reentrant snapshot admission | Material admission assumption: worker checks preceded `_current()` only; its Tcl calls may change worker/lifetime/session state | Source trace: both prompt-review and draft callers use `_request_review_snapshot`; repeat pure checks, bind exact app root/view/session/snapshot before/after `_current`. New deterministic reentrancy and thread tests added; runtime and independent review pending. HOLD for validation. |
| Prior worker ingress and cleanup stale success | Prior P2 UI defects; nested final widget callbacks and independent cleanup faults | Preserve sealed worker ingress, add draft revocation there through existing view cancellation; consume before publication, check after effects, clear success before other cleanup, fault latch/hide fallback. New fake-worker and before/after-effect fault tests authored; unexecuted. HOLD. |
| Cross-thread first-operation regression | Prior material ownership failure across UI/app paths | New controller entrypoints check creator thread first; composition delegates to its independently owned review thread check. New owner/UI/app foreign-thread negatives authored. HOLD for host proof. |
| Stale handoff, native Tcl lifetime, ignored bytecode and successor inventory | Historical evidence and environment limitations listed above remain relevant | No historical files/tests weakened, skipped or migrated. Fake-owned Tk uses no display; original native 8.36 tests remain required. Exact historical inventory refusal is EXPECTED until separately pinned Increment C. No seal/integration GO. |

Tests cover exact receipts, foreign/counterfeit/8.36 tickets, model/context
changes, expiry at 30 seconds, edit/restore revocation, root/pane/session changes,
reentrant Confirm/Prepare/Cancel, stale callbacks, widget teardown, fake worker
admission, display tampering, JSON bounds, publication/cleanup faults and effect
tripwires. No production thread, timer, worker, provider, credential, network,
action, process, file I/O, persistence or automatic approval is added.

### B validation / restart point

This session performs source/static checks only. Per the user's environment
constraint, Python is inaccessible in Codex: no interpreter workaround, runtime
tests or compileall are attempted, and no pass count is claimed. Host operator
must run with the authoritative Windows Python (use `-B` for unittest):

```powershell
$hostPython = 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe'
& $hostPython -B -m unittest tests.test_phase_837_offline_request_draft tests.test_phase_837_draft_consent tests.test_phase_837_draft_tk tests.test_phase_837_draft_application -v
& $hostPython -B -m unittest tests.test_phase_836_offline_request_review tests.test_phase_836_tk_request_review tests.test_phase_836_application_review -v
```

Static checks: `git diff --check` exits 0; all seven B paths have no trailing
whitespace. The index is empty, protected HEAD/branch and the 8.36 tag object
remain unchanged. A's Python SHA-256 values remain
`c4d39810d6cb220d3ca9e38e3c9ceab8554ae2b662732ebb24bbc9fe98f24cb3`
(draft) and `86b7d86931e924f9d830faa14c9a34ca738ba14ee881e8f12294b0e48b96b452`
(tests), identical to the pre-edit readback. No frozen guard is modified.

Native Tk layout, teardown/command retirement, affected trust-path/full Windows
regressions, `python -m compileall -q nayeon tests`, independent B source/security
review and the separately approved exact successor C remain required. Do not
convert expected scope-integrity HOLD into a passing or skipped test. Compilation
creates bytecode and must be coordinated with host inventory/evidence handling.
No staging, commit, tag, push, live BYOK, master workbook, release or ACL change
is authorized by this source candidate. **HOLD for runtime, independent review
and phase seal; next step is host validation of these exact B bytes.**

## PRESTAGE regression repair - 23 October 2026

This section records the later bounded repair request; prior increment evidence
above describes its own source dates. The completed authoritative Windows 3.12
run was **2,944 tests / 22 failures / exit 1**, 4,342.876 seconds, in
`D:\Nayeon\Phase_8_37\full_regression_pre_stage_20261023.log` and its result txt.
Both off-repo `prestage_837_initial_failure_triage_20261023.md` and
`prestage_837_successor_repair_design_20261023.md` were read before edits.
Their running-suite warnings are superseded only by the completed result.

Git preflight agrees with the requested protected parent
`a12565b9be070684e1d7d801ded4833d13121f94`, tree
`f2d35fef90add1bb3b14ab9a1b26b0235334bfbb`, and annotated 8.36 tag object
`aca0de5a873cf41454fe1fa144d12f34d44418a4`, on `nayeon-v1`.
`.codex/CURRENT_STATE.md` remains stale (describes 8.36 as unsealed); Git is
authoritative. This repair starts no new phase and leaves that file unchanged.

### Open Failures & Prior-Issues Review - PRESTAGE

All seven early failures are test-contract migrations, not demonstrated runtime
authority bypasses. Severity is MEDIUM for the blocked regression and assurance
gap. Each traceback was read; each root cause and repair remains **HOLD for
runtime and independent review** until the new exact bytes are validated.

| ID / exact failing caller and original line | Observed failure and root cause | Bounded repair / evidence |
| --- | --- | --- |
| R1 `test_bound_credential_lifecycle.Phase83ScopeGuards.test_exact_new_production_delta_and_every_preexisting_file_frozen`, 448 | `approved_830_scope` retains exactly the two new draft source paths, causing set inequality | Project only these literal paths after fresh full 8.37 raw disk/index/Git admission; keep the historical test and sealed comparisons unchanged. |
| R2 `test_connection_reconciliation.Phase89ProductionFreeze.test_all_phase88_sealed_production_and_requirements_preserved`, 288 | `approved_830_files` has the same two unexpected paths | Same exact guarded projection; no 8.9 test edit. |
| R3 `test_credential_onboarding_composition.Phase88FrozenProductionScope.test_exact_phase87_production_and_requirements_frozen`, 189 | Same inventory mismatch through `approved_830_files` | Same repair; no 8.8 test edit. |
| R4 `test_openai_canonical_client.Phase84ScopeGuards.test_checkpoint_exact_scope_and_frozen_production`, 225 | `migrated_scope` calls `approved_830_scope`, retaining both draft additions | Same repair; no 8.4 test edit. |
| R5 `test_phase_830_scope_integrity.Phase830ScopeIntegrityTests.test_frozen_production_rejected_on_wrong_branch`, 372 | Injection already reaches 8.37 through the reader chain; exact `Wrong 8.37 product branch` does not match old 8.36 regex | Patch 8.37 `_git` directly, first require valid live baseline, assert exact refusal and one consumed branch injection. |
| R6 `test_phase_830_scope_integrity.Phase830ScopeIntegrityTests.test_staged_modified_entrypoint_bad_blob_refused`, 199 | Forged `window.py` stage blob is rejected as `Frozen 8.37 historical file modified`; expected 8.36 text | Preserve malicious blob test against the frozen entrypoint, prove blob differs, patch live successor reader and assert exact refusal plus consumed index query. |
| R7 `test_phase_831_scope_integrity.Phase831ScopeTests.test_wrong_branch_and_wrong_parent_refused`, 171 | Branch refusal changes from 8.36 to 8.37; assertion aborts before existing wrong-parent check | Direct live-successor injections, exact branch/ancestor failure regexes and consumed-query assertions for both checks. Original historical parent fixtures remain. |
| R8 late 15 failures, presentation bootstrap/document/persistence/service/view/identity and provider composition/service/startup plus Windows credential scope callers | Every traceback terminates at `Ignored 8.37 executable or source`; 24 ignored CPython 3.12 cache files generated by the historical isolated subprocess | User reports positive identification and cleanup after the suite. Current ignored inventory is empty. Preserve the full ignored-source refusal and its adversaries. No deletion, cache exception or isolated-subprocess test change in this repair. HOLD for host revalidation. |
| Prior 8.36 Tk/thread/reentrant cleanup incidents | Shared UI/app callers required source and lifecycle repairs in earlier increments | Production bytes and pins remain exactly as supplied for 8.37. This test-only repair does not supersede their independent evidence or native validation requirements. |

The exact precedent was inspected with
`git show a12565b -- tests/phase_8_30_scope_migration.py tests/test_phase_830_scope_integrity.py tests/test_phase_831_scope_integrity.py`.
At this R2 repair checkpoint, the successor envelope expanded from 13 to **16 paths**: only those three
already-existing historical test/helper files become modified allowances.
`tests/phase_8_37_scope_migration.py` pinned all 16 raw files and its normalized
self hash; `tests/test_phase_837_scope_integrity.py` independently enumerates the
R2 16-path envelope. This RFC was already one of those paths. No other historical
test path or production path is added to scope.

Both projection adapters retain unrelated aliases and `.bak` names in caller
inventories. The actual whole-tree gate rejects those names on disk or in Git.
The new shared projection helper removes only `offline_request_draft.py` and
`offline_draft_consent.py` at their exact full paths, and accepts only exact
string states `COMPLETE_UNSTAGED`, `EXACT_STAGED` or `EXACT_CHILD` after actual
admission. It never treats a mock state, filename or earlier GO as authorization.
The modified `application.py` and `workspace_window.py` already have exact 8.37
pins; existing guarded current-reader/frozen-source adapters cover them. No
extra source projection or edit is needed. Historical tag/blob/tree pins and
private historical guard bodies remain intact.

Six focused projection tests were added within the existing 8.37 integrity test
file: all three complete topologies and fresh gate reads; unproven state refusal;
actual extra path/alias refusal; changed bytes of both new modules and both
modified entrypoints; wrong branch; forged staged application blobs in all
three topologies. Every fault injection asserts that it was consumed. Existing
ancestry, frozen-source, raw delta, ignored loader and historical canaries remain.
The positive caller-inventory test preserves aliases and `.bak` entries rather
than filtering them away. No new skip, xfail or weakened assertion is introduced.

### Validation and independent-review handoff

The authoritative Python path is inaccessible in this Codex sandbox: invoking
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe -B -c "import sys; print(sys.version)"`
produced PowerShell `CommandNotFoundException`. **Post-repair runtime tests
executed here: 0; no runtime PASS, compileall PASS or actual 8.37 gate GO claimed.**
No interpreter/package download, copy or alternate runtime is used. No full
suite is started. Static raw SHA-256/self-pin, exact inventory, protected Git
identity, empty staged/ignored inventory and whitespace checks are performed
before handoff; these do not substitute for executing the guard.

Host orchestration should first execute the real gate on the exact candidate,
then these bounded focused/affected selections with authoritative Python `-B`:

```powershell
$hostPython = 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe'
& $hostPython -B -c 'from tests.phase_8_37_scope_migration import assert_837_integrity; print(assert_837_integrity())'
& $hostPython -B -m unittest tests.test_phase_837_scope_integrity tests.test_phase_836_scope_integrity tests.test_phase_830_scope_integrity tests.test_phase_831_scope_integrity -v
& $hostPython -B -m unittest tests.test_bound_credential_lifecycle.Phase83ScopeGuards tests.test_openai_canonical_client.Phase84ScopeGuards tests.test_credential_onboarding_composition.Phase88FrozenProductionScope tests.test_connection_reconciliation.Phase89ProductionFreeze -v
& $hostPython -B -m unittest tests.test_presentation_configuration_bootstrap.PresentationBootstrapBoundaryTests tests.test_presentation_configuration_document.PresentationDocumentBoundaryTests tests.test_presentation_configuration_persistence.PresentationPersistenceBoundaryTests tests.test_presentation_configuration_service.PresentationServiceBoundaryTests tests.test_presentation_configuration_view.PresentationViewBoundaryTests tests.test_presentation_identity_contracts.PresentationBoundaryTests tests.test_provider_connection_composition.Phase86ProductionScopeGuards tests.test_provider_connection_service.Phase85ScopeGuards tests.test_provider_connection_startup.Phase87FrozenProductionScope tests.test_windows_credential_backend.ScopeGuards -v
```

These selections avoid the unrelated isolated-subprocess cache generator; they
do not alter or suppress it. Record actual native counts/exits and fresh ignored
inventory. Any full-suite/compileall/seal-time orchestration remains separately
controlled; this request explicitly forbids another full suite here.

**Disposition: SOURCE CANDIDATE READY FOR INDEPENDENT READ-ONLY REVIEW; HOLD for
host runtime/gate proof, regression closure and independent security verdict.**
For this R2 checkpoint, review exact 16 pins and three historical migrations, including true consumed
faults, before any staging/seal. No staging, commit, tag, push, original checkout,
Drive, dashboard, live service, provider, credential or PRC action was performed.


### R3 isolated A-02 child bytecode hygiene and successor manifest

A later root-cause investigation confirmed that the original A-02 subprocess
used python -I -c, which ignores environment-only Python bytecode controls
(PYTHONDONTWRITEBYTECODE, PYTHONPYCACHEPREFIX) and produced 24 ignored
CPython cache artifacts in the first full suite. The single reviewed hygiene
repair adds -B to that isolated child command (python -I -B -c), preserving
its import/network/native poison assertions and exact success marker.

A new adversarial 8.37 integrity test actually invokes the original A-02 child,
verifies its one real subprocess.run call uses -I -B -c, and requires an
empty ignored Git inventory afterwards. The whole-tree guard remains strictly
fail-closed for all ignored files, with no cache exception, waiver or skip.

The current 8.37 successor allowlist therefore supersedes the historical R2
16-path checkpoint: exactly 17 paths (9 ADD / 8 MODIFY), including
tests/test_pre_829_a02_fake_isolation.py as the sole additional modified
historical test. The manifest pins all 17 raw source/test/document bytes with
its unique normalized self-pin. All 8.30-8.36 historical Git seals and
adversarial assertions remain active. Independent Codex R3 SOURCE_GO reported
no unresolved HIGH or MEDIUM finding; full Windows regression and release
gates remain separately required and must not be inferred from static review.


### R5 historical 8.34 replay preservation, 23 October 2026

The R4 full run revealed new failures in the old 8.34 synthetic LEGACY
and partial-stage fixtures after 8.37 updated the A-02 fake-only isolated
subprocess test. The frozen 8.34 body correctly refuses that newer A-02
file against its earlier 8.33 checkpoint blob. Only the historical
synthetic candidate fixture now provides the genuine 8.33 Git blob for
exactly tests/test_pre_829_a02_fake_isolation.py when proving old 8.34
behaviour; all other frozen readers remain real and untouched. An added
adversarial test corrupts that genuine historical blob and requires the
original full historical integrity body to reject it. The 8.37 live
whole-tree guard is NOT patched, waived, or replaced; it continues to
check the actual current 8.37 A-02 bytes, every frozen blob and index.
The successor's scope expands to exactly 18 files (9 ADD, 9 MODIFY)
by adding only tests/test_phase_834_scope_integrity.py as a modified
historical test. Full original and repaired regression/independent
security review remain mandatory before release. No tests are skipped.


### R6 historical 8.32/8.33 replay preservation, 23 October 2026

The R5 pre-stage full run was stopped after definitive historical 8.30-8.33
failures; it was NOT a pass. Direct native Windows diagnostics showed the
8.32/8.33 synthetic checkpoint readers rejected the newer 8.37 A-02 file as
a frozen tracked-worktree mutation. Only explicit synthetic historical
fixtures now supply the genuine immutable 8.32 A-02 Git blob. The original
8.32/8.33 historical integrity bodies still execute unmodified, and new
adversarial tests corrupt the frozen A-02 evidence and require fail-closed
rejection. The actual 8.37 live guard remains unpatched and reads current
disk bytes. Scope is exactly 20 files (9 ADD / 11 MODIFY), including both
historical test modules. The mandatory 23 October impact-inventory gate
requires ALL direct, historical and cross-phase affected modules to pass on
these exact bytes before any new full regression; previous R5 results are
stale. This documentation is not a waiver or release approval.
