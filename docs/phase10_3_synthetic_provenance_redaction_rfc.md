# Phase 10.3: content-free synthetic provenance and redaction

Date: 2026-11-04. **TEST-ONLY SOURCE CANDIDATE / UNTESTED / RELEASE HOLD.**

This is an inert test experiment. Its public operations return fixed status
enums only. They do not return a grid, projection, artifact, receipt accessor,
content handle, callback, publication or permission. Private harness setup
keeps opaque receipt handles and synthetic matrices inside test code.
No production source changes are included.

## Authority and historical release verification

The original bounded implementation review is
`D:\Nayeon\phase10_3_final_scope_review_result_20261104.md`:
RETROSPECTIVE_EVIDENCE=GO, EXACT_SOURCE_ENVELOPE=GO, MATERIAL_FINDINGS=0,
AUTHORISE_BOUNDED_IMPLEMENTATION=YES. It approves bounded implementation,
not tested source or release. The exact scope proposal is
`D:\Nayeon\phase10_3_exact_source_scope_proposal_20261104.md`; the design is
`D:\Nayeon\phase10_3_design_candidate_v2_20261104.md`, independently accepted
in `D:\Nayeon\phase10_3_design_rereview_result_20261104.md`.

The controlling 4 November scope reduction amendment is
`D:\Nayeon\phase10_3_scope_reduction_amendment_20261104.md`, independently
approved by `D:\Nayeon\phase10_3_scope_reduction_review_result_20261104.md`:
SCOPE_REDUCTION_AMENDMENT=GO, SOURCE_ENVELOPE=6_ADDED_5_MODIFIED,
MATERIAL_FINDINGS=0, AUTHORISE_FOCUSED_SOURCE_FINISH=YES. The exact candidate
envelope is six additions plus eight modifications, fourteen paths total.
This approves only the focused source finish and literal pinning; independent
final-source assurance, native validation and release remain HOLD.

The protected `.codex/CURRENT_STATE.md` is untouched after sandbox access
denial, excluded from the candidate manifest and retained in the complete
sealed historical inventory. Its raw SHA256 remains
`5775c68f8d0428004de85c9a2695fd7d06ea8bb98d3e8dbbfdf2fe647e8373a1`.
Its historically stale HOLD text is preserved byte-for-byte and superseded
for current Phase10.2/10.3 status by this dated RFC and the sealed Git evidence
below. No protected-file write retry, permission change or alternative write
channel is authorized. This substitution is explicitly covered by the
independent amendment GO; Phase10.3 remains TEST-ONLY, UNTESTED, RELEASE HOLD,
with no real capture consent or provenance.

The immutable predecessor is Phase10.2 commit
`4aff3459ee127b0a7a124073aac2a9317e467301`, parent
`be6c126dc5f3a6814925bb95009ef2b2e6be80b7`, tree
`8f2054624120816d435b2cb567ef770759a3669f`, annotated tag
`nayeon-v1-phase-10-2-trusted-perception-privacy-01`, tag object
`443b247b89b7fb5b749b0f938b98070339018863`.
The predecessor has 456 tracked files and its original 14-path manifest.
Git supersedes the historically stale HOLD entries in its state file.

Historical release evidence is recorded in
`D:\Nayeon\phase10_3_prephase_retrospective_20261104.md` and its addendum:
three native Windows regressions, each 3165/3165 PASS with exit 0, on
COMPLETE_UNSTAGED, EXACT_STAGED and EXACT_CHILD. The preserved log SHA256s are:

| Historical run | SHA256 |
| --- | --- |
| FULL1 | `f3de8c1880a4c5305a5bb97b3c17c8bdb9d5e4040fe317378bdd05e2736342ad` |
| FULL2 | `5681064c879c03088083196a00d616aa1af2d70bf023bc8f68ca1c87877e8b2f` |
| FULL3 | `cc69476316f70b4ba5d750e0207325ec9d329a421b0056d9a81ca0274fb6298a` |

