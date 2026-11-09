# Nayeon v1 / BYOK C1 P135 — full Windows product regression triad and release gate audit

9 November 2026 | OM v2.1 | direct P134 base `52995d74764ea998f4732ce552c9dc301dfab334`

## This is a real, unfiltered full test execution gate, not another mini-suite

P134 already proved actual `CredWriteW`, `CredReadW`, `CredDeleteW` with disposable synthetic-only Windows Generic Credentials on a GitHub-hosted Windows account, while leaving Kristian and the real OpenAI target untouched. P133 introduced explicit Desktop Connection-page launch and P132 manual current-user Tk setup. Still missing: 3 FULL Windows product regressions, signed distributable/SAC acceptance, genuinely independent review of the reduced user-account threat model, and signed release.

P135 runs `python -B -m unittest discover -s tests -t . -p test_*.py -v` in a **fresh disposable GitHub-hosted Windows runner account exactly THREE times**, without filtering test files/classes or modifying assertions. Each full run stores its actual native exit code, test count, complete raw output log and SHA-256 into the runner TEMP directory. It reports failing TEST IDENTITIES, not potentially secret-laden tracebacks. The workflow fails closed if ANY pass fails or inventories drift; all logs are retained as private CI test artifacts when supported. All P134 real OS synthetic-only tests are still constrained by the parent strict ephemeral GitHub runner and random target guards.

### Known cross-phase risk: historical exact-branch seals

Longstanding Phase 8/P76/P132/P133/P134 scope and seal tests intentionally bind to specific historical commits/branches, and some older scope guards explicitly reject any newly approved credential consumer. These tests are not generic full-product functional tests. P132's initial run #42706404260 demonstrated genuine failures of such guards on a newer branch. The P132/P133/P134 focused runs deliberately retained historical tests unchanged but ran applicable older functional classes rather than pretending the old branch-seal tests would pass.

**P135 full discovery intentionally DOES NOT hide those failures.** If the full test suite fails due to historical branch/HEAD seals, report those exact names, identify which assertions are truly context-specific, and retain a mandatory HOLD. A proposed future branch-aware regression regime must be reviewed and formally authorised. Do not silently mark triple full product regression as PASS merely by excluding failures.

## Safe runtime boundaries

- Windows hosted runner ONLY, no unsigned test binary on Kristian; single clean exact GitHub HEAD and three identical discovery commands.
- No real OpenAI key or provider validation; P134 unique disposable random Generic Credential target for synthetic actual WinCred tests, with native cleanup, no real `openai.api_key` operations.
- No installed privileged service, protected journal/HKLM, TPM changes, Smart App Control alteration, source/credential signing or real app release.
- Frozen P49 source hash pins / P96 original fake-only old race proof remain in preceding CI evidence; P135 changes no production source or original tests.
- Store full evidence of failed tests rather than editing original expected branch refs or downgrading acceptance.
- This regression audit does **not** independently qualify any signer, reviewer or production runtime.

## Intended review outcomes

A credible release process needs THREE **authentic** green full-product Windows regressions *under an independently approved cross-phase scope definition*, a trusted pinned/signed installer and executable, verified Smart App Control policy acceptance, and a qualified outside-party review of the reduced current-user threat model. The full CLI run may expose old branch-pinned test failures, but they must remain visible until the regression governance review resolves them.

The original privileged BYOK C1 G0–G6 gate ledger remains OPEN. The alternative reduced current-user release U1 independent review, U3 signed package, U4 SAC compatibility, U5 three full product regressions and U6 original Google Drive master workbook-FIRST/dashboard only-on-release remain OPEN.

**P135 is an audit experiment and does not authorise real API key entry, GitHub merge/tag/release or Google Drive release tracking edits. BYOK C1 USER-SCOPED RELEASE HOLD.**
