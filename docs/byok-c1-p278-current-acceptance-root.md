# P278 - Exact checkout root and current P216 acceptance proposal

**18 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1**

**UNSTAGED REVIEW CANDIDATE; production HOLD; real keys NO-GO.** Codex is
the sole author of this four-path candidate. Independent Nayeon review,
publication and all qualified decisions remain outside this source edit.
No external approval, waiver, runtime PASS or production authority is implied.

## Provenance and bounded scope

Checkout: `D:\Nayeon\CODEX_P278_CURRENT_ACCEPTANCE_SERVICE_ROOT_20261118`.
Branch: `byok-c1-p278-current-acceptance-service-root-20261118`.
Exact P277 parent: `a0e07e55f6ea7953db02046a77c8e2b4a22410e3`.
Initial Git status was clean, with 1,119 inherited regular paths and no tag
at HEAD. Git supersedes the stale `.codex/CURRENT_STATE.md`, which describes
another workstream. That file remains unchanged under the explicit scope.

Exactly one inherited path changes:
`nayeon/brain/p216_service_store_decision.py`, only `_git_tracked_python`.
Exactly three paths are added: `tests/test_byok_c1_p278_current_acceptance_root.py`,
`.github/workflows/p278-windows-current-acceptance.yml`, and this document.
All 1,118 other inherited blobs, including every historical test, are frozen.
The later reviewed single-child candidate must contain exactly 1,122 paths.
No stage, commit, tag, push, release, workbook or dashboard update is authorized.

Frozen raw SHA-256 witnesses:

| Path | SHA-256 |
| --- | --- |
| `nayeon/secrets/windows_credential.py` (P275) | `9FFB136A73E4277B966FAE025A3962123433745B6BA8907AB3B8C4137F4A21B3` |
| `tests/test_p216_service_store_decision_inventory.py` (original P216) | `FF077BB4959A0EB5D33D95397649C772F395FE89143C5A8643589E5CB9B4A1F5` |

## Root defect, repair and architectural limits

P277 invoked `git ls-files --full-name -z` with `cwd=root` without proving
that root was the checkout top-level. A nested directory could inherit its
parent's inventory; root/ancestor aliases could also redirect the source view.
This affects the P216 reviewer inventory, not an installed security barrier.

The helper now requires an existing absolute ordinary directory, strict
resolution equal to the supplied Path, and no symlink/reparse point in the
root or any ancestor. Parent traversal, trailing dot/space and Windows device
namespace aliases are refused. A bounded read-only `git rev-parse --show-toplevel`
must return one strictly decoded, bounded LF/CRLF path matching that root.
Windows case and slash equivalence is accepted; other spellings are refused.
Only then may bounded read-only `git ls-files` provide a nonempty, strictly
decoded NUL-terminated inventory. Stderr, native failure, timeout, malformed
records and path/root failures fail closed with `ValueError`. Each Git call
has a 30-second timeout. Supplied filenames still cannot replace Git tracking.

The caller maps helper refusal to `TRACKED_SOURCE_UNPROVEN` with empty
findings and every authority bit false. The original P277 **SOURCE_UNPROVEN
FIRST** rule is unchanged: absent, unreadable or malformed required fixed
source returns `SOURCE_UNPROVEN` before any Git invocation. No review fields,
finding meanings, admission/migration denials or other product functions change.

Call path reviewed: P211 fixed text source witness -> P216 early source
refusal -> supplied-list validation -> exact-root Git inventory -> safe tracked
path checks -> AST parse/compile -> source-risk receipt -> unconditional denial
of admission and migration. P132 controller/P133 launcher and older native
routes remain visible risks; this patch neither executes nor isolates them.
Tests and receipt collection do not import credential implementations or
execute parsed source, packages, WinCred or native services.

Canonical pathname/Git checks are **not signed-source OS trust**, handle/FileId
binding, snapshot atomicity, protected Git configuration, service isolation,
authenticated consent or proof against concurrent substitution by a same-user
writer. Git tooling and the checkout remain local review dependencies. No
LLM output or claimed approval acquires machine authority. Preserve Permission
-> Policy -> Confirmation -> Execution -> Verification.

## Versioned replacement acceptance proposal v1 (not approved)

