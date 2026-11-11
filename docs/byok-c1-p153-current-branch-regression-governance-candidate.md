# Nayeon v1 — P153 current-branch security regression governance CANDIDATE

**11 November 2026 | OM v2.1 | FOR EXTERNAL INDEPENDENT REVIEW | RELEASE HOLD**

## Context and source custody

Exact predecessor is P152 SHA `0342125898215f194782809d1e9103d71b0c118a`,
draft PR #77. P152 real Windows guard invoked *unmodified* under the
actual later P152 branch and correctly refused with native exit 1:
`P76 offline source refused: wrong exact P76 prototype branch`. Its original
entire P76 module ended native exit 1, 8 PASS and 2 FAIL from real positive
P80-only admission expectations, zero errors/timeouts. Both original
positive tests **remain failing on a later branch**, not passed or waived.

Original frozen P76 `BRANCH` is EXACTLY
`byok-c1-p80-sealed-historical-fixture-20261106`. It was designed to
authenticate only that isolated P80 prototype's source/tree/index/parent
and tag, not to authorise a future unrelated product branch. The
unchanged source must continue to refuse later actual branches.

P153 is an isolated draft child of P152 with **exactly 3 additive
audit-only files**: this candidate decision packet, a native Windows
test-evidence driver and a GitHub Windows workflow. No original
historical test, P76 gate, P139 Win32 handle guard, P140 signed-launch
source, reduced P132 Credential Manager controller, P133 launcher,
WinCred implementation, Git tag, protected setting or source seal is
changed. CI compares **9 original source/test/security files byte for
byte with the P152 Git blobs**, and the original P76 branch constant
and P140 empty signer/main/helper SHA256 pins + Code Integrity policy
FALSE are verified via AST source literal inspection.

## Candidate security regression matrix

These tests are unmodified **original methods**, selected by fully
qualified ID and parsed from their actual original Python test-class
AST. They are **an explicit *supplementary named candidate***, not
the unfiltered historic branch suites or a whole-product regression.

| Candidate domain | Original test class | Named methods | Current-branch security question |
| --- | --- | ---: | --- |
| Historical P76 negative controls | `P76OfflineRoutingTests` | 7 | Immutable P76 manifest, no credential effects, genuine negative branch/tag/index-parent/loader controls, sealed historic refusal |
| Explicit current-user BYOK consent | `LocalOfflineControllerTests` | 8 | No implicit WinCred, one-use review, confirmed write/delete, uncertainty fail-closed, no startup provider read |
| Manual offline process launch | `LaunchBridgeTests` | 4 | Manual fixed module, no keys in process arguments or environment, no implicit launch, frozen helper separately reviewed |
| Frozen installed companion NO-GO | `FrozenSignedCompanionGateTests` | 6 | Empty immutable pinned images and signer, Code Integrity owner FALSE, negative unapproved companion launch |

**Total: 25 named original security tests.** The fixed list is encoded
in the read-only P153 runner. P153 executes the selected 25 original
tests once, in one bounded fresh disposable GitHub Windows-2025 Python
3.12 process, with a genuinely verified P139 opened-handle/no-reparse
local owned C: TEMP root. No test skips, fixture edits, xfails, new
fake positive-security admission, real OpenAI API key, provider call
or production WinCred on Kristian are involved.

P153 records the actual original test source SHA256, native exit,
full original unittest footer/count, failed IDs, duration, raw combined
stdout/stderr SHA256 and byte count. A passing *candidate* requires
native exit zero, `Ran 25 tests`, `OK` and no negative case. The
CI collection exit itself can be green after genuine original tests
FAIL/TIMEOUT; the *manifest* determines the original test verdict.
Even 25/25 CANDIDATE PASS is never qualified independent review,
a historical suite migration decision, a full product pass, or
authorisation to sign/store a real key.

## Original P76 positive cases are never waived

Two original test IDs are intentionally NOT in this separate candidate:

- `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_new_public_and_private_gate_agree`
- `tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_five_public_routes_use_same_source_proof`

They were actually executed by P152 and **failed** on the later P152
branch. P153 does not convert those two to green, mark them skipped,
rebase their branch context, or alter the old gate to accept a later
source. Their negative evidence stays in original logs and must be
reconciled by a genuinely independent qualified test/security reviewer.

An external reviewer must explicitly judge whether these exact-branch
historic positive claims belong only to the old P80 one-child scope.
If accepted, the reviewer must define independently auditable versioned
current-branch **positive and negative** source admission and
supply-chain tests: real parent/tag/tree/source/index/authenticity
verification, no arbitrary branch acceptance, no privilege or
credential effects on unapproved source, negative malicious source,
reparse, binary replacement, provider flow, fail-closed revocation
and signed-image loading. Do NOT simply substitute P153 selected
unit tests for missing signed-binary policy or whole-product suite.

## Independent reviewer acceptance form — unfilled

| Decision | Required evidence | Current |
| --- | --- | --- |
| Named qualified independent reviewer and conflict record | Authentic independent identity, date, remit | **NOT OBTAINED** |
| Current-user BYOK narrowed threat model GO | Explicit consent, same-user malware, same-presence ABA, crash uncertainty, UI secret lifetime | **HOLD** |
| P76 historical positive test ownership | Exact original P80 ref/tag/pins; authentic original negative and positive cases; reviewer-signed branch governance | **HOLD** |
| Versioned current-branch test migration | Reviewed new acceptance suite with authentic actual Git trust provenance, negative controls intact | **HOLD** |
| Original and current regression inventory | 169-module provenance, 15 old failed, remaining timeouts, full test counts, 3 complete native Windows passes | **HOLD** |
| Frozen main, companion, publisher, installer and update trust | Real PE signature proofs, immutable pins, protected install ACL and TOCTOU load-policy owner | **HOLD** |
| Smart App Control / WDAC policy owner approval | Dated and attributable actual owner consent; no bypass | **HOLD** |
| Production release authorisation | Full above plus 3 genuine accepted whole-product Windows green regressions | **HOLD** |

### Additional hard holds

P135 three *unfiltered full-product* Windows runs were incomplete.
P141's 570 scoped Windows executions cannot count as G6. P142/P144
and P149/P150 original negative failures remain genuine. P148
separately recovered 22/22 original A04 native tests. P151's synthetic
topology one-test PASS is not a full-module PASS. P152 demonstrated
real unchanged P76 branch refusal and 8/10 original historical
module PASS with 2 FAIL.

Original privileged BYOK C1 G0–G6 remain OPEN; P96 TOCTOU
revocation and P124 transferred-handle authorship are outside this
reduced offline current-user design. P140 release signing pins
remain EMPTY with Code Integrity GO FALSE. Never store a real
API key, run production WinCred operations on Kristian, request
provider validation before C2, change privileged Windows security
controls, bypass SAC, launch an unsigned EXE on Kristian, claim
independent review, merge/tag/release, or update the original
Google Drive master workbook/dashboard before a genuine authorised
production release.

**P153 = auditable supplemental current-branch security CANDIDATE
only. All original historical holds and production HOLD preserved.**
