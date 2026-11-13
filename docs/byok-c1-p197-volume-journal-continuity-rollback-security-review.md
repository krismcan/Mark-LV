# P197 — Volume-Journal Continuity, Rollback Resistance and Privileged Mutation Threat Model
**13 November 2026 — preparatory independent-security review; additive experimental Windows-only audit.**
**H/C/R = HOLD / isolated volume-journal research / HOLD.**

## Source custody and prior Windows evidence
Exact predecessor P196 Git commit: b5c37f3e718e7d9e75a0bc891b6a8dd237f7a1e6; prior draft PR #121. Original P196 real Windows run 43493093049, ZIP artifact 14071470076, **full SHA-256 C82F80658AE6D247ACBE3952C0CF24E7295C1FD7BC0840F9A4C9F863BAF5516D**. Exact two members, ZIP CRC validated; raw 30-case P196 Windows log SHA 7EC368FC2ED0B8C6639C07EE23A9452036C033739FC91014C5A36BC62D7940A3; original H/C/R ledger SHA 00AF6E2D79A03982C61B86C01E4A5B4D40BA554120DEB7885EEAF2D57EA4FC1F.

P196 observed genuine Windows C: named ADS and hardlink create+remove cycles refused by a per-file last-USN comparison; preserved original P195 unguarded reader still admitted the same cycles. The historical full private BYOK-B named ADS admission gap remains **unpatched**. Original P196 30 tests were **selected**, not full-product acceptance tests.

P197 branch must be an exact descendant of P196 and contain exactly three **new additive** paths: this review, scripts/p197_windows_volume_journal_continuity_review.py, .github/workflows/p197-windows-volume-journal-continuity.yml. Original P195/P196 experimental sources, original BYOK-B/product, historical tests and all prior H/C/R stays intact. Kristian original product worktree, existing modifications and HEAD must never be altered.

## OS authority, witness and trust-boundary architecture

Source reader boundary:
1. P194 synthetically pre-bound FileIdInfo root/ancestor/leaf and original literal B SHA (not independently trusted).
2. P196 same-held-source-HANDLE per-file USN; fail closed on missing, malformed or changed USN.
3. P197 **read-only actual volume journal query** through fsutil usn queryjournal on an already-active Windows C: journal. Record OS exit, journal ID, FirstUsn, NextUsn, LowestValidUsn and MaxUsn, and OS-reported Windows volume serial/GUID. Before/after reads compare identity and plausible monotonic bounds; fail closed on a discontinuity.
4. Report acceptance only for an unmodified synthetic fixture on that observed host; no product integration or independent volume trust is claimed.

Microsoft documentation: FSCTL_QUERY_USN_JOURNAL provides journal state; UsnJournalID changes on journal creation/restamping; LowestValidUsn identifies invalidated historic records; FirstUsn marks earliest currently readable records; NextUsn advances with new journal writes; these are **OS-reported values**, not cryptographically authenticated: https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-usn_journal_data_v1 and https://learn.microsoft.com/windows/win32/fileio/using-the-change-journal-identifier

Real P196 read-only Windows observed D: journal inactive (error 1179), C: existing journal active. Never create, enable, disable, delete or restamp volume journals. P197 uses disposable synthetic/nonsecret C: user TEMP source fixtures, with raw test output stored separately under runner.temp; no access to Kristian product files or disk administrative commands.

**Security nuance:** the last USN and its volume journal identifier are not atomic commit certificates. P197 uses a before/after observation. An attacker with privileges could modify, truncate, disable or replace a journal or volume; the underlying USN can be wrapped/reused and OS volume serial/GUID can be forged, restored or changed. An attacker could also mutate immediately after the last read, before source becomes trusted by a different consumer. Even if P197 selected tests all pass, atomic exclusion and production protection remain unproven.

## P197 selected Windows matrix

P197 inherits **30 unchanged P194/P195/P196 test cases**, including original physical Windows negative evidence, P195 ADS/hardlink ABA admission, P196 USN refusal, real legitimate sibling writes, simulated signature/rollback and basic trust problems. **10 additional** experimental cases:
- 31: genuine C: active journal ID, observed volume serial and GUID plus original source admission;
- 32: live legitimate unrelated parent sibling write does not falsely reject source when NextUsn advances;
- 33: injected **synthetic** journal ID replacement fails closed;
- 34: injected **synthetic** journal NextUsn rollback fails closed;
- 35: injected **synthetic** FirstUsn history truncation fails closed;
- 36: injected **synthetic** LowestValidUsn invalidation fails closed;
- 37: injected **synthetic** OS-reported volume serial or GUID change fails closed;
- 38: injected **synthetic** journal observation failure rejects even unchanged source;
- 39: real Windows child ADS create+remove held source HANDLE still refused by inherited actual per-file-USN observation;
- 40: real Windows child hardlink create+remove also refused.

Only initial/after snapshots and the real mutation cases use native Windows. The injected reset, rollback, disk replacement or journal failure **are not real OS reset/replacement evidence**. Preserve exact raw Windows logs, OS exits, ZIP member SHA/CRC and H/C/R, and keep any failed test records available, not waived.

## Critical trust and recovery gaps for independent expert