The cited retrospective records final assurance GO, GitHub publication
verification and connected readback of original same-ID Drive master
`1n0tDiBQCkPWluX6eakRiRfq57tflRW5L`, SHA256
`f0c409a5cecf61ab1a464f4f8cb7846fec95fe9b009a93915fea7d3b16004afd`,
198828 bytes, 16 worksheets. The archive did not contain a VBA binary;
macro-enabled MIME alone is not proof of embedded VBA. These are historical
review/readback records, not a fresh Drive, dashboard or test verification
in this source-only session. Stored process transcripts are not signed OS
attestations. Phase10.2, Phase9, PRC and BYOK C1 worktrees/statuses and every
existing tag remain untouched. No new release claim is made for any of them.

## Architecture

The registry owns its receipt identities, source identity and registry
instance identity. A private issued record binds exact request/session IDs,
source/purpose enums, target ID, operation instance, fixture ID, source and
observation generations and policy version. A caller-created receipt, copied
text, foreign registry handle or restarted instance cannot establish local
membership. The source registry attests only to its own synthetic origin.

Each owned record moves from ISSUED to CONSUMED or INVALIDATED. Verification
burns the record before checking scope or oracle output. Source replacement,
explicit invalidation and close clear pending scope/proposal references and
retain tombstones. Neither terminal state can be revived. All records count
toward the fixed 32-record lifetime cap; no eviction or recycled proof exists.
Source and observation generations are bounded by 256. Source saturation
closes the registry; receipt/observation saturation denies issuance.
Requests remain reserved for the registry lifetime, including across source
replacement. Reference removal does not promise Python memory zeroization.

The registry uses a local lock and invokes no caller callbacks. It has no
joint lock, clock, atomic completion or attestation contract with the existing
permission ledger. `SyntheticPermissionModel.complete()` is byte-unchanged
and remains a fake transition to USED returning True. Neither its success nor
an independently consumed fixture receipt proves a combined permission,
provenance and redaction transaction. Ledger expiry equality, rollback,
reentrant terminal transitions and close/completion races have separate
test-source assertions; these have not been executed here.

The private generator produces only hardcoded immutable ASCII tuple matrices:
1x1, 2x3 and 16x16 fixtures within the closed 1..16 row/column and 256-cell
bound. Tokens are SAFE_A, SAFE_B, SECRET_A and SECRET_B; output additionally
uses PRIVATE_MASK. The independent oracle imports no generator helpers. It
authors its own complete source, classification and expected-output matrices.
An exact tuple/string type check precedes comparisons. UNKNOWN or malformed
classification, wrong geometry, ragged/missing/extra cells, wrong source and
any positional mismatch deny the entire fixture. An allowlisted safe token
at a sensitive coordinate fails, as do shifted/swapped/duplicated masks.
Producer redaction metadata or a digest never substitutes for this oracle.

Objects containing private harness state hide str/repr and reject pickle,
copy and deepcopy with fixed errors. The registry and oracle emit no logs.
Public statuses and diagnostics contain no fixture data, user text, IDs,
hashes, coordinates, counts or receipts. Tests inspect representations,
logging arguments and formatted/chained serialization errors for inert
canaries. This does not protect against arbitrary Python introspection,
reflection, monkeypatching or a malicious trusted fixture reading/logging
its own memory. There is no claim of OS attestation or production privacy.

## Exact source admission and historical readers

The successor is restricted to branch
`phase10-3-synthetic-provenance-redaction-20261104` and the sealed predecessor
or exactly one direct child. The new gate authenticates raw annotated tag,
commit and full 456-file tree; reconstructs older private historical evidence;
checks all original Phase10.2 normalized pins plus its raw guard SHA256; then
checks the literal fourteen-path candidate manifest. It rejects partial staging,
forged modes/blobs/raw deltas, wrong refs/parents, aliases, ignored/extra
untracked paths, links/reparse points and hardlinks. A second disk/index/raw
proof and final ref checks reject observed read-window drift. It is a read-only
proof over observations, not an atomic filesystem snapshot or action authority.

Only COMPLETE_UNSTAGED, EXACT_STAGED and EXACT_CHILD are accepted. All other
tracked files must retain predecessor blob identity. The old Phase10.2 guard
is an exact byte prefix with a saved private alias and an unconditional public
route appended. The new gate calls no public predecessor admission and has no
historical fallback. Some exact Phase10.2 refusal strings remain deliberately
unchanged to preserve older adversaries' causal contracts. The protected state
file retains its entire sealed bytes and is checked as frozen historical source.
Only the new gate's own literal pin
is normalized once; live admission never computes replacement approval pins.

