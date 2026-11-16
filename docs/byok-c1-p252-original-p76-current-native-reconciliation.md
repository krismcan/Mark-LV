# P252 original P76 current Windows reconciliation

16 November 2026. OM v2.1. DRAFT; initial independent review GO_DRAFT_ONLY; remediation rereview pending. HOLD.

## Source identity and exact scope

Initial checkout was clean (empty `git status --porcelain=v1`). Parent HEAD is
`6e2717f13da253fddbb3c9cbcfdf55e124d6f8ac`, tree
`0fb23ea5758c925cda403b231f419ca8f799d0c9`, branch
`byok-c1-p252-original-p76-current-native-reconciliation-20261116`.
`git tag --points-at HEAD` returned no tags. Recent ancestry is P251, P250,
P249, P248. `.codex/CURRENT_STATE.md` has a stale 3 November Phase 10.2 header;
Git and the explicit P252 assignment govern this diagnostic. That file is unchanged.
This is neither a new product phase nor a historical acceptance repair.

Exactly three new, untracked files; no tracked source/index changes. The following hashes and 17-test count describe the INITIAL runner/test bytes only, not the remediated additions:

| Initial precommit path | Historical purpose | Original raw SHA256 |
| --- | --- | --- |
| `scripts/p252_current_original_p76_native_reconciliation.py` | Stdlib bounded exact-source runner | `cb3063e87379040cd9e2619efff8463250be8c130522b98f53b0475a1efe68a7` |
| `tests/test_p252_current_original_p76_native_reconciliation.py` | 17 effect-free synthetic/mocked tests | `8e66b862fa85a650f4f3614783d096f2769b8e566b84b8e8cacdda94731ba54f` |
| This document | Native reconciliation and decision request | Self-hash omitted; no recursive pin |

The original precommit runner permitted only these exact three untracked additions after the initial
clean checkout; every tracked raw blob must still equal the exact parent tree.
That original version rejects other dirty/ignored paths, hidden index flags, wrong root/HEAD/tree/
branch, source drift, links/reparse points, hardlinked tracked files, shallow
history, replacement refs and grafts. It has no root, method, branch, outcome or
authorization override. This additive envelope is explicitly distinct from an
entirely clean checkout: it does not pretend the three new files are absent.

## Original inventory and safety assessment before execution

AST inspection confirmed four methods in **two** real original modules, not four
separate original test modules. The exact original identities are:

1. M1: `tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay` (451–468).
2. M2: `tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected` (406–427).
3. M3: `tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission` (138–149).
4. M4: `tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route` (309–353).

Raw original B test SHA256:
`65dad89298a587d6bb5dde5455df4d701bb1a1fd9a7a96cecf3e647800e3ae8b`.
Raw original 8.34 test SHA256:
`8dc69ec770ea008dff9cd13e15299a73e38044f1671fd4fe78fbe2a431ccf57a`.
Raw original P76 gate SHA256:
`1c42912d9fc550dea56c9ba9bb70d9568f298223b5514af8d03c1723aaad3327`.
The runner and receipt enumerate all 23 raw-source pins: the 19-file static
local dependency graph (including function-local imports), `tests/__init__.py`,
and the preserved P234/P245/P248 script witnesses. No original is rewritten.

The inspected graph consists of historical test fixtures and source-admission
modules: 8.29 lifecycle, 8.30, 8.31, 8.32, 8.33, 8.34, 8.36, 8.37, BYOK A/B,
Phase10, Phase10.2, Phase10.3, P76, and test modules 8.30/8.32/8.33/8.34/B.
Imports are stdlib or these local test helpers. Source strings naming product
paths are data for disk/Git reads, not production imports. Top-level work is
literal containers, regex compilation, path construction, definitions and
in-memory callable aliases. `tests/test_phase_830_scope_integrity.py` also
installs `_current_approved_source` as an in-memory reader adapter at import.
Its Windows junction/subprocess test is an unselected method, not import-time
work. No selected class has a setup/teardown lifecycle effect. Module-main
`unittest.main()` blocks are inactive when imported by unittest.

M1 and M2 first require live B admission; M3 checks its historical literal
manifest before requiring live B admission. The final public B definition
delegates to Phase10 -> Phase10.2 privacy -> Phase10.3 -> P76. M4 first calls
8.34 -> 8.36 -> final 8.37 definition -> B -> the same chain. In P76, the
first operation is the real branch query. `_git` delegates to the sealed helper
and ultimately `tests/phase_8_30_scope_migration.py`'s `subprocess.check_output`
of `git`, with a 20-second timeout. The checked branch is unequal to the
unaltered literal `byok-c1-p80-sealed-historical-fixture-20261106`.
The subsequent `_baseline`, `_expected`, disk/index proof, historical fixture
factories, brain readers and causal tamper loops are therefore unreachable in
these four executions. The factories themselves use Git/disk source reads and
in-memory mocks; their product-source preimages are never executed here.

