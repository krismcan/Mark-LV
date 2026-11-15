# P245 — P76 historical/current-source split (candidate only)

**15 November 2026 | OM v2.1 | REAL-KEY NO-GO | PRODUCTION RELEASE HOLD**

## Exact source lineage
- Repository `krismcan/Mark-LV`; parent P244 `da9c436a177b3ec68db0eff2b610180b745bfb2b`.
- Branch `byok-c1-p245-p76-current-source-20261115`; four additive files only; no historical/product source modifications.
- Genuine original P234 Windows failure source `096048db17c7c1f9402dfd16a7deb31e9ebdc81d`.
- All four unchanged historical original failures remain **FAIL** (native exit 1): G0/M1, G0/M2, G1/M3, G6/M3. Do not reclassify as green or edit, skip or xfail original assertions.
- Original P76 `tests/phase8_byok_c1_p76_scope.py` contains an exact historical branch pin `byok-c1-p80-sealed-historical-fixture-20261106`. It rejects modern descendants before subsequent historical source checks. This is a valid security refusal.
- The original Phase10.3 public route still delegates to P76. Its frozen bytes and the BYOK-B and Phase8.34 test modules remain unchanged in this P245 proposal. Do **not** rewrite or override those historical routes.

## Candidate implementation
`scripts/p245_p76_current_source.py` defines a new separately named, read-only **C** (current-descendant) verifier. It:
- Requires a real github-hosted Windows push event for this exact P245 branch and head, exact P244 ancestor, nonshallow full-history SHA-1 repo and raw Git checkout.
- Rejects Git replacement refs/grafts, dirty index, ignored/untracked files and any nonadditive modification.
- Validates full actual Git/disk bytes of all four new diagnostic files and six frozen originals against immutable P233 SHA-256 pins, P244 parent source and current HEAD blobs.
- Preserves the original P76 literal, Phase10.3 annotated raw tag and current before/after Git state.
- Refuses wrong host, branch, event head, parent, source digest, source alias or unapproved path.
- Produces only evidence, explicitly marking all four historical P234 failures **unwaived**. It has no service actor, WinCred operations, keys, provider calls, signed install, credential migration or production admission capability.

`tests/test_p245_p76_current_source.py` supplies local pure negatives and genuine GitHub Windows positive/negative diagnostic tests. Windows workflow uploads raw test transcripts plus SHA-256 and child exit, and exits **3 on candidate PASS** to enforce HOLD. A red expected workflow is not a failed original P76 historical regression and is not product release acceptance.

## Limitations requiring independent decision
The proposed C contract does not by itself make any of the original four methods pass. It shows a way to test modern descendant source integrity without dishonestly calling an isolated P76 historical prototype a current-version gate.

A genuinely independent qualified governance and security reviewer must approve: (1) archival H versus current C inventory versioning and exact replacement-current positive/negative coverage; (2) whether any existing application routing should be migrated after preserving old negative admission; and (3) the full test inventory for three native unfiltered Windows regressions. Until then, preserve all four original FAIL records and 0/3 product regressions.

Separate high-priority production blockers persist: original P96 check-to-effect/revocation race, legacy Python user-scope CredWriteW/CredDeleteW, denial-only CustodyService, SEC-03 Windows service principal/SID/ACL/storage and SEC-04 signed broker/WDAC/IPC/human consent. Qualified approvals remain 0/7. Do not change system policies, install services, enter keys, merge/tag/release, edit Google workbook/dashboard or begin earlier-phase retrospective audit.

## Validation accounting
Local focused native tests, source AST compilation, parent diff, and authenticated hosted Actions logs must be recorded with their actual receipts. Do not infer GitHub acceptance before CI evidence arrives. No Codex execution is claimed merely from this artifact.
