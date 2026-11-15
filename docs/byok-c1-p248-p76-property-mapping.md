# P248 historical P76 property recovery and current-source assertions

15 November 2026. DRAFT / REAL-KEY NO-GO / PRODUCTION RELEASE HOLD.

## Source and decision

Initial branch `byok-c1-p248-p76-property-equivalence-20261115`, HEAD
`39dbb445fc08a1ef03c73f4a13c6f344be8dfa07`, clean tracked source and index, with exactly three untracked P248 additions.
`git tag --points-at HEAD` returned no tags. Recent lineage is P247 `39dbb44`,
P245 `e49810c`, `916d8a2`, `fcb610a`. The context file's latest header still
describes 3 November Phase 10.2. Git and the explicit P248 assignment govern
this bounded assurance work. The context file remains a preserved witness.

Acceptance remains **HOLD**. Current source contains five current-property
methods C01-C05 and four synthetic topology negative methods, nine named
unittest methods in total. The Codex sandbox launched zero tests. Separately
supplied Nayeon host-native receipts report 5/5 and later 9/9 PASS, as recorded
below. Initial five-case source review was GO for DRAFT ONLY. Final expanded
topology and genuine committed-case validation still require independent review.
The four original historical reports remain **FAIL, native exit 1, unwaived**.
Their later assertions have no executed-coverage credit from an early refusal.
No full product regression or qualified approval count advances.

## Original identities and source references

References below use the preserved files at the initial full HEAD above.

| Method ID | Exact original unittest identity | Source |
| --- | --- | --- |
| M1 / G0-M1 | `tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay` | `tests/test_phase8_byok_b_scope_integrity.py` lines 451-468 |
| M2 / G0-M2 | `tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected` | same file lines 406-427 |
| M3 / G1-M3 | `tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission` | same file lines 138-149 |
| M4 / G6-M3 | `tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route` | `tests/test_phase_834_scope_integrity.py` lines 309-353 |

The public B route calls Phase10, Phase10.2 privacy, Phase10.3, then P76.
Public A first runs B's `assert_byok_a_current_source`, binding A's adapter
bytes, then calls B. Current public 8.34 routes through 8.36 and 8.37.
The final 8.37 definition delegates directly to BYOK B and the same successor
chain. Its older A-delegating definition is superseded. The separately called
public A route still performs its adapter check before B. Public 8.31 routes
through 8.32, 8.33 and 8.34.
The terminal `assert_p76_offline_integrity` first requires the exact branch
`byok-c1-p80-sealed-historical-fixture-20261106`. Its `_baseline`, `_expected`,
tree/index checks, `_proof`, repeated reads and tag revalidation follow that
guard. The current P248 branch fails before those operations. P248 never
patches that branch, guard, Git replies, digest pins or public admission result.

## Fixture preconditions inspected

The two brain targets are `nayeon/brain/onboarding_coordination.py` and
`nayeon/brain/onboarding_recovery.py`. Their literal historical blob OIDs are
`189332fb17e81e0968ead9d992f6a34cacbdb416` and
`1045b642db51b5c244aae7f7861190709e96416f` respectively.

`_historical_byok_b_fixtures` at B test lines 387-397 selects the private
8.32, 8.33 and 8.34 historical guards. The factories are explicit synthetic
topology contexts. They supply `COMPLETE_UNSTAGED`, `EXACT_STAGED` and
`EXACT_CHILD` inventories, index, raw deltas and disk projections. Their scope
is historical replay only.

* 8.32 `snapshot` at `tests/test_phase_832_scope_integrity.py` lines 484-640
  authenticates the envelope from `03f247d8627bf1c51105f73b9de5c6bbdf389cf9`
  using original pins, normalized candidate bytes and raw tree blobs. It calls
  `_history` before installing seams. Adapter and A-02 raw blobs must agree
  with both baseline and sealed tree. Brain blobs must match both trees and
  the literal OIDs. Later B-modified paths and fourteen literal Phase10 test
  preimages are bound to immutable trees. It projects selected `Path.read_bytes`
  calls as well as `_disk`, `_raw_frozen_disk` and Git replies.