Safety disposition before launch: safe for these exact source bytes, selected
methods and early-refusal route. No actual WinCred read/write/delete, native DLL
load, provider construction, network request, GUI input, service/WDAC/policy
mutation or authorization occurs on that route. Source and Git filesystem reads
and child process creation are the intended diagnostic OS effects. This is a
bounded source assessment, not OS isolation, a general effect detector or proof
against a concurrently hostile checkout/installed Python/Git. The exact existing
host Python and Git installations are trusted execution prerequisites.

The runner rejects inherited `P134_*`, `GIT_*` and `PYTHON*` environment keys
without printing their values. Children receive only basic Windows process
environment plus read-only Git controls; credential/provider tokens and all
effect-authorization variables are excluded. No credentials were inspected.

## Genuine Windows-native evidence

Host: Kristian, Windows, native CPython **3.12.10**, MSC v.1943, AMD64, using
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`.
The sandbox could not locate that executable; the explicitly requested native
host orchestration used the existing host interpreter. Nothing was installed,
downloaded, copied, or changed in host policy.

Each original child command was exactly that interpreter followed by
`-B -m unittest <exact-ID-above> -v`, cwd the P252 checkout, stdin null,
shell false, timeout 60 seconds. No branch spoof, unittest wrapper, expected-
failure decorator or replacement fixture was injected. stdout/stderr were opened
as binary files and passed directly to the children, retaining native bytes.

Evidence directory:
`D:\Nayeon\P252_SECURITY_EVIDENCE_20261116\original-20261116T074026-23252`.
All four returned normal native exit **1**, `Ran 1 test`, `FAILED (failures=1)`,
and the exact original branch-refusal exception. No timeout, skip or error was
reported. Durations below include child startup as measured by the runner.

| Original | Result, exit | Duration seconds | stderr raw SHA256 |
| --- | --- | --- | --- |
| M1 | FAIL, 1, unwaived | 0.219 | `4bacba451bbf19133d5934ddf1a519b71819845ad0d74a508cd8e1fbb59c2ac2` |
| M2 | FAIL, 1, unwaived | 0.234 | `7fbe64e9b84a2cdcd0441d71c0880d9d08a1e8683a64479070d56fab07a5af10` |
| M3 | FAIL, 1, unwaived | 0.219 | `8b026718a739c4dde3e3aeb41d7f3f3e2dca4487a1f3898612abd35da492e258` |
| M4 | FAIL, 1, unwaived | 0.234 | `4a1340f25821e937fb9158d6c4e353e5fafba126e7ccecb44e9b10d9a8ef5ff2` |

Files are `m1.stderr.raw` through `m4.stderr.raw`; all four corresponding
`mN.stdout.raw` files are empty, each SHA256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
`receipt.json` SHA256:
`427ccddc4191292926d7986998cdd2651122c5f2c89738cbb5d2c6e0a8238a28`.
The receipt contains full IDs, per-stream hashes, duration, exits, timeout and
failure markers, source pins and runner hash. Runner native exit is **1/HOLD**.
The surrounding PowerShell reporting process exited 0 after displaying
`RUNNER_NATIVE_EXIT=1`; its exit is not substituted for the Python runner or
original child exits.

New focused synthetic tests: **17/17 PASS, native exit 0**, including exact IDs,
AST missing inventory, source drift/closure, immutable branch, unsafe environment,
credential-variable exclusion, wrong root/HEAD/tree/branch, dirty/ignored/missing
additive envelope, mocked exact child command/stdin/timeout, raw output hashing,
timeout partial logs, arbitrary exit preservation and no false GO.
Initial focused run also passed 17/17. After strengthening the independent
literal-ID assertion, the final focused run passed 17/17 in 0.039 seconds.
Final raw evidence at the evidence root: `focused-final.stdout.raw` (empty SHA
above), `focused-final.stderr.raw` SHA256
`29242521cb5f0c266e1c462fa30fc01f008826ff8a6fc6dc864cee4732da5c14`,
and `focused-final.receipt.json`. Earlier `focused.*` receipts are retained.
These tests mock subprocesses and do not import product modules.

No unfiltered product discovery or credential/native-service suite was run.
Those are outside this selected, effect-reviewed assignment; no full-regression
or milestone-verification claim follows. Syntax is checked in memory without
creating pyc files; `git diff --check` and the three-file inventory are checked.

## Cause, newer diagnostics and unexecuted coverage

P234's original failure inventory targeted the genuine B and 8.34 modules.
P245 preserves the four exact IDs and six frozen source witnesses and extracts
the historical P76 branch via AST. Its separate current-source diagnostic uses
its own current branch/source contract; it does not repair original admission.
P248's C01–C05 and topology negatives separately test historical witnesses,
current raw-reader causality, restoration and terminal denial. Neither newer
test family supplies successful original live admission or execution credit for
the unreachable original replay/tamper assertions. Their earlier results are
not rerun or promoted here. Their preserved raw script hashes are in P252's pins.

The common root cause is the original public successor route terminating in an
exact historical branch/topology gate on a current P251 descendant. It is not a
credential/provider failure. Native traces reproduce this at B method lines
452, 407, 148 and 8.34 line 312, ending at P76 line 237. M1/M2's initial positive
brackets fail before brain readers or historical replay. M3 reaches the first
live admission only after its literal manifest assertions; its second admission
comparison is not reached. M4 fails before historical pin loops, predecessor
reader counts and second-read corruption. None of those later checks is waived.

An honest repair of the **current descendant's original four acceptance results**
cannot be demonstrated under the present frozen contracts: their required live
positive admission conflicts with the immutable historical branch and exact
one-child source envelope. Even a historical branch name alone would not prove
that envelope. The public guard cannot be rerouted or relaxed under this scope.
A future explicitly approved, separately versioned current-source contract and
causal tests may establish current properties, but cannot retroactively turn
these original native failures into passes or repair historical acceptance.

## Open Failures & Prior-Issues Review and decision request

This is the bounded failure review for this diagnostic, not a prior-phase audit.

| Issue, severity | Root cause / affected boundary | Reproduction and containment | Review / disposition |
| --- | --- | --- | --- |
| P76 original four, material acceptance blocker, 16 Nov | Current public legacy routes reach historical branch/topology pin; later assertions unreachable | Four genuine single-method native failures above; preserve all source, controls, IDs and logs | Independent review pending; HOLD, unwaived |
| Current/historical coverage conflation, material assurance risk | P245/P248 current diagnostics cannot establish successful original admission or original causal-reader coverage | Separate exact source/IDs, raw exits, traces and absent coverage explicitly | Independent review pending; HOLD |
| Unsafe native effect execution, high if introduced | P251 documents Python WinCred/provider-adjacent routes; test import or dispatch must not reach them | Exact source-scoped early-denial path, environment exclusion, no product import or key inspection; no effect execution authorized | Safe for this bounded diagnostic only; no effect-exclusion qualification granted |
| Missing broader evidence, existing release blockers | P247/P96/Python WinCred/SEC/product-regression obligations remain separate | No new qualification credit or waiver | HOLD, unchanged |

P247 x64 **0/54** and x86 **0/54** remain; P96 race **OPEN**; Python direct
WinCred **OPEN**; SEC03/04 **0/7**; full unfiltered product regression **0/3**;
real-key **NO-GO** and production **HOLD** remain unchanged.

Governance decision requested: independently review the three additions and raw
receipts as source-preserving reconciliation evidence; retain all four original
failures and all wider holds. Any future current-source acceptance work needs a
separately approved bounded contract and independent validation. This document
requests no source-admission GO, test waiver or historical acceptance change.

No original file, historical branch literal, freeze control, recorded P234 source,
test/product source, tag or history was changed. No staging, commit, push, Drive
workbook or dashboard update occurred. Work remains uncommitted for independent
review. No production phase advancement or seal is claimed.

## Sole-writer remediation, 16 November 2026 (UNCOMMITTED)

The initial read-only reviewer completed with `P252_REVIEW=GO_DRAFT_ONLY`,
no critical/material flaw in its precommit scope, and four LOW findings.
The subsequent release-artifact reproducibility finding was material: the
original runner refused a legitimately committed P252 tree. This finding
concerns diagnostic reproducibility, not permission to repair original P76.
Remediation source rereview remains pending; disposition remains HOLD.

The ORIGINAL receipt above binds ONLY the original precommit runner raw SHA256
`cb3063e87379040cd9e2619efff8463250be8c130522b98f53b0475a1efe68a7`.
The exact initial runner is preserved externally as
`D:\Nayeon\P252_SECURITY_EVIDENCE_20261116\P252_INITIAL_RUNNER_SOURCE_BEFORE_COMMIT_SUPPORT.py`.
Neither that snapshot nor any existing receipt/log was edited or replaced.
The historical 17-test results and original four native failures do not bind
or validate the changed runner. No new original-method execution is claimed here.

The remediated runner admits precisely two states on the fixed P252 branch:

- Original pinned P251 HEAD/tree, with exactly the three untracked additions.
- A committed HEAD with exactly one parent, the pinned P251 commit, whose
  no-renames name-status delta is EXACTLY three `A` paths from this envelope.
  Tracked/staged/untracked/ignored status must be empty. No future child hash
  is embedded in its own source; actual Git HEAD/tree/parents are recorded.

Both modes compare every raw tracked disk blob against HEAD's tree object ID,
require full tree/index/path closure and normal index flags, and retain all
23 original SHA256 pins. The committed mode includes all three additions,
including the runner itself, in that Git-object verification. Regular-file,
ancestor reparse/symlink and hardlink checks now cover the additions too.
Repeated before/after preflight comparisons include addition hashes and
actual Git identity. These checks detect sampled drift; they do not lock the
checkout, bind open file handles through child imports, or prevent concurrent
replacement between lstat/read/import/Git calls. A quiescent trusted checkout
and trusted installed Python/Git remain prerequisites; no adversarial TOCTOU
isolation or general effect sandbox is claimed.

Failure recognition now requires the exact single-method verbose unittest
identity, one FAIL heading, one structured one-test summary and final
`FAILED (failures=1)`, exactly one original refusal marker, empty stdout,
and no ERROR/SKIP/other outcome markers. Receipt-level disposition requires
exactly the ordered four IDs; duplicates/reordering cannot qualify. It still
has no GO result. `receipt.json` uses exclusive create, preserving prior bytes.

| Finding | Repair and evidence | Disposition |
| --- | --- | --- |
| Material committed rerun refusal | Exact one-child additive mode; positive full traversal and wrong-parent/merge/extra-change/dirty-tree adversaries | Implemented; native focused PASS; postcommit native evidence REQUIRED |
| LOW added-path safety / TOCTOU description | Same checked regular-file/reparse/hardlink prerequisites on additions; limitations above; hostile metadata/hardlink cases | Implemented; rereview pending |
| LOW permissive failure recognition | Strict single-child grammar and ordered four IDs; duplicate/misleading-output adversaries | Implemented; rereview pending |
| LOW partial preflight coverage | Both full synthetic Git traversals, all 23 synthetic source witnesses, actual temporary file bytes, tracked/runner corruption and index/flag/link negatives | Implemented; native focused PASS; simulated committed topology is not a committed native receipt |
| LOW overwriteable receipt | Exclusive-create writer and preservation regression | Implemented; native focused PASS |

Final focused evidence:
`D:\Nayeon\P252_SECURITY_EVIDENCE_20261116\remediation-focused-lf-20261116T075413`.
Native CPython 3.12.10, **31/31 PASS**, 0.474 seconds, child native exit **0**.
`stderr.raw` SHA256:
`2435e1ec0552832dfbda91340f2256f29b54838f7bb6fa9cb3cc38f653bf3801`.
`stdout.raw` is empty with the empty SHA256 recorded above. `receipt.json`
retains native version, exit, raw-log hashes and the tested source hashes:
runner `b63fd4ef6657717922f08bb5fc01d52ac8838dd0958647780f32b66fd831018e`;
tests `227cc097499d35188d2b815a8678e79d020c32734f5be9f9df4acacd9e4e576b`.
Earlier 30-test and 31-test remediation runs are retained separately, not overwritten. Final LF normalization corrected two mixed-line-ending whitespace findings; the focused suite was rerun on the final bytes.
A read-only host preflight also traversed the actual original-parent checkout
successfully, and strict parsing recognized all four preserved historical logs.
One host inspection command initially ran from the wrong directory and raised
`ModuleNotFoundError: scripts`; setting the explicit checkout cwd corrected
that orchestration error. It was not an original-method run or test failure.

Controller handoff: leave these exact three additions UNCOMMITTED. After
controller review/commit, a **new committed native runner execution and new
receipt are REQUIRED**. Attach detailed native child exits, raw log hashes,
authenticated committed HEAD/tree/parent and changed runner hash to the draft
PR after that rerun. Do not reuse the original receipt as evidence for the
changed tool. Do not edit this committed document to insert that later receipt:
doing so would dirty the required committed tree; record it externally/in PR.
No commit, staging, push, PR creation, tag, release, workbook/dashboard,
credential/provider/service/policy effect or broader regression was performed
by this remediation. Original four FAILs, P96 race, P247 runtimes, SEC03/04,
real-key NO-GO and production HOLD remain unchanged and unwaived.
