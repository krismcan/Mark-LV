# Nayeon v1 — P155 Targeted Non-P76 Windows Security and Lifecycle Recovery

**11 November 2026 | OM v2.1 | DRAFT ENGINEERING EVIDENCE | PRODUCTION RELEASE HOLD**

## Authoritative custody and change boundary

P155 is isolated from exact Git commit 2103ccc658f0cea474ec8f5bc945eacb664771cd, the verified open draft P154 PR #79 head. P155 branch: byok-c1-p155-non-p76-security-lifecycle-recovery-20261111. Initial P155 GitHub search found no existing branch; no active Desktop Commander sessions. Kristian was online.

The original D:\Nayeon\BYOK_C1_PRODUCT_20261028 worktree was verified at HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1 and has exactly 17 pre-existing dirty paths. It was not edited or reset. The original verified clean source used for Windows diagnostics was D:\Nayeon\BYOK_C1_P154_FINAL_GITHUB_SOURCE_READBACK_20261111 at HEAD 2103ccc658f0cea474ec8f5bc945eacb664771cd.

P155 changes only additive audit, notes and workflow files. **No original product, old tests, P76/P85 branch seals, WinCred security source, P140 signing pins, credential storage, SAC/WDAC policy or protected release branch changes.**

## Actual native original Windows diagnostic results on Kristian

All three cases ran against unchanged original tests from exact P154. Python 3.14.7, native Windows; exit codes were captured immediately from the Python process; PowerShell stdout/stderr were retained as separate original host logs.

| Original test case | Native exit | Complete unittest footer | Status | Captured host output SHA-256 |
| --- | ---: | --- | --- | --- |
| tests.test_phase_832_lifecycle_assurance.Phase832StaticContractTests.test_every_direct_owned_method_has_first_pure_thread_gate | 1 | Ran 1 test; FAILED (failures=5) | HOLD | 22F457C9D4232738385ADD326522EDFEABA0AB05B25190AEF9E5E1CF240F4928 |
| tests.test_windows_credential_backend.ScopeGuards.test_exact_import_boundaries_and_no_forbidden_native_calls | 0 | Ran 1 test; OK | FOCUSED PASS ONLY | B29900E80535C681B4DCA0F287C340C9AB52A42A651083E3BFD741E2CB77A9D5 |
| tests.test_windows_credential_backend.ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused | 1 | Ran 1 test; FAILED (failures=1) | HOLD | 1578FB5C6F455A5C6F7D4855ED1BBC087A1515CE55A29B5EA5DEFC485091DD93 |

Host logs remain under D:\Nayeon\BYOK_C1_P155_NONP76_DIAG_20261111. No secrets were entered; neither Credential Manager write nor provider network verification was requested.

## Phase 8.32 non-P76 failure classification

The original first-thread-gate AST assertion had five subtest failures, all because it tests a method's *first AST expression*, which for these newer methods is the Python docstring rather than the first executable statement:
1. OfflineWorkspaceApplication._open_local_byok
2. ConnectionWindow.begin_synthetic_pending_observation
3. ConnectionWindow.cancel_synthetic_pending_observation
4. ConnectionWindow.publish_synthetic_pending_observation
5. ConnectionWindow.show_pending_custody_advisory

The original source shows an explicit self._require_creator_thread() immediately after each docstring. A method docstring is not an executable UI or credential effect. **Provisional category: historical source-shape assertion mismatch, pending real wrong-thread adverse probes.** This does not waive the five genuine failures. A true guard position defect must be repaired rather than classified away; the additive hosted P155 collector independently inspects the first executable statements and invokes real source methods on a synthetic foreign thread.

**No source repair yet justified:** moving or deleting docstrings merely to satisfy the old AST shape would conceal the versioned contract mismatch and alter frozen scope for test appeasement. Preserve the original test and request qualified historical regression governance before treating a versioned new test as equivalent.

## Windows Credential Manager contract classification

One original static import test *passed* on current source, but its separate historical allowed-consumer test *failed* with:

AssertionError: 'nayeon.secrets.contracts' unexpectedly found in {'nayeon.secrets.windows_credential', 'nayeon.secrets.contracts'}

The original test's historical allowed-consumer list predates new user-scoped BYOK modules. Current source explicitly imports canonical contracts in nayeon/brain/local_byok_user_scope.py and nayeon/desktop_alpha/local_byok_window.py. The narrow P132 design intentionally introduced a standalone offline human Review → Approve window and fixed-slot user-account credential controller, rather than a privileged writer. Its security status is nevertheless **not automatically cleared** by being intentionally introduced.

