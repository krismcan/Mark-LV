# BYOK C1 P195 — Authenticated durable source-root authority and ABA security review

**13 November 2026. Classification:** additive audit-only synthetic-signature security experiment and Windows diagnostic. **H/C/R: HOLD / experimental review only / HOLD.** No product source, frozen tests, credential, privileged operation, merge, tag or production release.

## Authenticated predecessor and physical trust boundary

Exact P194 parent: 6f9d6c4316522dec0b5f586bb8d3d9ab5eef9b2b; draft PR #119; original native Windows run 43467881579, artifact 14058754070, seven-member ZIP SHA-256 1E3CD354F2C0970E57212F7B99556FAE8F7159AB1043164750358F39558147C8. The P195 collector verifies the original ZIP bytes, ZIP CRC, all six source-specific log SHA-256 values, footers, actual native exits and H/C/R ledger before running new tests. **P189–P194 had 64 selected tests, NOT full-product regressions.**

P195 adds exactly three review-only paths: scripts/p195_windows_durable_root_authority_aba_review.py, this document and .github/workflows/p195-windows-authenticated-root-aba.yml. Exact P194 ancestry and unchanged product/test subtrees are enforced. Kristian's original worktree is not used or changed.

**Critical preserved evidence:** P189 original complete private BYOK-B admitted a named NTFS ADS, whereas original historical hardlink guard refused a hardlink. P193 accepted byte-identical source through an alternate ancestor. P194 experimental FileId pre-binding refused alternate physical root/ancestor/leaf only when enrolment occurred safely in a synthetic fixture. No original BYOK-B production verifier is patched.

## Proposed authority structure (not production implemented)

    OUT-OF-BAND authority, not writable source tree (NOT ESTABLISHED)
      | authenticated release signer / keys, policy and revocation
      | signed Git/index/tree/HEAD + executable/helper/installer identity
      | independent monotonic rollback and recovery witness
      v
    signed local manifest (UNTRUSTED BYTES until verified)
      | verify trusted key and scope before interpreting IDs
      v
    expected physical root + ancestor + leaf volume/FileIds
      | P194 held HANDLEs, NT RootDirectory single-component open
      v
    literal B SHA + same-HANDLE ADS / link observations
      | full current Phase 10 original gate NOT INTEGRATED
      v
    production G0–G6 + independent reviews + 3 full suites: HOLD

P195 demonstrates **ephemeral Ed25519 test-only signing**, with pinned public key and a synthetic epoch floor passed separately from the local record. A signature proves only that a chosen signer approved its claims; it does **not prove independent pre-enrolment root trust**. An attacker-controlled directory may be blessed by a compromised enrolment process. FileIdInfo is not cryptographic disk provenance and cannot independently cover volume replacement, disk cloning, FileId reuse, source mount/reparse changes, or privileged adversaries.

A durable product design requires independently distributed signer authority, key scope/rotation/revocation, strong process and signed installer provenance, genuine original complete Git/index/worktree/tree/HEAD/23-pin release mapping, documented recovery, and an independently protected monotonic epoch (TPM, approved remote witness or equivalent reviewed anchor). A locally restored old signed manifest could still be valid; a local checksum, ACL, DPAPI record or Credential Manager alone does not make it rollback-proof.

P195 file persistence is a basic local fixture read/write, **not** a crash-safe journal, guaranteed atomic recovery, real OS reboot, trusted signer lifecycle or independent anti-rollback implementation. Its simulated restart recreates readers but does not reboot Windows.

## New 22-case selected native Windows matrix

The new test class inherits P194's 14 physical Windows fixture cases unchanged and adds eight scenarios:

| Cases | Security diagnostic | Honest expected interpretation |
|---|---|---|
| 1–14 | Previously isolated physical root/ancestor/leaf alias refusals, true NT relative opens, persistent ADS and hardlink, real sibling writes, junctions, metadata failures | Re-executed on P195 source, separate from P194's original historical source run |
| 15 | Signed authority reloaded with fresh reader twice | Synthetic process-restart admission only |
| 16 | Untrusted substituted manifest signed by a different ephemeral key | Signature refusal; genuine first-install signer compromise remains OPEN |
| 17 | Previously valid signed old epoch restored | Refused only if externally protected higher epoch remains trusted; otherwise an old signature verifies |
| 18 | Partial pending record and corrupt active authority | Corrupt authority refuses; persistence and crash replay semantics remain OPEN |
| 19 | Correctly signed but wrong release Git commit | Refuse inappropriate source identity |
| 20 | Absent verifier trust anchor or independent epoch floor | Fail closed |
| 21 | Cross-process real NTFS ADS create and attempted remove between held-HANDLE observations | Record actual create/delete OS outcomes; if removed, **admission demonstrates ABA gap**; if blocked, mark unproven |
| 22 | Cross-process real hardlink create and attempted remove between observations | Record actual OS outcomes; do not equate blocked deletion with general atomic protection |

