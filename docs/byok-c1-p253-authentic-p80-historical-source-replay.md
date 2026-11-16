# P253 authentic P80 historical source replay

16 November 2026. Sole engineering writer. Independent read-only review pending.

## Observed historical outcomes

The unchanged authentic P80 P76 public gate returned **`EXACT_CHILD`**, native
exit **0**, in **19.922 seconds**. Two original positive methods also completed
successfully, including one of the four methods that failed in P252. Five
original denial methods passed. The other three requested original methods
hit the mandatory 60-second limit and have **incomplete acceptance evidence**.
Their terminated native children exited **1**. Their logs contain an unfinished
verbose method line and lack a unittest verdict. The timeout distinction matters
when interpreting those three exits.

| Case | Original-method outcome | Native child exit | Timeout | Elapsed seconds |
| --- | --- | --- | --- | --- |
| M1, live brain reader tamper | Incomplete, terminated at limit | 1 | yes | 60.031 |
| M2, historical brain corruption | Incomplete, terminated at limit | 1 | yes | 60.015 |
| M3, exact23 manifest and live admission | PASS, one test, OK | 0 | no | 55.593 |
| M4, 8.34 real candidate and predecessor route | Incomplete, terminated at limit | 1 | yes | 60.016 |
| M5, P76 public/private agreement | PASS, one test, OK | 0 | no | 40.781 |
| M6, wrong branch | PASS, one test, OK | 0 | no | 0.187 |
| M7, wrong annotated tag ref | PASS, one test, OK | 0 | no | 0.188 |
| M8, unknown untracked path | PASS, one test, OK | 0 | no | 0.172 |
| M9, wrong commit parent | PASS, one test, OK | 0 | no | 0.188 |
| M10, old sealed live body rejects successor | PASS, one test, OK | 0 | no | 0.297 |

## Actual original identities and assertion scope

All ten IDs were verified by AST against the original P80 files before import.
The selected methods have no decorators or class setup/teardown overrides.
Line ranges below describe the inspected historical source.

1. M1, lines 451-468 of `tests/test_phase8_byok_b_scope_integrity.py`.
   `tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay`
2. M2, lines 406-427 of that file.
   `tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected`
3. M3, lines 138-149 of that file.
   `tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission`
4. M4, lines 309-353 of `tests/test_phase_834_scope_integrity.py`.
   `tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route`
5. M5, lines 85-89 of `tests/test_phase8_byok_c1_p76_scope.py`.
   `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_new_public_and_private_gate_agree`
6. M6, lines 55-58 of that file.
   `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_branch_refused_before_other_work`
7. M7, lines 60-64 of that file.
   `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_annotated_tag_ref_refused`
8. M8, lines 66-71 of that file.
   `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_unknown_untracked_path_refused`
9. M9, lines 73-79 of that file.
   `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_wrong_commit_parent_refused`
10. M10, lines 81-83 of that file.
    `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_old_sealed_live_body_still_rejects_successor_branch`

M3 completed the literal historical B manifest checks, real public B admission,
and equality of the public A and B results. Its three live admissions take
55.405 seconds inside unittest. M5 directly calls the P76 gate and the public
Phase10.3 route, checks membership in the original three-state set, and checks
equality. Its unittest time is retained in its binary log.

The inspected P76 test file has no literal assertion that a live call equals
`EXACT_CHILD`. M5 is the bounded original positive selected for this task. A
separate direct observation records the exact return value from the original
gate. That observation receives its own receipt and contributes no additional
original-test count. Its child program installs stdlib `faulthandler` diagnostics,
imports the original P76 function, calls it once, prints its return, and cancels
the diagnostic timer. stdout is exactly `P76_RETURN='EXACT_CHILD'` followed by
the native newline. The 15-second stderr stack sample shows execution in
P76 `_baseline` at line 128 through the original Git subprocess reader. The
diagnostic text `Timeout (0:00:15)!` is a stack-dump timer message. This child
completed normally before its outer 60-second deadline.

