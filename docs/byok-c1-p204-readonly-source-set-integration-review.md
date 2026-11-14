# P204 — Current-Side Read-Only Windows Source Set: Exact Bytes, FileId and Trust Limitations

**14 November 2026 | H/C/R = HOLD / isolated modern-side physical-source candidate / HOLD**

## Verified predecessor

Exact P203 final commit 2ceac3142147f19707d858fa424b7dba1b02592a and genuine native Windows success run 43584081895, artifact 14108879465. Original artifact ZIP SHA-256 B6AF1F87772F78CDE86165E2AEE3CDB6D3C76B6A8746FD3A61FC17C73CE99FFB, two members CRC valid. Original p203_actual_Windows_current_public_authority_8.log SHA-256 2C2485E44B84D5477208B99EB111772DA5A45F66A2868337FD058F91AC155C5A, H/C/R p203_current_authority_implementation_readiness_HCR.json SHA-256 8C0D9ADD30C8909337907710E6E98F0A6BAB6BF9176B70A70F22586103676FF8. Genuine selected tests 8/8, OS exit 0, complete OK footer, original Git source before=after, H/R HOLD, accepted full unfiltered product native Windows regressions 0/3.

## Why this adds meaningful engineering rather than another legacy test

The current Phase 10/P76 public source authority is not the historical B private verifier; P201/P202's legacy 23-pin gate is not connected. P203 verified the actual public route and denial-only native C1 service. P204 begins a modern-facing generic read-only source-set component without claiming signed production authority.

**New dormant code:** nayeon/brain/byok_c1_readonly_source_set_candidate.py implements WindowsReadOnlySourceSetProbe. It operates on an absolute Windows root and a bounded supplied relative-path-to-SHA256 map, rejecting noncanonical aliases, ADS/traversal paths, malformed pins, missing metadata, extra hardlinks, NTFS named ADS, reparse root/parent/leaf and source pin mismatches through the P190 real Win32 HANDLE observation helpers. It reads exact bytes and real FileId identity from the same per-file HANDLE, compares before/after handle and observed parent metadata, closes the HANDLE, and returns immutable observation records. A partial set cannot return after a later source failure.

**Trust classification deliberately does not say ADMITTED:** results are NONATOMIC_SEQUENTIAL_READ_ONLY_OBSERVATION_NOT_ADMISSION; the caller's SHA map is UNTRUSTED. An attacker controlling both file data and its claimed digest can still make a successful physical observation. This is the exact P198/P199 content-claim limitation in another form; P204 retains an explicit real Windows negative example showing such untrusted self-repinning is UNSAFE. A later reopened source path can also change after the HANDLE closes, so returned raw exact bytes do not prove source set remains constant or that a signed trusted consumer executes those bytes.

**Source scope:** exactly one new dormant product candidate plus three audit-only files (script, this review, genuine Windows Action), based on the exact original P203 HEAD. Existing P76/Phase10 public route, private historical B, P201/P202 candidates, native service and frozen tests remain untouched. Kristian original D:\Nayeon\BYOK_C1_PRODUCT_20261028 remains at original HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1 with all 17 pre-existing changes preserved.

## Eight genuine native Windows selected cases

On a self-owned disposable hosted Windows test root with TWO harmless synthetic files and **no credential material**, test:
1. Two pinned originals return exact bytes + real 16-byte Win32 FileIds in records explicitly marked NOT_ADMITTED.
2. Real NTFS named ADS on one file fails closed.
3. Real hardlink sharing the source leaf fails closed.
4. Mutation of the source main-stream bytes refuses the original independently supplied test pin.
5. Canonical alias/traversal, ADS path and malformed/missing source inventory refuses.
6. Physical source path replacement AFTER successful HANDLE-based observation leaves returned original bytes intact, but another read against original pinned SHA refuses: no post-return “lease”.
7. Controlled modified bytes plus attacker-controlled recomputed SHA are observed as apparently valid **UNSAFE**: this proves no signed trusted manifest/root has been established, not successful source admission.
8. Source HANDLE stream-enumeration error refuses without returning a partially inspected set.

Authenticate predecessor P203 genuine Windows ZIP/CRC/member hashes, source/Git HEAD, its public P76 gate refusal and H/C/R before tests. Record actual OS exit, unittest footer, raw member hash and source-before/after in H/C/R. Eight cases are selected, not any full Windows product regression.

## What remains before BYOK C1 implementation is truly safe

**G0 source trust:** choose and independently authenticate current Phase10/P76 release/manifest and source-set identity; owner signed root, durable epoch/rollback, Win32 volume, directory, FileId and NTFS journal continuity, an atomic or otherwise protected source-set snapshot/transaction. The current P204 supplied pins are untrusted, two test files are synthetic, and source-set reads are sequential and close each HANDLE.

**G1 signed consumer and trusted UI:** independent qualified Windows security review for signed native service and approved UI broker, exact code-content-bound loader identity and authenticated protected IPC; a signed interpreter or caller-supplied receipt is insufficient.

**G2/G3 effect and durability:** service-owned one-shot consent ticket bound to actual exact bytes and operation, mutex/stop/revocation linearization, durable intent/consumption and HKLM/file anchor, sticky recovery with no automatic uncertain native retry.

**G4/G5/G6 platform and acceptance:** trusted installer/helper/Code Integrity, Windows x86 managed signing approval, all seven independent GOV/SEC/REL qualified reviews, G0–G6, original P135/P175/P178/P179/PERF-P187-01 failures/timesouts and three complete unfiltered product Windows regressions **0/3** remain open. No user API key entry until approved secure local UI.

**Disposition: user-approved isolated engineering CONTINUES; real credential/privileged C1 NO-GO.** No WinCred writes, service install, provider validation, signed release or Google Drive MASTER/dashboard production reconciliation. PR DRAFT, UNMERGED; any claims of source-enrolled protected release or qualified independent GO would be false.