* 8.33 `candidate` at `tests/test_phase_833_scope_integrity.py` lines 43-173
  reads the real protected tree, authenticates A-02 and both brain preimages,
  and checks fourteen literal Phase10 test blobs. Its candidate text and
  candidate SHA pins are synthetic, confined to the fixture. `_raw_frozen_disk`
  projects these preimages and preserves other real reads. Public admission
  is temporarily selected to the private historical guard inside that factory.
* 8.34 `candidate` at `tests/test_phase_834_scope_integrity.py` lines 55-178
  similarly authenticates the protected tree, both literal brain preimages,
  fourteen test preimages and A-02. Candidate text and pins are synthetic.
  It installs the private historical 8.34 guard only within the context.
* B's separate `candidate` at B test lines 51-134 authenticates the sealed B
  head `e3612279cb972e68e2487702183d5bf5b8f6c4a1` through Phase10 `_baseline`,
  all 23 static B pins and raw tree entries before synthetic seams. It selects
  `_assert_byok_b_historical`, with A-parent `_frozen` reads from `sealed_bytes`.
  That factory is outside the four requested methods' direct execution paths.

P248 reads these prerequisites as source. It does not claim the fixtures ran.
The earlier `repair_fixture` in the 8.32 module is a different fake-only helper
and does not establish the `snapshot` factory's executed behavior.

## Property mapping

`C01` through `C05` refer to the correspondingly prefixed methods in
`tests/test_p248_p76_properties.py`. Host-native evidence for these methods is
recorded below. Independent acceptance review remains open. P245 coverage describes assertions present
in its source and bounded prior reported evidence, without granting credit
to an unreachable original assertion.

