# P187 — Live BYOK-B Workspace, Index and Tamper-Refusal Equivalence

**13 November 2026 — Experimental isolated security audit only — production HOLD**

## Authentication and isolation

Exact P186 parent: 9c6b40ac0e81ac22851b7eb1237b0ec9f06ac3cf. Authenticate the original P186 Windows archive 14017997880 with SHA-256 D3500950814EE39C2B3FF85F4E6BC007AB4275C8EFDBF6DA034C4EB6CD3F3520, each complete 12/12, 12/12, 57/57 historical native log, and original HOLD ledger. P187 adds exactly one audit script, one document, and one Windows workflow. It changes no original product files, frozen tests, P180–P186 source or Kristian's original worktree (HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, 17 pre-existing dirty paths). Use isolated hosted Windows clones only.

## Security contract

The frozen historical B private verifier is _assert_byok_b_historical. The public current assert_byok_b_integrity entry point delegates to Phase 10; P187 neither changes nor bypasses this public production entry point.

Original B live admission includes: actual SHA1 Git format; exact branch, HEAD, protected A ancestry and annotated A tag; whole A parent tree; original sealed A source pins; complete current commit tree; full Git index, stage/mode/flags; staged/unstaged raw delta; untracked and ignored paths; canonicalised sources; all 23 literal B SHA256 pins across 7 new and 16 modified files; frozen untouched historical files/disk; and one of COMPLETE_UNSTAGED, EXACT_STAGED or EXACT_CHILD source topology.

An experimental wrapper invokes the original private full B gate BEFORE and AFTER each bounded P182 batch read, validates original sealed B blob mode/OID/SHA256, refuses changed state or any unexpected gate result, and permanently retires failed sessions. It never reuses cached successful admissions. It is not production integration or atomic transaction proof.

## Coverage matrix

| Security requirement | P187 exercise | Important remaining gap |
|---|---|---|
| Original full historical B verifier | Pre/post calls in original sealed-B synthetic fixture | Does not replace full current Phase 10 gate |
| Genuine Git branch/HEAD/index/disk | Original sealed B verifier run against disposable live Windows A-parent worktree | Isolated fixture, not production |
| Three exact stage/commit states | Native physical positive COMPLETE_UNSTAGED, EXACT_STAGED and EXACT_CHILD | Does not prove concurrency safety |
| Original B source integrity | Original full B gate plus 23 target-specific synthetic disk byte refusal canaries | Synthetic, not 23 physical filesystem edits |
| Physical tamper refusals | Actual Windows byte change, partial index stage, extra untracked source | Further physical ignored/ADS/reparse negatives open |
| Git mode/index/ignored/source aliases | Original full gate synthetic targeted adverse source queries | Windows junction, ADS, race physical coverage open |
| No stale cached admission | Post-read live-admission drift and poisoned next read refusal | Not atomic or lock-free safe against racing writers |
| Git reader failure/timeout | Original P182 bounded-reader native 12-case suite, separately source-bound | Full-product environment and signed Git identity unproved |
| Historical regression | Original P184 12, P185 12, P186 12 executed in exact source branches | P135/P175/P178/P179 historical failures remain unwaived |
| External authorisation | None claimed | Seven GOV/SEC/REL decisions OPEN, G0–G6 OPEN |

Every original negative must fail for the expected original B security reason. An unrelated exception cannot count as a successful tamper refusal. Native log, exit, unittest footer and SHA256 must be separately captured with source identity. Any unexpected timeout or failure is preserved and leaves P187 OPEN.

## Governance

Historical H: HOLD. Current C: ISOLATED EXPERIMENTAL EVIDENCE ONLY. Production R: HOLD. Accepted complete unfiltered Windows full-product regressions: 0/3. Qualified independent security review not obtained. Signing and SAC/WDAC Code Integrity GO absent. No WinCred or real credentials, live provider, privileged service, production source modifications, merges, seals, releases or false Google Drive MASTER/dashboard release updates.

P187 green targeted evidence is not production release eligibility or full equivalent trust. Full live source/index/Win32 race resistance and independent qualified review remain open.
