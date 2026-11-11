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
