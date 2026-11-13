# P192 — Stable Parent Windows HANDLE Identity & ADS Race-Hardening Assessment

**13 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1 | EXPERIMENT ONLY — RELEASE HOLD**

## Original immutable custody

P192 parent exact P191 HEAD 6c759056b380626991e86e2543fac855da8fc5c9; P191 draft PR #116 unmerged. Original P191 Windows run #43425359167, original archive #14037690093 with SHA256 91AA20D52EC8DD713C422548BF2C32637321B041D8815D40F943DAEF56E92A00, four original members, CRC and authentic separate source-bound Windows P189 4/4, P190 10/10 and P191 10/10 logs/footers plus original H/C/R HOLD ledger. Authenticate this original ZIP before any new P192 test.

P192 adds exactly three new audit-only files (this document, Python prototype test, Windows workflow). Historical full private BYOK B verifier and frozen tests, original 8.34 hardlink defence, current public Phase 10 successor, all earlier P180–P191 audit scripts, original product and 17 preexisting dirty paths on Kristian are never modified.

## Why P190 parent mtime is wrong

P191 physically proved that adding an unrelated sibling within an observed source parent directory changed that parent's mtime and caused P190's pre/post metadata equality test to refuse a valid, immutable source (PARENT_PATH_IDENTITY_DRIFT). This is an availability false positive: the trusted directory still has the same volume/FileId and is not a reparse point.

P191 also proved ordinary Windows sharing does NOT prevent a distinct process from adding a named NTFS ADS or a hardlink to an exclusive-open leaf, although P190's subsequent same-HANDLE stream/link queries refused those specific changes. Thus merely opening an exclusive leaf is not an atomic source/ADS seal; reversible changes and ancestor ABA remain unproven.

## New isolated P192 design

P192 keeps all original P190 leaf defences in a new experimental subclass. At the beginning of read, open Windows HANDLES to the existing temporary source root and each parent directory with:
- Win32 CreateFileW, desired FILE_READ_ATTRIBUTES
- FILE_FLAG_BACKUP_SEMANTICS plus FILE_FLAG_OPEN_REPARSE_POINT
- Share FILE_SHARE_READ | FILE_SHARE_WRITE, **not FILE_SHARE_DELETE**. This is intended to prohibit removal/rename of the held parent by standard same-volume Windows file sharing, without blocking independent sibling writes.
- GetFileInformationByHandleEx FileIdInfo to bind volume and 128-bit File ID, FileStandardInfo to require directory/non-deleting, FileAttributeTagInfo to reject reparse, and GetFinalPathNameByHandleW to require actual path agreement
- Hold those parent handles continuously while the same P190 exclusive leaf HANDLE is read, the original literal 23-source B static SHA is verified, and leaf FileStreamInfo/link count/FileId/final path are rechecked
- Re-query parent HANDLE FileId, attributes and path before acceptance. **Do not compare mutable parent st_mtime_ns**, eliminating the specific unrelated sibling false denial without silently accepting different directory identity.

All success remains bounded to the test process. A top-down sequence of **pathname-based CreateFileW** directory opens is NOT an atomic trusted relative-open transaction and does not prove that an attacker cannot replace a parent at the instant before a handle opens, or swap NTFS named streams/hardlinks in an ABA window.

## Actual Windows tests

P192 must run true source-bound original P189 4 tests (complete historical B alias verdict), original P190 10 tests (same-HANDLE NTFS ADS source), and original P191 10 tests (cross-process source/share race) from their original independently authenticated exact commits. New P192 12 tests use exact P192 HEAD and genuine original sealed B source bytes in unique hosted Windows temporary directories:

| Scenario | Expected interpretation |
|---|---|
| Original sealed B source | Same HANDLE reads exact source bytes and 23-pin manifest intact |
| Different process creates sibling in temp root while parent HANDLES are held | Sibling write allowed and original valid source admitted |
| Different process creates sibling inside held source parent | Sibling write allowed and same source still admitted |
| Different process adds named ADS while exclusive leaf read active | Genuine OS permits, post-HANDLE FileStreamInfo refuses |
| Different process adds hardlink while exclusive leaf read active | Genuine OS permits, post-HANDLE link-count refuses |
| Different process tries renaming a held source parent | Windows refuses with actual WinError 5 or 32 on this runner |
| Different process tries replacing leaf | OS refuses or candidate denies any source identity drift |
| Pre-existing junction parent | Reparse attribute detected via opened parent HANDLE, denied |
| Changed main sealed B bytes | Literal original SHA256 seal mismatch denied |
| Extra named ADS before handle open | Extra stream denied, no success fallback |
| Parent HANDLE metadata failure | Fail closed, close all handles, next normal read still works |
| After denial and restoration, independent sibling write and valid source read | No leaked HANDLE, no stale success |

These are **selected Windows tests across independent source identities**. No result counts as the three complete full-product Windows regressions. Preserve actual raw logs, complete unittest footers, native exits, SHA256s, source before/after and native failure artifacts, and never waive an original security assertion.

## Open security gates and performance

- SEC-P192-01 OPEN: top-down HANDLE pinning by absolute path, though stronger than P190 lstat mtime, still lacks true OS-enforced trusted-root relative opens/identity proof and a proven ancestor-replacement ABA resistance across all operations.
- SEC-P192-02 OPEN: named ADS and hardlink creation/removal between two valid snapshots can be reversible. Locking a file without exclusive stream namespace lock does not establish atomicity. Qualified independent Windows security review required.
- AVAIL-P192-03: solve confirmed sibling-mtime false denials in isolated prototype only, then benchmark under normal Git worktree changes before integration.
- PERF-P187-01 OPEN: repeated full historical B admission ~335s in earlier P187 audit conditions; cannot skip security witnesses to fake passing tests.
- Historical P135 full-suite three 600s timeouts, P175 source-era original failures, P178 B module timeout + original failures, P179 pin verification timeout all genuine UNWAIVED.
- H/C/R = HOLD / ISOLATED HANDLE DESIGN ONLY / HOLD. GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 qualified independent approvals OPEN; G0–G6 privileged admission OPEN. Zero of three complete unfiltered native Windows full-product regressions accepted. Signing, installer, SAC/WDAC absent. No real credentials, Windows Credential Manager, provider calls, privileged service, production verifier edits/merge/tag/release or false Google Drive MASTER/dashboard release status.

**P192 can close only as genuine narrow native Windows engineering evidence, not proof that BYOK C1 can be released.** The previously confirmed original historical full B ADS gap is still unpatched.
