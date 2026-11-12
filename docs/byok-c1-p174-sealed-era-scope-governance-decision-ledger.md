# BYOK C1 P174 — Sealed-era P140 regression recovery and current-version scope governance

**12 November 2026 | OM v2.1 | Source-bound audit, not a release | PRODUCTION RELEASE HOLD**

## Source-custody inputs (independently confirm in native Windows evidence)
- P173 starting commit: `b04af8858dbaab6d164352832c6757db0ec1681c` (PR #98 draft/unmerged).
- Historical P139 immutable parent: `052cf4f076d5f2c6e170593cab473d0c8eab7c3a`.
- Verified historical P140 branch HEAD: `9c47bac3308822e11300381017b30e913ffbc211` (`byok-c1-p140-frozen-signed-companion-gate-20261110`).
- P140 six source changes, using original unmodified `tests/test_p140_scope_migration.py`:
  1. `.github/workflows/p140-windows-frozen-signed-companion-gate.yml` — added
  2. `docs/byok-c1-p140-signed-frozen-companion-release-review.md` — added
  3. `nayeon/desktop_alpha/frozen_signed_byok_companion.py` — added
  4. `nayeon/desktop_alpha/local_byok_launch_bridge.py` — sole modified old source
  5. `tests/test_p140_frozen_signed_companion.py` — added
  6. `tests/test_p140_scope_migration.py` — added

GitHub compare of P139→P140 authenticated exactly these six paths prior to the P174 collector. Original P140 test blobs match P173. The authentic six-test P140-era Windows outcome is a **hypothesis until a real runner attests it**; never pre-label as PASS.

## Evidence protocol
- A new isolated P174 branch contains only this document, a source-bound Windows evidence script, and a Windows Actions workflow. The parent P173 `nayeon/` and `tests/` subtrees must be bit-identical.
- A real Windows Server 2025 runner clones exact P174 source and prepares two **detached** immutable source-era Git worktrees: historical P140 and P173. Each executes both entire original `tests.test_p140_scope_migration` (six) and `tests.test_p140_frozen_signed_companion` (24) with Python 3.12.
- Capture genuine per-module stdout, stderr, combined original output, original count, native exit, named FAIL/ERROR, execution time and raw SHA-256. Each run is always reported individually, even on original failure or timeout.
- Enforce verified Git ancestry; approved six-path P139→P140 diff; byte-identical immutable original tests; P173/P174 production and original test subtree equality; clean worktrees; P139 native Win32 handle-checked fresh local C:\ root. All original credential tests remain unchanged. Never run a live credential or signed executable.
- Actual evidence artifacts are the Windows runner's `p174_historical_current_scope_governance_ledger.json` and full native logs. Successful collection does **not** establish historical acceptance, current acceptance or release GO.

## Distinct acceptance contracts

| Category | Immutable/variable rule | Provenance and decision |
| --- | --- | --- |
| H — historical P140 exact source-scope | P139 parent; **exact six changed paths**; original `P140FrozenSignedLaunchMigration` must be run at P140 commit for historical assessment | Original historical test **unmodified**; outcome populated from genuine Windows log. A later P173 failure remains separately authentic, never waived. |
| H — original signed-companion negatives | All 24 mock/negative P140 controls, fail-closed blank pins and Code Integrity release false | Original complete 24-case module on each exact source; mock results do not sign or authorise a real EXE. |
| C — current descendant versioned source-shape | A future separately written, explicitly versioned test may assert approved *current* scope and complete source provenance | No retroactive change to P140's six-path test; independent historical test-governance authority must review replacement applicability. |
| C — Connection three-button contract | P133 offline setup adds third explicit user-click action; original P86/P87 two-button tests still FAIL on modern UI | New current-version tests may supplement; old results remain HOLD until qualified decisions. |
| C — Phase8.31/P86 import closure | Old `workspace_window.py` no-brain import vs later required P86 `pending_custody_status_view` import cannot both match | GOV-01 must adjudicate contract version; no disguised import or blanket exception. |
| C — three WinCred consumers | Three exact later user-scoped import edges; original immutable fixed consumer allowlist rejects them | SEC-03 approval required; preserve all rogue-import negative controls and old results. |
| C — Phase8.32 creator-thread guards | P171 scratch-only first-AST guard preserves refusals; docstring restoration uses import-time mutation | SEC-04 must review; do not adopt automatically in product. |
| Permanent negative security gates | P76/P85 wrong branch, P139 native path identity/no reparse, signed parent/helper, human consent, immutable release pins | Must never be weakened even by versioned test replacements. |
| R — production release | Approved signed parent/helper/installer; verified Authenticode, owner-approved SAC/WDAC image-load policy; 3 completed full Windows regressions; G0–G6 | **HOLD** until qualified independent approval and real evidence. |

## Required seven independent decisions — all remain OPEN

- **GOV-01** Historical test governance: Phase8.31 versus P86 import conflict and applicability of frozen P140 six-path test on later descendants.
- **GOV-02** Current UI/human presence: P133 three-button explicit click and original P86/P87 two-button conflict.
- **SEC-03** Credential import trust boundaries: exactly three added scoped consumer imports; native backend denial retained.
- **SEC-04** Python/Tk security: scratch-only first-AST creator guard and exact docstring restoration with import-time assignments.
- **REL-05** Windows signer and policy owner: signed main/helper/installer SHA/cert pins, protected install, code integrity at image load.
- **REL-06** QA/release owner: three complete unfiltered full-product Windows native regressions (0/3 accepted).
- **REL-07** Privileged service security owner: BYOK C1 G0–G6, including P96 race and P124 pipe-writer provenance.

No internal packet, GitHub runner success or self-review is qualified independent GO.

## Explicit release HOLD
Historical P140 release pins are empty; `_APPROVED_CODE_INTEGRITY_RELEASE=False`, `_release_pins_issued()=False` and approved frozen launcher unavailable. No signer image, approved policy owner, full regression triad or privileged service admission. Original P135 three native 600-second timeouts remain. No real user key, `CredRead`/`CredWrite`/`CredDelete`, provider validation, privileged service, merge, tag, installer shipment or false master-workbook release update. MASTER before dashboard **only** after a genuinely authorised release.
