# P179 — Historical Git/seal performance isolation and causality evidence

**12 November 2026 | OM v2.1 | BYOK C1: IMPLEMENTATION — PRODUCTION RELEASE HOLD**

## Baseline and frozen constraints

P178 diagnostic HEAD \`f114574ec24001103d9be0c421f6be8ff1ab04c9\`, draft PR #103 unmerged. Exact original genuine Windows P178 [run #43274727108](https://github.com/krismcan/Mark-LV/actions/runs/43274727108), [archive #13970391463](https://github.com/krismcan/Mark-LV/actions/runs/43274727108/artifacts/13970391463) ZIP SHA-256 \`676FAD4608D54EC6CDB40D3A1D7E5355F6587476DDB21DA4CFCE979FC4FC1353\`.

This ZIP includes three unfiltered original native Windows logs and SHA256 ledger. P178 results:
- Exact original adjacent control \`test_self_canonicalization_only_zeros_own_single_literal\`: **PASS** (1/1; 0.45s; Windows exit 0).
- Original P135 last-started single test \`test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused\`: **PASS** alone (1/1; 41.83s; Windows exit 0), even though P135 three original 600s full-suite runs had reached this same test without a complete footer.
- Entire unchanged original BYOK-B module: **native Windows TIMEOUT**, exit 124 after 165.125s, no full unittest count/footer, eight 20s \`faulthandler\` stack snapshots and original two FAIL outcomes before termination:
  - \`test_live_brain_reader_tamper_remains_rejected_after_historical_replay\`
  - \`test_projected_historical_brain_corruption_is_causally_rejected\`

The 165s module snapshots repeatedly show Python waiting on \`subprocess.check_output\` → \`subprocess.run\` → Git subprocess communication in \`tests/phase_8_30_scope_migration.py\` and recursively invoked historical B/A/Phase8.34–8.37 seal/parent history routines, notably during \`test_each_historical_a_pin_remains_an_active_witness\`.

**Interpretation, not assumption:** repeated genuine Git subprocess operations appear responsible for the cumulative native test-walltime, but a stack trace is sampled evidence, not a precise call count or proof of deadlock. Two historical module assertions genuinely fail and cannot be bypassed.

## P179 exact scope

Create a separate P179 branch from exact P178 source. Add only three diagnostic evidence paths: this document, a hosted Windows workflow, and \`scripts/p179_windows_historical_git_seal_profile.py\`. All historical \`tests/\`, real \`nayeon/\`, original P76/P85/P139/P140 test/gate source, signer pins and Kristian's original dirty product worktree stay completely untouched.

1. Fetch P178 archive using ephemeral read-only GitHub Actions token, verify exact ZIP SHA256/CRC and all three true original log digests. Authenticate original P178 true PASS/PASS/TIMEOUT, 0/3 complete full product and seven independent decisions OPEN, preserve two original module failures and eight native stack snapshots.
2. Reauthenticate exact Git HEAD, parent P178 \`f114574ec24001103d9be0c421f6be8ff1ab04c9\`, only three added audit-only paths, original 171 tracked test modules and complete unchanged \`nayeon/\` and \`tests/\` trees.
3. Use hosted Windows Server 2025/Python 3.12, P139 Win32 handle-verified owned randomized C:\ TEMP root. Run original adjacent control in its own unmodified fresh Python process (30s watchdog). Run the real, unchanged original expensive \`ExactBYOKBTests.test_each_historical_a_pin_remains_an_active_witness\` in a separate fresh child (130s watchdog).
4. **Observe only** the shared Python \`subprocess.run\` call timing in the profiling child. The wrapper executes every real Git command by calling the saved original \`subprocess.run\` directly, preserves actual parameters, stdout/stderr, errors, exceptions, and return code; no cache, no skipping, no synthetic Git bytes, and no security-test source edits. It writes aggregate Git command counts and elapsed walltime **by Git verb only** (no shell arguments or sensitive data) every 12 real Git commands, plus normal-exit snapshot if available. This diagnostic wrapper changes timing and **cannot qualify as an original uninstrumented test pass**.
5. Preserve full untouched native stdout/stderr, real exit 0/1/124, original unittest footers/FAILs, 25-second periodic faulthandler native thread traces, raw log SHA256, periodic bounded Git process count/timing JSONL and H/C/R ledger. A timeout is genuine evidence, not a PASS.
6. Distinguish whether the dominant walltime is repeated \`show\`, \`ls-tree\`, \`rev-parse\`, \`diff\`, \`cat-file\`, etc., and whether a **safe optimisation proposal** would preserve original integrity verification on each invocation. Do not change old tests or weaken controls; any caching or test source refactor would require an independent security/governance review and separate isolated PR.

## Independent security restrictions

Original P135 three 600s full discovery timeouts remain genuine; P154's 23/83 unresolved suffix modules remain; five original P175 historical case failures and source-era contradictions remain; P178 two original module failures remain. Unfiltered complete **full-product native Windows regression acceptance = 0/3**. All seven qualified decisions GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 OPEN. Signed Windows parent/helper/installer/cert issuance and SAC/WDAC GO absent; privileged BYOK C1 G0–G6 OPEN. No real key, native CredRead/CredWrite/CredDelete, provider validation, privileged service, merge/tag/shipment, or premature Google Drive MASTER/dashboard release-state update.

A green GitHub profiling job means its **original evidence was collected accurately**, not that historical tests were fixed or full regressions passed.