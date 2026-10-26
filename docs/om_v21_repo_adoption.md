# OM v2.1 — Repository adoption and executable canary boundary

Status: **IMPLEMENTATION CANDIDATE — NOT A VERIFIED RELEASE** (26 October 2026). This document is part of an isolated checkout based on sealed BYOK Increment A commit 4110fa69849f8127a325f9a9001284cd1bd3a59c. The original branch, protected release tags and product sources are not changed.

## Authority and precedence
Source policy: D:\\Nayeon\\Governance\\NAYEON_OPERATING_MODEL_V2_1_20261025.md, independent static governance verdict OPERATING_MODEL_V2_1_SECURITY_GO. That policy supplements historical v2 and all older STOP/security decisions. It does not itself reduce full test suites or grant native credential/provider/OS execution. No actual independent review or GitHub publication of THIS repository implementation is claimed here.

## Adopted in this candidate
- AGENTS.md: state-aware impact matrix, fail-closed actual negative canaries, native evidence, one writer, sensible long-test monitoring, remote Git + same-ID 16-sheet XLSM + served Pages closure.
- docs/engineering_failure_review_gate.md: phase preflight and state transition rules, no replacement of old security findings or manual approvals.
- scripts/om_v21_state_canary.py: auxiliary native-test runner which checks actual annotated baseline tag, predecessor/child identity, current Git status, exact changed-path set, disk SHA256 pins, untracked/ignored Python, and executes entire explicitly named test modules with process exit status and separate hashed logs. Denies mismatch before launching tests.
- tests/test_om_v21_state_canary.py: isolated disposable Git repository adversarial tests for all three topologies, wrong state, edited bytes, unsigned/lightweight tag, unknown/ignored path, invalid manifest/module.

## Explicit limitations and STOP boundaries
- A user-authored JSON manifest is NOT a cryptographically signed reviewer or durable PRC witness. A malicious release owner could alter that manifest; do not use this helper alone as release authority.
- The new auxiliary gate does NOT automatically intercept direct Python full-suite invocations. Production runner admission, independent durable witness, reviewer attestations, machine-enforced source/census verification and PRC remain PENDING. Review first; no claim of OM v2.1 fully enforced until bypass paths are addressed.
- Required full source-affected/historical module census and actual state-specific security probes (including prior BYOK refusal test) must be designed per scope, performed for each Git transition, and independently challenged. The helper's generic module runner is a supplement and by itself cannot prove the census exhaustive or that negative tests were run.
- No reduction from established three authoritative pre-stage/staged/postcommit suites. No real-key/provider/WinCred usage without separate consent. No implicit approval on model output, no Windows security-control alteration.
- This governance-only implementation does not change consumer release scores (architecture 5/19; consumer gates 0/12) and does not close overall Phase 8.
- Do not move a historical product tag, rewrite parent history or overwrite the original master XLSM as evidence of unsealed work.

## Next evidence required for promotion
Independent read-only source/security review on exact changed paths; resolve any HIGH/MEDIUM; focused tests, all relevant historical regression guards, stage/child real canaries with exact SHA; controlled three-suite release contract as applicable; verified GitHub and original same-ID workbook/dashboard. A draft branch is not product release.
