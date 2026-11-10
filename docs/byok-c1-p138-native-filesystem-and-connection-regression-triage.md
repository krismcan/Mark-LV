# Nayeon v1 — P138 Native Windows regression failure triage and branch-aware governance facts

**10 November 2026 | OM v2.1 | BYOK C1 user-scoped RELEASE HOLD**

## Verified predecessor

P137 exact HEAD `ad67c51aac72baaec41725693b267b415c3373e7`. It froze the real offline BYOK setup app to a genuine Windows PE but did **not** run that unsigned application, and safely executed a separate fake-store frozen Tk smoke executable on disposable Windows. Still no signed production launcher, Smart App Control acceptance or real user API key.

P135 actual unfiltered Windows full-product Python suite attempted 3 times on genuine Windows-2025: all 3 timed out (exit 124), no complete test count. The authentic raw log displayed 1,637 completed PASS, 37 FAIL, 7 ERROR, then one historical P8 BYOK B source-integrity test unfinished. P136 isolated the exact last test, reproduced 42-second timeout and captured four stack traces progressing through nested historical Git object-tree replay. None of those assertions are waived.

## What P138 actually isolates

The 37 FAIL cases are not uniform. Some are historical exact-branch or frozen-source seal checks, but **three** P86/P87 Connection-window tests assert an exact old **2-button** count. P133 deliberately added the explicit third offline local BYOK setup button. This is an accepted feature delta, but it makes earlier exact UI-count expectations stale. Historical tests remain unchanged; a qualified independent test-governance reviewer must explicitly accept a replacement current-branch UI contract and decide where frozen historical checks run. Do not silently modify original counts or report historical tests green.

**Seven** P135 `ERROR` cases ran genuine native Windows file and directory fixtures:
- `tests.test_directory_creation.NativeDirectoryCreationTests.test_only_self_owned_single_child_directory`
- `tests.test_directory_deletion.NativeDirectoryDeletionTests.test_owned_native_success_and_child_races_with_exact_handle_lifetime`
- `tests.test_directory_listing.TemporaryWindowsDirectoryTests.test_lists_only_self_created_temporary_directory`
- `tests.test_file_copy.NativeCopyTests.test_owned_binary_copy_no_overwrite_and_source_change_after_execution`
- `tests.test_file_creation.NativeCreationTests.test_creates_only_one_self_owned_empty_temporary_file`
- `tests.test_file_deletion.NativeDeletionTests.test_owned_fixture_real_binding_disposition_close_and_absence`
- `tests.test_filesystem.TemporaryWindowsFileTests.test_reads_only_created_temporary_file_through_native_handles`

The regression triage first runs each of these 10 exact failed original test IDs **unaltered**, in a separate Windows Python process using a bounded 50-second window, logs genuine exception type/native exit/test count/full log SHA-256, and retains all raw logs in Actions. Distinguish a repro in isolation (actual functional/environment issue) from only-in-full-suite interference. The test-owned paths are disposable `tempfile.TemporaryDirectory` resources inside a hosted runner; no user filesystem, secret, WinCred or privileged service.

This is diagnostic work. A successful diagnostic runner can legitimately contain reproduced failure/ERROR cases, which are reported explicitly. It must NEVER be represented as a passing full regression or an approved C1 release.

## Independent acceptance and signing route (not complete)

Before real-key use: (a) classify/repair any current product filesystem regressions without weakening protected file identity/access tests; (b) get branch-aware old-seal/current-branch suite design reviewed and execute THREE complete approved Windows product regressions; (c) establish pinned issuer/signing certificate, signed offline app and signed desktop/helper packaging, and obtain Smart App Control owner acceptance; (d) get independent reduced current-user security assessment. No known signing key or signed app is available. P133 `LocalByokLaunchBridge` intentionally refuses frozen main desktop mode until legitimate signed launch path approved.

No real API key, provider request, WinCred mutation on Kristian, privileged service/HKLM/TPM, unsigned binary executed on Kristian, SAC security change, P62 blocked-command retry, GitHub merge/release or draft-only Google Drive master/dashboard edits.

**P138 isolated failure-classification only, original G0–G6 and reduced user-scope release gates remain OPEN.**