P275 correctly retired direct Python CredWriteW/CredDeleteW and plaintext-read
effects. Restoring them to satisfy obsolete positive assertions would reverse
the security repair. The original P216 suite is unchanged and **UNWAIVED RED**:
reported 18 tests = 16 PASS + test02/test06 FAIL, raw exit 1.

| Immutable historical assertion | Proposed current replacement property |
| --- | --- |
| P216 test02 expects `direct_effect_source_reachable == True` | Require `False`; retain P132/P133 `source_mode_runtime_risk_reachable == True` and all authority fields false. |
| P216 test06 expects old `wincred_native_adapter == True` | Require `False`, exact current presence-only witness `True`, native CredReadW presence call `True`, and explicit native credential mutation call `False`. |

The 10 new tests cover these current properties and frozen hashes, actual
checkout acceptance to source-risk-but-HOLD, real nested-parent inheritance,
foreign top-level replies/nonrepository temporary copies, invalid/alias roots,
deterministic mocked symlink/reparse metadata (including an ancestor), malformed
or empty Git replies, stderr/exit/timeout, fake lists, malformed tracked Python,
and missing/unreadable/malformed fixed-source precedence. Windows case/slash
equivalence is tested without a skip. Forged external approvals remain refused;
positive authority receipt construction remains impossible. Synthetic payloads
are compiled only in memory, never executed. No symlink privilege is required.

This is a versioned proposal for qualified acceptance review, **not a waiver,
owner signoff, replacement of the historical suite or permission to merge**.
No GOV/SEC/REL decision has been fabricated or credited.

## Hosted evidence contract

Adapted from immutable P277: pinned checkout
`11bd71901bbe5b1630ceea73d27597364c9af683`, setup-python
`ece7cb06caefa5fff74198d8649806c4678c61a1`, upload-artifact
`ea165f8d65b6e75b540449e92b4886f43607fa02`.
GitHub-hosted Windows-2022 x64 and x86 use Python 3.12.8. Only the actual
same-repository `krismcan/Mark-LV` draft PR with the exact P278 head ref, P277
base ref, exact parent SHA above and direct single-child HEAD is admitted.
No checkout credentials persist; workflow permissions are contents-read only.

Before tests, record the actual PR event and hash, complete parent/HEAD/raw
disk Git blob SHA-1 and source SHA-256 receipts, exact 1,119 inherited / 1,118
unchanged / 1 modified + 3 added / 1,122 total scope and both frozen pins.
Run P278 10, unchanged P277 10 and unchanged P276 12 in separate processes,
all required GREEN with exact counts and no skipped/expected-failure credit.
AST compilation and actual current receipt have separate raw logs. The
unchanged original P216 18 runs separately even if focused tests fail.
Preserve its stdout, stderr and authentic native exit; record diagnostics for
exactly test02/test06 failing and raw exit 1. An unexpected outcome requires
investigation. Its failure keeps the workflow **RED/HOLD, unwaived**; no
continue-on-error, patched test, skip, xfail, fake-green or manufactured failure.

Afterward, verify the actual event hash, unchanged HEAD, all raw disk blobs,
all source SHA-256s and clean Git status again. Retain text-only event/source
receipts, stdout/stderr, raw exits and evidence hashes, including on failure.
Child test processes are bounded to 180 seconds; the job is bounded to 12
minutes. No provider, real credential, WinCred native harness, installer,
service execution, policy change or full-product acceptance is authorized.

## Open Failures & Prior-Issues Review

Sources reviewed: AGENTS, engineering failure gate, stale context for mismatch
only, P277 implementation/tests/workflow/review, P276 current witness/tests and
review, original P216 tests, P275 backend hash, and user-supplied hosted results
dated 2026-11-18. Reported prior runtime evidence below was not rerun locally.
This explicitly authorized repair is containment work under HOLD, not forward
production-phase approval or closure of the affected architecture.