The 29 existing direct-reader paths have these bounded dispositions (paths
below are relative to `tests/`):

| Reader | Disposition |
| --- | --- |
| phase10_2_privacy_scope_migration.py | Append-only current route; immutable original private witness |
| phase10_perception_scope_migration.py | Unchanged public delegation and historical helpers |
| phase8_byok_b_scope_migration.py | Unchanged public delegation and historical helpers |
| phase_8_30_scope_migration.py | Unchanged exact production projection and delta adapter |
| test_phase10_2_privacy_scope_integrity.py | Only historical delta method gets authenticated sealed fixture; live proof before/after |
| test_phase10_perception_scope_integrity.py | Only current reader/tamper method uses fourteen-path live scope |
| test_phase_836_scope_integrity.py | Only live method uses new parent/gate; historical identity preserved |
| test_phase_837_scope_integrity.py | Only live method section uses new parent/gate; historical identity preserved |
| test_phase8_byok_b_scope_integrity.py | Unchanged historical fixtures and current disk-reader canary |
| test_phase8_byok_scope_integrity.py | Unchanged historical replay and exact branch/tag/source injections |
| test_phase_830_scope_integrity.py | Unchanged staged-entrypoint and second-tree historical injections |
| test_phase_831_scope_integrity.py | Unchanged historical/current delegation canaries |
| test_phase_832_scope_integrity.py | Unchanged historical fixtures and live reader |
| test_phase_833_scope_integrity.py | Unchanged historical fixtures and live reader |
| test_phase_834_scope_integrity.py | Unchanged historical fixtures and live reader |
| test_computer_control_v1_freeze.py | Unchanged current public admission |
| test_connection_reconciliation.py | Unchanged current public admission |
| test_bound_credential_lifecycle.py | Unchanged current public admission |
| test_credential_onboarding_composition.py | Unchanged current public admission |
| test_openai_canonical_client.py | Unchanged current public admission |
| test_presentation_configuration_bootstrap.py | Unchanged current admission/projection |
| test_presentation_configuration_persistence.py | Unchanged current admission/projection |
| test_presentation_configuration_view.py | Unchanged current admission/projection |
| test_presentation_identity_contracts.py | Unchanged current admission/projection |
| test_presentation_configuration_service.py | Unchanged current admission/projection |
| test_provider_connection_composition.py | Unchanged current public admission |
| test_provider_connection_service.py | Unchanged current public admission |
| test_provider_connection_startup.py | Unchanged current public admission |
| test_windows_credential_backend.py | Unchanged current public admission |

The explicit historical test fixture authenticates every byte from the sealed
Phase10.2 tree before installing simulated index/delta/disk seams. It uses the
original 14-file pins without replacement and the original private verifier.
It models the original production pair tracked plus permission source untracked
in COMPLETE_UNSTAGED, and all three tracked in staged/child states. Historical
fixture admission cannot admit current source. Live acceptance brackets this
fixture; injected frozen reads must be reached and refused, then positives
restored. New topology parser fixtures are clearly fictional and cannot stand
in for live native admission. No excluded negative test is edited or skipped.

## Open Failures & Prior-Issues Review

Controlling process: [engineering failure review gate](engineering_failure_review_gate.md).
Issue-level evidence, dates and review dispositions come from the 4 November
retrospective/addendum and final scope review above. Historical closure is
limited to the sealed synthetic implementation.

