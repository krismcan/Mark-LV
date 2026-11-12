# BYOK C1 P175 — Source-bound current-version security candidate

**12 November 2026 · OM v2.1 · Versioned current C diagnostic / historical H preserved / release R = HOLD**

## Authority, source custody and scope

- Source parent is authenticated P174 commit \`98437f4c4e8a09b507bc998a2829bafcc430f8a7\`, draft PR #99. P175 must add exactly three files: this document, one new dedicated diagnostic test/evidence collector and one hosted-Windows workflow. It must not change any tracked \`nayeon/\` product source, \`tests/\` original test, P76/P85/P140 historical pin, signed release pin, credentials, Windows system setting or Kristian's original product worktree.
- Parent P174 genuine Windows [run 43248455614](https://github.com/krismcan/Mark-LV/actions/runs/43248455614), artifact #13957432345, ZIP SHA-256 \`D91607E9076A488F32023D257F106F0FB70A4AC5D408B38A870AC68F6E1A2853\`. P175 re-downloads read-only, validates original ZIP SHA, CRC, exact 13 members, four complete unchanged original test logs, counts, exit codes and fail name; will not silently trust a PR description alone.
- P140 historical source \`9c47bac3308822e11300381017b30e913ffbc211\` tested 6/6 PASS at own source and 24/24 signed negatives PASS. Later P173 source \`b04af8858dbaab6d164352832c6757db0ec1681c\` produced **5 PASS / 1 FAIL** in the *same original six-case* historical scope module and 24/24 signed negatives PASS. The original failure is \`P140FrozenSignedLaunchMigration.test_exact_p139_ancestry_and_approved_six_path_change\`. Original test files are byte-identical between eras. No waiver or rewriting is sought.

## Versioned current candidate — exact claims only

P175 supplements frozen tests with its own **eight** named unmodified-current-source assertions (an independent, separately authored candidate, not a substitute acceptance waiver):

1. Exact three Connection buttons: Back to Conversation / Manage provider (offline preview) / Open local key setup (offline, not connected).
2. Exactly three later user-scoped source imports, with original old WinCred consumer restriction remaining a historical HOLD.
3. Reject a rogue in-memory WinCred import from an unreviewed helper.
4. Reject an in-memory direct native credential backend import in the local Tk UI.
5. Reject in-memory provider/network UI imports.
6. Reject removal of any one of the exact new current import edges (set-contract negative).
7. Preserve original Phase8.31 forbids-brain-import versus later P86 requires-brain-import contradiction as an unresolved test-governance issue.
8. Actual source frozen signed-companion blank SHA/certificate pins and disabled Code Integrity release must remain fail-closed.

All attacker test inputs are synthetic in-memory AST strings; never injected into source files, registry, credential stores or executable launch paths. Static/current candidate tests **do not** establish end-to-end runtime provider isolation, signed Windows install security or qualified independent signoff.

## Original genuine Windows modules and continued historical HOLD

Hosted Windows Server 2025 / Python 3.12 records complete native \`unittest -v\` runs and exit codes for:

| Source-bound test run | Original cases | Required diagnostic outcome |
| --- | ---: | --- |
| New P175 versioned candidate controls | 8 | PASS |
| Original P133 explicit manual offline launch | 25 | PASS |
| Original WinCred fake-native controls | 20 | PASS — fake-only; no live CredRead/Write/Delete |
| Original P76 wrong-branch refusal | 1 | PASS |
| Real current Tk three-button/no-spawn default UI probe | 1 | PASS |
| Original Phase8.31 no-brain UI import | 1 | Genuine HOLD; retain FAIL/ERROR verbatim |
| Original WinCred fixed secret-consumer allowlist | 1 | Genuine HOLD; unapproved old allowlist is **not** expanded |
| Original P86 two-button assumptions | 2 | Genuine HOLD |
| Original P87 two-button assumption | 1 | Genuine HOLD |

All 60 original and candidate counts are mandatory (55 passing targeted cases plus five historical cases run that must preserve their authentic HOLD disposition). Native tests run with provider/API key environment stripped and a P139 handle-verified disposable random local C: root. Each complete original stdout/stderr, exact test count, named failure, true exit and SHA-256 is archived.

## Distinguish H / C / R

| Category | Source-governed status | Required independent decision |
| --- | --- | --- |
| **H** frozen exact historical tests | P140 genuinely passes at authentic source; old Phase8.31, WinCred and P86/P87 historical modern-branch conflicts remain genuine HOLD | GOV-01 and governed historical-applicability review |
| **C** current candidate | Eight explicit current-source assertions, plus P133, fake WinCred, real isolated Tk UI and P76 original negatives; no production-source changes | GOV-02, SEC-03, SEC-04 must approve/reject scope. Current C never rewrites historical H |
| **R** signed production release | Fail-closed blank signed parent/helper/cert pins, code integrity false, unknown credential runtime, 0/3 full product accepted | REL-05, REL-06, REL-07 and independent release authority |

**Seven review decisions OPEN:** GOV-01 historical test governance; GOV-02 three-button/manual human-presence security; SEC-03 exactly scoped new Windows credential imports; SEC-04 creator-thread AST/docstring design; REL-05 signed parent/helper/installer and SAC/WDAC owner; REL-06 three full authentic Windows regressions; REL-07 privileged C1 G0–G6 P96/P124 concerns. No external qualified GO is fabricated.

**Safety:** no real key, provider validation, native credential effect, privileged service, code-integrity bypass, frozen test rewrite, active product worktree mutation, merge, tag, shipment or false Google Drive release-status update. The original master workbook is updated first and dashboard second **only following a genuinely approved release**. Prior P135 3×600-second full product timeouts remain real.

**P175 release status: IMPLEMENTATION / REVIEW CANDIDATE ONLY — PRODUCTION RELEASE HOLD.**