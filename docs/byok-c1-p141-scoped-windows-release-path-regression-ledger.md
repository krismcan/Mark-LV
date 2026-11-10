# Nayeon v1 / BYOK C1 P141 — Repeatable scoped Windows release-path regression triad

**10 November 2026 | Operating Model OM v2.1 | DRAFT/UNMERGED | USER-SCOPED RELEASE HOLD**

Exact direct parent: P140 signed-companion NO-GO `9c47bac3308822e11300381017b30e913ffbc211`.

## Security-governance distinction — do not confuse test inventories

P135 attempted **three unfiltered FULL Python-product Windows regressions**. All timed out after 600 seconds, without reaching a `Ran N tests` footer. Authentic raw logs captured 1,637 completed PASS, 37 FAIL and 7 ERROR before the same historical BYOK-B integrity fixture stalled. P136 proved through four genuine faulthandler traces that the single unchanged test repeatedly traverses deep Git history, showing expensive progressing work rather than a proven deadlock. P138 independently reproduced 10 failures (7 Windows filesystem unsafe_path and 3 stale P86/P87 UI two-button assertions). P139 corrected **ONLY the disposable runner test fixture environment**, rerunning all seven **original unchanged real Win32 filesystem tests** under a newly owned, opened-handle-verified local C: directory: 7/7 PASS. P140 implemented the frozen desktop-to-companion signed-image gate with every approval pin empty / release policy false, so genuine frozen launching remains unavailable, and 474 preserved Windows native focused tests plus 195 Python test executions passed.

**None of that makes the P135 unfiltered triad green.** Its 37 failures include old Phase8/10 frozen source/branch seals, older product-consumer allowlists, three obsolete P86/P87 Connection-page assumptions, and P132/P133/P134 explicit per-branch migration tests that are intentionally tied to their own historical HEADs. The seven native filesystem errors have a known safe-fixture pass but are not a source guard defect/permission to weaken Win32 validation. A qualified security-and-test reviewer must authorise an explicit branch-aware migration policy before any scope exclusions could count toward G6. No reviewer GO has been obtained.

## What P141 actually tests

P141 adds **ONLY three new paths** (new Windows CI workflow, self-contained release-path triad driver, this report). It does not modify original production code, original P49/P96 native files, old migration/freeze tests or filesystem guard.

On a clean disposable GitHub-hosted Windows x64 runner, the driver repeats the **exact same named current-user functional test classes three times**. Test scope is visibly enumerated in the driver, with no plugin filter or fragile `-k` matching:

- P140 `FrozenSignedCompanionGateTests`: real negative and explicitly mocked positive authorisation wiring; immutable P140 release pins remain blank and no actual signed launch is authorised.
- P133 `LaunchBridgeTests` and genuine Windows `ConnectionPageTkLaunchTests`: explicit offline click, no automatic spawn, stale pane, second click and provider-key environment stripping.
- P132 `LocalOfflineControllerTests`, `WindowsUserScopeNativeMutexTests`, genuine Windows `WindowsLocalByokRealTkTests`: explicit once-only save/replace/delete review with fake WinCred and actual OS mutex.
- P134 `GenuineEphemeralWinCredTests`: **actual Win32 CredWriteW/CredReadW/CredDeleteW** on fresh UUID-random NONKEY Generic Credential target on the disposable hosted Windows account only; real `openai.api_key` target forbidden and never touched; unconditional per-test deletion.
- Original applicable functional backend/WinCred adapter, existing first-run credential UI, trusted operation host, bounded lifecycle and Connection page tests (without frozen exact-branch seal classes).
- Each pass separately runs **all seven original native Win32 filesystem tests** through the unchanged P139 runner with a newly owned C-drive local fixture checked by the original opened-handle no-reparse policy. No `unsafe_path` fallback, real filesystem permission change or skipped assertion.

Each completed pass records native exit, actual `Ran N tests` count, PASS/HOLD and SHA256 of full raw test output. The three runs must ALL PASS and have the exact same positive test count. P139 seven-test receipt must show seven PASS and zero HOLD, plus original guard unchanged. Original logs are retained as GitHub Actions artifacts even on failure.

**Even a green P141 triad means ONLY a reproducible SCOPED release-path acceptance**. It is NOT a full unfiltered product regression; no U5/G6/full-product gate is claimed. Tests omitted from this deliberately narrowed scope remain independently visible as historical tests, notably branch seal checks with 37 genuine failures and the P86/P87 three stale UI expectations; those are explicitly **NOT RUN / NOT CLAIMED PASS** here. The P135 real negative results stand until a reviewer approves a compliant current-branch functional versus historical-seal execution definition and their original branches are actually tested, with native exit/custody evidence.

## Remaining hard release gates

- **U1:** qualified independent Windows user-account security review, actual user clicked consent residual risk, historical test-governance decision, no same-user malware protection claim.
- **U3:** publisher-signed Nayeon main executable, signed separate local BYOK helper, trusted immutable release SHA/signer certificate pins, protected installation ACLs and review of time-of-check/time-of-use to signed image load. P140 pins deliberately empty.
- **U4:** written Windows Code Integrity/Smart App Control policy-owner GO and actual SAC/WDAC load acceptance on authorised target. No bypass or unsigned exe on Kristian.
- **U5:** THREE completed full-product Windows regressions according to an independently approved scope plus native filesystem and frozen source-integrity proof; P135 unfiltered attempt failed. P141 scoped triad is informative but cannot substitute.
- **U6:** independent production release GO; only on genuine release reconcile original persistent Google Drive master workbook FIRST, dashboard second.
- Original privileged BYOK C1 G0–G6 remain OPEN; P96 original revocation/effect race and P124 transferred-handle human authorship issue remain in frozen unused privileged programme.

No real API key, provider validation, privileged service, protected journal/HKLM/TPM mutation, native WinCred on Kristian, unsigned executable on Kristian, Smart App Control change, historical P62 blocked-operation retry, GitHub merge/tag/release or nonrelease master workbook/dashboard edit.

**P141 IS A SCOPED REPEATABILITY TEST, NOT FULL RELEASE APPROVAL. BYOK C1 USER-SCOPED RELEASE HOLD.**
