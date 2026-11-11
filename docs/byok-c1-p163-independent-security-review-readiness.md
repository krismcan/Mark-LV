# Nayeon v1 — P163 Independent Security Review Readiness and Immutable Git Integration Boundary

**11 November 2026 | OM v2.1 | DRAFT evidence for qualified independent review | PRODUCTION RELEASE HOLD**

## Source and provenance
P163 begins at exact P162 SHA 9c2422eb920d8b478520fca7de4bf974bf7c92c6 (draft PR #87, unmerged). P162 hosted Windows run 43089354076 genuinely demonstrated 95/95 matching original immutable Git show vs persistent cat-file --batch object bytes, 9/9 candidate corrupt-response negatives rejected, and a ~52.2x speed ratio in that narrow microbenchmark. An earlier P162 source run correctly failed on partial Windows pipe reads; the final run passed only after a bounded read-loop fix. These measurements do NOT prove complete suite acceleration or production security admission.

P163 changes only three additive paths: this security-review request, a source-preserving test/evidence runner, and a hosted Windows workflow. Historical product files, original tests, P76/P85 branch seals, P139 native handle policy, P140 frozen signed-companion refusal, current-user Credential Manager and all existing Git source objects remain byte-identical to P162. Kristian's original dirty product worktree remains off limits.

## Integration threat boundary: immutable object data versus mutable trust state

A persistent Git cat-file --batch reader may retrieve **only a literal content-addressed immutable Git blob object** after an *independently verified* original protected commit/tree/path proof. Every reply must verify exact object OID, type blob, trusted size bound, complete framing and delimiter, recomputed Git SHA1 blob identity and original path-specific normalized SHA-256 pin. No caching of changing trust decisions is allowed.

Never use this performance experiment to skip or change:
- Current HEAD, protected Git branch, annotated refs/tags, commit ancestry, tree/ref reach, original P76 or P85 exact branch negative controls
- Git index, staging flags, worktree content, untracked/ignored files, path aliases/case/ADS/reparse links
- Original test source, historical expected failures, signed main/helper/installer pins, SAC/WDAC policy-owner approval, real WinCred effects, external provider or any privileged Windows operation

The prototype is NOT imported into product or original tests. A future implementation cannot automatically replace independent branch-aware provenance or run on an untrusted mutable ref simply because 95 immutable-object reads matched.

## P163 genuine Windows review-readiness evidence

Exact hosted Windows-2025 Python 3.12 and P162 parent. Reject any source drift or candidate integration into product/tests; enforce 170 tracked unittest file inventory, current P76 BRANCH exact historical P80 prototype and P140 signed main/helper/signer SHA empty plus Code Integrity release owner FALSE. Use unchanged P139 Win32 opened-handle fixed local C: temp ownership guard.

Execute **25 unchanged original security test methods** on real Windows, selected from the original P153 source-bound independent-review candidate. These cover seven original P76 negative branch/ref/source controls, eight offline current-user fake Credential Manager human consent controls, four explicit manual launch/secret environment controls and six frozen companion signed/Code Integrity NO-GO controls. Validate each class and method against actual original Python AST. Do not run the two historical positive P76 old-branch tests in the current-branch candidate and do not claim them waived; their earlier actual FAIL/HOLD remains.

Independently read a real pinned historical 8.36 Git blob and prove its original path-specific SHA. Against the nonintegrated P162 candidate object verifier, rerun nine old synthetic wrong-blob cases plus seven additional synthetic cases: wrong expected historical SHA-256 pin; source path casefold alias; backslash alias; embedded NUL in Git header; forged empty object framing; trailing injected bytes; modified content with original SHA1. **All sixteen** must be rejected. No original Git refs/index/worktree/test source mutations or genuine API keys.

Archive exact native exit, genuine original unittest footer and FAIL/ERROR identities, original raw stdout/stderr SHA256 and size, exact reviewer source-custody SHA256 and count of candidate negatives. A green *collector* denotes actual recorded positive/negative evidence, NEVER unfiltered original historical PASS, security release GO or qualified independent reviewer approval.

## External reviewer decisions must remain unfilled

A real, named, qualified independent reviewer — not the assistant who created this work — must supply attributable date, qualification, remit and conflict declaration, and decide the following:

1. Does each immutable fixed-OID read retain raw original Git and pinned SHA256 identity, while mutable ref/tag/branch/index/worktree negative checks still execute without caching or short circuits?
2. Are malformed batch protocol, Windows pipe partial reads, excessive length, object substitution, forged tree/path, alias, same-user child process, handle lifecycle, crash uncertainty and binary/secret leakage sufficiently addressed?
3. Are original P76/P85 historical positive failures correctly governed by the original branch lineage and an independently reviewed versioned current-branch positive and negative acceptance suite, without editing original tests?
4. Can an eventual test-harness implementation demonstrate actual unmodified negative controls and complete native Windows product regression across a source-bound inventory, rather than a green subset?
5. Are signed exact main/helper/installer bytes, protected update paths and publisher pinned hashes, owner-approved Smart App Control/WDAC load enforcement, TOCTOU and reduced current-user WinCred one-use consent actually demonstrated?

External reviewer identity, signed decision, Windows security reviewer GO, original test-contract migration, Code Integrity policy-owner GO and exact signed executable pins are **NOT OBTAINED**. No assistant output is independent approval of its own design.

## Historical failures and release hold

P135 three full Windows product discoveries each timed out after 600s: **0/3 accepted unfiltered passes**. P150 original BYOK scope 190s timeout; P159 original Phase8.30 full module completed with 21 tests and 23 failure records while five original full modules remain timed out. P160 4/5 focused PASS and P161 genuinely resolved the single Phase8.37 hot case at 95.75s; these do not clear unfiltered modules. Original P76/P85 exact branch positive HOLD, P86/P87 UI button-count assertions, Phase8.31/8.32 static contracts and WinCred consumer allowlist failures remain. Privileged BYOK C1 G0–G6 including P96/P124 OPEN. No genuine user keys, production WinCred, provider validation, unsigned or unpinned native executable on Kristian, GitHub merge/tag/release or original Google Drive MASTER/dashboard release update.

**P163 = independent-review readiness, NOT a completed external review. Candidate integration NO-GO. Production release HOLD.**