**Provisional category: historical consumer import allowlist expansion requiring separate trust-boundary/adverse review.** The independent reviewer must explicitly verify exact permitted consumers, no accidental credential export, no startup retrieval, no provider calls, fail-closed WinCred errors, one-use consent and isolation. The original historical allowlist must not be edited or bypassed to turn red to green.

## Authenticated historical failure register (original P144)

The original P144 artifact 13804256598 has verified archive SHA-256 4D62B64CB9872601AF271B8D47DE1CE7B76468E9013F0A9A8417CF9DC79C41E3, 15 genuine original Windows HOLD modules, 30 original FAIL/ERROR records and full per-module test logs. P154 independently authenticated this evidence.

| Failure domain | Original native disposition | P155 classification status |
| --- | --- | --- |
| Phase8.31 Tk/import closure | 19 tests, 2 failure/error records, EXIT 1 | Import/fixture causes unresolved; root retained by unittest _SubTest is not itself a production leak |
| Phase8.32 lifecycle | 14 tests, 5 failure/error records, EXIT 1 | Five first-AST-statement/docstring mismatches; adverse worker-thread test needed |
| Windows Credential Manager | 24 tests, 2 failure/error records, EXIT 1 | Historical allowlist vs new current-user source, independent review required |
| P76 and P85 | Historical exact-branch refusals | Security refusals remain intentional; no branch spoofing |
| P77 historical causal tests | Original causal errors differ under later branch | Historical seal and causal precedence, governance required |
| Presentation/provider 9 modules | Genuine unchanged P144 failures | Original raw tracebacks required before blame or repair |

The P155 hosted Windows job will reauthenticate and retain all 15 original P144 logs under their original SHA-256, extract exact failure IDs into machine-readable custody, and run three narrow original methods unchanged on Windows Python 3.12 under the verified P139 local-TEMP handle policy. Collection PASS is *not* historical test PASS, nor full-suite clearance.

## Completed P155 hosted Windows evidence, source authentication and raw failure analysis

**Verified hosted run:** https://github.com/krismcan/Mark-LV/actions/runs/43046066329

Run on disposable Windows-2025 Python 3.12, genuine GitHub SHA fe363a440bbc93bea6e710a2714162efb349e9db. GitHub Actions job 130610193128 returned success **for evidence collection only**. Original P154 parent SHA and only three additive P155 diagnostic paths were confirmed. The P154-authenticated original P144 ZIP was independently retrieved again and all 15 complete original Windows raw logs and all 30 original FAIL/ERROR records matched their pinned SHA-256 identities.

**Evidence ZIP artifact 13867820258**, uploaded at 2026-11-11T15:12:56Z, outer archive SHA-256 4B7FA12077080AA1A6A6A560FD4F446B5F5556EC300B77394B12B8A54241E45C. Contains 15 authenticated P144 historical raw logs, three fresh original focused Windows logs, and the machine-readable P155 JSON custody/decision ledger. Artifact expiry: 25 November 2026; retain before expiry.

**P155 focused native Windows 3.12 original test outcomes:**

| Original unchanged case | Native exit | Original outcome | Raw log SHA-256 |
| --- | ---: | --- | --- |
| Phase 8.32 first pure thread gate AST assertion | 1 | 1 test, 5 failed subtests, HOLD | A3CBF50DA530A918AAC355BD40B78F4A9E160C4351CA8E4F1743D6E39D7459D0 |
| WinCred exact import boundary/native-call prohibition | 0 | 1 test, PASS only this focused case | 1529E130917F01513DC1DA48D242F36799B9DD607339FDDBAE73894B0C293F9E |
| WinCred only approved consumers/legacy store unused | 1 | 1 test, 1 failure, HOLD | FD9EFF7D7504BCEE43D2EF6518218504B19B6608A7BCDFD3C3A7DFBC0C59C2B3 |

**Adverse synthetic thread-security results:** inspected 118 original owner-method definitions in six production classes; all 118 used self._require_creator_thread() as the first executable statement after an optional docstring. Exactly five carried docstrings that violate the older literal first-AST-node test. Invoking each of those five actual production method objects on a synthetic foreign worker thread, with the real class thread gate bound to a non-Tk sentinel, produced five immediate WRONG_THREAD refusals before any other object attribute access. This is focused defensive evidence, not an assertion about all Tk lifecycle behavior or a qualified security sign-off.

**New evidence-based source-failure grouping (all historical failures remain red):**

