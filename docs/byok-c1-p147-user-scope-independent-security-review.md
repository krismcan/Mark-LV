# Nayeon v1 / BYOK C1 — P147 independent user-scope security and regression governance review packet

**10 November 2026 | OM v2.1 | REQUEST FOR INDEPENDENT REVIEW — NOT AN APPROVAL | PRODUCTION RELEASE HOLD**

## Identity, immutable source and scope

Exact predecessor P146 commit: `a215b4b23063092ed6087dd4581d50b2b53cde1a`, draft PR #71.
P147 is a new isolated **audit-only** branch. It must add exactly three files:
`.github/workflows/p147-windows-governance-source-custody.yml`,
`docs/byok-c1-p147-user-scope-independent-security-review.md`, and
`scripts/p147_windows_review_packet_custody.py`. No P132 credential controller,
Tk window, P133/P140 launch bridge, P139 native Win32 guard, old integrity
tests or original product files may be altered. CI must verify current
byte-identical source against exact P146 `git show` blobs and SHA-256.

**Approved reduced first release**: current-Windows-user local Credential
Manager slot `openai.api_key`; explicit manual Review and Approve for
save/replace/delete; standalone offline Tk window; no startup read,
no provider validation/network until BYOK C2, no privileged writer service.
This is NOT the original privileged G0–G6 security architecture.

## Genuine Windows evidence, no counts manufactured

- **P132/P133:** user-scoped controller and explicit Connection-page offline
  launch, source-only and faked launches on P133; preserved old tests.
- **P134:** genuine disposable Windows `CredWriteW/CredReadW/CredDeleteW`
  with random synthetic NONKEY target, never Kristian or production slot.
- **P135:** three real *unfiltered full-product* Windows regression attempts
  all exited timeout 124 at 600s before a completed footer: per identical
  partial log, 1,637 PASS, 37 FAIL, 7 ERROR and one unfinished historical
  nested Git BYOK-B test. **ZERO complete full-regression passes.**
- **P136:** exact historical BYOK-B test's Git history replays shown by four
  native Windows faulthandler dumps; slow work, not a proven deadlock.
- **P137:** actual unsigned frozen PE structural build; only separate
  FAKE backend smoke executed on disposable Windows. No signed release.
- **P138/P139:** P138 reproduced seven original Win32 `unsafe_path`
  failures and three old two-button assertions; P139's verified user-owned,
  opened-handle exact C: temporary fixture recovered all seven original
  filesystem tests without changing security source.
- **P140:** frozen sibling helper gate requires exact pinned main/helper
  SHA256, same valid Authenticode certificate and independent Code Integrity
  owner GO. **All three source pins remain EMPTY and approval FALSE.**
  Real frozen companion launch is unavailable; no unsigned binary on Kristian.
- **P141:** three scoped user-BYOK/WinCred + native filesystem suites,
  **190/190 each pass**, total 570/570 *scoped executions* on hosted Windows.
  These do NOT replace 3 full-product regression passes.
- **P142:** 83 post-stall original test modules: 54 PASS, 20 HOLD, 9 TIMEOUT.
  Raw logs contain 29 failed assertions plus 99 errors in completed failed
  modules. Its diagnostic per-test failure regex undercounted CRLF; original
  raw unittest footers are authoritative.
- **P143:** five original modules, 187/187 tests PASS under independently
  native-handle-verified safe TEMP, without source/test modifications.
- **P144:** fifteen other original modules all remained HOLD, zero timeouts,
  even with safe TEMP; unchanged old branch/seal tests cannot count as green.
- **P145:** 19 original Phase8.31 methods each run unchanged in fresh
  Windows interpreter, 18 PASS, 1 HOLD (legacy import-closure + Tk teardown).
- **P146:** exact original static closure test still native EXIT 1. Independent
  observational test-result probe observed a `unittest._SubTest` failure
  carrier holding the retired test-case Tk root, released after the result
  naturally fell out of scope and GC ran. Does not automatically clear the
  original assertion, nor prove general production cleanup acceptance.
- **P147:** automated read-only reviewer manifest checks 13 original source
  and historical test paths from the exact P146 commit and preserves every
  pending group; a successful audit is only source-custody evidence.

## Review questions requiring a qualified, independently identified reviewer

