# P186 — Original historical sealed A11 and B23 envelope witnesses

**13 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1 | PRODUCTION RELEASE HOLD**

## Objective

Extend isolated Git object transport proof from P185's two historical sealed-A source files to **all 11 original BYOK A manifest pins at the sealed A commit**, plus **all 23 original BYOK B manifest pins at the sealed B commit**. Validate every source's original literal SHA256, canonicalised source-self pin where applicable, regular-file Git tree mode, real Git blob OID and full historical bytes. Test **34 individually targeted modified-file responses** with no mutation of any real source or Git tag. Verify annotated A parent tag/tree and linear A→B parent relationship before and after the full envelope.

**This is NOT the original live full BYOK B product integrity verifier.** A positive result is a narrow immutable-historical-source evidence checkpoint and cannot replace the original B live working tree, index, filesystem, ignored-path, security policy, complete older source-era seals, or all frozen tamper negatives.

## Source identity and historical evidence

P186 descends from **exact P185 \`68b338723ba9130be071289c7662c9d68db748f4\`** and creates only three new audit-only paths: \`scripts/p186_windows_full_historical_envelope_witness.py\`, this document, and \`.github/workflows/p186-windows-full-historical-envelope-witness.yml\`. All 171 original tracked \`tests/test_*.py\` modules, entire frozen \`nayeon/\` and \`tests/\` trees, prior P180–P185 scripts, historical seals and Kristian's original dirty product worktree remain untouched.

Historical literal facts (original Git/test sources):
- **Sealed A:** commit \`4110fa69849f8127a325f9a9001284cd1bd3a59c\`, tree \`747f172144794d687251545ca923d5ebb5b1551b\`, parent \`87208af710bac90c440f2e0851854318b22e9b88\`, annotated tag \`nayeon-v1-phase8-byok-first-run-owner-fake-only-01\` with exact tag object \`7496961c83de9607402dcdabff25917674d6688a\`. The original \`tests/phase8_byok_scope_migration.py\` manifest has **11** SHA256 pins and \`_digest\` exact self-canonicalisation.
- **Sealed B:** commit \`e3612279cb972e68e2487702183d5bf5b8f6c4a1\`, tree \`99624a766e864addf5d096bb1a907c85d11401dc\`, parent **exactly the sealed A commit above**. \`tests/phase8_byok_b_scope_migration.py\` has **23** separate immutable original B SHA256 pins and its own \`_digest\` self-canonicalisation. These are the historical sealed B bytes, NOT current P186 source-tree bytes.
- Both A and B historical Git trees use the original Git SHA1 object-format; actual content is independently bound to original frozen SHA256 literals, not merely SHA1 OIDs.

The original [P185 corrected Windows run #43336508403](https://github.com/krismcan/Mark-LV/actions/runs/43336508403), [artifact #13997207555](https://github.com/krismcan/Mark-LV/actions/runs/43336508403/artifacts/13997207555) ZIP SHA256 \`81A985B84CE819AE1254FB01E51051F727C7966E3B64447E2C228FCEEF52AC3C\`, contains original P184 12-case log SHA256 \`9009A6C295D83A425BB4E049C4A5E0A8BEDB6E926B4216DB417F3571BF1BA612\`, original P185 57-case log SHA256 \`6AD2CCB4C31FCC1D37022EECBFBC7D8319DA197C2307C9F1C7596FBB43771669\`, native exits both 0. The original first-failed P185 [run #43335912752](https://github.com/krismcan/Mark-LV/actions/runs/43335912752), evidence artifact #13996119140 remains preserved, NOT erased.

## P186 native Windows evidence scope

1. Independently authenticate original P185 ZIP SHA256, member CRC/inventory, both native original 12+57 logs/exit/full complete unittest footers, exact original P185 source, historical A/B pinned manifest counts, H/C/R release governance. Reject missing evidence.
2. Clone the **original P184 exact branch** at \`a66a5221ab74d0b7f65fd381c554f186cd6c8ed1\`; execute its original unedited 12 branch-bound tests there and capture complete raw Windows log, native exit and SHA256.
3. Clone the **original P185 exact branch** at \`68b338723ba9130be071289c7662c9d68db748f4\`; execute its original unedited 12 branch-bound tests there and capture separate raw Windows log, native exit and SHA256.
4. On exact P186 source, run original P180 8, P181 12, P182 12, P183 12, one untouched frozen BYOK-B source-self canonicalisation control, plus P186 **12 new tests** = **57 native cases**. Combined **12 + 12 + 57 = 81** genuinely native tests **across THREE explicitly separate source identities**, NOT a fabricated single 81-case suite. All tests must have full original Python unittest footers and native exit zero.
5. P186 new tests fetch full real original Git bytes from all **11 A pins** and **23 B pins** and pass each through the bounded P182 \`git cat-file --batch\` reader, validate original A/B distinct SHA256 self-canonicalisation and real \`git ls-tree -z\` ordinary blob identity, and compare to independent \`git show\` raw bytes. Test **34 targeted tamper refusals** using each original real blob plus a synthetic modification, and reject forged tag/tree/linear parent/HEAD, wrong Git blob OID, cross-epoch paths and aliases. Original history and filesystem are **never** changed.
6. Re-run current original tagged-ancestry observation after envelope. No approved source, bytes or policy decision is reused between source identity test executions. **Important limitation**: P186 observes historical tag/ancestry before and after the *whole immutable envelope*, not atomically per source against concurrent Git repository writers; it proves historical pinned object parity, not production per-request Win32 race/ref trust.

## Original security limitations and release decision

P186 does NOT call or replace \`tests/phase8_byok_b_scope_migration.py\`'s complete live source admission (\`_index_flags\`, \`_canonical_paths\`, \`_disk\`, \`_raw_delta\`, all ancestor and staged/unstaged cases). It also does not prove the full older 8.30–8.37 historical source-era chain, signed Git executable identity, Windows atomic reparse-resistant file handles, any privileged service identity, new C1 WinCred or real provider action. **No full-product performance gain or historic negative test recovery is inferred.**

Original P135 3×600s full-product timeouts, P175 historical failing cases, P178 original B-module 165s timeout/two genuine FAILs, and P179 original historical pin-witness timeout all remain genuine and unwaived. Seven qualified external decisions GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 **OPEN**. Accepted complete unfiltered Windows full-product regression passes **0/3**, G0–G6 privileged C1 OPEN, signed main/helper/installer/cert and SAC/WDAC policy release approval absent.

**Release state: IMPLEMENTATION IN PROGRESS — PRODUCTION RELEASE HOLD.** No real keys, WinCred effects, provider calls, privileged service, original source modifications, legacy test waivers, merge/tag/release/install or false Google Drive MASTER/dashboard production-state synchronisation. An independent qualified security review is still required before any real historical verifier integration.
