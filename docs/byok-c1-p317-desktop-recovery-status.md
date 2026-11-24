# BYOK C1 P317 desktop recovery status: source-only follow-up

Date: 2026-11-24. Parent: `ed769a2f472cbaecc2c2df3fff9deea606c36036`.
Branch: `byok-c1-p317-desktop-recovery-status-20261124`.
Codex is the sole source writer. Production/release HOLD; hosted validation and independent review pending. This is the explicitly authorized text-only successor test scope amendment, not security approval or release.

Changed paths:

- `nayeon/desktop_alpha/local_byok_window.py`: ordinary display text only in native observation and synthetic denial polling. Unavailable status states cause unknown instead of suggesting an expected ACL cause. Fixed denial is explicitly untrusted, with no attested peer. Both outcomes state that no recovery state is verified, retain release HOLD/no keys or approval, prohibit credential entry or retry, and direct the user to qualified service recovery review.
- `tests/test_byok_c1_p317_desktop_recovery_status.py`: keep the five reviewed deterministic cases using existing inert P308 UI/clock/thread helpers, with observer/requester methods replaced and native transport/credential access blocked. Cases cover unavailable status, fixed denial, worker exception, thread-start failure, and deadline/late-result guidance. Add a separate exact-source successor helper and negative source fixtures. These are authored source cases, not executed evidence.
- `tests/test_byok_c1_p310_native_synthetic_request.py`: amend only `test_existing_ui_methods_frozen_ast_and_only_button_calls_new_handler` as detailed below; all other P310 tests and transport source remain unchanged.
- `.github/workflows/p317-windows-desktop-recovery-status.yml`: new bounded, hosted Windows-2022 draft-only fake-class workflow; authored only, not published or run here.
- `docs/byok-c1-p317-desktop-recovery-status.md`: this scope and pending-validation record.

Exact candidate envelope: two modifications and three additions, five paths total. Routing, observer/requester implementations, deadlines, polling, buttons and authority are unchanged. No other product source changes. No service, credential, provider or network operations, interpreter access/probe/execution, test execution, compilation, sandbox changes, staging, commit, push, merge, workbook or dashboard updates are performed here. The workflow is source for later hosted validation only; publication/execution is outside this task.

## Open Failures & Prior-Issues Review

Bounded inputs: supplied P317 task/parent and previous host-Python sandbox refusal; current Git status; relevant UI polling and P308/P310 fake harness/test slices; P316 recovery-boundary review; engineering failure gate; direct UI-path guard references only. Git HEAD matches the supplied P316 base. This reconciliation began with the three reviewed candidate paths already present. `.codex/CURRENT_STATE.md` predates this branch; it is preserved and is not a current P317 baseline. No earlier broad investigation was rerun.

| Issue | Evidence / cause | Containment / disposition |
| --- | --- | --- |
| P96 HIGH OPEN | No reproduced closure or root-cause evidence supplied by this task | Unchanged; no custody/effect repair claimed; HOLD |
| P292 UNKNOWN | SCM teardown qualification remains unproven | Unchanged; no service invocation or teardown work; HOLD |
| Misleading unavailable display | UI attributes unavailable status to expected service-only ACL without evidence of cause | Display-only correction; no recovery state or diagnosis verified; source review and runtime validation pending |
| Previous sandbox refusal | Supplied previous task stopped accessing host Python | No retry, probe, alternate interpreter or sandbox change; runtime validation pending |
| Historical P310 AST freeze | Original current-UI comparison includes the two changed display expressions | Explicit successor scope amendment retains the original P309/P310 AST comparison on immutable historical source, plus exact P316 successor equality; authored only, independent review and runtime evidence pending |
| Older guard conflicts | P264 `test_frozen_raw_bytes` pins the entire live UI to SHA-256 `55EA8B1C9EAF4179725127B36B0A7B0D7342ADCD860FEDC854C330A7926346BA`; candidate raw UI is `98562073D6F27E3798721BF894C6779436F257018326644DAF355FF74AD393DF`. P133/P134/P140 have older exact-scope/committed-blob expectations | Reported source conflicts, not executed failures or newly established root causes. All remain unchanged; no full-suite compatibility claim, scope widening or waiver. Review remains open before any milestone |

