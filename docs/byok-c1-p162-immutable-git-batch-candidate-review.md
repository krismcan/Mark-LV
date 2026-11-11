# Nayeon v1 / Mark-LII — P162 immutable Git batch-read performance candidate

**11 November 2026 | OM v2.1 | ISOLATED ADDITIVE EXPERIMENT | PRODUCTION RELEASE HOLD**

## Exact source custody and observed bottleneck

P162 begins from authoritative P161 Git commit **fe26dc1aeda0422c9aaadee63edae4f2b583fa81**, open draft/unmerged PR #86. P161's genuine hosted Windows-2025 Python 3.12 run **43087207943** invoked the original immutable Phase8.37 method and produced **native exit 0, Ran 1 test, OK**, in **95.75 seconds**. Its per-Git-call evidence traced **2,470 actual completed Git subprocesses** consuming **93.892 seconds**, 1,292 of them \`git show\` consuming 49.698 seconds. The original test's 19 tamper-negative iterations all passed. The evidence is archived as GitHub artifact 13886812899, immutable ZIP SHA-256 19B490809F819932D32519B014A2F5ECDC84253F1960B8B1D6B644542C5D02C5.

The underlying issue is repeated Windows Git process startup and exact historical read/validation work, not an individual indefinitely hung subprocess. Historical source, Git trust, and adversarial assertions cannot be modified or memoized merely to obtain faster test results.

## P162 candidate: immutable object protocol, no integration

This checkpoint isolates and benchmarks **only fixed-commit, immutable Git blob reads**, not any mutable security decision. It creates precisely three additive files on a new isolated branch: the evaluation script, a hosted Windows workflow, and this review packet. **No production source, historical test, P76/P85 exact branch seal, P139 real Win32 opened-handle verifier, P140 unapproved signed binary gate, current-user WinCred source, installer or security-control mutation.** Kristian's existing original 17 dirty paths remain untouched.

P162's disposable genuine GitHub-hosted Windows-2025 Python 3.12 runner must establish exact P161 base ancestry, clean Git checkout, original test inventory (170 tracked Python test files), and byte identity of nine original test/security modules. The new evaluation then:

1. Imports the existing read-only Phase8.37 source and obtains its **exact frozen original 8.36 SHA** and the exact **19 independently pinned historical source paths and SHA-256 values**. The specific protected commit is \`a12565b9be070684e1d7d801ded4833d13121f94\`.
2. Reads the authentic Git object tree at that **literal immutable commit OID**, resolving exactly those 19 source blobs and rejecting malformed, non-regular, missing or duplicate pinned entries. No branch name, ref, tag, working tree or index is accepted as a read authority.
3. Runs **95 real original \`git show <fixed-commit>:<pinned-path>\` processes**, five full rounds of 19 each. Revalidates each original returned byte string against the real Git blob OID and the existing historical SHA-256 pin reader (\`scope.prior._digest\`), including the existing self-pin normalization, without altering source.
4. Separately issues **95 fresh actual Git object requests** through one \`git cat-file --batch\` child using only those previously authenticated fixed object IDs. Every reply must contain an exact matching object ID, type \`blob\`, bounded exact length, unmodified bytes and delimiter; independently recompute the real Git SHA-1 blob object identity and the historical **SHA-256 pin**. Every candidate result must match the original \`git show\` bytes and SHA256 exactly. The candidate performs no source pin caching or Git trust/admission calls.
5. Execute at least nine strictly in-memory adversarial candidate-reader refusals: changed object OID, object type, tampered bytes, malicious length, truncated content, corrupted delimiter, unknown file, wrong expected OID and bad header. No original test is patched and no security check skipped.
6. Capture genuine Windows cumulative wall times, exact byte-comparison count, per-path original byte hashes, original Git tree hash, adversarial refusal counts and source-bound JSON evidence. A fast candidate is not automatically accepted: every mismatch or unexpected acceptance **fails** the audit.

**Critical boundary:** the prototype is not wired into any existing original security test or production control. The original security code exercises branch, commit, tag, index, worktree, path alias, parent and proof-of-reach guards. An immutable object read optimisation cannot replace those mutable-state and adversarial checks. No actual release-regression run is claimed. A future test-harness acceleration would require an independent qualified reviewer, separate source-preserving equivalence proof across real adverse inputs, and original unfiltered test results. No unreviewed fallback to the candidate is allowed.

## Remaining admission blockers

P135 all 3 genuine complete-product Windows discovery attempts timed out after 600 seconds with 1,637 PASS / 37 FAIL / 7 ERROR before completion. Accepted full-product genuine Windows triad is **0/3**. P150 original BYOK scope 190-second timeout, P159 original Phase8.30 completed failed and five original full modules timed out, frozen exact P76/P85 positive-branch assertions, P86/P87 older UI contract, Phase8.31/8.32 old static source-closure and WinCred consumer allowlist remain unresolved. Independent named security and historical test-governance GO not obtained; actual signed/pinned production main, helper, installer and Code Integrity policy-owner approval absent. Privileged C1 G0–G6 including P96/P124 are OPEN.

No real API keys, production WinCred effects, external provider verification, protected OS policy changes, unapproved signed/unsigned executable launch on Kristian, GitHub merge/tag/release or original Google Drive MASTER release workbook/dashboard update.

**P162 is isolated performance research only. Production: RELEASE HOLD.**