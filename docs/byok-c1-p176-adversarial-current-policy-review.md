# BYOK C1 P176 — Adversarial current-policy candidate and independent-review evidence

**12 November 2026 — OM v2.1 — isolated diagnostic only; H = HOLD / C = scoped candidate / R = production HOLD**

## Provenance
Direct source parent: verified P175 `381abcf4976dd01736bb542533c837e9afa66a56`, PR #100 (DRAFT/UNMERGED). Exactly three additive P176 files: this document, new dedicated Windows mutation-negative evidence script and new Windows Actions workflow. Entire original `nayeon/` and `tests/` must remain byte-identical. The original Kristian product worktree and its pre-existing 17 changes are out of scope.

P175 genuine Windows Server 2025 / Python 3.12 [run #43250880376](https://github.com/krismcan/Mark-LV/actions/runs/43250880376), original artifact #13959541839, ZIP SHA-256 `14D1D41E81E9CD1466C2D58244AE55B2C1C54A64D52BF398D79B381202D569BD`. P176 must reauthenticate that exact archived ZIP plus all nine complete original native logs and original failures, without reclassifying them.

## New separate *adversarial* current-version security candidate

P175's eight current-version controls established a narrow baseline; P176 now tests an exact source-contract predicate against realistic **in-memory AST mutations**, using current product Python source read into a disposable dictionary without writing files. These are *candidate* acceptance tests, not production security controls or evidence of an approved signer.

1. Exact source-wide current credential import predicate admits the real current source only.
2. Removing any of the three exactly approved user-scoped secret import edges is refused.
3. Injecting direct WinCred backend access into local Tk UI is refused.
4. Adding a rogue new helper with direct WinCred access is refused.
5. Duplicating an approved import edge is refused rather than silently deduplicated.
6. Replacing the local UI's narrow `SecretValue` import with a wildcard is refused.
7. Replacing `SecretValue` with an unauthorised secret symbol is refused.
8. Importing `requests`, `socket`, `openai` or `winreg` in the local controller is refused.
9. Importing a provider validator from the local UI is refused.
10. Adding a new unauthorised native backend import through Python's plain `import` form is refused.
11. The actual production P140 frozen launch gate remains fail-closed even when synthetic user-process environment keys *pretend* to contain signed release hashes/Code Integrity approval.

P176 does not modify `CURRENT_CONSUMERS`, `HISTORICAL_ALLOWED`, old WinCred allowed consumers, real source, original P76/P85, P140 pin constants or original security test assertions. Tests never execute a real WinCred call, provider request, signed binary, installer or privileged service. An actual human reviewer must approve any future current-version gate revision; passing Python self-tests alone is not production admission.

## Native evidence protocol
- GitHub hosted Windows Server 2025, Python 3.12, exact triggering push SHA, P175 commit ancestry and only three added evidence paths.
- Reauthenticate prior P175 10-member ZIP: nine untouched original logs + JSON; original counts, exit codes, named FAIL/ERROR and SHA-256 including five historical failing cases.
- Execute the **complete new original eleven-case P176 versioned module** in a fresh Windows native unittest process; no manual count curation, preserve complete log and true exit. Use P139 verified local fixed-drive, OS-handle-inspected random fixture root; no reparse traversal.
- Archive full raw Windows stdout/stderr, SHA-256 and machine-readable independent-review ledger. If evidence is missing, altered, or any candidate unexpectedly passes a rogue injection, fail closed and retain HOLD.
- Successfully collecting all diagnostics is not qualified external security approval.

## Seven independent decisions still OPEN
- GOV-01 historical Phase8.31/P86 contract contradiction and source-era applicability
- GOV-02 P133 exact three-button explicit human click vs older P86/P87 assumptions
- SEC-03 exact three current user-scoped WinCred import edges and negative import restrictions
- SEC-04 import-time creator-thread AST guards/docstring preservation design
- REL-05 approved signed main/helper/installer, publisher/cert SHA and Windows SAC/WDAC image policy
- REL-06 three complete native full-product Windows regressions (currently **0/3 accepted**)
- REL-07 privileged BYOK C1 G0–G6 including P96 race and P124 writer provenance

Historical negative cases remain `HOLD`; P135's three 600-second full-regression timeouts remain real. All release signing pins empty, Code Integrity release false. **PRODUCTION RELEASE HOLD.** No real key entry, live CredRead/CredWrite/CredDelete, provider validation, privileged admission, merge, tag, shipment, or premature Google Drive MASTER/dashboard release status.