**A. Threat model and credential lifecycle (U1):** Does current-user
Windows Credential Manager storage fit the narrower stated threat model,
including same-user malware, same-user external writers and ABA, uncertain
CredWrite/Delete errors, process crash/restart, in-memory plaintext during
manual entry, UI masking, clipboard/key exposure, one-use Review/Approve,
separate explicit destructive delete consent, and no automatic provider
access? Document each remaining exposure and severity. The in-process
review token is NOT a cryptographic attestation of a human. Presence-only
status is NOT durable secret verification nor API-key/provider validity.
No independent security GO is available yet.

**B. Frozen launch trust (U3/U4):** Confirm signed main and companion
identity, trusted installer/protected install directory ACL, update
and replacement policy, symlink/reparse resistance, malicious same-user
replacement/TOCTOU between hash read and process launch, and actual
Smart App Control / WDAC enforcement at process image load. Actual publisher
certificate, signing authority and policy-owner GO MUST be real, not mock
unit values. Do not propose unsigned Kristian tests, policy disabling,
side-loading or using a signed Python host as proof that Nayeon is signed.
Until independently approved, leave P140 pins empty and frozen launch NO-GO.

**C. Scope and source governance:** Preserve P76/P77/P85 and other frozen
exact-branch/source-seal assertions as genuine historic evidence on their
original admissible branches. Do not mutate, skip or `xfail` old tests to
declare green. Independently decide whether a **new** separately named
current-branch migration suite is appropriate, with its own exact source
commit, explicit coverage, no lost negative tests, and provenance mapping
each earlier assertion to the new required behaviour. A reviewer must
distinguish stale topology assertions from actual production defects.
Never claim that this packet itself approves any partition.

**D. Full-product Windows regression execution (U5/G6):** Design a bounded
but complete and auditable run of all current-product test cases: resolve
nine outstanding P142 module timeouts and the P135 historical Git fixture
cost without silently excluding expensive modules; reconcile all genuine
failures; preserve the original full 169-module inventory and full-case
counts as provenance; obtain independent reviewer signoff on any
branch-aware scope change *before* counting three complete Windows passes.
Every qualifying run needs final unittest/test host count + full native
exit zero, source SHA, full raw logs, native Windows evidence, SHA-256 and
independently reviewed fail-closed negative coverage. Three repeats of a
scoped suite do not satisfy the whole-product requirement.

**E. User review, release and records (U6):** A genuine production release
requires named qualified security reviewer dated GO, explicit production
signer/policy-owner authority, authorised real installer/package release,
three complete accepted Windows product regressions and explicit product
release approval. The original Google Drive MASTER release workbook must
be updated FIRST, followed by dashboard reconciliation. Draft PRs and
diagnostics require NO such updates.

## Reviewer decision template — unfilled until genuine external decision

| Field | Required independent evidence | Current |
|---|---|---|
| Reviewer identity/qualifications/organisation | Named dated authentic record | **NOT OBTAINED** |
| Review independence from engineering author | Conflict-of-interest declaration | **NOT OBTAINED** |
| Source Git SHA and bounded threat model | Exact P147 review tree + source custody | **PENDING REVIEW** |
| User-scope WinCred and explicit consent (U1) | Security decision and findings register | **HOLD** |
| Historical test partition & full-suite governance | Written, versioned migration decision | **HOLD** |
| Signed images, install/update integrity (U3) | Signer/certificate, binaries and ACL proof | **HOLD** |
| Smart App Control / Code Integrity policy owner (U4) | Host policy-owner signed verdict | **HOLD** |
| Three complete full Windows regressions (U5) | Three final original results and logs | **HOLD** |
| Release authority & Drive-first reconciliation (U6) | Release GO/receipts | **HOLD** |

**Neither the assistant nor automated CI may impersonate the independent
reviewer. An audit PASS is NOT a reviewer GO.**

## Explicit preserved and out-of-scope holds

Original high-assurance privileged C1 **G0–G6 remain OPEN**. P96
check-to-effect race and P124 transferred-handle authorship remain unresolved
and are NOT part of a release-privilege elevation. P62 Desktop Commander
support case #18729810 evidence preserved; never rerun a blocked operation
to work around safety controls. No real key use, provider validation, live
Nayeon slot WinCred on Kristian, protected Windows registry/TPM changes,
privileged service, signing-key use, unapproved installer, SAC bypass,
GitHub merge/tag/release or premature Drive mutations.

**P147 disposition: GOVERNANCE PACKET PREPARED ONLY — USER-SCOPED BYOK C1
PRODUCTION RELEASE HOLD.**
