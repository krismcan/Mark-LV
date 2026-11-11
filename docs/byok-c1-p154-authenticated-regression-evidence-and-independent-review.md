# Nayeon v1 — P154 authenticated full-product Windows regression inventory

**11 November 2026 | OM v2.1 | SOURCE-PRESERVING EVIDENCE RECONCILIATION | RELEASE HOLD**

## Provenance and purpose

Exact reviewed base P153 `08eb591a6a414f0a9eddbf309327475c99a18752`,
draft PR #78, with **25/25 unchanged supplemental Windows security tests
passing**. That scoped candidate neither replaces the original historical
security tests nor establishes whole-product readiness. P154 adds exactly
three audit-only files and creates **zero new product test executions**:
it reconciles genuine earlier Windows evidence for external review, without
re-running expensive frozen history, changing credentials or altering
original product and test code.

P154's disposable GitHub-hosted Windows-2025 Python 3.12 job must obtain
**exactly seven prior, separately archived real Windows Actions artifacts**
from this same GitHub repository. It uses the ephemeral per-job
`actions:read` GitHub token only to retrieve pinned artifact IDs. The
token MUST NOT be emitted, put in logs or forwarded to the external
redirected artifact-blob host; the runner explicitly rejects unknown
redirect hosts. Each archive must match the **original GitHub-reported
SHA-256 byte-for-byte**, and each original native per-module log is then
matched against its earlier source manifest SHA-256. No provider API
tokens or other real credentials are used.

