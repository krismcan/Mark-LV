# P201 — Original BYOK-B ADS Admission Remediation Candidate & Integration Plan

**14 November 2026 | Isolated dormant candidate | H/C/R = HOLD / test-only candidate / HOLD**

## Actual authenticated ancestry and why P201 exists

P200 final source HEAD e9f9a0a01d2c2615087a6183c27a8ab478d67c78, draft PR #125. Real genuine final Windows Actions run 43573289163, artifact 14104818687, ZIP SHA-256 42EFB773B25A3A018719A6C1DFAC6F5DA51AD7B8F5A2794ED9A062665F8E1CB0. Two members:
- p200_real_Windows_executable_content_70_selected.log SHA-256 1FD63A482DDA650FF566CBF8DFC8C4D87BFF9710F560A81B4CCDD0F5EEEF3213
- p200_executable_content_HCR_ledger.json SHA-256 54B288F6EAEF8063D1277D6C121D51D17C66F726B8858C51A97FA4AED8F004A6

Native OS exit 0, 70/70 source-specific selected Windows tests and complete OK footer; original source_before == source_after, H/R HOLD, complete full unfiltered Windows product acceptance 0/3. The historical P195 cross-process reversible ADS/hardlink ABA admissions, P198 path re-open attack, P199 signed-interpreter script spoof and P200 execution-content substitution UNSAFE negatives remain immutable.

**Identified original defect, actually reproduced at P189:** original historical BYOK-B full verifier validates 23 reviewed source main-stream hashes, Git objects, index, worktree and frozen release ancestry and refuses a second hardlink. But adding a named NTFS alternate data stream to a source file did not change its reviewed main-stream SHA or the original Git scope; the **original full historical BYOK-B gate ACCEPTED** the file despite unreviewed metadata. This is a genuine refusal gap in the old legacy historical verifier. It is not resolved by later independent lab prototypes unless the check is adopted in the actual production trusted gate.

## P201 code change: an actual callable remediation candidate, not only a review

P201 adds one **dormant, importable, standalone candidate** at nayeon/brain/byok_b_ntfs_physical_admission_candidate.py. It accepts an explicitly supplied historical full-B-gate callback for use in the lab, invokes the original complete historical B gate **before and after** a pass over the **exact original 23 reviewed files**, and uses the previously tested P190 true Win32 HANDLE reader on each source.

For each of 23 reviewed source paths, this P190 HANDLE reader demands canonical literal path, original immutable B SHA, no extra NTFS named streams, no multiple hardlinks, no reparse leaf, a stable handle-bound FileId, regular non-deleting file, bounded bytes and matching final HANDLE path. It refuses OS/metadata errors instead of downgrading to the old gate. An old gate failure is never ignored or replaced with a new successful verdict. It is a new physical pre-admission check, not a rewrite or exception of original security rules.

**Scope and important limitation:** The old original B full-gate callback is injectable for isolated fixture tests; the production caller must eventually be bound to a separately trusted, independently verified actual product authority. The 23 file-HANDLE reads happen one file at a time. The HANDLE snapshots, parent directory path and original gate before/after snapshots are NOT an atomic filesystem/release transaction; ABA across files or a malicious privileged actor may evade observation. No pre-enrolment durable external trust anchor, main/helper/installer signing, trusted executable-loader/IPC consumer or whole-file-set snapshot custody is established. This candidate is NOT enabled in public current Phase 10 and does not yet fix the original historical legacy gate itself.

**Exactly four new additive paths** relative to P200:
1. nayeon/brain/byok_b_ntfs_physical_admission_candidate.py — **dormant unintegrated product candidate**, with no existing product source modified
2. scripts/p201_windows_original_b_ads_remediation_candidate.py — genuine Windows original legacy gate + new candidate integration-security tests
3. docs/byok-c1-p201-original-B-ADS-remediation-integration-review.md — this source-bound threat and phased integration review
4. .github/workflows/p201-windows-original-b-ads-remediation.yml — native Windows source-custody and archived result workflow

All original tests and existing product modules remain unchanged; old sealed/historical sources and P189–P200 untrusted-negative test evidence must remain independently immutable. Kristian original worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028 at HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1 with 17 pre-existing paths must not be staged, overwritten, reset or cleaned.

## P201 real Windows tests

Use authentic P187 real B historical disposable worktree: clone exact original A parent commit, place all 23 **original B committed raw bytes** into the actual Git worktree (no self-created fake B source), run the original full historical B verifier in its own actual Python process in that old original branch and inspect actual Win32 file objects for all pins. Keep P189's original four real full-B cases (original pristine passes, outside hardlink refused, single named stream admitted, both ADS and hardlink refused). Add P201 nine cases:
- Clean full historical B before and after 23 HANDLE-verified sources admits a single isolated candidate result.
- Original full historical B still admits native ADS on its self-pinned original source while new candidate refuses the exact named-stream physical state.
- Original full historical B still admits native ADS on a **different** pinned original B application source while candidate refuses it.
- Real extra hardlink refused by existing original B gate and by physical HANDLE reader (the forced mock gate is a test-only isolated physical-refusal probe).
- Modified original B main-stream bytes refused by both original full gate and source digest guard.
- Missing original full gate callback refuses, no fallback.
- Unavailable native HANDLE stream enumeration refuses, no success by omission.
- Named ADS removal leads to fresh reinspection of all 23 source HANDLEs and candidate admission, no cached denial/approval.
- Historic full-B gate failure is never downgraded to physical-only approval; after restoring original bytes, fresh inspection can pass.

