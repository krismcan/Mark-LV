# Nayeon v1 / BYOK C1 — P142 Windows post-stall inventory audit

**10 November 2026 | OM v2.1 | DIAGNOSTIC ONLY | USER-SCOPED RELEASE HOLD**

## Why P142 exists

The authentic P135 FULL unfiltered Windows product discovery ran THREE times and NEVER completed. Each run reached 1,681 original test outcomes (1,637 PASS / 37 FAIL / 7 ERROR), then timed out on the same BYOK-B historical source-integrity test. P136 showed the original isolated case repeatedly walked expensive nested Git history, not a proven deadlock. P139 later showed the original seven Win32 filesystem tests pass under a verified own fixed-drive temporary root without changing their protections. P140 implemented but DID NOT authorize frozen sibling signed launch. P141 passed THREE scoped 190/190 Windows feature and safe-filesystem runs. The P141 scoped suite is NOT the full product test inventory.

P142 executes all 83 original Python test modules lexically AFTER the original P135 stalled module. Previously P135 never reached them. Use disposable GitHub Windows-2025 and retain exact frozen test source. Each module gets its own 35-second subprocess, so one expensive integrity fixture cannot mask product issues elsewhere. No test methods are filtered from a module, no tests rewritten, no unittest.skip, no fake green or silent waiver.

## Exact test inventory and source trust

Direct exact verified P141 source HEAD: bd2c0b7f5d74b2987c82b5802ea66a732d79faa4.
P135 last module: tests/test_phase8_byok_b_scope_integrity.py.
P141 Git-tracked original inventory: 169 tests/test_*.py files; pivot 0-based index 85; precisely 83 unreached modules. The new driver recomputes and requires these counts, refusing drift.

For every remaining original module, execute python -B -m unittest -v tests.<module>, reporting native exit, actual Ran N tests footer if present, FAIL/ERROR markers, SHA256 of full log and explicit PASS/HOLD/TIMEOUT. Four subprocesses at most run simultaneously, each with 35s hard timeout. The P135 original stalled module is explicitly OUTSIDE this diagnostic suffix, and its original P135/P136 timeout evidence remains a blocking fail. This script is NOT a regression subset that replaces an unfiltered full suite.

Raw original per-module outputs and 83-row machine-readable manifest are stored as private CI artifacts. Diagnostic workflow SUCCESS only signifies collecting all 83 dispositions, not 83 passed or full product passed. Any module failure, timeout or error remains HOLD.

## Source and security boundaries

Only THREE ADDED source paths: the P142 script, hosted Windows CI and this packet. Original P132/P133/P134/P139/P140 product source, original P49/P96, historical Phase8/9/10 seals, and P135/P136/P141 test sources unchanged. No privileged service, signed installer, Code Integrity bypass, independent approval, real API key, provider request or WinCred mutation on Kristian. GitHub runner has no user provider credentials; the production OpenAI credential slot is forbidden.

Qualified independent test-governance/security review must still approve a future clear distinction between current-branch functional tests and preserved exact-branch historical seals. P142 does NOT grant such approval.

## Mandatory release hold

Even if all later 83 modules PASS, P135 37 FAIL/7 ERROR and BYOK-B original test TIMEOUT remain unresolved, with no three completed unfiltered full product Windows passes. Original privileged G0–G6 OPEN. User-scoped U1 independent security approval, U3 signed and pinned helper/desktop with protected installer, U4 Smart App Control policy owner GO, U5 three approved full Windows product regressions and U6 independent release plus original Google Drive master workbook FIRST/dashboard after release all remain OPEN. No real key entry.

**P142 = post-stall Windows inventory diagnostic, NOT a waiver, signed release, or real credential consent.**
