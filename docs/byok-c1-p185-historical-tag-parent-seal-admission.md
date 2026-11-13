# P185 — Historical annotated tag, parent-tree and sealed-source admission

**13 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1 | PRODUCTION RELEASE HOLD**

## Grounded source and original historical baseline

P185 is based on verified P184 HEAD \`a66a5221ab74d0b7f65fd381c554f186cd6c8ed1\` (draft PR #109, unmerged). Reauthenticate [P184 genuine Windows run #43325646435](https://github.com/krismcan/Mark-LV/actions/runs/43325646435), [artifact #13991643573](https://github.com/krismcan/Mark-LV/actions/runs/43325646435/artifacts/13991643573), ZIP SHA256 \`98F49A33B184E1FE67F4FA99EEE2B14814DDD515219E2312E441A0197640BECD\`, raw complete 57-case native Windows log SHA256 \`1E3785DB99F365B37FAE5DAD7E5E03C31F99E39A0447A57B2CDA8265C3BE4E8C\`, real exit 0, qualified decisions OPEN and production HOLD.

P184's source-admission prototype freshly observed exact current HEAD, branch, Git index, tree mode, disk SHA256 and reparse paths around two narrow read-only current historical source reads. P184 did **not** prove original tagged ancestry or the full historical 23-file B security envelope. P185 tests a separate, narrower **historical A-parent blob** cryptographic-seal contract; it is not a production verifier patch and not a substitute for full original historical source admission.

Only **three new review-only paths**: \`scripts/p185_windows_historical_tag_parent_seal_admission.py\`, this document, and \`.github/workflows/p185-windows-historical-tag-parent-seal-admission.yml\`. The entire original \`nayeon/\` and \`tests/\`, all original P180–P184 scripts, original signed launcher/CI/source signatures and dirty product worktree on Kristian must remain untouched. All 171 tracked original \`tests/test_*.py\` modules remain in their original state.

## Immutable historical parent identity

Read-only values from original frozen \`tests/phase8_byok_b_scope_migration.py\`:

| Source-of-trust property | Exact pinned value |
|---|---|
| Historical B parent (sealed A commit) | \`4110fa69849f8127a325f9a9001284cd1bd3a59c\` |
| Historical parent tree | \`747f172144794d687251545ca923d5ebb5b1551b\` |
| Historical parent of sealed A | \`87208af710bac90c440f2e0851854318b22e9b88\` |
| Annotated A tag | \`nayeon-v1-phase8-byok-first-run-owner-fake-only-01\` |
| Exact annotated tag Git object | \`7496961c83de9607402dcdabff25917674d6688a\` |

The immutable original A SHA256 manifest in \`tests/phase8_byok_scope_migration.py\` establishes these *historical A commit* blob pins, distinct from current branch disk bytes:

- \`tests/phase_8_30_scope_migration.py\` SHA256 \`23d5b1a0a9e4f83ffd870f6b72693bb8878c85f94d8d7c142ca2a57fa0aeb218\`.
- \`tests/phase_8_37_scope_migration.py\` SHA256 \`79cbfffb932aea28321f017b76d26185774747a3d30cc0a7455530b6d01188cd\`.

## P185 narrow experimental contract

The new isolated \`TaggedParentSealedRead\` uses an expected 40-hex current audit HEAD, refuses every non-allowlisted source path, and executes a **fresh complete historical snapshot before and after each single read**. Each snapshot collects genuine Git:

- exact current audit HEAD/branch/root and SHA1 object format;
- annotated tag ref OID \`git show-ref --verify --hash\`, type \`tag\`, and exact Git tag object peeling back to pinned sealed-A commit;
- historical commit type \`commit\`, original \`^{tree}\` tree ID and **exact single-parent** \`rev-list --parents -n 1\`;
- exact \`100644 blob OID\` for canonical historical source path in the original sealed A parent-tree, from \`git ls-tree --full-tree -z\`.

A separate P182 bounded \`git cat-file --batch\` read obtains the full original historical blob for the exact observed OID. Every response is verified by Git object SHA1, followed by immutable original frozen A SHA256; the live observations are then re-executed and both signed-off-by-nobody snapshots must be strictly equal. Any pre/post tag, parent-tree, ancestry, path, object-ID, Git mode, current HEAD/branch or source-hash drift **fails closed** and retires the Git child. No cached security approval, no source edits and no access to real credentials or privileged service.

### Actual source-preserving Windows tests

Authenticate exact P184 source parent, 57/57 original Windows log ZIP SHA256/member CRC, original ledger and seven OPEN independent decisions. Execute original P180 **8**, P181 **12**, P182 **12**, P183 **12**, P184 **12**, one untouched frozen BYOK-B self-canonicalisation case **1**, plus P185 **12** new synthetically mutated tag/tree/ancestry/type/mode/blob/parent and full payload cases = **69 genuine native Windows cases**.

The P185 originals include real Git metadata/tag-tree verification on the exact historical commit and two separate immutable original A-source bounded Git byte reads. The synthetic mutation cases are **not** real history modifications: their purpose is to assert refusal without touching source.

A 69/69 passing narrow result is evidence that the **two-blob historical tagged-parent contract** behaves as specified, **not** evidence that the full original BYOK B 23-file historical integrity verifier, all A/8.30–8.37 seals or security-negative tests now pass. No original security test can be replaced or mocked to achieve a passing suite.

## Remaining independent review and release gates

The original untouched B historical verifier also evaluates the entire original 23-file sealed B envelope, all prior phase tags/ancestry, exact Git staged/unstaged/commit tree/disk reparse/racing-parent identities and historic pinned 11 A files — much wider than P185's two A historical blob checks. Original P135 three 600-second full-product regressions timed out, P175 old historical FAIL cases remain, P178 whole original BYOK B module timed out with two FAILs, and P179 original pin witness timed out. No historical failure is waived.

GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06 and REL-07 qualified independent decisions all **OPEN**, full-product native Windows accepted complete passes **0/3**, privileged C1 G0–G6 OPEN, signed Windows main/helper/installer/certificate SAC/WDAC GO absent. No qualified external security reviewer has signed, no production integration, no real API key/WinCred/provider call, no merge/tag/install/release or false Google Drive MASTER/dashboard status change.

**P185 can be completed only as a narrow source-bound read-only experimental tagged-parent proof; all security and production admission remain HOLD.**