M1 contains four live-admission calls. M2 brackets three historical fixture
families across three synthetic topologies with live admissions, including
causal corruption and restoration assertions. M4 includes five live route
calls plus historical byte and reader assertions. A single direct admission
took 19.922 seconds here. Repeated reconstruction/read work is a plausible
runtime explanation for the 60-second overruns. The uninstrumented truncated
logs do not identify their last completed internal assertion. Their final
causal tamper/restoration coverage remains unverified. No timeout was extended
and no incomplete method was retried or credited as passing.

## Pinned source identities and preservation

Writer worktree is `D:\Nayeon\CODEX_P253_HISTORICAL_P76_20261116`, branch
`byok-c1-p253-historical-positive-p76-evidence-20261116`, clean intake HEAD
`20cafb444365d62dba855115173b00c63133718b` (P252), sole parent
`6e2717f13da253fddbb3c9cbcfdf55e124d6f8ac`, tree
`15f98fa7f0c17fff13e22b6d17c8f54fb739030a`. No tag points at intake HEAD.
`.codex/CURRENT_STATE.md` retains a stale 3 November Phase10.2 header. Git and
the explicit P253 assignment govern this diagnostic continuation.

Authentic historical source worktree is
`D:\Nayeon\P253_AUTHENTIC_P80_READONLY_20261116`, on the genuine supplied branch
`byok-c1-p80-sealed-historical-fixture-20261106`, HEAD
`24da07345c67566d2e79f442aabfba36a1ebddb4`, sole parent
`cacb5c320d26ffa28faf1f15a5e088029ee1453b`, tree
`1795b59895b7fd52da525d237eb4282d5d10851f`.
The exact local remote-tracking ref
`refs/remotes/origin/byok-c1-p80-sealed-historical-fixture-20261106`
was checked with `show-ref --verify --hash` and equals the full P80 HEAD.
Remote provenance was preauthenticated by the task owner. This task performed
local ref verification throughout the replay.

Preflight and eleven postflights bind all **470 tracked files** by raw disk
SHA-256 and Git blob identity, full tree/index equality, stage-zero entries,
normal index flags, and empty tracked/untracked/ignored status. Checks reject
linked/reparse ancestors, hardlinked or nonregular tracked files, replacement
refs, grafts and shallow history. They also compare the physical index SHA-256,
HEAD/config metadata hashes, full ref inventory hash, branch, HEAD, parent,
tree and exact remote-tracking SHA. Every postflight equals the original
baseline. Git optional locking is disabled for these reads. Test children
receive `-B`, preventing Python bytecode output in the target.

The sandbox initially reported Git dubious ownership and denied access to the
installed host Python. Authorized host-user orchestration completed the reads
and executions. Git trust configuration and system security policy were untouched.

## Source and effect-safety trace before launch

The AST closure contains 20 local modules plus `tests/__init__.py`. Full raw
pins, import statements, call expressions and selected original method bodies
are retained in `source-inspection.json`. The principal raw SHA-256 witnesses are
as follows.

| Historical file | Raw SHA-256 |
| --- | --- |
| `tests/test_phase8_byok_b_scope_integrity.py` | `65dad89298a587d6bb5dde5455df4d701bb1a1fd9a7a96cecf3e647800e3ae8b` |
| `tests/test_phase_834_scope_integrity.py` | `8dc69ec770ea008dff9cd13e15299a73e38044f1671fd4fe78fbe2a431ccf57a` |
| `tests/test_phase8_byok_c1_p76_scope.py` | `ee6bb4cecc5d8a388623b635b8172ca7c526d87f284feb6b09a5e3e74f651e2d` |
| `tests/phase8_byok_c1_p76_scope.py` | `1c42912d9fc550dea56c9ba9bb70d9568f298223b5514af8d03c1723aaad3327` |

The closure spans 8.29 lifecycle, 8.30-8.34, 8.36-8.37, BYOK A/B,
Phase10/10.2/10.3 and P76 source guards, together with B/P76 and
8.30/8.32/8.33/8.34 test helpers. Function-local imports were included.
Imports outside those helpers are stdlib. Import-time work consists of literal
containers, regex/path construction, definitions, decorators and in-memory
callable aliases. The 8.30 test helper installs its existing in-memory source
reader adapter at import. Module-main blocks remain inactive under unittest.