| Original P144 source | Exact failure IDs or raw signature | Supported causal category | Decision |
| --- | --- | --- | --- |
| Phase8.31 effect isolation (19 tests, 2 records) | test_static_production_import_closure_forbids_test_and_effect_routes; tearDownModule | Static import closure forbids nayeon.brain from workspace_window.py, while current source has four lazy imports from nayeon.brain.pending_custody_observation_boundary/status_view. A separate fake Tk root remains held by unittest _SubTest at module teardown; P146 scope did not establish production leakage. | Two independent holds: contract boundary change requiring design review, and test-host ownership/teardown investigation |
| Phase8.32 lifecycle (14 tests, 5 records) | five first-method-node failures for specified app and ConnectionWindow methods | Historical docstring-before-guard literal AST-shape mismatch; 118 first-executable gates verified and 5 worker denials reproduced | Do not alter old test; independent equivalence and UI threat review |
| Windows Credential Backend (24 tests, 2 records) | test_exact_phase_8_3_delta_and_other_production_frozen; test_only_approved_secret_consumers_and_legacy_store_unused | First source gate cascades to P76 exact-branch refusal; second old consumer allowlist rejects current user-scoped modules importing canonical secrets contracts and native WinCred | Split branch-security and consumer trust boundary governance; no replacement of original tests |
| P76 (10 tests, 2 records) | test_five_public_routes_use_same_source_proof; test_new_public_and_private_gate_agree | Direct exact frozen P76 historical branch refusal | Preserve true security refusal |
| P85 (6 tests, 1 record) | test_exact_child_or_precommit_source_gate_succeeds | Direct exact frozen P85 review branch refusal | Preserve true security refusal |
| P77 (7 tests, 4 records) | 3 historic tamper causal-error tests and test_phase10_2_tag_ref_rechecked_after_live_source_window | Earlier P76 frozen branch refusal masks three requested historic causal exceptions; the fourth sees no expected tag ref calls because earlier gate refused | Governance of causal coverage required |
| Presentation 6 modules (112 observed original tests, 11 failure records) | Document/bootstrap/persistence/service/view/identity scoped historical tests | Original raw stack traces descend through Phase10.2 → Phase10.3 → P76 exact frozen branch refusal | Do not re-label these modules green; historical branch-security refusal is established, but their other passing cases cannot substitute for current-branch approved equivalence |
| Provider 3 modules (48 observed original tests, 3 failure records) | Composition/startup/service sealed scope assertions | Raw stack traces likewise end in frozen P76 exact branch refusal | Governance, not ad hoc provider/network repair |

**Important:** The module test counts shown above are those of the original unfiltered P144 runs, not new full-product passes. Every failed module remains a HOLD even when the causal prefix is a deliberate security refusal. Original test bytes and production source remain unchanged.

## P155 repair decision after the focused evidence

No defensible direct source correction has been established at this checkpoint. The P76/P85 refusals must be preserved; the Phase8.32 code enforces the thread guard as the first executable operation on all inspected methods, including five confirmed foreign-thread refusals. The WinCred consumer boundary and Phase8.31 brain import closure represent real **architectural scope changes** requiring independent threat and current-branch regression-governance decisions, not permission to auto-widen older tests. The P146 fake-Tk unittest retention observation is not grounds to rewrite runtime code without evidence of a production leak.

No failed test was patched, no production source changed, and no regression or release gate was declared recovered. Next recommended engineering checkpoint P156: independently review the versioned contract boundaries and current-branch negative test equivalence; isolate and investigate Phase8.31 lazy-import authority, WinCred fixed-slot consumer authorization and Tk ownership in separate bounded adverse tests, while preserving all original failures.

## Internal adverse review versus external authority

Internal engineering assessment: **do not patch either historical AST/allowlist test**; perform focused adverse thread and credential boundary diagnostics and recommend explicit branch-aware governance. This is not a qualified independent security approval. A demonstrable runtime defect would instead require minimal product repair and repeated real Windows adverse tests.

## Mandatory unresolved release holds

- Three complete genuine accepted full-product Windows regressions: **zero of three**; original P135 three full attempts all timed out native EXIT 124. Independent module recoveries cannot substitute.
- Qualified independent user-scoped security reviewer: **not obtained**.
- Independent historical regression-governance approval: **not obtained**.
- Genuine signed and pinned main app, helper, installer and publisher cert: **not obtained**.
- Smart App Control / WDAC Code Integrity owner GO: **false**.
- Original privileged C1 G0–G6 including P96/P124: **OPEN**.
- Production key entry, provider validation, protected Git merge, production release, Google Drive master release closure: **not authorised**.

**P155 remains engineering-only; BYOK C1 production release remains HOLD.**