| Original source evidence | GitHub Actions run | Artifact ID | Expected original archive SHA-256 |
| --- | --- | ---: | --- |
| P135 three full-discovery attempts | [P135 #42717686606](https://github.com/krismcan/Mark-LV/actions/runs/42717686606) | 13721186316 | `AA179E18E3AA39FC3254A6C44D8654FFE93685DD792D84BA1E79049A96F86856` |
| P142 83 original module inventory | [P142 #42869600063](https://github.com/krismcan/Mark-LV/actions/runs/42869600063) | 13787854664 | `1525E5779F015101DF3FEE3A71739D383DAD75DF6579CA47F7CFDAEEDCB2B9C1` |
| P143 five safe-TEMP module recoveries | [P143 #42871497308](https://github.com/krismcan/Mark-LV/actions/runs/42871497308) | 13788724995 | `74AD38F57E4A29346BA2DFD1F191781CA25CA6BFC186AE71DFB38BCBFE0651EE` |
| P144 fifteen residual Windows failures | [P144 #42904284147](https://github.com/krismcan/Mark-LV/actions/runs/42904284147) | 13804256598 | `4D62B64CB9872601AF271B8D47DE1CE7B76468E9013F0A9A8417CF9DC79C41E3` |
| P148 original A04 22-case pass | [P148 #42911514225](https://github.com/krismcan/Mark-LV/actions/runs/42911514225) | 13807736953 | `A7BE0131798C5E734CD0D7BBAB6AF3DF6B4522271390FD9C90B9D07506A238B` |
| P149 original Phase8.36 11-case fail | [P149 #42915587821](https://github.com/krismcan/Mark-LV/actions/runs/42915587821) | 13808993133 | `917D8964CA36EB1E3161495BFC72A17A88E6CBC66E3492433DB419D38DEF68CC` |
| P150 original BYOK scope 190s timeout | [P150 #42916722272](https://github.com/krismcan/Mark-LV/actions/runs/42916722272) | 13810925078 | `BD308A9CA778569F7FF63AF6B695B9DB5D1C59B311DE51D562352D534144801C` |

### Historic raw Windows baseline

P135 ran **3 genuine unfiltered Windows Python discovery commands**, each
native exit **124** (600-second timeout; recorded in original P135
GitHub job #129503338552). Raw byte-identical original logs,
`SHA-256 31F844EE8C29B9886885303DF983FFA7C0452C2A671866400A9768535C6DD113`,
contain exactly **1,637 completed original OK outcomes, 37 FAIL and
7 ERROR**, or 1,681 completed records, and one unfinished historical
`test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused`.
**None** produced a final whole-suite unittest footer, and **zero** of
the three full-product regressions have passed.

P142 independently ran the 83 original Git-tracked test modules
lexically AFTER that historical stall, each with its own 35-second
Windows process: **54 PASS / 20 HOLD / 9 TIMEOUT**.
Its first failure parser undercounted CRLF unittest FAIL/ERROR headings;
P154 uses the **raw original P144 logs and footer**, not the
incorrect earlier P142 per-test summary regex. P143 verified five
original previously-failing modules passing in the unchanged P139
native opened-handle safe temporary root: **187 tests**, all PASS.
P144 ran fifteen other original HOLD modules unfiltered under the
safe fixture: all **15 remain HOLD**, zero timeout, with **30 genuine
original FAIL/ERROR headings** across the full logs. These failure
records cannot be marked passed.

P148: original A04 was 35s TIMEOUT in P142; whole 22-test module
completed genuine native EXIT 0 / PASS under an adequately bounded
68-second Windows execution. P149: original Phase8.36 was 35s TIMEOUT
in P142; entire 11-test module completed native EXIT 1,
**9 PASS / 2 FAIL**, a genuine historical exact-branch HOLD.
P150: original BYOK-B predecessor suite ran 190 seconds, native
EXIT 124 with 8 completed PASS, 2 observed FAIL, one still executing,
two not reached, no final unittest footer; it remains TIMEOUT/HOLD.
P151 later proved the synthetic topology original case passes
individually while two live admissions genuinely fail P76; it did
not convert the full P150 module to a pass. P152 repeated the whole
original 10-test P76 module: 8 PASS/2 FAIL on the later Git branch
and real P76 exact branch refusal. P153 separately ran **25/25 named
supplemental security tests** successfully, not original suite clearance.

### Reconciled module inventory (not one completed full-product run)

| Module cohort | Original P142 | Later authenticated evidence | Latest independently observed module status |
| --- | --- | --- | --- |
| P142 suffix of 83 | 54 PASS / 20 HOLD / 9 TIMEOUT | Five P143 HOLD→PASS, one P148 TIMEOUT→PASS, one P149 TIMEOUT→HOLD, one P150 still TIMEOUT | **60 PASS / 16 HOLD / 7 TIMEOUT** |
| 86 modules up to and including P135 stall | Incomplete P135 whole-suite discovery | No complete new unfiltered run across whole cohort | **Not cleared** |
| All 169 Git-tracked original `tests/test_*.py` modules | Enumerated from actual Git source | P154 emits full per-module source SHA-256 and actual evidence mapping | **NO complete full-product PASS** |

The suffix figures are **individual module dispositions obtained on
separate old branches and fixtures**. They are *not* a simultaneous
169-module production test result. The P154 machine ledger lists all
169 test source paths and their current original source SHA-256;
86 before/at the P135 interruption are expressly unapproved, and 23
post-stall suffix modules retain an authentic HOLD or TIMEOUT.

### Named unresolved failure domains, not speculative root cause claims

P144 original raw logs show multiple security and test-contract failure
types. P154 identifies **non-exclusive trace-signature flags**, while
preserving each source log's original failing test IDs and final footer:

- **P76 exact historical branch refusal:** original P76, P77, older
  presentation-configuration and provider-scope modules frequently
  refuse newer branch lineage. This is a real negative security
  response, not grounds to relax the P76 gate.
- **P85 exact historical branch refusal:** at least one original P85
  positive-control assertion refuses the newer branch.
- **Other historic causal assertions:** P77 expects a specific
  tamper error and instead hits the earlier P76 branch check,
  requiring a qualified reviewer to decide correct branch-specific
  scope and causal coverage.
- **Static UI/ownership/effect tests:** Phase8.31 original import
  closure and one retained fake Tk root, Phase8.32 direct-method
  first-thread-gate position assertions remain genuine original
  failures; they are not proved harmless by a P76-only explanation.
- **Windows credential import closure:** one original
  `test_windows_credential_backend` static assertion sees
  `nayeon.secrets.contracts` where its older import set disallowed
  it. Requires separate review of the newer consumer design.

No automatic remapping or waiving of any of those historical tests is
authorised, and no actual independent reviewer GO has been obtained.

## Next independent reviewer / release acceptance decision register

1. **Independent identity and authority:** qualified reviewer with
   dated source, remit, conflict-of-interest declaration and signed
   decision; assistant's own reviewer notes cannot satisfy this.
2. **Source-seal governance:** immutable original P76/P85 older
   Git-branch fixtures, negative tests, exact tags/object trees,
   and explicit independently approved current-branch positive and
   negative admission suite; no global branch substitution, xfails,
   disabled tests or broad ignore filters.
3. **User-scoped BYOK threat model:** manual Review→Approve consent,
   one-use ticket, Windows account isolation, same-user malware,
   WinCred exception/unknown results, crash/ABA and race, memory
   lifetime, logout/launch TOCTOU and secret leakage; do not claim
   credential-manager protection against same-user malware.
4. **Whole-product Windows regression:** explicit versioned 169-module
   inventory and approved classification for all original historical
   failures, current-branch equivalent controls, actual genuine
   native zero exits, complete unfiltered footers and log hashes for
   **three complete full-product executions**.
5. **Publisher-signed deployment:** main/help/installer real signed
   bytes and pinned exact SHA-256/certificate, hardened installation
   ACL and update path, authenticated frozen helper source,
   Authenticode load and TOCTOU rejection, dated independent Smart
   App Control or WDAC policy owner GO. The P140 defaults remain
   all empty and policy FALSE.
6. **Release authority:** only after all of the above, explicit
   production admission. Original privileged C1 G0–G6 remain
   separately OPEN (including P96 and P124), outside narrow
   current-user first release. User enters any real API key locally
   only after the secure signed window has independently passed.
   No pre-release Git merge/tag/release or Google Drive master
   workbook/dashboard change. On an actually approved release,
   update the original Drive MASTER workbook first, dashboard second.

## P154 acceptance and provenance conditions

The P154 GitHub workflow requires exact P153 parent ancestry,
**only three audit-only added paths**, clean source, genuine hosted
Windows, exact SHA for seven original archives and original contained
logs, exact 169-module inventory, P135 raw 1,681-case partial
outcomes, P142 status and P144 fail counts, P143/P148 genuine passes,
P149 real failure and P150 real timeout. All discrepancies **fail
the evidence job** instead of yielding a plausible ledger.

This documentation's numbers are preliminary source-derived inputs
until the new Windows verifier has actually succeeded. The emitted
JSON manifest and raw prior archives are the reviewer-auditable source
of truth. GitHub prior artifact retention expiry means the reviewer
should preserve the resulting consolidated P154 receipt and original
archives before historical GitHub Actions artifacts expire.

**P154 inventory audit does not run a production binary or provider;
it cannot grant security review, three full-product passes, signed
install, SAC owner approval, a release or a Google Drive update.**