M1-M3 enter B -> Phase10 -> Phase10.2 -> Phase10.3 -> P76. M4 enters
8.34 -> 8.36 -> 8.37 -> B and that same chain. P76 reads the real branch first,
then authenticates historical tags/commits/trees, original manifests, current
disk/index views and the one-child proof, and repeats drift checks. Source
readers terminate in `Path` reads and the original 8.30 `_git` helper's
`subprocess.check_output`, with a 20-second per-command timeout. Inspected Git
operations query objects, refs, ancestry, inventories and raw differences.
The older 8.29 migration helper also contains read-only index/HEAD subprocess
queries. The outer 60-second child deadline remains active.

The 8.32 snapshot and 8.33/8.34 candidate factories authenticate original Git
preimages, then use in-memory dictionaries and `mock.patch` to replay synthetic
topologies, disk readers and corruption. Their existing synthetic pins and
private historical routes belong to the original fixtures. The external
controller supplies the ordinary unittest invocation. Product paths naming
credentials/providers are source data read as bytes. Their product modules
are never imported by the selected routes.

M6-M9 use original in-memory Git/commit mocks for their denial assertions.
M10 invokes the preserved old live body and requires its original branch
refusal. These source-scoped paths have no reachable WinCred, provider,
credential, network, GUI, file-mutating or security-policy action. The
transitively imported 8.30 module also defines `test_junction_parent_refused`,
which creates temporary directories and runs `mklink /J`. That method was
excluded because its filesystem effects violate this task's selection boundary.
The ten selected methods were eligible after inspection.

Child environments are built from an explicit basic Windows process-variable
allowlist and four read-only/noninteractive Git controls. All `P134_*`, inherited
`GIT_*`, `PYTHON*`, credential and provider authorization variables are excluded
from forwarding. Receipts record variable names only. The installed native
Python/Git and a quiescent source are trusted prerequisites. These source
checks provide sampled preservation evidence, with a residual concurrent
replacement window between checks and imports/reads. They supply no general
OS effect-isolation qualification.

A supplemental final Git-configuration check initially rejected the presence
of configured driver names. It found the host's `astextplain` textconv and LFS
filter definitions. Effective attribute inspection across all 470 pinned paths
then found zero assigned filter, diff-driver or working-tree-encoding attributes.
The original Git calls request no textconv operation. These definitions have
no selected-path application in the checked tree. This configuration/attribute
check occurred after the runs and is retained in `git-effect-attributes.json`.

## Native binary evidence and receipts

