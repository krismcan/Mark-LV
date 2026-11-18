# P277 — Current service-store source inventory reconciliation

**18 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1**

**Status:** DEVELOPMENT REVIEW CANDIDATE — REAL KEYS NO-GO — PRODUCTION RELEASE HOLD.
This file records source work and the planned hosted evidence; it does not claim native Windows OS isolation, historic test waiver, external approval, or production readiness.

## Provenance and source scope

- Exact parent: P276 commit b763e3dd6cf666290c0b9ffabc6a4dfa3a35b726.
- Candidate branch: byok-c1-p277-current-service-store-inventory-20261118.
- Codex was the single product/test/workflow source writer. Nayeon independently reviewed the source, corrected the regression specification and prepared this review record.
- Exactly one inherited product source modified: nayeon/brain/p216_service_store_decision.py.
- Exactly three additive files: tests/test_byok_c1_p277_current_store_source.py; .github/workflows/p277-windows-current-store-source.yml; this document.
- Expected parent inventory 1,116 regular files; 1,115 inherited blobs must remain unchanged, giving a 1,119-file candidate. All original history and tests remain unmodified.

## Root cause and actual product change

Original P216 was written when the Python credential backend contained native CredWriteW/CredDeleteW operations. P275 deliberately retired the native mutation and plaintext-read functions, while retaining presence-only CredReadW/CredFree and an inert read-denial shim. Therefore original historical P216 test02 and test06 now assert source capabilities that are correctly absent.

P277 updates the real P216 source inventory without changing those historical assertions. P216EffectSourceFinding now distinguishes wincred_presence_only_adapter from explicit_native_credential_mutation_call; the original wincred_native_adapter and direct_effect_source_reachable semantics remain unchanged (false in current source). A CredReadW presence call does not count as credential modification or plaintext access. Dynamic loading, getattr/alias risk, other same-user native callers and injected test adapters remain distinct, unresolved trust concerns.

P216StoreReview now reports source_mode_runtime_risk_reachable separately from direct native mutation. The P132 controller and P133 Python child source-route remain visible; this is not evidence of a working native mutation actor or OS-enforced isolation. Source review remains SOURCE_RISK_REQUIRES_OWNER_DECISION, and every release, real-key, signed-installer, migration and consent authority bit is false.

## Independent security finding and correction

The partial P277 change initially moved a SOURCE_UNPROVEN refusal behind tracked-Git-source comparison. Independent review identified the regression against unchanged historical P216 test12: required fixed source missing must return SOURCE_UNPROVEN before considering supplied inventory. Codex restored this exact early refusal and verified the block was relocated without changing unrelated source or frozen tests.

P277 also in-memory compiles each tracked Python AST to reject parse-valid-but-compile-invalid source. It compares the caller's tracked source list with the actual Git index before allowing a bounded source finding, and preserves strict malformed/path/case/alias refusals. Static analysis does not authenticate a loaded signed image, service token, or external trust root.

## Focused tests and independent evidence contract

- New P277 source-only unit suite: 10 adversarial cases for current presence vs mutation witnesses, source-mode risk, deny-only receipts, injected synthetic AST native-call aliases, malformed source, hostile tracked paths, forgery and missing-source precedence.
- Previously verified P276 current source suite: 12 selected cases; previously verified P275 selected fake tests: 18. Neither establishes product-wide acceptance.
- Original unchanged P216 native-source historical suite: 18 cases, with test02 and test06 previously genuinely failing due to retired direct native effects. Preserve raw process exit and stderr; no replacement, xfail, skip or waiver.
- GitHub-hosted Windows-2022 x64/x86 workflow uses exact draft PR/base parent and single child, action commit pins, source/blob/disk hashes for all 1,119 files, real Python 3.12.8 runtime, separate current and historical test steps, and text-only logs/exit/sha256 artifacts.
- Local Python execution on Kristian remains unavailable under Windows Application Control; no interpreter install, copy or policy workaround is authorised. Hosted Windows raw results are pending until the draft PR run completes.

## Open Failures & Prior-Issues Review

| Finding / trust boundary | State and disposition |
| --- | --- |
| P277 missing-source refusal precedence | Independently detected and source-corrected; new adversarial test, hosted verification pending |
| P216 original test02 and test06 | Historical source contract requiring retired native credential mutations; UNWAIVED RED/HOLD, original tests unchanged |
| P211 original historical test02 | Still unwaived after P276; original current-source P211 21/22, replacement P276 suite 12/12 on x64/x86 |
| P275 retired native adapter historical tests | Earlier 2 FAIL and 5 ERROR remain; old operations must not be restored |
| Original P76 acceptance | Four original current-branch failures remain unwaived; qualified acceptance migration required |
| Original P96 terminal operation race | HIGH OPEN in original production coordinator; P274 synthetic OS effect timing is not a repair |
| Windows service principal/store architecture | Original LocalSystem SCM assumptions conflict with proposed NT SERVICE virtual-account owner; qualified SEC-03/SEC-04 decision absent |
| Service credentials, IPC and Code Integrity | Service user profile and user-scoped DPAPI, separately protected monotonic antirollback, restricted ACL, signed image, authenticated IPC and trusted user-present consent NOT proven |
| Same-user alternate credential effects | Independent Advapi32 access, older deployed copies and fake-injection paths are not OS-isolated by source edits |
| Qualified GOV/SEC/REL decisions | 0/7 recorded as externally approved; cannot self-approve |
| Full native Windows product regressions | 0/3 accepted; no scoped source suite counts as a full run |

## Release decision and continuation

**Engineering source candidate only — HOLD.** No credentials were read or written, no native service installed, no OS security policy altered, no provider connected, no production merge, and no historical test or release seal changed. Real API keys stay NO-GO. Preserve draft/unmerged GitHub review and raw Windows historical reds.

Next engineering work after authentic x64/x86 results: independently review focused failures, repair any actual source/test defects without weakening controls, reconcile old historical acceptance through qualified versioned governance, and secure the external service identity, protected store, signing/consent/IPC and antirollback decisions. Do not update the Google Drive master workbook or dashboard until BYOK C1 is fully completed.
