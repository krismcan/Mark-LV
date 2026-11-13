# P190 — Isolated Windows HANDLE-Bound ADS and Source-Identity Prototype

**13 November 2026 • Nayeon v1 / Mark-LII • BYOK C1 • OM v2.1 • RELEASE HOLD**

## Authentication and exact scope

Exact P189 parent: 75a312cce7e0231b41b2920c45c3c002bd59f120. P189 successful genuine hosted Windows run #43410788905, artifact #14029676768, original ZIP SHA256 54AECDB6A275155D70881761AF4B1ABA602398E8D6DC0E67898DDB1D44447D71. Authenticate three original archive members, original P188 9/9 and P189 4/4 source-specific logs/footers/SHA and original H/C/R HOLD ledger.

P189 demonstrated the **complete historical private BYOK-B source gate admits a genuine NTFS alternate stream** attached to sealed source without changing approved main source bytes, while refusing an off-worktree hardlink through the original 8.34 guard. This is NOT evidence of bypass of the later current public Phase 10 admission or production privileged service.

P190 adds exactly three audit-only files. Product, frozen tests, historical/source pins, current public Phase 10 verifier, old P180-P189 scripts, original Kristian worktree and authenticated evidence remain untouched.

## Experimental handle-bound contract under review

A native Win32 prototype requests a **single exclusive GENERIC_READ HANDLE** with CreateFileW, OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT and zero share mode. It queries the same handle with:

- GetFileInformationByHandleEx(FileIdInfo): volume serial and 128-bit file ID.
- GetFileInformationByHandleEx(FileStandardInfo): link count exactly one, source size bounded, not directory/deleting.
- GetFileInformationByHandleEx(FileAttributeTagInfo): reject leaf reparse attribute.
- GetFileInformationByHandleEx(FileStreamInfo): parse aligned variable-length stream records, reject any other than default unnamed stream. Fail closed if unsupported or incomplete.
- GetFinalPathNameByHandleW: observed file path agrees with the exact approved B-envelope pathname.
- ReadFile from same opened handle; original B literal static SHA-256, including original SELF canonicalization, recomputed each invocation.
- Repeat handle ID, file attributes and streams before return. Parent-directory reparse and identity observations occur both before and after, but this is explicitly NOT a race-free parent handle transaction.

No source admission cache, forged source mode, hidden stream acceptance or fallback after kernel-query failure. Importantly this candidate **does not call the complete original historical B gate** for admission, does not inspect full HEAD/tree/index/tag/ancestry, and must never be used in production without that original and current successor admission equivalence.

## Native physical scenario matrix

| Scenario | Evidence requirement |
|---|---|
| Original sealed B file | Genuine original exact source bytes through single handle |
| Named NTFS ADS | Reject based on opened HANDLE FileStreamInfo, though historical B gate admitted ADS |
| Second physical hardlink | Refuse NumberOfLinks, preserving original 8.34 control |
| Directory junction parent | Refuse before source open |
| ADS/traversal/backslash/unknown pathname | Reject before opening handle |
| Changed main-source bytes | Refuse pinned original B SHA256 |
| Existing conflicting source handle | Real Win32 exclusive sharing violation |
| Attempt competing source writer while candidate holds handle | Real sharing violation, no writer admitted |
| Successful read then ADS added then removed | Fresh rejection in middle; never reuse stale approval |
| Synthetic kernel metadata query failure | Fail closed, no success fallback |

Original P189 genuine four-case Windows test class executes against its exact source branch with its own raw native log, OS exit and SHA. New P190 ten cases execute against exact current P190 HEAD with separate native evidence. Original B full-gate ADS acceptance remains an OPEN security finding regardless of P190 test results.

## Review findings and governance

**SEC-P190-01 OPEN**: exclusive opened source handles and parent path lstat observations do not prove secure relative opens from trusted ancestor HANDLEs or prevent all attacker-controlled parent swap/revert (ABA) races; privileged kernel agents or file-system filters may evade user-mode assumptions. No atomic Win32 source transaction established.

**SEC-P190-02 OPEN**: stream enumeration failure, structure bounds, unsupported filesystems, reparse and final-path behavior require independent qualified Win32 security review. Prototype is unintegrated.

**PERF-P187-01 OPEN**: repeated complete original B gate expensive. No caching, bypassing or suppressing tests to accelerate production. Genuine historical P135 full native 3x600s timeouts, P175 five original failures, P178 165s B-module timeout and two original failures, P179 130s history-pin timeout remain preserved and unwaived.

**H/C/R = HOLD / ISOLATED EXPERIMENT ONLY / HOLD.** Accepted complete unfiltered native Windows full-product regressions 0/3. Qualified GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 reviewer decisions OPEN; privileged G0-G6 OPEN; signed main/helper/installer/cert and SAC/WDAC Code Integrity approvals absent. No real credentials, WinCred, provider validation, privileged service, production verifier integration, merges, tags, releases or false Google Drive MASTER/dashboard production release claims.

P190 may close ONLY as a selected native Windows evidence checkpoint once full genuine exits/footers/SHA source identities and unresolved findings are published. Do not call a green result production-ready.

Win32 references: Microsoft Learn CreateFileW, GetFileInformationByHandleEx, FILE_STREAM_INFO and FILE_ID_INFO.
