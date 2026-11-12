# P183 — Historical security equivalence gap proof and qualified-review decision packet

**12 November 2026 | Nayeon v1 / Mark-LII BYOK C1 | OM v2.1 | PRODUCTION RELEASE HOLD**

## Why P183 exists

The P182 isolated batch-Git candidate [draft PR #107](https://github.com/krismcan/Mark-LV/pull/107) has a real-source 32/32 native Windows test receipt and mitigates P181's poisoned-session and unbounded-read prototype issues **within a narrow transport-only experiment**. It is not wired to the historical integrity verifier.

Original authenticated hosted Windows P182 [run #43315530588](https://github.com/krismcan/Mark-LV/actions/runs/43315530588), [artifact #13986804363](https://github.com/krismcan/Mark-LV/actions/runs/43315530588/artifacts/13986804363), ZIP SHA-256 \`F70932E5F47630F0C8E9E31388D9A82221A1B4CF99AC73ED9F6CCECE213664DC\`; complete 32-case native log SHA256 \`263E442E53D243D48CA89FB185E00EB0E4CC7A429150E97B04E7F70EB32A69B9\`, real original exit 0. None of that evidence can substantiate full historical security/production equivalence.

## P183 scope

P183 is a child of verified P182 HEAD \`653cae658e057878a1c010a8dba486cc7f00cb5b\`, and adds exactly three review-only artifacts: this document, \`scripts/p183_windows_historical_security_equivalence.py\`, and \`.github/workflows/p183-windows-historical-security-equivalence.yml\`. Entire original \`nayeon/\` and frozen original \`tests/\` tree, plus previous P180/P181/P182 candidate sources, are source-byte identical. Kristian's dirty original product worktree must remain unchanged.

1. **Native Windows custody:** authenticate original P182 source, 32 original unfiltered native Windows case results (real exit, complete unittest footer), original ZIP SHA256/member CRC/raw log SHA256, original H/C/R and seven qualified reviewer decisions OPEN. Fail if any original evidence changes.
2. **Genuine regression/negative coverage:** run untouched P180 8, original P181 12, untouched P182 12, **12 newly authored P183 security-scope differential tests**, plus **one original frozen BYOK-B source-self control** as native Windows Python 3.12 on an ephemeral exact-head GitHub Actions runner. Require 45/45 complete, native process exit 0. This narrow complete suite **does not count** toward full-product Windows regressions.
3. **Evidence matrix:** record which candidate-specific transport mitigations are exercised and which historical security controls remain unproven. Deliberately demonstrate that accepting a valid opaque Git blob OID does not prove the caller's historical commit, path, HEAD/index/tag, Win32 reparse/alias identity, or sealed SHA256 admission.
4. **Negative preservation:** verify original frozen historical BYOK source files and original signed companion gate byte identity; preserve all historical test failures/timeouts, never patch or hide them. Source-blind batch reads, even correct ones, are **not** equal to full frozen source-integrity verification.
5. **Reviewer handoff:** prepare machine-readable decision packet with all nine security equivalence rows, review owners unassigned, all seven qualified governance/security decisions explicitly OPEN, source and raw-log SHA256. **No claim of reviewer signature, request or GO.**

## Source-to-source security matrix

| ID | Original required protection | P182 candidate | Reviewer status |
|---|---|---|---|
| TRANSPORT-P181-01 | Bounded read/timeout and child retirement | **Tested in isolated P182** | External decision OPEN |
| TRANSPORT-P181-02 | Protocol failure poisons session | **Tested in isolated P182** | External decision OPEN |
| HIST-01 | Live, canonical source commit/branch/path and disk/index/HEAD re-verified on every invocation | **Not in OID-only API** | NOT ESTABLISHED |
| HIST-02 | Original frozen Git ancestry, tags, tree/object-mode, byte-content SHA256 seals and all tamper negatives | **Not integrated** | NOT ESTABLISHED |
| HIST-03 | Win32 reparse, symlink, aliases, alternate data streams and racing writers | **Original source unmodified, no equivalence proof** | NOT ESTABLISHED |
| HIST-04 | Trusted Git executable/process origin, isolation, environment and lifetime | **Partial experimental sanitisation only** | NOT ESTABLISHED |
| REL-05 | Signed main/helper/installer/cert Code Integrity; SAC/WDAC policy GO | **Not issued** | HOLD |
| REL-06 | Three unfiltered complete native product Windows regression PASSes, historical FAILs handled by qualified governance | **0/3** | HOLD |
| REL-07 | Privileged C1 G0–G6 signed service/IPC/custody/race admission | **Not undertaken** | HOLD |

The new self-authored tests that show **missing historical equivalence** should PASS: they deliberately confirm that all seven wider security and release protections remain unproved. A successful *gap-detection* suite is **not** approval of the integration.

## Original historical issues that remain real

P135 original three 600-second full-product discovery **TIMEOUT**, P175 old source-era negative test conflicts and five original failing cases, P178 original BYOK-B 165-second full-module TIMEOUT with two original FAIL cases, P179 original pin-witness 130-second TIMEOUT under instrumented Git subprocess profile; 0/3 accepted full-product native Windows regression PASSes. All prior evidence frozen, unchanged and unwaived.

External qualified decisions **GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 OPEN**, no actual independent reviewer signed or asked in this checkpoint. Signed Windows main/helper/installer/cert, CI release, SAC/WDAC and privileged G0–G6 remain OPEN.

Never run real API keys, native WinCred CredWrite/CredRead/CredDelete, live provider validation, privileged service or unsigned installer; no merges, release tags, approvals, unauthorised source changes or false Google Drive MASTER/dashboard production status.

**P183 can be completed as a reviewer-ready security equivalence gap evidence packet. Source-verifier adoption still requires original native negative tests, independent security/governance approval, three complete full-product regression passes and original production admission gates.**