| Property ID | Original assertion and call chain | Exact source or fixture prerequisite | Historical-only or current executable | P245 coverage | New assertion | Remaining gap and disposition |
| --- | --- | --- | --- | --- | --- | --- |
| P01 | M1 lines 452,468 require successful B public admission before and after | Complete modern public chain must reach an admitted exact P76 topology on its pinned branch | Historical public acceptance only here | Partial. P245 supplies a separately versioned current diagnostic and preserved terminal denial | C05 proves each real legacy route reaches the unchanged terminal refusal | Positive historical public admission agreement remains HOLD. Refusal cannot satisfy `assertIn(..., STATES)` |
| P02 | M1 lines 453-467 patch Phase10 `successor._disk`, corrupt each brain target, require exact Phase10.2 frozen-source error and `reached == [target]` | Successful admission first, Phase10 reader selected through actual successor route | Original reader path remains historical-only on P248. Current raw-reader successor is executable | Partial. Generic tracked tamper and false-clean-status controls exist, without these two causal target routes | C03 runs real complete HEAD/index/disk scans, injects returned bytes only at P245 `raw_source`, requires exact target mismatch and one reach per target | Phase10 `_disk` route and original error contract remain HOLD. C03 has its own P245 mismatch contract |
| P03 | M1 final positive admission after mock removal | Same admitted topology, restored reader | Original positive historical-only. Current scan restoration executable | Partial. General proof and receipt equality exist | C03 compares each fresh restored scan pair to its positive baseline | Host-native draft PASS reported below. Original final admission remains HOLD |
| P04 | M2 lines 407,427 require public B admission around all replay contexts | Exact P76 historical branch and finalized public topology | Historical-only on P248 | None for the successful public brackets | C05 supplies denial-route evidence only | Both original brackets remain HOLD |
| P05 | M2 lines 408-411 require each private guard to return each of three states across three factories | Authenticated 8.32/8.33/8.34 preimages, synthetic topology factories described above | Historical replay can be investigated separately. Current full-method entry is refused | None for nine fixture/state positive controls | No new replay or topology assertion | HOLD. No branch override or newly invented replay used to fill this gap |
| P06 | M2 lines 412-425 corrupt each `_raw_frozen_disk` brain read, require rejection and exactly one reached target | Each of nine positive fixture/state controls, both literal historical brain blobs, active private guard | Historical projection causality | None. Current raw-source controls do not execute historical projection | C03 supplies separately named current target causality only | All 18 historical target/state/fixture causal cases remain unexecuted here, HOLD |
| P07 | M2 line 426 restores private guard to the same state after each target loop | Fixture patches unwind and all original pins/readers remain intact | Historical restoration | None for fixture restoration | C03 current reader restoration only | Historical restoration and fixture isolation remain HOLD |
| P08 | M3 lines 139-142 require literal B parent/tree/tag object and `PARENT_PARENT == historical.PARENT` | Preserved B/A modules, immutable A parent objects | Current executable historical witness assertions | Partial. B module is among six byte witnesses, but literals are not asserted individually | C01 repeats every literal/relation and reads real tree, annotated tag type/ref/peel | Host-native draft PASS reported below. Witness evidence carries no public admission result |
| P09 | M3 lines 143-147 require 16 modified, 7 added, exact23, disjoint sets and exact candidate-pin key inventory | Original B manifest and pins | Current executable historical manifest assertions | Partial. Preserves module bytes, no exact23 assertions | C01 repeats all five manifest assertions | Host-native draft PASS reported below. Current P248 three-addition envelope has a separate identity |
| P10 | M3 lines 148-149 require state membership and equality of A/B public admission | A adapter byte proof, same fresh public successor admission | Positive historical-only here | None for successful A/B public agreement | C05 checks five real public routes each reach P76 once and refuse | Positive original equality remains HOLD. A refusal is outside the three-state contract |
| P11 | M4 lines 312-320 require successful 8.34 and 8.36 state agreement, twenty pin keys, literal 8.36 protected commit | Entire public route admitted, sealed `b0490cd9e72104a74a32dc5315cbc55bc4034676` available | Public positive agreement historical-only. Key inventory and commit executable now | Partial. Complete bytes authenticated, these assertions absent | C02 checks exact twenty-key inventory and protected commit. C05 checks public refusal routing | Positive state agreement remains HOLD |
| P12 | M4 lines 321-326 read each of twenty sealed blobs, zero exactly one original self-pin literal, compare SHA-256 | Real sealed 8.34 commit, original regex, original 20 pins | Current executable historical-byte assertions | Partial. Frozen module witnesses do not perform the twenty Git-blob comparisons | C02 executes the original source loop as a separately named assertion, adds per-file appended-byte digest mismatch | Host-native draft PASS reported below. Negative comparison exercises the hash assertion. It does not invoke historical admission |
| P13 | M4 lines 327-337 call old 8.31 public gate while observing Phase10 `_disk`, require exactly two conversation-session reads | Admitted public successor path and original Phase10 reader | Original historical route positive remains inaccessible here. Current P245 raw route executable | Partial. Generic full scans, no causal assertion for this exact target's two reads | C04 observes exactly two real reads in `current_read_pair` | P248 explicitly composes two P245 complete scans. Original predecessor-to-Phase10 reader path remains HOLD |
| P14 | M4 lines 339-353 corrupt only the second target read, require exact Phase10.2 frozen-source refusal, exactly two reaches, then restored public admission | First target read valid, second target read reached through original public gate, unchanged reader after context | Historical public-route assertion plus separately executable current corruption property | None for this exact second-read causal control. Receipt comparisons cover a different boundary | C04 corrupts only the second raw target read, requires exact Git-byte mismatch, two reaches and fresh positive restoration | Host-native draft PASS reported below. Current composed-scan property is separate. Original error and restored public admission remain HOLD |

