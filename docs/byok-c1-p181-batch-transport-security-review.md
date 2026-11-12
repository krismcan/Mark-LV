# P181 — Adversarial security review of the P180 Git blob transport candidate

**12 November 2026 | OM v2.1 | Internal security assessment; qualified independent GO NOT obtained | BYOK C1 RELEASE HOLD**

## Exact original source and genuine Windows evidence

P181 descends **only** from P180 \`20a3611cfcbc6c770b369120fd07c303cbb76eff\`; P180 [draft PR #105](https://github.com/krismcan/Mark-LV/pull/105) unmerged. P180 original GitHub-hosted Windows [run #43302364708](https://github.com/krismcan/Mark-LV/actions/runs/43302364708), [artifact #13981329771](https://github.com/krismcan/Mark-LV/actions/runs/43302364708/artifacts/13981329771), ZIP SHA256 \`98162805A2C144B9B25E541D2A993AB8C75EA670E0EA7D6CC5FF5C9C97856056\`: eight real original P180 protocol tests **PASS**, 48/48 real Git blob SHA256 parity from fresh no-cache batch transport vs \`git show\`; 48 \`git show\` reads 1.328s vs 48 batched requests 0.047s on one disposable Windows runner. That was prototype equivalence, **not** a security-reviewed verifier change or a full-product regression.

Earlier original P179 pin-witness test still timed out at 130s under instrumentation, P178 original complete BYOK-B module timed out after 165s with two original FAIL records, and P135 three 600s full-product discovery runs never completed. Their raw evidence remains immutable and unwaived.

## Objective: review rather than secretly ship an optimisation

P181 creates only **three new review-only files**: this document, \`scripts/p181_windows_batch_transport_security_review.py\`, and the real Windows workflow \`.github/workflows/p181-windows-batch-transport-security-adversarial-review.yml\`. It modifies **no original \`tests/\`, \`nayeon/\` or P180 candidate file**. GitHub Windows runner source ancestry and 171 original test modules are verified before and after the exercise; Kristian original product worktree remains separate and untouched.

1. Reauthenticate P180 archived original ZIP SHA256/CRC/members, original eight-case complete real native Windows PASS log SHA256, 48 exact real blob equivalence proofs, source identity, seven unsigned external decisions and 0/3 full native Windows regressions.
2. Reexecute the unchanged P180 eight native protocol tests and **12 new P181 isolated adversarial tests** in the same genuine hosted Windows Python 3.12 environment. A 20/20 completed unittest footer shows the test harness correctly records behaviour, **not** that the discovered security findings are resolved.
3. Synthetic malformed responses are injected only through an independent dummy pipe passed to an unmodified P180 \`FreshGitBlobBatch.read\` method. No historical tests are monkeypatched; no privileged Git changes, real credentials, WinCred, provider calls or Windows signed-launch actions are made.
4. Preserve original Windows stdout/stderr, process exit and SHA-256, machine-readable risk register with **six OPEN findings** and exact H/C/R release posture. No independent qualified signer, GO or production release may be inferred from a successful test-collection job.

## Review findings — all OPEN

| Finding | Risk | Required independent disposition |
|---|---|---|
| **SEC-P181-01 — HIGH** | P180 \`stdout.readline\` and \`stdout.read\` are blocking with **no bounded I/O deadline**. A stalled child may hold a verifier indefinitely, even when the input OID is valid | Bounded supervised subprocess or worker; timed-out operation kills and retires child; never authorises a stale success |
| **SEC-P181-02 — HIGH** | A malformed batch response raises but leaves the same session usable. A subsequent good response on a synthetic poisoned stream is accepted. A verifier must **retire the session after ANY protocol fault** | Kill/retire session on I/O, header, payload, digest, trailer, pipe-close, process-exit or timeout anomaly, then require fresh authenticated verification |
| **SEC-P181-03 — HIGH** | P180 resolves commit/path/OID once for a narrow immutable benchmark; it does not prove the original **every-invocation** historical disk/index/HEAD/commit/tag/reparse/alias/source-seal checks survive real integration | Original branch/source/seal security contract proof with genuine source-era adversarial tests and negative tamper cases; no caching of approval |
| **SEC-P181-04 — MEDIUM** | Persistent Git child executable identity, environment/config, process origin and cross-process Git repository writer races are unproven | Explicit executable/environment pinning and independent peer/source/provenance verification, fail closed on drift |
| **SEC-P181-05 — HIGH** | Raw Git SHA1 blob parity is insufficient for production source-security acceptance; full historical SHA256 seal, signer and Code Integrity policy contracts remain independent | Demonstrate unchanged full original SHA256 and Code Integrity provenance, signed pin policy, original P76/P85/P140 negative assertions |
| **GOV-P181-06 — RELEASE BLOCKER** | Successful 8/8 P180 prototype and P181 self-authored adversarial tests are **not independent qualified review**, nor 3/3 complete native product passes | Signed qualified review, three genuine unfiltered native Windows complete regressions, independent security governance and authorised signer/policy owner/privileged-service approvals |

**Important interpretation:** An adversarial test that demonstrates the existing session-reuse gap is a **successful detection test**, not evidence that P180 passes the stronger security requirement. The review disposition for the existing implementation remains **HOLD**. Further implementation requires a new isolated candidate with bounded process I/O, session poisoning and comprehensive original source-era differential tests, followed by independent review.

## Permanent release gates

- Historical H **HOLD**; current C **assessment only**, release R **HOLD**.
- GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06 and REL-07 qualified external decisions **OPEN**; none signed.
- Original P135 3×600s full-product timeouts, P178 legacy FAIL cases and P175 source-era conflicts preserved, no historical waiver.
- **0/3** genuinely completed full-product native Windows regressions accepted.
- Signed Windows main/helper/installer/cert and SAC/WDAC policy GO absent; G0–G6 privileged C1 **OPEN**.
- No real API key, native WinCred effects, provider validation, production installation, merge/tag/release, or false Google Drive MASTER/dashboard production release-state update.

**P181 can close as a source-bound adversarial evidence checkpoint only, even when OPEN security issues are demonstrated. No production admission.**