Expect 13 **selected genuine native Windows** test cases, not full-product regression runs. The canonical P200 predecessor ZIP, two member SHA hashes, genuine footer, source HEAD and both original historical negatives are authenticated before test execution. Actual unittest raw log, OS exit, unique security markers, source identity before/after and H/C/R ledger retained even on failures. No false SUCCESS if original B gate refused for unrelated fixture cause or native ADS did not actually exist on filesystem.

## Production integration route — NOT yet authorised for release

**Stage I — candidate source governance:** independent review of original historical private gate, actual Windows APIs and newly added candidate. Review whether using P190's exclusive source HANDLE is adequate across all directory components and 23 files, especially ABA, USN/drift, source path aliases, journals and snapshot coherency. No arbitrary callback or exception-based override may reach production. Do not mutate historical test assertions to pass.

**Stage II — production path and trust ownership:** bind actual production current Phase 10 signed source/manifest authority to protected initial root, version, epoch and signed executable-loader chain; require a stable, authenticated full 23-file source identity across checked sources and actual consumer. Freeze an independently authenticated signer/anti-rollback policy, and define how source HANDLE/validated bytes are delivered to a trusted process. Existing product code and historical parent/frozen release remain immutable until approved additive/isolated integration is demonstrated.

**Stage III — unfiltered regressions and independent GO:** run focused real native Windows tests on the actual product, all original historical adverse/recovery cases, complete unfiltered Windows full product regression three accepted times with native raw exit/log SHA; repair original P135, P175, P178, P179 and PERF-P187-01 failures/timeouts without waiver; obtain all seven independent GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 qualified signoffs and privileged G0–G6 GO, signed product helper/installer Code Integrity, WDAC/SAC review. The review in this draft does not replace any external security sign-off.

**H/C/R remains HOLD / isolated original B physical admission candidate / HOLD.** No real API keys, Windows Credential Manager production writes, provider validation, privileged service installation, Git PR merge, tag/release or Google Drive MASTER/dashboard production release reconciliation. Keep PR DRAFT and UNMERGED. Claiming the original full private B gate is remediated in production before actual integration would be inaccurate.


## Authenticated P201 initial Windows evidence and preserved failure — 14 November 2026

**Initial native success source HEAD:** 332e6cc88a7461dac72d56ddf2b68630588f3f58. Original genuine Windows GitHub Actions run **43581530942** completed **SUCCESS**, original artifact **14108382238**. Exact ZIP SHA-256 **41D936E28C46C979EB04548D06C36640141FC72FD831D343ED7BF8485BF26DBB**, exactly two members, both ZIP CRC valid:
- p201_real_original_B_plus_physical_candidate_13.log raw genuine Windows log SHA-256 **E3DF685ACD80FF3CE9762EE0F0520D4501E8E438A1F7293D24D87816F1121DCE**.
- p201_original_b_ads_candidate_HCR_ledger.json SHA-256 **4D37BE45D5D42656FB3A1C8158367D810276206F4F0CA9BACF25686D7AC02CE3**.

**Authentic result:** real Windows test runner executed 13/13 selected cases, native OS exit code **0**, complete original unittest footer **OK** (118.70 seconds for these expensive historical Git gate calls; **NOT** production performance acceptance), original exact P200 full Windows artifact 14104818687 and 70 test results reauthenticated before tests. Source_before == source_after and both match P201 HEAD. H/R HOLD, original full unfiltered full-product native Windows accepted regressions **0/3**.

**Actual old/full B vs new candidate historical defect remediation:** original historical B gate **admitted** one named NTFS ADS on the exact original full-B self-pinned source and separately admitted ADS on another original reviewed application pin; the new callable dormant physical admission candidate **refused both**, through HANDLE stream metadata refusal. Clean original 23 source files and valid full B gate were admitted by the candidate, with 23 Windows HANDLE observations per pass. External hardlink refused by both original and physical gates; byte corruption, missing gate, stream-enumeration error and historical original gate failure refused; after ADS removal and restoration, all 23 sources were freshly inspected and admitted. Source history and frozen security test assertions remain unchanged.

**Preserve first P201 collector failure, not a test failure:** real Windows run **43581265134**, source HEAD dd24e2aab6cccc212ccdcb3f9a4eb724ded7505a, original artifact **14108647712**, ZIP SHA-256 **C0C4D42045413423720F6C1F6ECE218623168E1748B5702BDAB9959A81DE5075**. Its raw actual native test log **passed all 13/13 with OS exit 0**. The evidence collector then falsely failed because it anchored P201 marker extraction to the start of lines; unittest -v prefixed many test names to those markers. The collector was changed to search the complete line, without weakening **any security case** or changing the old gate; its real failure artifact is retained. The clean second run above confirmed source custody, every required marker and H/C/R ledger.

**Important non-claims and unreleased security decisions:** This only demonstrates a candidate's named-stream refusal and positive operation against the historical A/B fixture. The actual old historical B source remains vulnerable to ADS; current public Phase 10 source admission is **not connected** to the candidate. The P190 original parent-path ABA and non-atomic 23-file batch windows, original self-enrolment/signer-root trust, trusted callback ownership and actual signed loader/IPC consumer remain unresolved. These limit the candidate even when selected Windows tests are green. No protected production changes, actual provider keys, privileged Windows system modification, PR merge, signed release or production dashboard/Drive MASTER release reconciliation. Independent review and full original Windows product acceptance remain OPEN, not fulfilled by this review.

**Closure control:** A final documentation-inclusive source commit must pass a new exact-Git-HEAD authentic Windows run before the P201 experimental candidate can close. The production release HOLD is unaffected.
