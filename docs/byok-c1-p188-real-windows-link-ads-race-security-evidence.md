# P188 — Actual Windows hardlink, alternate-stream, junction and source-race evidence

**13 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | Experimental only | PRODUCTION RELEASE HOLD**

## Proven baseline and source-authority boundary

P188 begins from exact P187 HEAD a00b888e38fad5fed06ba05190be9c2838fb0320. Original authentic P187 Windows run #43403521185 has ZIP artifact #14026576593 with SHA-256 7D76BFF5944AEF80A0821F295F542E03BBE49A3ADF8A2E298AD8EE67F0B52643; it contains four complete selected exact-source Windows logs (P184 12, P185 12, P186 12, P187 13) and an original hold/custody ledger. This is **49 selected tests across four identities**, not a full product regression. Authenticate it before P188 tests.

P188 adds exactly three review-only files. No modifications to frozen original source/test code, source seals, prior P180–P187 scripts, current public Phase 10 successor, original Kristian product worktree, real credentials or privileged services. Host-allocated native Windows disposable directories only.

## Motivation

P187 demonstrated the historical private B full source gate in disposable Windows Git worktrees but explicitly left hardlink, reparse, alternate data streams (ADS) and concurrent parent-replacement assumptions untested physically. The original tests/phase8_byok_b_scope_migration.py delegates _disk through 8.37 to original tests/phase_8_31_scope_migration.py::_disk, which calls 8.30's linked-parent check and symlink/is_file check, then independently reads bytes. That original component does not explicitly test Windows hardlink count or enumerate named alternate streams.

Physical Windows test classification is **two-sided**:
- Observe original unmodified reader behaviour, including any actual **acceptance of a physically hardlinked or named-stream-bearing source**. Those observations are security **GAPS**, not PASS for production trust.
- Separately demonstrate an additive, never-integrated experimental inspection prototype refusing links, reparse parents, ADS, wrong paths, corrupt immutable B source and a deterministic parent swap during source read. Its success only proves test coverage in the disposable fixture. It does **not** establish atomic Win32 HANDLE / OS-level race resistance or full B verifier equivalence.

### Planned actual Windows test coverage

| Native scenario | Original reader expectation | Experimental inspection expectation | Admission limit |
|---|---|---|---|
| Ordinary original sealed B source | Original direct disk reader accepts bytes | SHA-256 pin + Win32 type/stream observation accepts | Not entire live B verifier |
| Physical hardlink to B source | Record *actual* original reader behaviour, even if it accepts | Refuse if st_nlink > 1 | Original hardlink acceptance must remain OPEN security gap |
| NTFS named alternate data stream on source | Record original base reader behaviour | Enumerate FindFirstStreamW/FindNextStreamW; refuse non-default stream | Stream metadata is not a signed Win32 source handle |
| NTFS directory junction replacing parent | Original linked-parent assertion should refuse | Refuse reparse in component lstat | A static check is not race-free |
| Changing bytes after initial observation | Original B immutable SHA256 must remain authority | Refuse changed B seal | No cached approval |
| Parent changed to junction after initial observation | No production race claim | Refuse on post-read observation | ABA / instantaneous reversible race remains OPEN |
| Canonical alias / stream path / wrong historical path | Original canonical-path policy retained | Reject before reading | No new trust |
| Restore valid source after corrupted source | Live decision recomputed | No success cache | Reversible races not disproved |
| Frozen historical original B negative | Run original test source *unchanged* as diagnostic, preserve any FAIL | No test weakening or result waivers | Diagnostic is not counted as green |

P188 reenacts original P184 12/P185 12/P186 12 at their exact branches, and original P187 six Windows physical fixture tests at its exact original branch. Each has native OS exit, log and SHA-256. The P188 new physical tests run separately under its own exact source identity. The frozen original B link/reparse/hardlink test runs *diagnostically* and is never counted as accepted if it fails.

## Risk register and qualified review

HARDLINK-P188-01: A physically hardlinked original B source may remain acceptable to the historical 8.31 reader even though the original frozen B negative test expects link refusal. Physical acceptance is a gap, not an approved baseline.

ADS-P188-02: An original B source could have unreviewed NTFS named streams invisible to its original byte-hash / Git tracked source envelope. A separate prototype can enumerate streams, but no production admission is approved.

RACE-P188-03: Filesystem parents and leaf bytes are checked at different moments. A deterministic replacement rejected by a pre/post prototype does not prove resistance to an attacker restoring the original file before the second observation. OS handle no-follow / file identity / directory handle pinning and races remain OPEN.

PERF-P187-01 remains OPEN. P187's repeated full historical B verifier invocations took ~335 seconds for seven selected synthetic test methods. There is no approved optimization to cache successful security admission.

Older P135 3×600s full-product Windows timeouts; P175 five original historical FAILs; P178 165s original B module timeout plus two original FAILs; P179 130s historical pin timeout **all UNWAIVED**. Accepted full unfiltered native Windows product regression: **0/3**. Qualified independent GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 decisions OPEN; G0–G6 privileged gates OPEN; signed main/helper/installer and SAC/WDAC release GO absent. No WinCred, keys, provider calls, production verifier modification/merge/tag/release or false Google Drive MASTER/dashboard release status.

**P188 can close as an experimental original-filesystem behaviour discovery only when genuine Windows evidence and authentic SHA-256 custody are produced. Any original reader accepting a hardlink/ADS stays a blocking security issue, even if all independent audit tests pass.**
