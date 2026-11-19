# P280 — P279 mutation-canary exception correction and hosted Windows native proof

**19 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1**

**DEVELOPMENT-ONLY REVIEW CANDIDATE — REAL KEYS NO-GO — PRODUCTION RELEASE HOLD.**

## Exact parent and original failure

The frozen P279 candidate commit `82409600ebfc00748304a9d0ae21cd370ab78bab`, draft PR #199, produced genuine hosted Windows x64/x86 RED on workflow run [44430601276](https://github.com/krismcan/Mark-LV/actions/runs/44430601276). On BOTH architectures, current P279's 10 cases ran with 9 PASS / 1 ERROR, and preserved P278 10, P277 10 and P276 12 all PASS. Original unchanged P216 18 ran with 16 PASS and two historical failures (test02/test06), raw exit 1. Native P279/P261 SCM runtime steps were **SKIPPED** because the focused suite failed. This prior RED evidence is preserved on PR #199 and must not be rewritten.

The actual test error arose in P279 `test_10_in_memory_negative_mutation_canaries`: it deliberately removes `clean &= Release(process, false);` from an in-memory source copy. The source checker `_sid_and_recheck` then used `observe.index("Release(process, false)")` without first verifying the cleanup fragment existed, causing uncaught `ValueError` when the test expected an explicit security `AssertionError`. This is a **test-harness exception classification defect**, not a reason to remove the canary or a demonstrated native token failure.

Codex, as sole implementation writer, added **one source line** in `tests/test_byok_c1_p279_runtime_token_source.py` before the existing ordering comparison:

```python
_need("Release(process, false)" in observe, "missing required process-handle cleanup")
```

The 10 test methods and all 21 in-memory mutation canaries remain. Missing cleanup now intentionally produces `AssertionError`, so its negative mutation proof is retained. No broad exception catch, test skip, xfail, waiver or historical contract edit.

## Current bounded source provenance

Exact parent: P279 commit `82409600ebfc00748304a9d0ae21cd370ab78bab`.

Branch: `byok-c1-p280-p279-test-checker-fix-20261119`.

Exactly one inherited test file modified: `tests/test_byok_c1_p279_runtime_token_source.py`. Exactly two new paths: `.github/workflows/p280-windows-runtime-token-recovery.yml` and this document. No C# native service source is modified. Expected parent 1,127 regular Git paths; **1,126 other inherited files remain byte-identical**, and the direct-child P280 candidate has 1,129.

P279 C# observer SHA256 `6CB05A5DB96D83D61387CE90237358C7DF5C10ED7FBFFFB146D4C1E50A8602BB` and P279 runtime harness SHA256 `4CDCB93EC91DD9EF343C1CA5579FEA0272F8AAC88EFFDC99F9CC74BB8889ECA9` must remain unchanged. Earlier P261/P215/CustodyService, P275 backend and original P216 historical tests are all immutable, with their raw hashes enforced via source custody.

## Authentic Windows test contract

The new draft-only hosted Windows-2022 x64/x86 workflow uses pinned GitHub actions, verifies same-repository exact head/base, direct one-child parent, three-path change envelope and all 1,129 raw Git/disk source identities. It runs current P279 **10/10**, preserved P278 **10/10**, P277 **10/10**, P276 **12/12**; no skip, expected failure or waiver. It separately runs original unchanged P216 18 tests with authentic old test02/test06 failures and raw exit 1, so the workflow remains **RED/HOLD** until a qualified versioned acceptance migration—not an artificial green.

Once focused tests pass, the workflow warning-as-error compiles both **P279 read-only running-service token observation** and the preserved **P261 read-only SCM configuration observer** with `C1_REVIEW_ISOLATED_ASSEMBLY`, checks the expected negative build without review-only flags, and executes native tests **only on disposable GitHub-hosted Windows x64/x86** with an expected Nayeon SCM service status `Missing` and all authority denied. It captures genuine native exit codes, bounded stdout/stderr, full source before/after custody and SHA256 text-only artifacts. Any unexpected service, inaccessible OS evidence, process/token mismatch, compiler error, native exception or timeout is **HOLD** and never a token or credential authorization. Nothing is run locally on Kristian except static PowerShell and nonexecuting compilation already reviewed.

## Open Failures & Prior Issues Review

| Dependency | Disposition |
| --- | --- |
| P279 source-test mutation canary ValueError | Confirmed test checker bug; one-line explicit security assertion; genuine hosted proof pending |
| P279 actual native service process/token observer | Implemented review-only, unmodified; real hosted runtime missing-service execution pending |
| P261 read-only service configuration observer | Frozen and unchanged; runtime regression pending |
| P216 old tests02/06 requiring retired Python credential writes | Original historical RED unwaived; qualified versioned contract review required |
| Original P211 test02, P76 four original failures, old P275 adapter 2 FAIL +5 ERROR | Unwaived historical and governance debts |
| Original P96 production revoke/effect race | HIGH OPEN; P268/P274 are separate development experiments |
| Proposed virtual account versus original LocalSystem service gate | HIGH OPEN external SEC-03/SEC-04 qualified service principal and store decision |
| Service-owned protected DPAPI credential store/ACL, code signature, authenticated IPC/user presence and independent monotonic antirollback | OPEN, not implemented or proven |
| External qualified GOV/SEC/REL security approvals | 0/7 |
| Three accepted unfiltered Windows native product regression passes | 0/3 |

## Decision

P280 is a **development-only repair and acceptance-evidence checkpoint**. No local/remote credential material, service installation or configuration change, OS security policy alteration, provider connection or production effect was attempted. No historical test was modified or waived except the specifically identified **new current test-checker one-line bug fix**, and no old PR was rewritten.

**REAL KEYS NO-GO / PRODUCTION HOLD.** The direct-child PR must remain draft and unmerged. Do not update the Google master workbook or dashboard until BYOK C1 is fully completed.