## Additive implementation and evidence boundary

The three P248 files are this mapping, one nine-method unittest module and
`scripts/p248_p76_properties.py`. The script is a test-only source helper.
Its schema is `P248-LOCAL-SOURCE-OBSERVATION-V2`.

The helper requires the assigned absolute root and branch, full SHA-1 history,
original Phase10.3 annotated-tag identity, no replacements/grafts, zero
supported index flags and complete HEAD/index/raw-disk agreement. It reuses
P245 `git_identity`, `complete_source` and bounded readers without changing
P245 globals or its hosted contract. All six P245 literal frozen SHA-256
witnesses must match. Git/P134 environment overrides are rejected before Git.

Two separate source topologies are supported.

* `EXACT_UNSTAGED_DRAFT` requires P247 HEAD
  `39dbb445fc08a1ef03c73f4a13c6f344be8dfa07` and exactly the three untracked
  P248 additions. Draft additions receive bounded raw hashes and filesystem
  identities, including alias checks and repeated observations.
* `CLEAN_ONE_CHILD_CANDIDATE` requires a clean status and an authenticated raw
  commit with exactly one parent, the P247 HEAD above. Its tree must match the
  raw commit header. The complete raw Git delta must consist of exactly the
  three additive paths, each regular mode `100644`, with exact raw addition
  records. Complete index/tree/raw-disk scans cover all tracked paths,
  including the committed additions, P245 and P247. Raw child evidence and
  topology are revalidated.

Extra untracked/ignored paths, staged changes and tracked edits refuse.
Each source observation performs two complete scans and requires equality.
Observed hashes bind source observations to bytes. Independent source approval
remains unset. The committed case has **not been genuinely run**. It requires
separate after-commit native validation and independent review of the exact
committed source before it can receive validation credit.

Each test class obtains a source observation in `setUpClass` and registers
class cleanup requiring final observation equality, including after individual
failures. C03/C04 obtain fresh full scans around in-memory reader corruptions.
A wrong failure reason or unreached target fails the method. The two-scan
helper requires complete manifest equality. Continuous immutability between
reads remains outside this contract. These assertions supply no service
admission or effect token.

### Named unittest inventory

All methods below are in `tests/test_p248_p76_properties.py`.

| Class | Named method | Bounded assertion |
| --- | --- | --- |
| `P248CurrentPropertyTests` | `test_c01_literal_byok_b_parent_and_exact23_witness` | C01 authenticates B parent/tree/tag literals, relation to A, exact23 manifest and real immutable objects |
| `P248CurrentPropertyTests` | `test_c02_sealed_834_twenty_source_pins_and_corruption` | C02 checks twenty sealed blobs and pins, self-pin normalization and appended-byte digest mismatch |
| `P248CurrentPropertyTests` | `test_c03_current_brain_reader_corruption_and_restoration` | C03 checks both current brain targets, exact raw-byte mismatch, single target reach and restored full scans |
| `P248CurrentPropertyTests` | `test_c04_current_predecessor_second_read_corruption_and_restoration` | C04 observes two current conversation-session reads, corrupts only the second and checks exact refusal and restoration |
| `P248CurrentPropertyTests` | `test_c05_legacy_public_routes_reach_exact_p76_refusal` | C05 checks five real public routes each reach the unchanged P76 branch refusal once |
| `P248TopologyNegativeTests` | `test_child_raw_commit_and_delta_negatives` | Synthetic parser positive control followed by missing/wrong/multiple-parent, empty/duplicate/modified/mode/case delta and raw-commit tamper rejection |
| `P248TopologyNegativeTests` | `test_status_rejects_staged_dirty_ignored_and_extra_paths` | Synthetic status controls at P247 and a distinct HEAD reject staged additions, extra/ignored paths and staged/unstaged tracked edits |
| `P248TopologyNegativeTests` | `test_environment_override_refuses_before_git` | Injected `GIT_INDEX_FILE` causes refusal before any Git call |
| `P248TopologyNegativeTests` | `test_draft_addition_alias_refuses` | Synthetic draft identity alias to a tracked source file causes the exact alias refusal, with a draft projection available on a child |

