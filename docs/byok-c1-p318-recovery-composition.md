# BYOK C1 P318: paired synthetic first-run recovery presentation

2026-11-24. OM v2.1; Codex sole source writer. Exact parent
`34b97a0a457d5012809daacaec5d5f289dba3569`, branch
`byok-c1-p318-recovery-presentation-20261124`; clean intake, no tag at HEAD.
CURRENT_STATE is stale and unchanged. User-supplied hosted evidence: P317
68/68 PASS, run `45444468729`; P316 4/4 PASS. Neither was rerun here.
**Source candidate only. Full regressions 0/3; production/release HOLD.**

## Missing composition and bounded change

`pending_credential_recovery_document` already rejects malformed structural
evidence and explicitly disclaims authentication, rollback protection and
retry safety. `pending_custody_status_view` already validates canonical
advisory decisions and fixes every authority/verification flag false. Neither
needs another model or codec change. However, `summarize_first_run` only takes
legacy connection observations and can suggest CONNECT, validation, replacement
or removal without considering the separately presented pending-custody claim.

The new pure `summarize_pending_custody_first_run` composes an exact existing
custody view with the existing first-run summary. Missing, wrong-type or
cross-display inputs raise; there is no legacy fallback. Every valid claim,
including claimed absence, returns `REVIEW_UNKNOWN_STATE`, no suggested
operations, reobservation required and no execution authority. It preserves
the legacy display as a hint, never as verified recovery. Repeated identical
inputs cannot progress the state or schedule retry/replay. Matching display
states do not establish freshness, provenance or recovery clearance.

The same checkpoint now consumes this composer through an explicit
`FirstRunReadOnlyController(observe_paired_synthetic=...)` mode and the existing
`FirstRunStatusWindow`. No live host mounts this mode. Legacy `observe=...`
callers and the legacy summary API retain their behavior, including the old
recursive-observation outcome. The modes are mutually exclusive and require
a callable; construction calls neither callback. No new observation, summary,
custody or refresh model is introduced.

Each explicit non-reentrant paired refresh invokes its one injected callback
once. It must return an exact two-item tuple of the existing exact
`ConnectionObservation` and `PendingCustodyStatusView`. The controller checks
both models' existing invariants again, then composes the matching display
states. Missing, malformed, wrong-type, cross-display or exceptional input
returns UNAVAILABLE with no summary. A nested refresh returns UNAVAILABLE
without calling the observer and also invalidates the outer paired refresh,
even when its callback returns a valid pair. No retry, cached observation,
legacy fallback or operation callback exists. The next explicit refresh starts
independently. Repeated matching synthetic claims remain unverified; neither
tuple pairing nor matching enums proves freshness or provenance.

The paired panel shows `Manual unknown-state review required`, explicitly
states `Recovery is unverified` and suggests no credential operation. It never
presents the preserved legacy hint as readiness. On unavailable input both
labels replace prior display data and retain manual review/unverified recovery
guidance. Its only button remains Refresh status. Actual observation/provenance,
live composition and lifecycle qualification remain separate HOLD obligations.
Journal bytes must never become readiness proof.

Final changed paths (five modifications, three additions; eight paths total):

- `nayeon/brain/first_run_summary.py`: existing models plus the pure composer.
- `tests/test_first_run_summary.py`: extend only the exact import allowlist for
  the existing pure custody-view dependency, with rationale; retain every
  behavioral assertion.
- `nayeon/brain/first_run_refresh.py`: explicit mutually exclusive paired
  synthetic callback, model checks and fail-closed reentrancy latch; legacy
  observation behavior retained.
- `nayeon/desktop_alpha/first_run_status_window.py`: paired-mode manual review
  and unverified recovery presentation, including unavailable results.
- `tests/test_first_run_refresh.py`: only its exact import allowlist gains the
  existing pure custody-view model, with rationale; all six old behavioral and
  boundary tests remain intact. No host/transport import is admitted.
- `tests/test_byok_c1_p318_recovery_composition.py`: original four authored pure
  cases: 63 status/claim/action combinations, removal of legacy suggestions,
  missing/spoofed/cross-status rejection and repeated/immutable claims.
  Six added deterministic real-controller-to-fake-panel cases cover inert
  construction/exclusive modes, every connection status and custody state,
  missing/malformed/forged/mismatched pairs after a valid display, exception
  sanitization, nested/outer rejection and a later explicit refresh, repeated
  stale claims without promotion, no retry, no live observation or action UI.
- `.github/workflows/p318-windows-recovery-presentation.yml`: one draft-only
  Windows-2022 validation workflow, source only; exact scope below.
- `docs/byok-c1-p318-recovery-composition.md`: this record.

## Open Failures & Prior-Issues Review

Narrow inputs: failure gate, stale state, exact Git intake, P316/P317 reviews,
the two requested modules, first-run summary/refresh/panel and their relevant
tests; direct old compatibility assertions only. No historical audit rerun.

