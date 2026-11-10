# Nayeon v1 / BYOK C1 P143 — safe temp root for failing original Windows fake fixtures

**10 November 2026 | OM v2.1 | ORIGINAL GUARDS UNCHANGED | RELEASE HOLD**

## Exact starting point and actual failure evidence

Direct P142 Windows post-stall inventory baseline: 0a645a5935e42bb345da30b6af96e045604d193f, draft PR #67. P142 actually ran 83 previously unreached original modules on disposable hosted Windows: **54 PASS, 20 FAILED, 9 TIMEOUT**. Its 20 completed failing modules emitted 29 failed assertions + 99 error cases according to the genuine raw unittest footers. The P142 per-module individual FAIL/ERROR parser was CRLF-incompatible, so its zero failure-marker fields are not trustworthy; authoritative data are the original retained raw unittest logs at Actions artifact 13787854664.

Of those 99 error cases, 50 occurred in original Phase8.29 integration, 18 in pre8.29 A01 ownership, 12 in pre8.29 A02 fake isolation and 17 in pre8.29 host exception cleanup: exactly **97 cases** in four temporary-root-sensitive modules. P142 also recorded one original native text-file creation error (the remaining case is Phase8.31 test teardown). Authentic original tracebacks repeatedly included the strict refusal: Test temporary-directory ownership changed.

## P143 safe verification without bypass

**Only three new paths**: the P143 host runner, hosted Windows CI and this review packet. Reuse the **UNCHANGED P139 original native Windows opened-handle verifier** already used to make all seven original file and directory tests pass under a fresh user-owned local C-drive fixed root. The P143 runner calls the existing P139 guard for newly created C:\NayeonP139_UUID root after checking its absence, validating fixed local drive, lexical exact path, Win32 file handles and no reparse. Then only in the disposable test child process environment, set TMPDIR, TEMP and TMP to that verified root. Do not modify machine-wide TEMP, filesystem security checks, original source or tests.

Run ALL original methods in five original test MODULES (53+18+12+17+87=187 expected) in independent Windows subprocesses; do not cherry-pick successful methods, modify code, waive root identity or patch expected outcomes. Every module must exit native zero, show genuine expected Ran N tests and OK and no failed test names; otherwise the CI gate fails, logs preserved. Use 95s per module hard timeout. No real WinCred, provider API keys, signing action, protected registry/TPM or Kristian current-user changes.

This experiment can demonstrate compatibility of genuine original test fixtures with a separately verified local canonical temporary root, but it does NOT establish whether GitHub's default TEMP failure is due to junction, casing, alias, drive or another policy-specific reason. It also does NOT repair the many historical exact-branch integrity seal failures, expired test expectations, slow nested Git historical tests or the three mandatory full-product regressions.

## Remaining release blockers

Original high-assurance G0–G6 open. Narrowed user-scope U1 independent security/test governance approval, P140 signed/pinned companion and protected installer/signer absent, Smart App Control owner GO absent, U5 three full independently accepted Windows product regressions incomplete and U6 signed release / original Google Drive master workbook FIRST, then dashboard outstanding. P141 570 scoped Windows executions passed but are not full-product acceptance.

No real key entry, unapproved app launch, unsigned exe on Kristian, live provider validation, original P62 replay, GitHub merge/release, SAC change/bypass or nonrelease Drive mutations.

**P143 original-test safe TEMP experiment only. BYOK C1 USER-SCOPED RELEASE HOLD.**
