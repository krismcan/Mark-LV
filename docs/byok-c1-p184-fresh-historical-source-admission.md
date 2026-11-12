# P184 — Fresh historical source admission and tamper-refusal proof-of-contract

**12 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1 | PRODUCTION RELEASE HOLD**

## Baseline and frozen source

P184 starts from exact verified P183 source HEAD \`c450307d414aae3fe87b7c027a151073e9de2a08\` (P183 draft PR #108, unmerged). Its authentic [P183 original Windows run #43316688575](https://github.com/krismcan/Mark-LV/actions/runs/43316688575), [artifact #13987763174](https://github.com/krismcan/Mark-LV/actions/runs/43316688575/artifacts/13987763174) ZIP SHA256 \`F51ADF001521A7D1CFC4C4228C030519FE2BA98D2862EB2EEEC3CB8F236D8DCD\`, native 45/45 case log SHA256 \`D1D504877CCC61FE2DA571EF27E52C6B4950363FE80DA9115A1F0912D6DDC3F4\`, genuine Windows native exit 0.

P183 conclusively found a source-authority gap: P182's isolated fast batch transport accepts a raw Git object ID, **without itself proving the caller's exact source commit, canonical path, branch, index, disk bytes or historical tag seal**. P184 adds a separate **experimental source-admission guard before and after every read**. It does not replace the old historical verifier.

Exactly three new paths are created on an isolated branch: this document, \`scripts/p184_windows_fresh_historical_source_admission.py\`, and \`.github/workflows/p184-windows-fresh-historical-source-admission.yml\`. The entire original \`nayeon/\`, \`tests/\`, prior original P180/P181/P182/P183 scripts, historical frozen signed companion, code integrity policy and original Kristian product worktree remain unchanged.

## Versioned source admission contract

The new experimental \`FreshSourceAdmittedBatch\` takes an **exact branch and expected 40-hex commit** plus an exact allowlisted, canonical source path. The only two allowed original historical source files are pinned byte-for-byte to immutable P183 SHA256:

- \`tests/phase8_byok_b_scope_migration.py\` — \`84CED2F31F5DAF985DE462C384ABDFE47F8B705425F8BDEFB8CF1E04E56EE010\`
- \`tests/phase_8_30_scope_migration.py\` — \`F9AA8C8DF0144C83BAA4EDC8CC8D5F99CE5221C8C1263B13378FEAEB87060487\`

For **every separate read**, P184 performs new Git HEAD and branch observations, canonical top-level repository root, Git SHA1 object-format, exact \`git ls-tree --full-tree -z HEAD -- path\` regular-file \`100644 blob OID\` entry, exact stage-0 \`git ls-files --stage\` matching index OID, Windows \`lstat\` of each parent to refuse symlink/reparse ancestry, and live disk content SHA256 matching the static literal source pin. The disk Git SHA1 blob hash must also equal the fresh HEAD tree OID. The P182 bounded Git batch child returns actual full object bytes, verified by SHA256 against that pin; then **all above Git and filesystem measurements are collected again** and both the validated pre and post snapshots must be identical. No accepted admission state, object bytes or source trust is cached between calls; an error retires and closes the whole candidate transport.

P184 deliberately performs **more** Git process operations than the fast P182 object reader to prove freshness first. No assertion of production performance uplift is justified. A subsequent independently reviewed integration design would need to keep each live security invariant without reintroducing the historical P179 excessive process overhead.

## Actual test plan

Authenticate source exact ancestry and Git three-addition envelope, all 171 tracked frozen test modules, original \`nayeon/\` and \`tests/\` subtrees and prior candidate scripts. Download P183 archive and verify exact ZIP SHA256, CRC, member inventory, original native 45-case complete footer, raw log SHA and H/C/R receipt. Then run **57 complete genuine Windows native tests**: original P180 8, original P181 12, original P182 12, original P183 12, **new P184 12**, and one untouched frozen BYOK-B self-canonicalisation control.

The twelve new tests include 2 live original-source fresh reads (real indexed files), repeated per-read freshness, stale HEAD before/after, changed branch, staged/index tamper, live disk SHA256 tamper, Windows reparse and repo-root disagreement, wrong Git object mode or index stage, noncanonical/traversal/ADS paths, tampered batch payload, and confirmation original BYOK-B full scope remains separate and unwaived. Mocked source observations are **synthetic** and do not change actual files; real source-read tests use genuine Windows Git.

## Security boundaries not closed

The new guard is an **experimental narrow source read contract**, **not** a full original historical B admission. The actual original B verifier also authenticates protected annotated tags, all historical parent tree/ancestry, complete 23-file source-envelope SHA256 pins, multiple source-era seals, exact Git diffs/working tree, ignored files, Win32 races and other security requirements. P184 does **not** run or replace that full verifier; the old source still fails/times out in the known broader historical cases.

- Original P135 3×600s complete full-product discovery TIMEOUT, original P175 historical FAILs, original P178 complete original B module TIMEOUT/two FAILs and P179 original pin-witness TIMEOUT remain unwaived.
- Complete accepted full-product native Windows regressions remain **0/3**. The 57-case narrow suite is not a substitute.
- Qualified external GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 decisions **all OPEN**; neither external security reviewer signature nor actual production integration approval has been obtained.
- Signed Windows main/helper/installer/cert + SAC/WDAC policy GO absent; privileged C1 G0–G6 OPEN; real API keys, WinCred operations, provider validation, production merge/tag/install/release and false Google Drive MASTER/dashboard state changes prohibited.

**P184 may close only as source-authenticated experimental proof of fresh read admission. Full historical security equivalence, independent review and BYOK C1 production admission remain under HOLD.**