# Nayeon v1 — BYOK C1 P177: Qualified Independent Review Evidence Consolidation

**12 November 2026 | Operating Model v2.1 | READ-ONLY EVIDENCE | H/C/R release posture: HOLD**

## Purpose and boundary

P177 is a **reviewer-intake packet**, not a completed independent review, a historical test waiver, a production admission or any real BYOK deployment. It prepares individually reviewable, source-bound evidence and seven unresolved questions for actual independently qualified security / engineering owners.

P177 starts from P176 commit \`ea77c8115c68520a08d3f259f994354cfa1d0601\`, draft PR #101. The new branch may add **only three evidence paths**: this document, \`scripts/p177_windows_qualified_review_evidence_packet.py\` and \`.github/workflows/p177-windows-qualified-review-evidence.yml\`. No changes to any \`nayeon/\` product module, any original \`tests/\` module, original historical test expectations or Kristian's dirty product worktree.

## Archived genuine Windows evidence to independently authenticate

| Original native evidence | Exact source/run | Immutable GitHub artifact and ZIP SHA-256 | Source-custody / test result |
| --- | --- | --- | --- |
| **P174** historical P140 vs current P173 original test modules | P174 \`98437f4c4e8a09b507bc998a2829bafcc430f8a7\`, [Actions run 43248455614](https://github.com/krismcan/Mark-LV/actions/runs/43248455614) | [Artifact 13957432345](https://github.com/krismcan/Mark-LV/actions/runs/43248455614/artifacts/13957432345) \`D91607E9076A488F32023D257F106F0FB70A4AC5D408B38A870AC68F6E1A2853\` | P140 six original historical scope tests **6/6 PASS**, P140 signed companion 24/24 PASS; P173 unchanged six-case scope test **5 PASS / 1 FAIL**; P173 signed companion 24/24 PASS |
| **P175** current user-scope diagnostic, old negatives | P175 \`381abcf4976dd01736bb542533c837e9afa66a56\`, [Actions run 43250880376](https://github.com/krismcan/Mark-LV/actions/runs/43250880376) | [Artifact 13959541839](https://github.com/krismcan/Mark-LV/actions/runs/43250880376/artifacts/13959541839) \`14D1D41E81E9CD1466C2D58244AE55B2C1C54A64D52BF398D79B381202D569BD\` | Genuine Windows: 55/55 targeted current-compatible cases PASS; original Phase8.31, WinCred allowlist, P86/P87 **5 historical failing tests** and 6 named FAIL/ERROR log records unwaived |
| **P176** current-source adversarial negative contract | P176 \`ea77c8115c68520a08d3f259f994354cfa1d0601\`, [Actions run 43253203624](https://github.com/krismcan/Mark-LV/actions/runs/43253203624) | [Artifact 13959548133](https://github.com/krismcan/Mark-LV/actions/runs/43253203624/artifacts/13959548133) \`A8E0F8B030C5B8579CAB97A5EA2D6B3C64C74C4E5EA49D5C35D539179C983D7B\` | **11/11 genuine Windows PASS** in a separate new versioned candidate; native import-edge mutation refusals and frozen signed gate still cannot be approved through environment changes |

Three artifacts are currently scheduled to expire approximately **26 November 2026**. Keep original ZIPs, source commits and SHA-256 externally preserved before expiry when qualified reviewers need a longer retention window.

The P177 Windows runner reads those exact three artifacts via short-lived read-only Actions access, verifies ZIP SHA and CRC, checks every original native count, exit status, complete raw log digest, named historical failures and source-custody ledger. It then writes a fourth archive: the prepared P177 reviewer packet JSON plus a new complete nine-case genuine Windows review-contract log. All tests are focused native security diagnostics, **not full-product regressions**.

## Independent decision register — all seven are OPEN

| ID | Required independent owner | Precisely required decision / outcome |
| --- | --- | --- |
| **GOV-01** | Historical test-governance and source-era owner | Decide original P140 six-path scope test source-era applicability on later descendants, and Phase8.31 forbids-brain UI imports vs P86 requires them. Document both original failures; never edit original tests to turn them green. |
| **GOV-02** | UI security and human-presence owner | Sign off or reject P133 explicit offline three-button Connection interface relative to three original P86/P87 two-button failing tests. Verify only explicit human click can open offline setup; no startup credential operation. |
| **SEC-03** | Secret dataflow / Windows Credential Manager security owner | Accept/reject **exactly three** later user-scoped import edges; preserve original WinCred historical allowlist and rogue-native import negative tests. Review P175 fake-native 20/20 and P176 adversarial 11/11. |
| **SEC-04** | Python/Tk lifecycle and import-time security owner | Review P171 scratch-only creator-thread first-AST guard, docstring preservation and real Windows worker-thread refusals. The P171 prior evidence is **referenced but not directly reauthenticated in P177**. No product patch until signoff. |
| **REL-05** | Windows software-signing and Code Integrity policy owner | Issue reviewed signed main/helper/installer, immutable cert and SHA pins, verified Authenticode, protected installed path, independently attested SAC/WDAC at actual image-load. Currently all real P140 signed pins are empty and Code Integrity release flag false. |
| **REL-06** | Independent native full-product Windows QA/release owner | Resolve three original P135 600-second full-suite timeouts and furnish three complete source-matched, unfiltered Windows regressions with genuine exit/log SHA receipts. **Accepted: 0/3.** |
| **REL-07** | Privileged BYOK C1 security owner | Close G0–G6, including P96 race and P124 named-pipe writer identity/provenance. Current local-user offline slice is not a privileged service and provides no GO for real key operations. |

For each decision the eventual outside reviewer must provide **(1)** name/authority, **(2)** approved/rejected scope and version, **(3)** specific evidence IDs, **(4)** findings and mitigations, **(5)** dated attested signoff. P177 contains **no reviewer identities or fabricated approvals**; all seven status fields remain \`OPEN\`.

## Strict safety and next authority

- Do not reduce a historical H failure count, overwrite original \`tests/\`, mutate original source, bypass P76/P85/P139 negatives or infer release success from a green GitHub collector.
- Do not enter or test a real BYOK API key, contact provider networks, use live WinCred effects, launch protected signed executables, issue signer pins, enable privileged G0–G6, or merge/release on behalf of an absent security owner.
- Three new audit-only files and a draft PR are not an authorised production implementation.
- Original Kristian worktree \`D:\Nayeon\BYOK_C1_PRODUCT_20261028\` is not the audit worktree; preserve existing 17 dirty paths and its exact current HEAD.
- No Google Drive MASTER/dashboard claim of a release. When genuinely approved and issued, update Google Drive **MASTER first, then dashboard**.

**Disposition:** P177 source-bound reviewer evidence preparation is eligible to close as a diagnostic checkpoint *only if* the authenticated Windows workflow and 9/9 reviewer-contract cases truly complete. Otherwise P177 evidence remains HOLD. In all cases H/C/R production release remains **HOLD**, seven independent qualified security decisions **OPEN**, full-product Windows regressions **0/3**.