| Issue / severity | Cause, affected boundary and repair | Evidence and disposition |
| --- | --- | --- |
| P10.2-REPLAY / HIGH | Cross-session request reuse; ledger-lifetime reservation before TTL/clock after genuine fake approval | permissions.py + original ledger adversaries; final prototype/release GO and historical three full runs; CLOSED for sealed fake ledger |
| P10.2-REENTRANCY / HIGH | Clock callback invalidated issue scope; post-clock generation/closure recheck under lock | Original source/replay tests and final assurance; CLOSED for sealed fake ledger |
| P10.2-STATE-REENTRANT / MEDIUM | synthetic_state overwrote callback terminal state with EXPIRED; recheck state after callback | phase10_2_source_rereview.md and phase10_2_final_prototype_review.md; CLOSED, terminal-state adversaries retained |
| P10.2-DELTA / MEDIUM | Partial tracked/untracked view confused inventory projection; exact authenticated Git-view adapter | Original migration/parser tests and final-source GO; CLOSED historically; native successor canaries OPEN |
| P10.2-HIST-830 / MEDIUM | First full run failed two obsolete negative error assertions despite actual rejection; exact reviewed causal repair | phase10_2_full1_historical_830_final_source_review.md; later three full runs; CLOSED historically; seven excluded test files untouched |
| P10.2-RECEIPT / MEDIUM | Missing native exit transcripts in first assurance; preserved receipts supplied with explicit limits | phase10_2_three_full_native_process_receipts_20261104.txt and final_release_assurance_R2; CLOSED historically |
| P10.2-STATUS / LOW | Stale protected state HOLD text versus sealed Git and same-ID Drive readback | Dated RFC supersession explicitly approved by independent scope reduction amendment GO; protected state untouched and frozen; source change UNTESTED |
| P10.3-STATE-WRITE / environment constraint | Protected state write denied by sandbox; candidate initially unpinned | Independent amendment GO removes state from candidate, retains sealed historical checks and authorizes only three already-added source edits and literal pinning; no retry or permission change; native validation OPEN |
| P10.3-SOURCE-ENVELOPE / HIGH | Current-vs-historical reader ambiguity | Final scope review explicitly GO, zero material findings; bounded source implementation authorized; final source review remains OPEN |
| P10.3-EXECUTION / environment constraint | Previous sandbox could not access host Python | No retry, install, process inspection or sandbox expansion; native workflow owns all validation; HOLD for release |

Historical assurance limitations remain explicit: the original close/complete
test did not correlate return value with state, its capacity test covered
policy capacity, and its AST effect lint had bounded alias detection. The new
source adds correlated registry and ledger race assertions and genuine consumed
and invalidated tombstone-capacity assertions. These are proposed tests, not
executed evidence or proof that older product vulnerabilities existed.

Disposition: **GO for this authorized source-only slice; HOLD for validated
source and release.** No unknown material failure has been waived. Any native
failure requiring another path stops the workflow for a named scope amendment.

## Native handoff and remaining gates

Exactly six additions and eight modifications (fourteen paths) are permitted; no production,
other worktree, Git index, commit or tag change is part of this session.
All Python execution, interpreter lint, compileall and tests are deliberately
NOT RUN. Static source review and byte pinning do not establish syntax/runtime
success. There is no new production or capture evidence.

The separate authorized native host workflow must first run new focused tests,
historical/current admission canaries (including the seven excluded files),
then affected/trust-path suites. Resolve every failure causally before full
regressions. Independent final-source review, all three native full regression
topologies, compileall, exact staging, seal review, one child commit, immutable
annotated tag, separately approved push/remote verification and original same-ID
workbook/dashboard reconciliation remain OPEN. No source pins may be silently
updated to hide a failed canary or scope expansion.

Phase10 major remains IN PROGRESS; verified real-consumer acceptance is 0/12.
On 4 November, independent source-security review identified a post-import
self-pin literal tamper gap. The scoped fix compares the on-disk literal
against the approved in-memory pin before normalized hashing and adds an
adversarial cached-import test. This source change remains RELEASE HOLD
until native canaries and independent re-review approve it. There is
no screen/camera capture, real consent, platform permission, provider/BYOK,
credential access, network, real image redaction or autonomous action. Preserve
Permission -> Policy -> Confirmation -> Execution -> Verification. Model claims
and synthetic fixture statuses confer no machine authority.

## 4 November historical reader canary amendment - RELEASE HOLD

Previously approved 6 additions + 5 modifications remain authentic intermediate
evidence. Native 8.32, 8.33, 8.34 canaries initially failed at a strict
one-read count: Phase10.3 intentionally checks every frozen file twice
before admitting source, so those three historical live-reader tests saw
two genuine read calls. An independent exact-scope amendment authorized
three narrowly modified legacy test methods only; each now proves exactly two
clean reads and injects a forged second read requiring exact source refusal.
The current new gate binds all fourteen paths literally and remains
synthetic-only. This source revision is HOLD pending native canary replay,
full 14-path source review, mandatory full regressions and final release gates.
Verified real end-user perception acceptance remains 0/12.