| Issue / severity / source | Root cause, reproduction and impacted boundary | Repair, evidence, independent review and disposition |
| --- | --- | --- |
| P278 root identity / material source-review defect / current source | `cwd` alone permits parent Git inheritance; P216 callers can receive the wrong root inventory. New nested/foreign/alias tests target the failure. | Exact-root checks authored; runtime and independent review pending. HOLD, no verified closure. |
| P277 source-before-Git regression / material prior finding / P277 review | Earlier reordering misclassified missing fixed source as tracked-unproven; shared P211/P216 source witness affected. | P277 restored early refusal. Preserve P277 test10 and extend missing/unreadable/malformed-source tests. User reports P277 x64/x86 10/10; P278 rerun pending. HOLD. |
| P276 source classification / material prior repair / P276 review | Retired direct effects and malformed fixed Python previously confused source-risk/readability. | User reports x64/x86 P276 12/12. Preserve source/tests; rerun 12. Original P211 still has 1 historical FAIL, unwaived. HOLD. |
| Original P216 / material acceptance conflict / P277 hosted report | test02/test06 positively require the native effects retired by P275. | Original hash frozen; 18 = 16 PASS + 2 FAIL, raw exit 1 reported. Separate authentic hosted rerun required; versioned proposal above has NO qualified waiver/signoff. UNWAIVED RED/HOLD. |
| Original old native adapter / material historical failures / P275/P277 review | Legacy tests require retired native operations; backend is shared by older entrypoints. | Original 2 FAIL + 5 ERROR remain open. No test edit, adapter restoration or native rerun. HOLD. |
| Original P96 race / HIGH OPEN / prior reviews and user checkpoint | Production approval/revocation races terminal effect ownership across original callers. Synthetic successor tests do not repair the original coordinator. | Original bytes unchanged. No production race fix or closure evidence; independent repair/review outstanding. HOLD. |
| Original P76 / material historical governance failures / prior reviews | Four original failures remain distinct from successor source gates. | No edits/waivers; original four FAIL remain OPEN. Qualified acceptance review absent. HOLD. |
| Service/store ownership / HIGH unresolved / P216 and current checkpoint | Current service configuration uses LocalSystem; proposed distinct `NT SERVICE\NayeonByokCustody` virtual account is unresolved. P261 is read-only SCM observation, not installation. | No service, account, installer or OS policy changes. Protected service-owned DPAPI user profile/ACL, signed IPC, authenticated user-present consent and monotonic protected antirollback missing. Qualified service/store decisions absent. HOLD. |
| Same-user/older image/process/restart routes / HIGH residual OS threat / P277 review | Other Advapi32 callers, injected backends, old binaries/children, process memory and replacement across restarts escape static pathname checks. | No isolation, migration, credential cleanup or signed-image trust claimed. Independent Windows security review and deployment evidence missing. HOLD. |
| Qualified GOV/SEC/REL / material missing evidence / current checkpoint | Seven external decisions cannot be supplied by code or forged claims. | 0/7; denial tests retained. No external owner approval. HOLD. |
| Complete Windows product regressions / material validation gap / current checkpoint | Scoped hosted suites cannot establish unfiltered product-wide behavior across old entrypoints. | 0/3; all mandatory full runs remain outstanding, with original failures unresolved. HOLD. |
| Local runtime / environment limitation / user instruction | Windows Application Control blocks Kristian Python. Static checks cannot prove Python parsing/runtime behavior. | No local interpreter invocation, copy, reinstall, download, alternate interpreter or policy workaround. Hosted execution and independent review pending. HOLD. |

**Gate disposition: HOLD.** Source editing is authorized only for this bounded
repair candidate. No security-sensitive seal, qualified acceptance, deployment
or production phase progression is approved by this document.

## Local verification and handoff

Local static checks passed: all 1,119 parent/index blob identities match,
all 1,118 other inherited raw disk blobs match their immutable parent OIDs,
and only the specified P216 source differs. Exactly three new paths are
present; the index is unchanged. Both frozen SHA-256 pins match. All three
action pins match exactly; the four extracted PowerShell blocks parse and
compile without execution. Ten new test methods and four-path whitespace
were checked, and `git diff --check` is clean. These are static/PowerShell
results, not Python parser, AST or runtime results.

Python parsing, focused execution, affected
regressions, full unittest discovery and compileall have not run locally.
No hosted P278 results or independent review are claimed before execution.
Prior hosted P277/P276 results are historical user-supplied evidence only.

Nayeon independently reviews these exact four unstaged paths and owns any
later staging, single-child commit, draft PR/publication and raw hosted result
review. Original tests remain immutable. Resolve actual findings and external
owner decisions without suppressing historical RED. Workbook/dashboard remain
untouched until C1 is fully done. **STOP BEFORE STAGING/COMMIT/PUSH.**
