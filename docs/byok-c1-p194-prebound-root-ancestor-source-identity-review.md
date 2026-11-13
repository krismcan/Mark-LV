# P194 — Pre-bound Windows source-root, ancestor and leaf FileId identity

**13 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1 | DRAFT / PRODUCTION HOLD**

## Original source

Exact parent P193 SHA ce605cd301f979e735963278c47c09b239b715ce, draft PR #118 open unmerged. Original P193 final genuine native Windows run #43451793773, artifact #14051350366, ZIP SHA256 E6CF30C6C81314E631C12C37F760A628263A90BCD8C71FFC829AA9A2B95149B7. Verify six ZIP members/CRC and original true exact-source P189 4, P190 10, P191 10, P192 12, P193 14 complete Windows test footers, native exits/SHA, unchanged H/C/R and P193 root provenance failure.

Only three new audit files: this review, new P194 isolated script, new hosted Windows workflow. No changes to original source seals, historical B full private integrity gate, Phase 8.34 hardlink protection, current Phase 10 public successor, original product or frozen tests, P180–P193 audit sources, Kristian's original 17 dirty paths.

## Distinguishing independent FileId authority from self-pinning

Original P193 experimental NtCreateFile OBJECT_ATTRIBUTES.RootDirectory parent-HANDLE traversal refused junctions but accepted *different ordinary physical tests directory with identical original sealed source bytes*, substituted before its first child open. P193's byte hash still matched original; the problem was that the prototype had no external expected physical ancestor identity.

P194 uses a newly introduced **immutable SyntheticPreboundFileIds object** supplied separately from the read call. A test-only pre-enrolment operation:
1. Verifies *actual original historical sealed B Git source bytes* against literal original B SHA authority and 23 source pins.
2. Opens genuine Windows root directory HANDLE and reads FileIdInfo volume and 128-bit FileId, path and non-reparse status.
3. Opens the expected tests ancestor with a genuine parent-rooted NtCreateFile call and captures its exact FileIdInfo identity.
4. Opens the original B source leaf relative to that trusted-in-the-fixture ancestor, obtains leaf volume and FileId, stream inventory/hardlink count, reads original source bytes, verifies exact bytes, then closes **all** HANDLEs.
5. Freezes root/ancestor/leaf ID data in a separate dataclass and injects it into the **new P194 source reader**. The reader MUST NOT generate fresh trusted values or re-enrol itself during admission. It opens root and components using P193's genuine NT RootDirectory calls and validates every opened HANDLE against the *previously supplied* identity. Then it performs literal original B SHA validation and pre/post leaf ID/ADS/link and held parent identity.

This specifically denies a physically different root, source ancestor or leaf even if **all main source bytes remain identical**. The same physical source with unrelated sibling file creation should still admit, since directory mtime is excluded.

**Critically:** this is an independently pre-bound **temporary fixture**, not a signed or OS-certified production trusted root. Before real integration the source of expected root/ancestor/leaf file IDs must be proven authoritative, durable, anti-rollback and tied to an authenticated Git/release/OS process; merely capturing IDs once from a possibly already-compromised filesystem is self-attestation. NTFS File IDs have reuse / disk clone / remount / reparse / TOCTOU questions. No formal source-root attestation proven.

## Real Windows matrix

Original exact P189 4, P190 10, P191 10, P192 12, P193 14 genuine suites against their own historical SHA clones. New P194 14 isolated genuine Windows tests:
- Real original sealed B source with earlier pre-bound root, ancestor, leaf identities admitted.
- **P193 exploit-relevant negative:** different regular physical tests directory containing byte-for-byte identical original sealed B source, substituted after pre-enrolment, **REFUSED due ancestor FileId mismatch**.
- Different genuine leaf FileId with byte-identical original B sealed bytes under same trusted tests parent **REFUSED**.
- Different physical temp root with byte-identical tests/B tree under original path **REFUSED root FileId mismatch**.
- Separate Windows child writes independent sibling in source parent; same pinned source admitted.
- Separate Windows child writes sibling in original temp root; still admitted.
- Separate real Windows process adds NTFS named ADS mid-read; same HANDLE post-scan refuses.
- Separate real Windows process creates hardlink mid-read; same HANDLE link count refuses.
- Mutated original B main-stream bytes with unchanged underlying file ID refused by literal SHA.
- Preexisting named ADS refused; after stream removed correct source admitted.
- Genuine existing directory junction refused and no HANDLE leaked.
- Junction inserted after root acquisition, before NT rooted child open refused and safely cleaned.
- Synthetic unavailable root metadata fails closed without leaked root HANDLE.
- Pre-enrolment refuses invalid original historical sealed source bytes.

Original P193 selected negative diagnostic continues to run against exact P193 source **and still observes acceptance**, while P194 new source identity test must separately observe refusal. Do not rewrite old evidence or conceal that prior prototype was inadequate.

## Security constraints and release

SEC-P194-TRUST-01 OPEN: enrollment itself is test-fixture trust, not an independent durable signed attestation. A compromised path before enrollment could be falsely approved. Needs signed trusted root / disk/volume identity, authenticated original index/tree/HEAD physical source custody, anti-rollback and lifecycle review.

SEC-P194-ABA-02 OPEN: reversible ADS or hardlink add/remove between two scans, advanced filesystem and privilege operations, FileId reuse/reparse/mount and Symlink edge cases not fully eliminated. A FileId pin is not sufficient atomic transaction proof.

SEC-P194-APP-03 OPEN: original complete historical private BYOK-B gate continues to admit actual named ADS, from P189 original physical proof. None of P190–P194 audit prototypes replace or integrate production or the current public Phase 10 successor.

Genuine P135 (3×600s native full-suite timeout), P175 (five original source-era failures), P178 (165s original B timeout plus two old failures), P179 (original source pin timeout), PERF-P187-01 all preserved and UNWAIVED. Original 0/3 complete unfiltered native Windows full-product regressions accepted. Seven qualified GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 independent security reviews OPEN, privileged G0–G6 OPEN, signed main/helper/installer/certificate SAC/WDAC GO absent. No real key, Windows Credential Manager, live provider validation, privileged service, product verifier edit, Git merge/tag/release or false Google Drive MASTER/dashboard release GO.

**H/C/R = HOLD / ISOLATED WIN32 SOURCE IDENTITY TEST ONLY / HOLD.** P194 can close only as authentic source-preserving experimental Windows evidence with original logs/OS exits/ZIP SHA and explicit remaining trust-authority risk, never as BYOK C1 production authorization.