Evidence root and exact aggregate receipt location are
`D:\Nayeon\P253_HISTORICAL_P76_EVIDENCE_20261116\receipt.json`.
Original-method run window was 11:17:00-11:21:56 UTC on 16 November 2026.
Interpreter is the existing
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`,
CPython **3.12.10**, MSC v.1943, **AMD64**, native Windows.

Each command was `[python.exe, -B, -m, unittest, exact_original_ID, -v]`, cwd
the authentic P80 worktree, shell false, stdin null. Each child received its own
60-second deadline. stdout/stderr binary files were passed directly to the
child. On expiry, the controller called `kill()` and retained the actual
`wait()` return code and timeout flag. Per-method receipts are
`m1.receipt.json` through `m10.receipt.json`. Corresponding streams are
`mN.stdout.raw` and `mN.stderr.raw`. All ten stdout files are empty, each SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

| Case | stderr raw SHA-256 |
| --- | --- |
| M1 | `5603ee4a4f983aae2e74dde4d449d50d8f6f18597cd664cc815122fbb9d539b5` |
| M2 | `9a296abfeeb652128b65722851630d06d857e073c850c49e6d3f39179058cad2` |
| M3 | `acae55fbd63fb906f13314fa4831574c52534bc1c6348c370eff384a68127587` |
| M4 | `7c7b85b925766fbe706107fe384414396894b46f22ec2224531d50d2ce9e1971` |
| M5 | `81fef0b47220998e86963b3defc04461d8320a781cd014990a29219ad66ac2a2` |
| M6 | `153bb2579889879ad7042db485bed28bc2dac75436f0b7149d8ecc4c2cbeb500` |
| M7 | `aed003c06edb0ed1fdcf4a3e2255e38cebd9a17db5d8dbb809cd19612eae66aa` |
| M8 | `9106b445a494f75d9844d0a6bfbded6d711eac4e1efedce3617ea8e281c09ebb` |
| M9 | `5032a1a7e6cd8e7554091fa127a11fe074f32b7c55661c7f63d58583dcda05c8` |
| M10 | `d52d58f3285a4bdb59bd661cff825c2804762de2017dc6960178a0bf78e4ec5f` |

Additional evidence files are retained at that same external root.

| Artifact | SHA-256 |
| --- | --- |
| `receipt.json` | `4a4b947b61cdd4ab5ae4c19a3978b4f75a955345103270a3f2bf5d6aeb996c8c` |
| `p253_replay.py`, external controller | `57e2349aee32a8549dc3ae6611c313adcd1689a385fa3bd4be0b7ce566e11f94` |
| `source-inspection.json` | `d9ba644f3aaf4f5c4c67139e31f296e2e411ca991f04915f3fbe91414dbe50e8` |
| `target-preflight.json` | `d1cad581d6816837f721d0260f644280c97fd6963b6aee98acab4ad0d033df31` |
| `direct-p76.receipt.json` | `260b4edd8900105e6547c973ef871179da79cb1a0c6060a1600b943b67786d0f` |
| `p253_direct_observation.py`, external controller | `cfa4b93a4a3cee1eca097558c213bcc2be2385b27d6366fa78344519988202ea` |
| `direct-p76.stdout.raw` | `18d3d9052136704ba6bfd7b7c3b8d0958b08a37bb6c2443859f817fb1c523fd0` |
| `direct-p76.stderr.raw` | `dc7914287406c9bda465be28c9551b9e6106978d2d0cb9db2091684066b0319f` |

`mN.postflight.json` and `direct-p76.postflight.json` retain full target
preservation snapshots. Controllers create log/receipt files exclusively and
retain native child exits separately from controller exits. The aggregate
controller exited 0 upon completing evidence collection. Outcome interpretation
uses each child record and raw unittest grammar. Seven completed methods each
report `Ran 1 test` and final `OK`. Three timeout records remain incomplete.
`final-verification.json` records independent hash/grammar readback by the same
sole writer, full snapshot equality and the exact one-document writer scope.
Its verification is separate from the forthcoming independent technical review.

## Relationship to P252 and bounded failure review

P252's four authentic modern-source executions remain **four FAIL, native
exit 1**, with the original wrong-P76-branch assertion. Their preserved
record is `docs/byok-c1-p252-original-p76-current-native-reconciliation.md` and
the external P252 evidence it identifies. P253 has the exact clean sealed P252
parent as intake. Its single added report leaves those tests, guards, historical
branch literal and P252 receipts intact.

P80's authentic branch and one-child source envelope permit a genuine positive
P76 state. The successful M3, M5 and direct observation establish bounded
historical-source behavior on this host and date. Current P252 acceptance
continues to have the four original failures. M1/M2/M4 historical acceptance
also remains incomplete under this task's execution budget.

| Issue and severity | Evidence, root cause and affected boundary | Containment and disposition |
| --- | --- | --- |
| P252 original four, material acceptance blocker | Original public routes terminate at an exact historical branch/topology contract on the modern descendant. P252 records four normal failures. | Preserve recorded failures. Historical positive evidence has its own source identity. HOLD for current acceptance. |
| P253 M1/M2/M4, material missing evidence | Native children exceeded 60 seconds. Raw logs lack final verdicts. Repeated source admission is runtime-expensive, but exact final internal progress is unknown. | Preserve logs and exit/timeout distinction. No waiver or completion credit. Independent review pending, HOLD for complete historical four-case acceptance. |
| Evidence conflation, material assurance risk | Historical `EXACT_CHILD` and seven completed historical methods have bounded source applicability. | Keep P252 failures and all unmet qualification counters explicit. Review pending. |
| Native effects, existing high exposure | P251 documents Python direct WinCred/provider-adjacent routes. Selected P253 imports/calls are source-only and synthetic as traced above. | Keep execution within inspected original methods and read-only observation. Broader effect exclusion OPEN. |
| Established release blockers | P96 race OPEN, Python direct WinCred OPEN, P247 x64 0/54 and x86 0/54, external SEC03/04 0/7, full product regressions 0/3. | REAL KEY NO-GO. PRODUCTION HOLD. Independent qualification remains outstanding. |

Governance request is to independently review this single additive report and
its external receipts as genuine historical P76 `EXACT_CHILD` evidence, with
the exact original-method outcomes above. Keep the three historical timeouts
and current P252 four failures open. Completing the outstanding historical
methods would require a separately approved bounded execution plan that
retains their original assertions and source identity. This assignment ends
at the requested review handoff with **REAL KEY NO-GO and PRODUCTION HOLD**.

The sole repository delta is this add-only document. Target source/index/ref
preservation evidence accompanies the receipts. Staging, commit, tag, push,
workbook/dashboard changes and broader product regression execution remain
outside this review handoff.

## Independent-review remediation and supplementary original P76 result

The first technical independent review returned `P253_REVIEW=GO_DRAFT_ONLY`.
It recorded MEDIUM incomplete M1/M2/M4 timeout evidence, MEDIUM missing second
positive original P76 test, LOW historical WIP/prototype provenance disclosure,
and LOW source-level effect-exclusion qualification. This addendum preserves
the original report above and records the bounded remediation for rereview.
The original report bytes are also retained externally as
`second-p76-positive.original-report.md`, SHA-256
`1347363e9463bf3a91bcaf6dea9e941a0f9c093f136e0adc6e97a23811a54166`.

The authentic P80 commit subject is explicitly
`WIP P80 sealed historical self-pin fixture migration (NO CREDENTIAL EFFECTS)`.
The branch name contains `sealed`, while this commit's own subject identifies
WIP historical fixture migration. The original P76 gate describes itself as
`P76 exact offline C1 source successor PROTOTYPE; not release authority.`
The original test module likewise disclaims independent review, release proof
and service consent. These provenance facts bound the historical results.
Release acceptance remains HOLD.

One additional isolated native original method was executed once, unchanged,
on the same authentic P80 worktree and HEAD. Its exact identity is
`tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_five_public_routes_use_same_source_proof`.
The inspected method occupies lines 91-102 of the original M5 source file.
It calls the original P76 gate, asserts membership in the original three-state
set, then checks equality through public BYOK A, BYOK B, Phase10, Phase10.2
and Phase10.3 routes using five subtests. It supplies a second positive original
P76 method alongside M5. The separately preserved direct P76 observation
continues to supply the exact `EXACT_CHILD` return-value evidence.

Before launch, the controller reproduced the entire original source-inspection
record exactly, then inspected this selected method and verified every entry
in its transitive source closure against the original reviewed closure.
The complete physical Git tree/index/source snapshot matched the existing
`target-preflight.json`, including all 470 tracked files, raw disk SHA-256,
Git blobs, normal index flags, physical index/metadata and refs, branch/HEAD,
parent/tree and empty tracked/untracked/ignored status. The actual preserved
supplementary preflight and postflight JSON files both have the same SHA-256
as that existing baseline. Original aggregate, direct-P76 and ten-method
receipts and streams were checked against a separately preserved preflight
hash inventory after execution and remained unchanged.

The existing Windows CPython 3.12.10 AMD64 interpreter ran
`-B -m unittest tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_five_public_routes_use_same_source_proof -v`
with shell false, stdin null and the same sanitized basic environment allowlist.
No P134 credential/native-effects authorization was forwarded. The maximum
child deadline was 240 seconds. The run began at 11:34:18 UTC and finished at
11:36:06 UTC on 16 November 2026. Native child exit was **0**, timeout **false**,
controller-measured elapsed **108.765 seconds**. Raw stderr ends with
`Ran 1 test in 108.599s`, a blank line and `OK`. Raw stdout is empty.

The first external controller stopped before test launch on an incorrect
source ending-line assertion, 103 instead of 102. Its bytes are preserved as
`second-p76-positive.controller.py`. The corrected external
`second-p76-positive.controller-v2.py` performed the sole supplementary test
execution. Historical source and prototype bytes were unchanged throughout.

All supplementary artifacts reside in the existing external evidence directory
`D:\Nayeon\P253_HISTORICAL_P76_EVIDENCE_20261116`.

| Supplementary artifact | SHA-256 |
| --- | --- |
| `second-p76-positive.receipt.json` | `8ad298a79eff4e9cd2ea166efac7275c00aa2c667b2e45890f01a2e82e12e4fd` |
| `second-p76-positive.stdout.raw` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `second-p76-positive.stderr.raw` | `b993f535dd701bf60b03c05c65651cfb59d5e5f124b350b981830be56a19eb40` |
| `second-p76-positive.source-inspection.json` | `8d690aea6e8f40ca49a2a10f112156e5174fa975d362326f6d50fe3a7c90f1a3` |
| `second-p76-positive.preflight.json` | `d1cad581d6816837f721d0260f644280c97fd6963b6aee98acab4ad0d033df31` |
| `second-p76-positive.postflight.json` | `d1cad581d6816837f721d0260f644280c97fd6963b6aee98acab4ad0d033df31` |
| `second-p76-positive.original-evidence-preflight.json` | `98617f4c2c519ec61079058f8275a18e859b5dac60473db8eaaa5eef64a42a83` |
| `second-p76-positive.controller-v2.py` | `79dd45882a1003917f220685569dfb7f176de74b895697895e8165a3ef5e74a1` |
| `second-p76-positive.controller.py`, stopped before launch | `6c67d4a51d5b0cc003ba21f954cbecfd67d5e49f50059115072198a2a523287f` |

The selected original test source SHA-256 remains
`ee6bb4cecc5d8a388623b635b8172ca7c526d87f284feb6b09a5e3e74f651e2d`.
The original ten-run aggregate remains separately pinned at
`4a4b947b61cdd4ab5ae4c19a3978b4f75a955345103270a3f2bf5d6aeb996c8c`.
The supplementary receipt has its own identity and contributes one additional
completed original method. The original ten-method table remains the record
of its original run window.

Effect-safety evidence remains source-scoped. Inspected original routes read
source/Git and perform in-memory assertions. Independent OS effect telemetry
was absent. Native interpreter startup, site/customization/import resolution,
installed executable behavior, Git child-process behavior and concurrent
replacement between sampled checks retain residual risks. The sanitized
environment, `-B`, source closure and matching postflight bound this execution's
evidence. Credential/provider effect exclusion and broader OS effect isolation
remain unqualified by independent runtime telemetry. No credential/provider
calls, WDAC/policy changes or native-effects authorization were requested by
the supplementary controller.

| Review item | Remediation evidence and disposition |
| --- | --- |
| MEDIUM second original P76 positive | Additional unchanged original method PASS, native exit 0, one test/OK, complete supplementary receipt and matching 470-file snapshots. Evidence gap addressed, independent read-only rereview pending. |
| MEDIUM M1/M2/M4 timeouts | Original 60-second timeouts and incomplete causal assertions preserved. OPEN, unwaived. |
| LOW WIP/prototype provenance | Exact authentic commit subject and original gate/test disclaimers disclosed above. Rereview pending. |
| LOW source-level effect exclusion | Source-scoped assurance, absent independent OS effect telemetry and residual startup/child-process risks disclosed above. Broader effect qualification remains OPEN. |
| P252 four original FAIL and SEC03/04 | Original failures and external qualification gaps remain OPEN, unwaived. Supplementary P76 success supplies no closure credit for these items. |

This remediation is ready for final independent read-only technical rereview.
**REAL KEY NO-GO and PRODUCTION HOLD** continue to apply.
