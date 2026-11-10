# Nayeon v1 — BYOK C1 P144: unchanged original Windows residual-module triage

**10 November 2026 | OM v2.1 | AUDIT ONLY | USER-SCOPED RELEASE HOLD**

## Source custody and purpose

Direct immutable P143 parent: `3e4075afa119b7cecf14dc349ac620661cb36403`, draft PR #68.
P144 is an isolated GitHub draft branch that adds only this review file, one hosted-Windows
workflow and one bounded original-test runner. No P132 offline credential setup controller,
P133 manual launch, P140 fail-closed frozen signer gate, P139 native filesystem
handle verifier, historical source guards or original test assertions are changed.

P142 genuine post-stall diagnostic ran **83 previously unreached original test modules**:
54 PASS, 20 HOLD (original assertions/errors), 9 TIMEOUT. Its raw CRLF unittest
footers, not its earlier faulty summary regex, are the source of error counts.
P143 then ran five original HOLD modules unchanged under a fresh, handle-verified
owned canonical local C: temporary fixture, with **187/187 genuine native Windows
tests PASS**. This left **15 original P142 HOLD modules** needing discrimination.

## P144 authentic experiment and limitations

On a disposable GitHub-hosted Windows-2025 Python 3.12 account ONLY:

1. Re-establish exact P143 ancestry and require exactly three additive P144 paths.
2. Reuse the existing, unchanged P139 Win32 opened-handle verifier against a fresh
   unique user-owned C:\NayeonP139_<UUID> root. Never relax reparse, case or
   local fixed-drive checks, change global TEMP, or fix test fixtures by bypassing
   the production security boundary.
3. Run **all original tests within each of the 15 modules**, unfiltered and
   unmodified, in fresh independent Python child processes, with only child
   TEMP/TMP/TMPDIR redirected to the verified fixture. Use no real API keys,
   no production `openai.api_key` OS credential slot and no provider validation.
4. Bound each module at 80 seconds, with at most three concurrent children.
   Record native exit 0/1/124, genuine unittest count/footer, failure IDs,
   elapsed time, complete combined stdout/stderr SHA-256 and byte length.
   Retain original full logs and a machine-readable 15-row manifest.
5. Mark PASS only for a true native zero with complete unittest OK footer and
   no error records. Every native nonzero, timeout or missing footer remains
   a named HOLD. Collection workflow SUCCESS only means all 15 disposition rows
   were captured; it must **never** be represented as 15 passing modules.

The fifteen include original P76/P77/P85 source/branch seals; Phase8.31 effect
isolation and 8.32 lifecycle; presentation config/identity; provider
composition/startup/service and original Windows Credential backend tests.
This experiment does not authorise changing fixed historical assertions, nor
does it establish that all failures are test-environment problems.

Nine P142 original module timeouts are **not covered** by this scope:
Phase8 BYOK scope integrity, Phase8.30/31/32/33/34/36/37 scope integrity,
and pre8.29 A04 two-process recovery. The earlier P135 slow historical
BYOK-B integrity case remains OPEN as well. Full-suite three-pass recovery
needs qualified branch-aware, immutable historical custody and separate
cost-bounded regression governance.

## Security and release gate disposition

P140 frozen signing pins (actual main/helper immutable SHA256, publisher
certificate) and Code Integrity policy-owner approval are absent and
default fail-closed. A legitimate signed/installed production companion,
protected replacement/update policy, qualifying Smart App Control load
enforcement, and independently named Windows user-scope security reviewer
GO remain missing. Same-user malware/ABA, crash uncertainty and
read/launch TOCTOU are not solved by user-scoped credential storage.

P141 three scoped 190/190 genuine Windows test runs remain valid,
but **ARE NOT** three complete whole-product Windows regressions.
Original privileged C1 G0–G6 remain separately OPEN, including P96 and
P124 historical gaps. No production API key use, WinCred effect on Kristian,
privileged LocalSystem or HKLM/TPM mutation, unapproved code signing,
unsigned executable run on Kristian, SAC bypass, GitHub merge/release
or pre-release Google Drive master workbook/dashboard mutation.

Only after an actually approved signed release, update the original
Google Drive MASTER release workbook first, then the dashboard.

**P144 = precise diagnostic evidence collection, NOT security signoff,
repaired legacy seals, a full-product regression pass or a release GO.**
