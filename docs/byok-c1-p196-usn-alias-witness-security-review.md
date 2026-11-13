# P196 — Windows NTFS per-file USN reversible alias witness and authority recovery review
**13 November 2026 | AUDIT-ONLY | HOLD / isolated Windows research / HOLD**

## Authentic source boundary

Exact P195 parent 56ff1722a4704c28b228d5f6d5137227bde7ded2. P195 original Windows Actions run 43482531077; artifact 14065617573; authenticated two-member ZIP SHA-256 82881132D15908E19D4F1761C91D2247C6914F5061640A02007BA2C3F438DF14. Its raw 22-test Windows log SHA-256 7D3AEEC639EE07AD2787F76EB1A657E595F9CEC2F5D809817E7EFC44EF4A2B98 and H/C/R ledger SHA-256 46767CC7CF66809D595EBC1D6B4036382A3C8D186CB0824D04115D59A344DAB5 authenticate the **P195 ADS and hardlink ABA admissions**. All original P195 tests, original BYOK-B tests, product sources and reviews are preserved, not altered.

P196 must differ from P195 by exactly three **new** audit paths: this review, scripts/p196_windows_usn_aba_source_witness.py and .github/workflows/p196-windows-usn-aba-witness.yml. The current runner clone must be an independently source-identical clean Windows Git tree, and no writes to Kristian's product worktree are authorised.

## Technical candidate

Microsoft documents FSCTL_READ_FILE_USN_DATA on a **file HANDLE** to get its last Windows NTFS/ReFS change-journal USN, and documents USN_REASON_STREAM_CHANGE (named stream create/delete) and USN_REASON_HARD_LINK_CHANGE (hardlink create/delete). See https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_read_file_usn_data and https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-read_usn_journal_data_v0 .

The *test-only* P196 reader subclasses P194's held-HANDLE, pre-bound physical root/ancestor/leaf reader without changing its existing FileId, original literal B SHA, source stream, hardlink and NT relative component checks. It queries FSCTL_READ_FILE_USN_DATA on the **same held leaf HANDLE** as each initial/final identity observation and includes the current file USN in the compared identity tuple. Any unavailable, malformed, unsupported or drifting USN fails closed. Real first/final observations must record the actual native response and different USNs when separate processes create+remove a named ADS or hardlink between observations. Legitimate root/parent sibling writes must not drift the leaf USN.

This is a **candidate ABA-detection witness, not an atomic exclusion mechanism**. It does not protect against privileged filesystem/journal manipulation, disabled/unavailable USN, journal resets, volume replacement, USN reuse/rollover, signal races around the last query/return, other filesystems, untrusted file enrolment, or signer compromise. A single last-USN sample also does not independently establish an end-to-end **volume journal continuity** proof; separate authenticated volume/journal identity would be required.

## Physical Windows matrix

Run P194 14 unchanged inherited tests + P195 8 unchanged inherited tests (including explicit old unguarded reader ABA admission) + P196 8 added synthetic/nonsecret tests = **30 selected Windows tests**. They are not full-product regressions:

- 23 genuine file-USN initial/final stable original sealed-source read;
- 24 independent sibling file creation in same source parent accepted, unchanged leaf USN;
- 25 separate process ADS create+remove **while held leaf HANDLE**, experimental USN reader must refuse and demonstrate changed native file USN;
- 26 same real Windows cross-process hardlink create+remove, changed file USN reader must refuse;
- 27 simulated USN query failure refuses even literal original good source;
- 28 malformed/unsupported USN record decoder refuses, no fabricated OS evidence;
- 29 valid signed older source manifest still needs a **separate independently trusted** epoch floor (USN cannot confer rollback protection);
- 30 sibling write in root accepted without leaf-USN false refusal.

Windows runner source custody, original P195 evidence ZIP integrity, native exit code, complete full raw test log, per-file observations and SHA-256 must be preserved, including failures. A new selected green case proves only the named physical fixture's observed refusal. Do not infer production ATOMIC security, full original Git/index/tree/HEAD equivalence or a reliable journal across restarts.

## Recovery and root authority: product architecture requirements, NOT implementation

An actual product would need signed installer/binary/source-root origin independently authenticated *before* source FileId enrolment; an authentic release signer/manifest and original Git/index/tree/HEAD version; file and volume identity joined with an independently protected monotonic release epoch, signed cert key IDs and revocation; recovery for disk replacement, journal reset and loss of trusted anchor. No local file hash, DPAPI, Credential Manager or signed file *alone* supplies anti-rollback or safe initial root enrolment.

Proposed fail-closed decision hierarchy:
1. deny if signer/release authority not independently validated;
2. deny if trusted root/ancestor/leaf not bound before ordinary filesystem lookup;
3. deny if platform/volume/journal unavailable or changed and no independently reviewed recovery policy exists;
4. deny if any source byte hash, NT stream, physical link, handle identity or USN witness differs;
5. deny until exact original historical BYOK-B gate, current Phase 10 gate, signed executable/helper/installer, trusted caller and source namespace are separately reviewed;
6. deny any live credential/privileged operation until qualified governance and production gates provide explicit GO.

A false-positive unrelated write, missed transient event, concurrent privileged mutation, volume migration, USN journal truncation/reset, process restart and crash replay all need additional review; P196 is not a transaction proof.

## Independent security review decision conditions

**Open:** SEC-P195-ROOT-01 trusted pre-enrolment, SEC-P195-DURABLE-02 independent rollback/recovery, SEC-P195-ABA-03 proven P195 reversible alias admission, SEC-P195-GIT-04 original entire B and Phase 10 product identity, SEC-P195-ADS-05 historical original full BYOK-B named ADS gap (UNPATCHED), SEC-P193-HANDLE-01 original product resource gap, and PERF-P187-01. Genuine historical P135 3 full-product Windows timeouts, P175 five original failures, P178 original B timeout+2 failures, P179 source pin timeout remain UNWAIVED.

Qualified external GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 review decisions OPEN; G0–G6 privileged admission OPEN; signed main/helper/installer SAC/WDAC/Code Integrity GO ABSENT; native full-product Windows accepted **0/3**. An assistant-authored review and experimental Windows lab evidence do not count as independent reviewer signoff or product release.

**No credentials, production Windows Credential Manager writes, real provider validation, privileged service operations, source test weakening, Git PR merge, tag or release.** MASTER workbook and dashboard are not release-reconciled without actual release. H/C/R remains **HOLD / isolated experimental security research / HOLD**.