The four topology methods are parser/status/environment/alias controls.
They supply no original historical replay evidence or production acceptance.
Their synthetic parser control supplies no genuine committed-case run.

Unittest imports occur before class setup authentication, as with existing
project tests. This local engineering diagnostic provides no hostile-code
execution isolation or signed runner attestation. Every later source topology
and exact source revision requires its applicable validation and review.

## Open Failures & Prior-Issues Review

| Issue and evidence | Severity, root cause and affected route | Bounded response and tests | Review and disposition |
| --- | --- | --- | --- |
| Four historical P234 failures retained by P245, genuine source `096048db17c7c1f9402dfd16a7deb31e9ebdc81d` | High acceptance blocker. Exact historical branch prerequisite stops modern public calls before subsequent assertions. A/B and older public routes share the terminal guard | Preserve all four FAIL records and original bytes. C01-C05 add explicit historical witness and current assertions with per-property gaps above | Independent H/C acceptance approval outstanding. HOLD |
| P246 acceptance mapping finding | High. Complete-source authentication does not prove historical replay or original reader causality | Trace original helpers, all states/targets and public chain. C03/C04 target current reader causality, C05 observes original denial routing | Host-native draft runs reported below. Independent acceptance review pending. HOLD |
| P245 hidden-source and cached-proof incidents | P2 findings recorded in P245 document. Incomplete inventory or stale proof can hide predecessor tampering | Reuse repaired complete source/index/raw-byte primitives and bracket observations. Preserve all 52 local and 7 hosted P245 assertions | P246 reported no further material implementation findings in bounded P245 scope. Initial five-case draft source GO precedes final expanded topology. Final review pending. HOLD |
| P245 Windows ctime and hosted temp-alias failures | P2 environment/fixture failures described in P245 evidence | Reuse unchanged bounded reader, run against assigned checkout, no new temporary repository or OS-policy workaround | Host-native draft PASS reported below. Committed-case validation and final review remain open. HOLD |
| P246 workflow exit-accounting finding | Medium. Requested outer HOLD exit 3 differed from observed hosted outer exit 1, while native children reported 0 | Preserve the distinction. P248 uses standard native unittest exit accounting and makes no hosted workflow claim | Existing P245 accounting finding remains open. HOLD |
| P96 effect/revoke race, separate Python WinCred routes, SEC03/04 evidence | High existing production blockers identified by P246. Alternate effect routes and missing qualified service/broker evidence | P248 scope is source assertions only. Existing denial-only model and all older code remain byte-preserved | Qualified approvals 0/7, full product regressions 0/3, real-key NO-GO, production HOLD |
| Codex sandbox Python launch unavailable | Environment blocker. PowerShell returned CommandNotFoundException before Python started, zero tests executed | Preserve both original sandbox launch failures. Separate Nayeon host-native receipts are recorded below | Sandbox result remains zero executed. Host draft PASS does not close final review or committed-case validation. HOLD |
| Interrupted prepublication document patch | Documentation recovery issue. apply_patch context mismatch interrupted the Codex doc edit, then the PowerShell wrapper aborted on Codex stderr. Surviving source/test changes are preserved | Read actual current mapping and perform this bounded doc-only recovery. Preserve prior evidence | Prior prepublication patch remains incomplete with no final repair receipt. This interruption establishes neither source failure nor a safety block. Review HOLD |
| P247 runtime | Existing runtime HOLD retained from the additive model checkpoint | P248 provides bounded source assertions without product effects | P247 runtime HOLD remains explicit |