Disposition: production/release HOLD. This follow-up does not start or seal a new architecture phase, close prior findings, or verify recovery. P96 HIGH/P292 UNKNOWN remain unresolved. No real keys are used or authorized. Green focused hosted results, if obtained later, cannot close those findings or the older guard conflicts.

## Historical witness and exact successor amendment

The original P309 witness is still `adff32e2978c7dd21fb3c10f9a8805e555d5c41f:nayeon/desktop_alpha/local_byok_window.py`. The unchanged AST comparison, original synthetic-node filtering, and all original assertions now compare it with the historical P310 UI at immutable commit `97e1f57d0e5dbd1f96228615d13598a3de775409`. Existing live constructor/main inspection assertions remain. No historical tag or commit is moved. This preserves the original P310 proof rather than stripping string constants from its AST.

Separately, current UI must equal `ed769a2f472cbaecc2c2df3fff9deea606c36036:nayeon/desktop_alpha/local_byok_window.py` with precisely the two literal `DISPLAY_SUBSTITUTIONS`: the complete native-status conditional display expression and the complete synthetic-status conditional display expression. Each original must occur exactly once in the baseline and zero times in current source; each replacement must occur zero times in the baseline and exactly once in current source. Full resulting source equality rejects every unrelated change, including other strings, code, comments and spacing. The normal UTF-8 text reader handles checkout line endings; there is no generic string stripping or AST constant normalization. Missing Git witnesses fail without fallback.

Negative fixtures cover neither/one substitution, removed or duplicated expressions, changed guidance, a changed deadline, a changed main signature, an unrelated comment, and missing/duplicated originals or preexisting replacements in the supplied baseline. The five original fake UI cases remain intact. Static Git inspection found no UI or P310-test delta between the pinned historical P310 commit and P316 base; this observation is not execution of the historical AST witness.

The direct P308/P310 affected guards were read narrowly. Their forbidden-route/source assertions, fixed transport pins, enum/outcome substring expectations, deadlines and no-authority checks are retained. No additional conflict was identified in those selected class sources. Older whole-source/exact-branch conflicts are recorded above and have not been weakened or added to the focused run.

## Hosted test scope (authored, not executed)

The workflow accepts only a same-repository draft PR in `krismcan/Mark-LV` (repository ID `1402212689`), exact head `byok-c1-p317-desktop-recovery-status-20261124`, exact base `byok-c1-p316-service-recovery-boundary-20261124`, and base SHA `ed769a2f472cbaecc2c2df3fff9deea606c36036`. It uses SHA-pinned checkout of the event head without persisted credentials, requires base ancestry and exactly the five paths/statuses listed above, and checks input hashes, HEAD and clean index/worktree before/after. Only normal checkout can download source; no setup/install/download step or credential/service operation is included.

One installed Python 3.12 x64 runs on hosted Windows-2022, with a five-minute job bound, 90-second child bound, bounded cleanup and output drain. Absence of installed Python fails closed. It runs exactly:

- P317 `RecoveryStatusDisplayTests` (the five retained fake cases) and `SourceSuccessorTests` (the added source fixture case), through the P317 module selector.
- P308 `ObserverTests`, `UIRoutingTests`, `SourceBoundaryTests`.
- P310 `RequesterTests`, `SyntheticUITests`, `SourceBoundaryTests`.

There is no discovery, full regression, compileall, real Tk window, service build or OS-pipe test. Both `DisposableWindowsPipeTests` classes and all credential API integration suites are excluded. The selected P310 invalid-endpoint child check rejects before any OS call. Native transport imports are blocked outside the existing inert fake overrides; DLL loaders and native credential loading are blocked. `subprocess` is preimported before blocking `_winapi` so read-only Git witness subprocesses retain their standard Windows implementation. Failure, skip or zero tests refuses the focused result. This scope does not qualify x86 SCM teardown or recovery and grants no security/release approval.

## Validation pending

Verification here is source inspection and `git diff --check` only, including untracked-file whitespace checks. Runtime tests, hosted workflow execution, affected/cross-phase/full regressions, compile checks, visual layout validation and independent review remain pending. No interpreter path is accessed, probed or executed. No verified milestone or test PASS is claimed.

Whitespace verification reported no errors: tracked changes use `git diff --check`; the three new untracked files use `git diff --no-index --check` against `/dev/null`. A no-index difference exit is not runtime validation. The product diff contains only display string changes in the two polling methods.
