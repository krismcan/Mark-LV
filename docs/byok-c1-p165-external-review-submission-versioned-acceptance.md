# Nayeon v1 — P165 Independent Review Submission and Versioned Windows Acceptance Contract

**11 November 2026 | OM v2.1 | REVIEW PACKET PREPARED — NOT SENT | PRODUCTION RELEASE HOLD**

## Verified source and purpose

Exact predecessor P164: commit **4c669d68b832f885331f7e63e3d9e18af9d3a7ff**, draft PR #89 unmerged. P165 is a separate branch with exactly three additive-only files: this external reviewer dossier, a source-preserving native Windows dual-version test collector, and a hosted Windows Actions workflow. No changes to product code, frozen original P76/P85 tests, historical source/branch security checks, P139 native Win32 opened-handle policy, P140 signed-companion release gate, WinCred or Kristian's original 17-dirty-path checkout.

The intent is a real independent reviewer submission package, not an assertion that it has been sent or an approval exists.

## Source-bound Windows evidence index

| Checkpoint | Actual run | GitHub artifact | Archive SHA-256 | Proven scope |
| --- | --- | --- | --- | --- |
| P161 | 43087207943 | 13886812899 | 19B490809F819932D32519B014A2F5ECDC84253F1960B8B1D6B644542C5D02C5 | One original Phase8.37 hot test PASS; 2,470 Git calls in 93.892 seconds |
| P162 | 43089354076 | 13887973012 | 93AD0988AB1ED94D5DABD68462CBA23AAD31A3F132AC369CF6C2AF2D19AD226F | 95/95 immutable Git show vs batch byte matches; 9/9 corrupt objects refused; 52.2x narrow benchmark |
| P163 | 43090896372 | 13888034604 | 383E24B67A2BACFC9C0EEC713045897CE3314EEBB2E3386676DDB04E5B269D5B | 25/25 selected original Windows security methods PASS; 16/16 corrupt candidate responses REJECT |
| P164 | 43105642826 | 13894685552 | A4D16B1B789380CD015D3FA02D454AE969B1CF839673E54CA0C0CA590802AF5F | 19/19 original Git fixed-object matches; 7 pre-IPC denies; 2 valid, 9 negative native pipe cases |

Verified original commit SHAs: P161 fe26dc1aeda0422c9aaadee63edae4f2b583fa81; P162 9c2422eb920d8b478520fca7de4bf974bf7c92c6; P163 51ecaa8eaf2e3f092d1006cf2ffba4f402c1de87; P164 4c669d68b832f885331f7e63e3d9e18af9d3a7ff. Original GitHub artifacts expire **25 November 2026**. Download and retain immutable copies before review if needed.

## P165 genuine Windows two-version differential evidence

Run both tests on actual windows-2025 CPython 3.12 after clean exact P164 ancestry, 170 current tracked original Python test modules, exact old security source blobs, genuine P139 handle ownership and no-reparse safe local TEMP.

**Original historical version H:** execute the **entire original ten-method** P76 security test class without changing tests, source, branch seal, mocks, or skips. Its source explicitly requires frozen branch **byok-c1-p80-sealed-historical-fixture-20261106**; on new descendant branches its two historical positive acceptance methods can authentically FAIL. Their genuine native exit, complete unittest footer, failure IDs and raw SHA256 must remain a distinct **HOLD**. Never treat collector green or passing other negatives as an accepted original historical module.

**Reduced current-user safety candidate C:** also execute 25 unchanged original methods selected by P153, covering seven P76 branch/security negatives, eight offline human-consent fake WinCred controls, four source-only launch/environment negatives and six P140 unapproved signed companion no-go controls. This is a versioned subset and is **NOT equivalent** to the original P76 two historical branch positives or the full unfiltered original module.

## Three non-substitutable acceptance dimensions

1. H — immutable historical P76/P85 acceptance applies only to their frozen protected branch and exact source/tag/parent/ref identities. Wrong-branch positive failures on later branches are *authentic historical refusals* and must never be waived, xfailed, relabeled or rewritten.
2. C — a current-branch successor acceptance contract needs explicit new positive-and-negative security tests, source-bound threat analysis and independently qualified approval. P153's 25 selected tests, P162 95 byte matches and P164 19 fixed-object matches do not automatically establish C acceptance. No mutable ref, index, working tree, P76/P85 branch, Code Integrity or WinCred decision may be cached by the immutable reader.
3. R — full production admission demands three completed source-bound **unfiltered native Windows full product** regressions, a real qualified external reviewer verdict on H/C equivalence, exact publisher-signed/pinned main/helper/installer hashes, independently approved Smart App Control/WDAC code-integrity owner policy and all BYOK C1 G0–G6 controls.

P165's 10-item read-only review matrix records every outstanding item and proves that satisfying any *one* alone cannot clear the remaining blockers. It is not a launch authorizer under any hypothetical input.

## Required independent reviewer decision

A named, qualified reviewer, separate from the author, must provide attributable identity, credentials, conflicts, date, exact source commit, SHA-bound reviewed artifacts and a signed GO/NO-GO covering: historic branch/source/negative reachability, immutable Git tree/path/blob SHA1 and SHA256 equivalence, possible collision/TOCTOU, same-user interference and child ownership, Windows partial-pipe/deadlock/abort, source/mutable ref separation, full original module and native full product regression outcomes, P140 signed native main/helper/installer and Code Integrity owner, local user WinCred one-use consent and privileged C1 gates.

**Reviewer identified: NO. Review submitted to external person: NO. Qualified external signed approval: NOT OBTAINED. Current-branch versioned contract approval: NOT OBTAINED. Product signed/pinned release and policy-owner GO: NOT OBTAINED.**

## Unchanged release blockers

P135 native full-product three 600-second attempts TIMEOUT: accepted **0/3**. P150 original BYOK scope 190s TIMEOUT. P159 Phase8.30 original whole module real failures; five whole historical modules TIMEOUT. P161 isolated one Phase8.37 hot method PASS only; not the full original module. Historical P76/P85 positive old-branch tests, P86/P87 old UI, Phase8.31/8.32 AST/source static contracts and WinCred source consumer closure remain unresolved. Privileged BYOK C1 G0–G6 including P96/P124 OPEN.

No real API key, live WinCred, external provider, protected Windows policy change, unapproved release binary on Kristian, GitHub merge/tag/release or original Google Drive MASTER/dashboard update.

**P165 is reviewer packet preparation plus genuine test evidence, not external review or production GO.**
