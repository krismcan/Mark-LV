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
