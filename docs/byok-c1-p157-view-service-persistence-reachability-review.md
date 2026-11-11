# Nayeon v1 — P157 view-to-service/persistence reachability

**11 November 2026 | OM v2.1 | ADDITIVE SECURITY EVIDENCE ONLY | RELEASE HOLD**

## Verified predecessor and custody

P156 finished at SHA fb54dfcd6dafb9a5ec474e7c3b32df7dac849a98, draft PR #81, hosted Windows final run 43051898453. The P156 original current-user fake-WinCred/Tk suite passed 36/36, manual launcher fake-Popen/Tk suite passed 25/25, and import-effect denial passed. The original Phase8.31 static import-closure still failed and its retired fake-Tk-root teardown error was preserved. P157 must not change original source, original tests, P76/P85 exact branch refusals, the P139 native handle policy or the P140 frozen signed-launch gate.

The isolated P157 branch is based on that exact SHA and adds only this document, an evidence-only Python driver and a Windows workflow. Original Kristian product worktree remains untouched.

## Concrete architectural risk

ConnectionWindow.show_pending_custody_advisory lazily imports the P84 read-only presentation projection. That projection imports the legacy onboarding-status view, which imports reconciliation and recovery advice. The resulting **13-module transitive graph** contains connection_bootstrap, connection_service and connection_persistence: actual definitions with filesystem load/save/replace capability. Their presence in a module import graph does not itself imply UI invocation or grant a separate OS right. It does broaden coupling, maintenance risk and potential future capability access. Python imports are not a sandbox.

## Original and additional defensive tests

P157 hosted real Windows-2025 Python 3.12 checks exact P156 ancestry, only three additive audit files, clean checkout, unchanged P139 native opened-handle disposable C: temp root, and the original P156 four-method thread-guard/lazy-import scope.

P157 enumerates direct calls of the actual ConnectionWindow advisory method, present_pending_custody_advice, PendingCustodyStatusView.__post_init__ and assess_pending_credential_action, fails on new direct service/store/native/file/process calls and checks canonical typed advice.

A real Tk ConnectionWindow child then denies ProviderConnectionFileStore.load/save, ProviderConnectionService.initialize/replace/clear, bootstrap_provider_connection, observe_connection, Path.open, os.replace/fsync/system, tempfile.NamedTemporaryFile, subprocess.Popen, ctypes.WinDLL and socket network connections. It exercises 63 typed combinations of seven legacy observations, three pending states and three actions against both pure mapping and actual Tk output, including forged assessment, arbitrary-text and wrong-thread refusals. Any attempted native/service/file/process effect is a test failure. NO production keys, live WinCred writes or provider calls.

Four ORIGINAL unchanged test modules also run with real native Windows child exits/logs: test_pending_custody_status_view, test_p86_live_pending_status_integration, test_p87_readonly_custody_observation and test_p88_pending_observation_lifecycle. Native stdout/stderr, test counts, SHA-256 hashes and pass/fail status are preserved; any failure remains HOLD.

## Review discipline and residual holds

An isolated type-only legacy-status extraction could reduce this import graph, but would change product source and historical migration governance and is out of this diagnostic scope. Do not move imports merely to bypass the original Phase8.31 assertion. Passing the bounded specific UI calls does not establish universal Python isolation or qualified independent security approval.

Current-user WinCred limitations, transient key lifetime, same-user threats and non-durable reconciliation remain. Original privileged C1 G0–G6, including P96/P124, remain OPEN. Full accepted unfiltered Windows product regressions remain 0/3. Qualified independent security and historical governance review are NOT OBTAINED. Signed/pinned main/helper/installer and Smart App Control/WDAC owner GO are absent. Original P76/P85 and Phase8.31 failures remain immutable. No release merge, real credential, protected Windows operation or Google Drive master workbook update is authorised.

**P157 is a genuine Windows security-evidence packet, not a production GO.**


## Genuine Windows discovery: original widget-count assertions diverged after P133

First P157 native hosted Windows source SHA 5954412d4f46c765fbcd80ff69bfe7dff88b1984, run https://github.com/krismcan/Mark-LV/actions/runs/43058404118, job 130653972929. This initial run was correctly **RED** because 3 original historical assertions actually failed. Full evidence archive ID 13871409812, SHA256 AD15573EA5E7F9AF9DE3A025A76E1570B83525C0655D0942E919D943E58E63BD.

- P157 new adverse real Windows Tk child: native exit 0/PASS; 63 typed combinations, 63 actual UI updates, 3 forged/wrong-thread refusals, 0 transitive service/store/native/process/network effects. Original raw log SHA256 DB77CD33863BF3DE4F0CCBA169EC1E2C4E90DBFE2FA47C6C8BC54C12A4A48666.
- Original P84 exact module: native exit 0, 6 PASS, raw SHA256 FFE7886E055173C50023DDF292D4C014B4A1B2AAB8CEC2368A2D75D6A55400C5.
- Original P86 exact module: native exit 1, 7 ran, **2 FAIL / 5 PASS**, raw SHA256 A68EC640704AAFC3F23B056E09A8473CE1A214FA114296203C295AB95261629E.
- Original P87 exact module: native exit 1, 18 ran, **1 FAIL / 17 PASS**, raw SHA256 04EB25F7A12B5D1DD9C89BCD7590C6FDE7912CBF494901049BC4F6DDB2D7E8DA.
- Original P88 exact module: native exit 0, 10 PASS, raw SHA256 F15744F633D2D6F8EB19509EF2D06186FDADBD3012847C5CA5783874F0B2E556.

The three exact untouched old assertion failures are:
1. P86 test_live_connection_page_default_is_explicitly_unobserved
2. P86 test_no_credential_action_and_no_implicit_refresh
3. P87 test_production_default_remains_not_observed_without_any_session

All three assert the original Connection page contains exactly TWO ttk.Button widgets. P133 intentionally added a third button, labelled Open local key setup (offline, not connected), in addition to Back to Conversation and Manage provider (offline preview). The same product source has never created a secret or provider effect merely by adding its explicit manual-launch button. P156 previously tested P133's 25 original explicit/fake launch controls successfully. This is a historical exact widget-inventory difference, not evidence of an executed WinCred or provider effect, but the OLD assertions remain legitimately FAIL/HOLD until separately approved historical regression migration.

After recording this causal finding, the P157 **audit-only** runner is permitted to finish green only when all exact known original two-button failures are reproduced with genuine native negative exits and NO unexpected original errors/failures; its machine ledger still marks every P86/P87 affected original test as FAIL/HOLD. This does not edit an old test or make an original failure a test PASS. The new independent real-Tk adverse probe additionally verifies the exact three intended button labels, the new control disabled when no explicit launch callback is supplied, and zero automatic credential/store/provider effects.

If the exact expected original failures change, any new test fails, an effect is reached, or P139/P156 source identity drifts, P157 evidence collection must fail closed.

## Release recommendation

Retain the three original P86/P87 assertion FAIL/HOLD records and the original Phase8.31 branch/import-closure HOLD. An authorised qualified historical-governance reviewer should assess a separate branch-aware post-P133 widget-inventory successor assertion; original sealed historical sources/tests must not be rewritten or suppressed. Do not remove the requested explicit offline setup button simply to reproduce a two-button pre-P133 snapshot.

The project still needs three complete accepted full-product Windows regressions, signed/pinned production package, owner Code Integrity approval and qualified independent security review before any real-key or production deployment decision.