| Issue | Evidence / boundary | Disposition |
| --- | --- | --- |
| P96 HIGH OPEN | No reproduced closure/root-cause evidence in this scope; custody/effect repair untouched | No closure or independent approval claimed; HOLD |
| P292 UNKNOWN | SCM teardown qualification remains unproven; no service startup/teardown invoked | HOLD |
| Composition gap | Legacy summary suggests operations independently of custody advice; pure overlay now has an explicit paired synthetic controller/panel consumer, suppressing suggestions even for absent claims | Original four pure tests retained plus six fake integration tests authored; runtime and independent review pending |
| Refresh isolation | Separate observations or legacy fallback could mix claims; legacy recursion intentionally permits an outer observed result | One exact pair per call; new-mode nested and outer refresh fail unavailable; no old behavioral assertion changed; adversarial evidence pending |
| Old P264 conflict | `test_frozen_raw_bytes` pins live `local_byok_window.py` to `55EA8B1C9EAF4179725127B36B0A7B0D7342ADCD860FEDC854C330A7926346BA`; P317 records different successor bytes | Inherited source conflict, not a newly executed failure; unchanged/unwaived |
| Old P133 conflict | `test_exact_p132_ancestry_seven_changed_paths_and_clean_diff` expects its historical seven-path delta | Inherited exact-scope conflict; unchanged/unwaived |
| Old P134 conflict | `test_exact_parent_and_four_added_files` expects its historical four additions; frozen-source checks compare committed blobs with P133 | Inherited scope/blob conflict; unchanged/unwaived |
| Old P140 conflict | `test_exact_p139_ancestry_and_approved_six_path_change` expects six historical paths; `test_only_one_existing_product_launch_bridge_changed` freezes its sole modification | Inherited scope conflict; unchanged/unwaived |

User authorization covers this same-checkpoint bounded source follow-up only;
it does not close the failure gate or approve release. Release HOLD, full
regressions 0/3 and independent review pending. Focused P317/P316 supplied
passes do not waive these findings or qualify this new source.

## Hosted validation scope (authored, not executed)

The single workflow follows P317's event, checkout, installed-runtime and
bounded-child structure. It admits only same-repository draft pull requests in
`krismcan/Mark-LV` (repository ID `1402212689`), exact head
`byok-c1-p318-recovery-presentation-20261124`, exact base
`byok-c1-p317-desktop-recovery-status-20261124` at
`34b97a0a457d5012809daacaec5d5f289dba3569`. Checkout is SHA-pinned to
`actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`, checks out the
event head, persists no credentials and enables neither LFS nor submodules.
Head identity, base ancestry, the exact eight paths with five M / three A
statuses, whitespace, clean index/worktree including ignored files, source
hashes and unchanged HEAD are checked. No other delta is admitted.

Only an already installed Python 3.12 x64 in the hosted tool cache is used;
absence fails without installation/download. The job is bounded at five
minutes, its single child at 90 seconds, with bounded cleanup/output drain.
There is no discovery, compileall, full suite, real Tk or native test. These
explicit class selectors contain 33 authored cases, verified fake/pure by
source inspection only:

- `tests.test_byok_c1_p318_recovery_composition.RecoveryCompositionTests`
- `tests.test_byok_c1_p318_recovery_composition.PairedSyntheticPanelTests`
- `tests.test_first_run_summary.FirstRunSummaryTests`
- `tests.test_first_run_refresh.FirstRunRefreshTests`
- `tests.test_first_run_status_window.FirstRunStatusWindowTests`
- `tests.test_pending_custody_status_view.PendingCustodyProjectionTests`

The retained modules construct typed enum/dataclass claims and inspect source;
the status-panel tests replace Label/Button with inert widgets and use Mock
roots. They never construct a Tk root or observe a credential. Their reached
model dependencies and metadata module imports were read narrowly: persistence,
bootstrap and credential contracts define functions/types without performing
profile/credential I/O at import. Selected tests do not call persistence or
bootstrap. The workflow additionally blocks real Tk creation, DLL loaders,
native credential-module import, metadata bootstrap/load/save, `_winapi`,
socket/network, registry and subprocess/native-loader audit events during the
test child. Recorded forbidden attempts fail even if a controller catches the
exception. Importing Tk definitions is not creating or mounting a native UI.
Nonzero exit, loader errors, failed tests, skips, a count other than 33 or a
recorded forbidden attempt rejects validation. Only normal checkout uses the
network; there are no setup, package, service, credential or API steps. Source
hash/HEAD/cleanliness checks run after the child as well. This workflow has not
been published, executed or independently reviewed.

## Validation and boundaries

Source inspection and `git diff --check` only, including no-index whitespace
checks for the three additions. No runtime PASS, compile, independent review or
milestone is claimed. No interpreter access/probe/execution, profile or
credential access, OS/service/IPC/provider operations, network operation,
protected-journal change, sandbox change, staging, commit, push, merge, workbook
or dashboard update. No refusal or new material safety issue was encountered.

Whitespace check outcome: tracked `git diff --check` exited 0 with no
diagnostics. Each of the three untracked additions was checked using
`git diff --no-index --check -- /dev/null <path>`; each exited 1 for the new-file
difference with no whitespace diagnostics. This is source hygiene only,
not runtime or hosted evidence. Full regressions remain 0/3; release HOLD.