The accessible P246 transcript was read locally at
`D:\Nayeon\P245_SECURITY_EVIDENCE_20261115\P246_CODEX_RELEASE_GATE_TRIAGE_20261115.jsonl`.
Its SHA-256 is `27FF353541952922205173C7300349367F71503493E5FA7334397B0B986DD59F`.
Its final review reports supplied 59/59 P245 evidence and the outer-exit
discrepancy, while explicitly limiting artifact revalidation and native
execution. Those are prior review reports. P248 did not rerun or independently
authenticate their hosted artifacts. P247's committed additive model is part
of this exact HEAD and remains unchanged.

## Validation record

The initial native availability command was attempted through PowerShell.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B --version
```

Tool process exit 1, `CommandNotFoundException`. Python did not start.
The original focused command for the three-addition draft was below.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B -m unittest -v tests.test_p248_p76_properties
```

The focused command was attempted. Tool process exit was 1 with
`CommandNotFoundException`, `FullyQualifiedErrorId` also
`CommandNotFoundException`. Python did not start. Actual executed test count
is **0** for that Codex sandbox attempt. Its pass/fail/skip counts and native
Python exit are unavailable. Source inventory at that attempt was **5**
methods. Current inventory is **9** named methods. Syntax compilation and
compileall were unexecuted in that sandbox attempt. Broad regression remains
unexecuted and full product regression qualification remains **0/3**.

### Separate Nayeon host-native receipts

The following are user-supplied host evidence and review receipts. This
doc-only recovery neither executed tests nor independently rehashed those
external logs.

| Receipt | Actual reported result | Log or receipt SHA-256 | Scope and remaining gap |
| --- | --- | --- | --- |
| Original focused R2 | 5/5 PASS, native exit 0, 33.888s | `D:\Nayeon\P248_SECURITY_EVIDENCE_20261115\P248_NATIVE_FOCUSED_R2_20261115.log`, SHA-256 `8049102C6A826E35A0920704D7C1FD8E802DB6A2589C1A663F5AA8C8CEA15AD8` | Original five current-property methods on the draft |
| Post-hardening draft R3 | 9/9 PASS, native exit 0, 49.158s | `D:\Nayeon\P248_SECURITY_EVIDENCE_20261115\P248_NATIVE_DRAFT_R3_20261115.log`, SHA-256 `9FDA05E88668783335CB268B0625AD45B7F43E5F7E550422B2889813544F5A76` | Five current-property plus four synthetic topology negative methods on the draft. Genuine committed-case validation remains open |
| Initial read-only Codex source review | `REVIEW_SOURCE=GO` for **DRAFT ONLY**, exit 0 | Review log SHA-256 `6725AE780334ACD62254BBB9C514EB5F40B2430D941E08308307E8EDE5771F9C` | Reviewed initial five-case source. Two LOW fixes are now targeted. This review precedes final expanded topology and grants it no approval |

The interrupted prepublication Codex document patch has no final repair
receipt. Its context mismatch and wrapper stderr abort remain recorded as an
incomplete documentation operation. Source/test changes survived. The supplied
native PASS receipts remain separate evidence. Final expanded-source review,
genuine after-commit native validation and independent review remain open.

### Preserved earlier bounded checks

The following records describe the earlier checks and retain their original
results. This recovery performed only the final document/scope checks recorded
at the end.