All fixture files live under genuine hosted Windows RUNNER_TEMP. Preserve actual OS exits, raw test output, SHA-256, source HEAD, ZIP checksum and H/C/R ledger including failure evidence. Two agreeing observations **are not a transaction or universal alias-free proof**.

## Open security findings and reviewer package

SEC-P195-ROOT-01 (trusted root before enrolment): OPEN. SEC-P195-DURABLE-02 (durable restart/rollback, disk replacement/restore, signer and ACL lifecycle): OPEN. SEC-P195-ABA-03 (reversible ADS/hardlink races): OPEN. SEC-P195-GIT-04 (complete original source authority and current Phase 10 integration): OPEN. SEC-P195-ADS-05 (unpatched original full BYOK-B named ADS gap): CONFIRMED OPEN. SEC-P193-HANDLE-01 (experimental NT HANDLE exceptional cleanup not a product fix): OPEN. Historical P135, P175, P178, P179 and PERF-P187-01 unresolved and unwaived.

Independent reviewer must examine the original authentic Windows logs, physical Win32 sharing results, trust anchor selection and revocation, rollback/migration/recovery, FileId reuse/reparse/volume controls, Windows file stream/hardlink ABA atomicity, original Git and current Phase 10 source authority, error and performance behavior, original release verifier integration, signed main/helper/installer Code Integrity/WDAC/SAC and all original negative security tests. **Assistant-written review is only a submission, never external signoff.**

GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07: OPEN. Privileged G0–G6: OPEN. Signed executable/helper/installer and SAC/WDAC/Code Integrity GO: NOT ESTABLISHED. Accepted full unfiltered genuine Windows full-product regressions: **0/3**. Require independent security approval and 3 passes before future production GO.

**Conclusion:** P195 may close only as an isolated research checkpoint when authentic test evidence passes. Full current gate integration, root provenance, durable anti-rollback, reversible alias race resistance and release remain **HOLD**. No Git merge/tag or Google Drive production release reconciliation is justified by selected tests.


## Authenticated first successful native P195 experiment — 13 November 2026

The physical Windows run 43482220893 (source 7dcf26aa9d198a748bef1e455b5f2f1242bdbd1f; artifact 14065398100; artifact ZIP SHA-256 0B6C39BF10935DBCE20CB7B5F13C3750D1977BD112BF214D7DA6FAD6BA6AF503) independently yielded two ZIP members with valid CRC: native raw 22-test log SHA-256 9C28FC828187BB30B473CEEC9EB5B49F3B0CAB7DB485B95986A1D82335C30FD3 and exact H/C/R ledger SHA-256 9FA35071C9C0ED227A621B201EB5BE8E9CA5E2CC8874C0621FDF917B52F42A30. All **22 selected native Windows tests had real OS process exit zero**, a complete 22-test footer and no test failures. Source-before and source-after were identical; P194 original seven-member evidence and 64 selected prior source-bound tests were authenticated from the source-accurate ZIP.

**Security finding SEC-P195-ABA-03 upgraded from hypothetical to experimentally CONFIRMED:**
* In test 21 a genuine external Windows process **created and removed** a named ADS while a held P194 source leaf HANDLE was active. Both physical operations succeeded; the experimental two-snapshot reader accepted the original sealed source.
* In test 22 a genuine external Windows process **created and removed** a hardlink during the same observation interval. Both physical operations succeeded; the reader again accepted the original sealed source.
* These are **admission gaps observed in the isolated prototype**. They do not prove every filesystem schedule is exploitable in the current product, because no reviewed product integration has occurred. They do disprove the proposition that two matching snapshots and an exclusive read HANDLE alone provide atomic NTFS alias exclusion.

**Decision:** The diagnostic tests passed because they accurately *observed a vulnerability*; they are NOT a security GO. Keep the historical original B ADS admission unpatched status, 0/3 full Windows regressions and all independent GOV/SEC/REL and G0–G6 holds. Any future remediation must prove a stronger atomic or fail-closed alias policy, and verify the complete original historical gate and current Phase 10 integration without weakening old tests.