- **SEC-P197-VOLUME-01:** No independently authenticated original volume or initial journal ID. Same-host self-observation cannot independently attest original installation provenance. GUID and serial are labels, not cryptographic disk attestation.
- **SEC-P197-JOURNAL-02:** No verified journal continuity across reboot, journal deletion/recreation, restamp, truncation, disk image restore, filesystem repair, USN reuse/rollover, FSCTL unavailable/errors, NTFS/ReFS policy change or cross-volume migration.
- **SEC-P197-ROLLBACK-03:** No independently protected monotonic release/epoch source. Old valid signed metadata plus a restored local epoch can be replayed. DPAPI, Credential Manager, ACLs and local file checksums alone do not solve rollback.
- **SEC-P197-PRIV-04:** No proof against admin/SeManageVolumePrivilege/kernel-driver adversary, signed loader tampering, volume snapshot mount/reparse, arbitrary handle or journal mutation, or TOCTOU after the reader returns.
- **SEC-P197-FULLGATE-05:** Original complete historical BYOK-B ADS weakness remains unpatched; current Phase 10 full original 23-pin Git/index/tree/HEAD/physical path/process policy not integrated. Held P194/P196 source handle plus selected lab tests do not mean production admission.
- **SEC-P197-PERF-06:** Native fsutil subprocess invoked twice per read is an **audit diagnostic**, not a performance-ready/privileged production implementation; measure genuine Windows duration and review a bounded signed native API design later.

**Fail closed** whenever witness source, journal or volume continuity, trusted epoch/release, original source identity, process caller or environmental capability cannot be established. Migration and recovery require separately signed policy and independently reviewed administrative process; silent auto-re-enrolment is forbidden. There is no actual production recovery mechanism or key rotation in P197.

## Existing external review, regression and release hold
Open issues: SEC-P195-ROOT-01, SEC-P195-DURABLE-02, SEC-P195-ABA-03 (P195 experimentally confirmed), SEC-P195-GIT-04, SEC-P195-ADS-05 (original full gate vulnerable), SEC-P193-HANDLE-01, and P135, P175, P178, P179, PERF-P187-01 original failures/timeouts. Seven independent GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 decisions **OPEN**. Privileged G0–G6 **OPEN**. Signed main/helper/installer; Code Integrity/SAC/WDAC GO **ABSENT**. Accepted genuine complete unfiltered native Windows full-product regressions **0/3**.

The review authored here is preparatory evidence, not a qualified independent reviewer signoff. P197 may close as an **isolated experiment only** when authentic complete 40-case selected Windows output, source custody and H/C/R are verified. A successful P197 experiment cannot unlock credential entry, Windows Credential Manager production writes, privileged operations, live provider validation, merge, tag or release. No Google Drive MASTER/dashboard production release reconciliation without an actual release.


## Authenticated initial genuine P197 Windows evidence — 13 November 2026

**Source SHA** a6d41dfbedfbc8e7a445b8d0d41ae2f9c1a5f526; hosted Windows Actions run 43495428663; artifact 14071617308. Entire ZIP independently SHA-256 authenticated: **24BB52D7C95131196A59D90593711B5DBECDB77A6CC5EBE22326FCA9F78EED1E**. ZIP two members and CRC passed:
- p197_original_and_volume_native_Windows_40.log SHA-256 **D38883C424965D54A16530FFFFE4ABC01C0DEBD939F4BCE812E3AD5773D2EAA1**;
- p197_volume_journal_source_HCR_ledger.json SHA-256 **1A4C46BF9BA9DBF2A2470CDD3A0FA1A285C4BDC3A5C74F3AE3C17098BC7DCC4A**.

**Actual selected tests: 40/40 PASS, Windows OS exit 0, complete OK footer; 4.066 seconds for tests.** Source-before == source-after; historical H=HOLD and production R=HOLD, original P196 archive and 30 selected predecessor tests independently authenticated. Source diff remains exactly three new audit paths. Note that 4.066 seconds is **not a production performance result**.

**Native Windows events:** real C: volume journal stable/unchanged source admitted; independent legitimate sibling write admitted. Genuine different Windows process created then removed an ADS, and separately created then removed a hardlink; both physical changes were OS-allowed and the original P196 same-HANDLE file-USN guard refused source admission. Original P195 deliberately unsafe read still admitted in its unchanged inherited control cases.

**Synthetic-only events:** journal ID restamp, NextUsn reversal, FirstUsn truncation, LowestValidUsn invalidation, volume GUID/serial replacement and unavailable journal observation were deliberately injected into the new reader and refused. No actual journal was reset, deleted, restamped or disabled, and no physical disk replacement, privileged attack, real system restart, trusted epoch source or crash recovery was executed.

**Material exposure remains OPEN:** Before/after journal and USN snapshots are non-atomic observational signals and cannot independently prove immutable root provenance, resistance to privileged journal tampering, disk cloning/restore or rollover, safe migration, signed binary admission or recovery. A previously compromised source at first enrolment can still be incorrectly trusted. Source content after the final query and before executing a different consumer remains a TOCTOU risk. A product-ready monitor would need a reviewed OS privilege/driver boundary and cryptographically independent release identity rather than treating fsutil stdout, volume labels, locally stored keys or USNs as trust anchors.

**H/C/R decision:** Experimental checkpoint eligible for closure once the final documentation-inclusive commit is tested against its exact HEAD. Production release remains HOLD; current original historical BYOK-B ADS gap unpatched, 0/3 full-product native Windows regressions, all independent qualified security reviews and G0–G6 admission OPEN. Preserve original source failures/timeouts, PR draft and unmerged. Google Drive MASTER/dashboard are not updated as a production release.