| Bounded check | Command or exact operation | Observed result |
| --- | --- | --- |
| Tracked and staged scope | `git diff --exit-code HEAD`, `git diff --cached --exit-code` | Both exits 0, empty diffs |
| Complete draft inventory | `git status --porcelain=v1 -uall --ignored=matching` | Exit 0, exactly the three P248 additions listed above, no ignored entries |
| Ordinary Git flags | `git ls-files -v`, grouped by leading flag | Exit 0, 1,018 entries all `H`. P248's runtime proof additionally requires P245 raw-index validation |
| Raw tracked bytes | `git ls-files --stage` plus the same ordered paths piped to `git hash-object --no-filters --stdin-paths`, compare every OID | Exit 0, 1,018/1,018 raw files match index |
| Index versus HEAD | `git diff-index --cached --quiet HEAD --` | Exit 0 |
| Frozen witnesses | `Get-FileHash` SHA256 on all six `source.FROZEN` paths | Exit 0, all six match the literal P245 pins |
| Sealed 8.34 source | Read twenty literal pins from `CANDIDATE_SHA256`, obtain each raw blob using `git --no-replace-objects cat-file blob b0490cd9e72104a74a32dc5315cbc55bc4034676:<path>` through .NET binary streams, zero exactly one self literal, SHA256 compare | Exit 0, 20/20 matches. This is a PowerShell/.NET static witness check |
| B parent/tree/tag prerequisites | Quoted `git rev-parse '4110fa69849f8127a325f9a9001284cd1bd3a59c^{tree}'`, exact `show-ref`, `cat-file -t` and quoted tag peel | Exit 0, original tree `747f172144794d687251545ca923d5ebb5b1551b`, tag object `7496961c83de9607402dcdabff25917674d6688a`, type `tag`, peel to original A parent |
| A adapter prerequisite | `Get-FileHash tests/phase8_byok_scope_migration.py -Algorithm SHA256` | Exit 0, `7EAA989E141E17C7303EDE283B3A979DC77680FA5B74D86A75DC8233EA4324B1`, equals B's original raw adapter pin |
| Whitespace | `git diff --check` and .NET checks for trailing spaces/tabs and final LF in each new file | Exit 0. New files are untracked, so their whitespace was checked separately |
| Additive diff inspection | `git diff --no-index --check -- /dev/null <each new path>` | Each exit 1 for present differences, no whitespace diagnostics |

One exploratory PowerShell Git command used an unquoted `^{tree}` suffix.
PowerShell interpreted the braces as a script block and Git reported an
ambiguous `dAByAGUAZQA=` argument. The quoted invocation above returned the
correct tree and exit 0. Repository contents remained unchanged by that read.
`rg` was unavailable, so bounded PowerShell reads and .NET regex searches were
used. These tool failures establish no test outcome.

The complete raw tracked-byte equality check preserves every original report,
historical method, branch guard, witness, P245 file and P247 file at the assigned
HEAD. Only the three new draft files appear in the scope diff. Final identity
remains the assigned branch and full HEAD. Work is unstaged and uncommitted.

## Independent-governance decision request

Independent governance must decide which original historical properties still
require positive admission or replay evidence and whether each current
assertion can receive separately bounded credit. The unresolved evidence
includes P01/P03/P04 public positive admission and restoration, P05's nine
fixture/state positives, P06's eighteen historical causal corruptions, P07
fixture restoration, P10/P11 positive public-state agreement and P02/P13/P14
original reader-route, error-contract and restoration evidence. P08/P09/P12
have host-reported current witness coverage, subject to acceptance review.
The synthetic topology controls cannot close those historical gaps.
No full historical equivalence is claimed.

The four original P76 **FAIL, native exit 1** records and P76 guard remain
preserved and unwaived. **P247 runtime HOLD**, **P96 effect/revoke race**,
**SEC03/04 open**, **0/7 qualified approvals**, **0/3 full regressions**,
**REAL-KEY NO-GO** and **PRODUCTION RELEASE HOLD** remain controlling.
This file remains **DRAFT** with no new product effects.

## Doc-only recovery scope

This recovery edits only this mapping document. Final source checks passed
for Markdown headings/tables/fences, all fourteen property rows, nine named
inventory rows, trailing whitespace and final newline. Tracked and staged
diffs are empty. Branch/HEAD and the three untracked P248 paths match the
assigned checkpoint. Source/test SHA-256 values match the pre-edit observations.
This recovery executed zero tests.
The requested disposition is **independent review HOLD**. The earlier
interrupted prepublication run retains its incomplete status and absent final
repair receipt.
