# P258 legacy interactive UI containment decision

## Current disposition: final post-remediation host evidence, corrected review pending

17 November 2026 | OM v2.1 | SOURCE CANDIDATE / UNSTAGED / UNMERGED

**The user has explicitly resolved BLOCKED_EXTERNAL_DECISION:** replace the
default legacy interactive-user credential-write workflow with read-only
status until a future trusted Windows SERVICE-ONLY credential owner is
qualified. This is product behavior approval only. It supplies no SEC-03 or
SEC-04 approval, native effect permission, service installation, real-key
entry, provider network permission or production release. **Real-key NO-GO;
production HOLD; security/failure gate HOLD.**

The final post-remediation independent Windows host receipt now documents
23/23 P258 synthetic tests PASS, including default `get()` refusal before
and after presence refresh. This is focused test evidence for the corrected
source, not independent source/release GO. The immediate first reviewer
returned `P258_INDEPENDENT_REVIEW=HOLD`; corrected-source review remains
PENDING. Nine selected historical test failures remain UNWAIVED; full product
regressions are 0/3 and qualified independent GOV/SEC/REL approvals are 0/7.

This section supersedes the prior no-patch decision below. The original
investigation is retained verbatim as historical evidence, including its
then-applicable BLOCKED_EXTERNAL_DECISION and source-unchanged statements.

### Verified intake and inherited host baseline

Before editing, Git confirmed exact HEAD
`23d7343dfcc016eefa047c241a45417d91b0b6c5` and branch
`byok-c1-p258-legacy-effect-containment-20261116` in the specified P258 root.
The index and tracked worktree were clean; the preexisting untracked decision
document was preserved. No tag points at HEAD. The nearest tag and stale
`.codex/CURRENT_STATE.md` mismatch are recorded in the historical intake below.
Git lists other preexisting linked worktrees; none was entered, created or
changed. This checkout is the sole source-writing location. This repair does
not start or complete a new product phase or refresh the historical handoff.

For this documentation-only reconciliation, Git again confirms that branch
and parent HEAD. The existing three modified product paths and two untracked
additions (this note and the P258 test file) are preserved; only this existing
untracked note is edited. The stale Phase 10.2 state file is not reconciled in
this bounded task. No staging, commit, tag, push or other worktree change.

The user-supplied original Windows host baseline, **before these source
changes**, is:

| Original host suite | Baseline result |
| --- | --- |
| P132 | 39 PASS / 2 FAIL |
| P133 | 30 PASS / 2 FAIL |
| Combined | **69 PASS / 4 FAIL; native controller exit 1** |

Receipt:
`D:\Nayeon\P258_LEGACY_CONTAINMENT_EVIDENCE_20261116\p258-original-P132-P133-native-receipt.json`.
Supplied receipt SHA-256:
`4261DFC05F8F15DDE5DAD9FF4AB569CA15461FBACCC9AA41E05721AB6644EBE9`.
Source was unchanged during that original host baseline. That historical
baseline is preserved separately from the final post-remediation receipt
below. Frozen ancestry/scope and old checkout-name failures remain unwaived;
the original baseline is not a passing acceptance result for this candidate.

### Implemented source behavior and alternate-route audit

Exactly three product files change; one focused test file is added, and this
preexisting document is updated. The child bridge source is unchanged.

* `local_byok_user_scope.py`: the exact `LocalByokController` factory type is
  preserved. Construction with the default backend supplies no mutation
  backend binding. Both `begin` and `approve` check absence of that binding
  before presence observation, mutex acquisition, candidate handling or
  effects. Forging an exact pending review, confirmation, operation or
  observation backend does not supply the missing binding. Approval refuses
  and clears pending state. Explicit refresh still uses `is_available` only.
* `local_byok_window.py`: the default window announces read-only status and
  the wait for a qualified trusted Windows service-only credential owner.
  Save/replace/delete review buttons, secret entry, both confirmations,
  approval and rejection controls are disabled. Direct review/approve
  callbacks also return before reading entry or confirmation state. Refresh
  remains enabled. The explanatory notice survives status refresh.
* `windows_credential.py`: default `WindowsCredentialBackend().get/put/delete`
  now raise the fixed `SecretStorageError` before lazy native setup or
  candidate reveal. Default denial persists after a presence read has cached
  the real adapter. Put/delete also refuse an explicitly supplied native
  adapter. Existing exact
  argument checks and backend public method surface are retained. `get` uses
  only the read adapter explicitly injected at construction; lazy presence
  setup cannot supply that binding. The default status controller/window
  never calls it or copies stored key plaintext.

The existing `_native` fake-injection seam remains. Read access captures
explicit injection at construction; mutation eligibility still distinguishes
absence/the native `_Advapi32Adapter` from an explicitly injected fake adapter.
The controller captures a mutation backend only from that preexisting seam,
at construction. There is no environment/release/test mode switch, new
writable argument, default factory override or writable-child fallback. The
presentation property has no setter and does not authorize effects. This
preserves original explicitly fake-injected controller/Tk and fake-DLL ABI
test behavior without editing any original test. It is not test detection.

The trusted native adapter's original write/delete implementation remains for
the original fake-DLL ABI/cleanup tests. It is **not removed from the source
package**. Arbitrary Python code can still instantiate/call that private
adapter, replace private state/code or supply its own adapter; an interactive
user can call WinCred independently. The new default-backend denial and
default-controller composition are source containment, not same-principal
tamper resistance or proof of exclusive service custody. Direct native Python
API exposure remains **HIGH / OPEN** until OS service-principal/store
isolation and package/load exclusion are implemented and qualified.

Entry path: existing Connection callback -> unchanged fixed source bridge
`[sys.executable, '-B', '-m', 'nayeon.desktop_alpha.local_byok_window']` ->
`main()` -> the actual presence-only factory. Direct manual module execution
reaches that same `main()` and factory. Construction/launch does not observe
credentials. No automatic refresh or write is added. Frozen bridge admission
continues to refuse without a qualified companion, with no Python fallback.
Existing live children remain independently owned; this patch neither kills
nor revokes older children, copied source, other processes or old packages.
Restart of this updated source constructs another read-only default.

### Open Failures & Prior-Issues Review (current)

| Issue / severity | Root cause, affected callers and evidence | Repair / tests / independent review / disposition |
| --- | --- | --- |
| Default legacy interactive mutations / HIGH | Default source child, manual module and direct default controller previously composed the same writable backend | Source repair and actual-factory forged-review negatives covered by final P258 23/23 native PASS. Corrected-source independent review PENDING; no verified architectural closure. HOLD |
| Direct default backend / HIGH | Backend wrappers previously lazily obtained native write/delete authority outside UI; first independent reviewer found default get could return stored plaintext and returned HOLD | Default get/put/delete refusal before adapter access and after presence refresh covered by final P258 23/23 native PASS. Corrected-source review PENDING. Current-user same-SID direct private native adapter/API use remains HIGH OPEN; source default refusal is not exclusive effect ownership. HOLD |
| P132 product compatibility / resolved owner decision | Read-only behavior replaces previously approved save/replace/remove | Explicit user approval now supplied for this replacement only; original fake acceptance tests unchanged. Security approvals unaffected |
| Selected original historical regressions / material | Frozen ancestry, expected checkout name and old scope/consumer inventory assumptions; original baseline and final postfix receipt | Final P132 scope 2 FAIL, P133 launcher 1 FAIL, P133 scope 1 FAIL, original backend 2 FAIL, first-run/onboarding 3 FAIL: nine UNWAIVED failures, each failing group native exit 1. Base P257 WinCred/P133 comparison reproduced the same three historic failures before P258 source edits. No assertion rewrite or waiver. HOLD |
| Original P76/P251 regressions / material | Four original P76 failures enter historical admission; P251 original checkout assertion fails on descendant root | P76 4 FAIL and P251 1 FAIL retained. Original guards unmodified; no new closure. HOLD |
| Original P96 / HIGH | Separate approval/lease observations and later effect callback; older routes/process/restart boundaries remain affected | Original finding unchanged; P258 is denial on default Python routes, not the P96 service-owner repair. OPEN/HOLD |
| Native and qualified acceptance / HIGH missing evidence | P247 Windows Code Integrity blocks runtime; service-only Windows principal/store/signer/IPC/consent/durable custody not selected or proven | P247 x64 0/54 and x86 0/54 remain blocked; no Code Integrity bypass claimed. Qualified independent GOV/SEC/REL approvals 0/7; full Windows product regressions 0/3. Focused Python synthetic credit does not qualify native effect-owner acceptance. HOLD |
| Historical source admission / material | P132/P133 and earlier exact-source contracts predate this intentionally approved product change; P251/P255/P256 diagnostics pin earlier source/root | Contracts and tools retained; source drift must remain refused/UNKNOWN where applicable. No migration of their acceptance or historical assertions is claimed. Independent governance/review pending. HOLD |

Reviewed the engineering failure gate, original implementation and relevant
tests, preexisting P258 investigation and recent P255/P256/P257 evidence.
This is the explicitly authorized containment repair under those holds, not
forward product-phase advancement or a security-sensitive seal.

### 17 November 2026 controlled default-read correction

The immediate original P258 independent reviewer returned
`P258_INDEPENDENT_REVIEW=HOLD`: the earlier mutation-only backend refusal left default
`get()` able to return a stored secret, contrary to the approved presence-only
interface. `get()` now raises the existing fixed
`SecretStorageError("Secret storage operation failed")` before adapter access
when no read adapter was explicitly injected at construction. The separate
construction-time read binding remains absent after `is_available()` lazily
caches its presence adapter. Exact identifier validation, explicitly injected
fake reads (including original fake-DLL tests), and default put/delete refusal
are preserved; no original historical test is changed.

Two new purely synthetic negatives assert fixed-error default get denial
before setup and after successful fake-DLL presence refresh, with no adapter
access, plaintext read or additional DLL event. They assert the mocks were
never called, so exception normalization cannot hide an attempted read.
The remediation changes only `nayeon/secrets/windows_credential.py`,
`tests/test_byok_c1_p258_legacy_effect_containment.py`, and this document;
the other two preexisting source modifications are preserved.

Review record:
`D:\Nayeon\P258_LEGACY_CONTAINMENT_EVIDENCE_20261116\codex-approved-migration-independent-review.jsonl`,
SHA-256 `AB2FCA063F0D615D1BC4F963FA4FF5DAD784CC53A77BA53280A13AF45BC55B67`.
The sole writer's remediation record is
`D:\Nayeon\P258_LEGACY_CONTAINMENT_EVIDENCE_20261116\codex-readonly-get-fix.jsonl`,
SHA-256 `476C230192376DBC217910DF71AB11561B34B79F9880BB770BEEC1AA3957ACE8`.
Both hashes were rechecked during this reconciliation. The correction captures
only the constructor-supplied injected read adapter; lazy presence setup
cannot authorize a default read. Original fake-adapter tests are preserved.

The authoritative Python `--version` attempt during remediation failed before
startup with PowerShell `CommandNotFoundException`. No runtime tests or
compileall ran in Codex. The subsequent independent Windows host run below
supersedes that pending-test handoff for its selected suites only. It does
not supersede the first review HOLD with a source- or release-GO: corrected
independent review remains PENDING. Historical failures, P96, private/native
exposure, native acceptance and qualified approval gates remain OPEN/HOLD.
No verified milestone, real-key permission or production release is claimed.

### Final post-remediation independent Windows host evidence

Authoritative receipt for the changed source:
`D:\Nayeon\P258_LEGACY_CONTAINMENT_EVIDENCE_20261116\p258-postfix-windows-native-focused-receipt.json`.
SHA-256, independently rehashed during this documentation reconciliation:
`E62F93196796AA63ADB3254B4CC7115B08323861546940B4057B0407148AD843`.
Host: Kristian, Windows Python 3.12.10 x64, exact branch/parent HEAD above.
The host controller completed with native exit 0; that controller result
does not turn the failing selected test groups into passes.

All **1,041 tracked paths plus two untracked additions** have identical
SHA-256 values before and after the host run (1,043 entries in each receipt
snapshot, zero changed entries). This proves source stability during that
run, including the corrected backend and expanded P258 tests. This later
documentation edit changes the note's hash; the receipt remains the preserved
record of the source snapshot actually tested.

| Final postfix selected suite | Result | Suite native exit |
| --- | --- | --- |
| P258 Python synthetic containment | **23/23 PASS**, including new default get refusal before/after presence refresh | 0 |
| Original P132 functional | **36/36 PASS** | 0 |
| P132 frozen scope | 3 PASS / **2 FAIL** | 1 |
| P133 original launcher | 24 PASS / **1 FAIL** | 1 |
| P133 frozen scope | 6 PASS / **1 FAIL** | 1 |
| Original Windows credential backend | 22 PASS / **2 FAIL** | 1 |
| Inherited P257 | **23/23 PASS** | 0 |
| First-run/onboarding selected group | 92 PASS / **3 FAIL** | 1 |
| P140 frozen denial | **24/24 PASS** | 0 |

The nine failures are UNWAIVED frozen ancestry, expected checkout name or
old scope/consumer inventory failures in unchanged historical tests. These
groups cannot be reported all passing or accepted. The base P257
WinCred/P133 comparison reproduced the same three historic failures before
P258 source edits; this supports inheritance for those three, not a blanket
baseline proof or waiver of all nine. Original assertions remain unchanged.

The earlier stable host receipt
`D:\Nayeon\P258_LEGACY_CONTAINMENT_EVIDENCE_20261116\p258-final-windows-native-focused-receipt.json`,
SHA-256 `F6075842A29A484020153A5915F1A5F5880BDF6C8AF6CA41D26961A97281D9EF`,
is preserved and was rehashed here. It predates the default-read correction;
the **postfix** receipt above is authoritative for the changed source.

### Coverage limits and outstanding host handoff

Added `tests/test_byok_c1_p258_legacy_effect_containment.py`: actual default
factory, forged exact/malformed pending state, post-refresh denial, observation
backend substitution, restart, direct default backend denial, explicit native
adapter refusal, actual `main`, manual `__main__` execution with fake Tk,
unchanged fixed bridge/frozen refusal, and actual Windows Tk controls/direct
callbacks. All credential adapter/DLL and process surfaces used by new tests
are fake; the Windows Tk tests create only the UI. A positive explicitly
fake-injected case protects the existing functional seam. The final 23/23
host result above covers this suite after the default-read correction.

The required Python `--version` attempt again failed before Python startup
with PowerShell `CommandNotFoundException`. No interpreter/package was
installed/copied, no alternate interpreter or host/network workaround used.
No Python test or compileall ran in this sandbox. The recorded independent
host execution is separate from these sandbox limits. Static diff review and
`git diff --check` are the available local checks; they do not prove runtime
or production acceptance. Original tracked tests and child bridge retain
their HEAD bytes. No credentials/native effects, service/security changes,
provider network, staging, commit, tag, push, PR, Drive or dashboard actions.

The commands below are retained as reproduction/outstanding handoff commands,
not a claim that every listed command ran in the postfix receipt. In
particular, no full discovery, compileall or P251/P255/P256 result is inferred
from that receipt. Any further host runs must preserve actual exits, logs and
source hashes separately so a later success cannot obscure an earlier failure.

```powershell
Set-Location -LiteralPath 'D:\Nayeon\CODEX_P258_LEGACY_EFFECT_CONTAINMENT_20261116'
$p258Python = 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe'
& $p258Python -B -m unittest -v tests.test_byok_c1_p258_legacy_effect_containment
& $p258Python -B -m unittest -v tests.test_local_user_scope_byok tests.test_p132_user_scope_migration
& $p258Python -B -m unittest -v tests.test_p133_connection_launch tests.test_p133_scope_migration
& $p258Python -B -m unittest -v tests.test_windows_credential_backend tests.test_p140_frozen_signed_companion tests.test_p140_scope_migration
& $p258Python -B -m unittest -v tests.test_first_run_credential_management_window tests.test_credential_onboarding tests.test_credential_onboarding_composition tests.test_credential_operation_host tests.test_bound_credential_lifecycle
& $p258Python -B -m unittest -v tests.test_byok_c1_p251_effect_exposure_gate tests.test_byok_c1_p255_effect_boundary tests.test_byok_c1_p256_source_compatibility tests.test_byok_c1_p257_private_host_refusal
& $p258Python -B -m unittest discover -s tests -v
& $p258Python -m compileall -q nayeon tests
git diff --check
```

Original native mutex/Tk acceptance remains in the original suites; credential
effects use their existing fakes. Full discovery must remain unfiltered with
failures reported, not waived. Compileall creates ignored bytecode; inventory
and account for it under existing source admission. Corrected-source
independent review and complete affected/cross-phase/full acceptance evidence
remain required; full product regressions are **0/3**, qualified independent
GOV/SEC/REL approvals **0/7**. The final focused host results establish only
the listed test outcomes, not full effect-owner security. Current-user
same-SID direct private native adapter/API use is **HIGH OPEN**, original P96
race **HIGH OPEN**, original P76 **four FAIL**, P251 **one FAIL**, and P247
x64 **0/54** / x86 **0/54** Windows Code Integrity blocked. No service-only
Windows principal/store/signer/IPC/consent/durable custody is selected or
proven. **Real-key NO-GO; production HOLD; corrected review PENDING.**
No master workbook/dashboard update until BYOK is fully done. This task
edits only this existing untracked document: no product code/test assertion,
other worktree, credential/native effect, Windows policy, staging, commit,
tag or push action.

---

## Preserved prior investigation (before product decision approval)

16 November 2026 | OM v2.1 | DRAFT / UNMERGED

**BLOCKED_EXTERNAL_DECISION. No product source or test changes. Real-key
NO-GO; production HOLD. No runtime containment has been implemented.**

Intake: exact root `D:\Nayeon\CODEX_P258_LEGACY_EFFECT_CONTAINMENT_20261116`,
branch `byok-c1-p258-legacy-effect-containment-20261116`, HEAD
`23d7343dfcc016eefa047c241a45417d91b0b6c5`. Index and working tree were clean;
no tag points at HEAD. Nearest tag reported by Git is
`nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`, 598 commits behind.
`.codex/CURRENT_STATE.md` starts with stale 3 November Phase 10.2 material.
Git and this assignment govern this investigation; no new product phase or
context refresh is claimed. This note is the sole addition.

## Concrete compatibility evidence

The current path is `application.py:638` `_open_local_byok` -> bridge
`launch()` -> fixed Python child argv at `local_byok_launch_bridge.py:94` ->
`local_byok_window.py:295` `main()` -> actual factory at line 300 ->
`local_byok_user_scope.py:205` -> `LocalByokController.approve()` -> backend
delete at line 175 / put at line 181 -> native backend. Direct manual module
entry bypasses the bridge. Direct controller construction and backend get,
put and delete remain separate routes. A bridge-only refusal is incomplete.

| Proposed boundary | Original evidence | Compatibility decision |
| --- | --- | --- |
| Refuse all source-mode launches | `tests/test_p133_connection_launch.py:38` requires LAUNCHED_OFFLINE and exact existing module argv; line 188 requires the real Tk button to call fake Popen | Changes required functional behavior; cannot silently suppress launch |
| Disable all controller or window approvals | `tests/test_local_user_scope_byok.py:182,191,228` require fake save/replace/delete success; lines 379,391 require actual Tk callbacks to produce fake effects | Blanket denial conflicts with original functional assertions |
| Make only the real default factory/window composition read-only, preserving explicit fake injection | Factory test at line 104 requires exact LocalByokController and zero native activation, but does not assert subsequent factory mutation | Not proven test-incompatible. Nevertheless removes the explicitly selected product workflow; passing injected tests would not establish behavioral compatibility |
| Replace this workflow with existing first-run management/onboarding | `tests/test_first_run_credential_management_window.py:135,164,177` require validated connect/replace and acknowledged delete; `credential_onboarding_composition.py` constructs OpenAICredentialValidator | Not an offline replacement. P132 explicitly avoids provider validation until C2 |

The approval conflict is explicit in
`docs/byok-c1-p132-user-scoped-offline-first-release.md`, "Authorised scope
change": the user selected current-user save/replace/remove by deliberate
local UI. P133 then explicitly integrated that window into Connection-page
navigation (`docs/byok-c1-p133-desktop-connection-launch-review.md`).
P258 explicitly requires stopping before silently disabling this functionality.
Therefore a default factory denial cannot be treated as routine engineering
merely because fake-injected original tests might stay green.

Original governance is separately incompatible with current descendant topology:
`tests/test_p132_user_scope_migration.py:53` requires exactly six paths since
P131; current Git already contains later product additions. Its immutability
check compares original backend/host/entrypoint blobs; the inspected paths
remain unchanged from P131. P133 migration similarly pins its seven-path delta.
The original P133 launch test also constrains cwd to historical checkout names,
which this P258 root does not satisfy. These are source-derived expectations,
not newly executed failures, and must not be patched, filtered away or called
passing. P76/P96/P251 originals remain untouched.

P206 is dormant and refuses reads as well as mutations; its adapter also fails
the local controller's exact WindowsCredentialBackend requirement. P211 is a
nondeployable package preflight. Neither contains this runtime launch path.
P257 is a separate denial-only native owner, with no OS credential isolation.

## Open Failures & Prior-Issues Review

| Issue / severity | Cause, evidence and affected boundary | Repair / review / disposition |
| --- | --- | --- |
| Legacy Python effects / HIGH | Traced source above; UI, direct controller/backend and manual child share interactive user's native authority | No repair applied. Owner must resolve P132 behavior first; independent review absent. HOLD |
| P132 compatibility / material decision | Default read-only composition revokes approved save/replace/remove even if fake-injected tests pass | BLOCKED_EXTERNAL_DECISION; no allow-legacy environment flag or test-detection workaround |
| P96 / HIGH, inherited | Approval/lease checks precede separate effect callback; original race OPEN | No repair or rerun here. HOLD |
| Original regressions / material, inherited | P76 four original FAIL; P251 one original FAIL; later checkout differs from historical admission | Unwaived. No test modifications or reruns here. HOLD |
| Native/qualified acceptance / material missing evidence, inherited | P247 x64 0/54 and x86 0/54; qualified approvals 0/7; full unfiltered Windows regressions 0/3 | No substituted synthetic credit; P257 denial evidence does not close these. HOLD |

Recent P255/P256/P257 records and the engineering failure gate were reviewed.
No independent acceptance or new release evidence is asserted.

## Feasible corrective route requiring owner disposition

The P132 product/consent owner must explicitly choose whether this draft's
interactive default may become read-only pending an accepted effect owner.
If approved, implement a versioned default composition that cannot supply
mutation authority, keep explicit fake injection for unchanged original
functional tests, cover BOTH bridge-launched and manual-module entry, retain
explicit presence-only refresh, and clearly show mutation unavailable in the
UI. Add fake-adapter negatives proving zero write/delete through that actual
default composition. Do not rely on hiding buttons, process environment,
test detection, or a wrapper around the same live factory. Review existing
child lifetimes and restart behavior; a new default cannot revoke old running
children or copied source. Any historical contract migration needs separate
qualified governance review, retaining the original tests and failures.

This can be partial UI containment only: direct backend calls under the same
principal remain reachable. Total effect ownership requires separately owned
OS principal/store isolation and package/load exclusion, plus original P96
repair and qualified security acceptance. If the P132 mutation workflow must
remain available, that larger approved route is necessary; no cosmetic Python
gate resolves the competing requirements.

## Host verification handoff

The single authorized Python `--version` attempt was unavailable in this
sandbox (PowerShell CommandNotFoundException). No interpreter/package was
installed or copied, no retry/workaround used, and no Python tests executed.
Static Git/source inspection is not runtime acceptance. `git diff --check`
passes. No credentials, provider/network calls, native WinCred calls, service,
Code Integrity changes, staging, commit, tag, push or Drive actions occurred.

After an approved source amendment, run each command separately on the primary
Windows host and preserve actual exits/output; do not treat the known historical
topology failures as new containment failures or waive them. These commands
exercise unchanged original tests; they do not launch the real setup module.

```powershell
Set-Location 'D:\Nayeon\CODEX_P258_LEGACY_EFFECT_CONTAINMENT_20261116'
$p258Python = 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe'
& $p258Python -B -m unittest -v tests.test_local_user_scope_byok tests.test_p133_connection_launch tests.test_p140_frozen_signed_companion
& $p258Python -B -m unittest -v tests.test_windows_credential_backend tests.test_p132_user_scope_migration tests.test_p133_scope_migration tests.test_p140_scope_migration
& $p258Python -B -m unittest -v tests.test_first_run_credential_management_window tests.test_credential_onboarding tests.test_credential_onboarding_composition tests.test_credential_operation_host tests.test_bound_credential_lifecycle
& $p258Python -B -m unittest -v tests.test_byok_c1_p251_effect_exposure_gate tests.test_byok_c1_p255_effect_boundary tests.test_byok_c1_p256_source_compatibility tests.test_byok_c1_p257_private_host_refusal
& $p258Python -B -m unittest discover -s tests -v
& $p258Python -m compileall -q nayeon tests
git diff --check
```

New containment negatives must additionally exercise the eventual approved
implementation; none were fabricated for this no-patch decision. Compileall
creates ignored bytecode: preserve/inventory it and account for strict source
admission before further checks. Full discovery remains required, without
filtering historical failures; isolated historical evidence remains separate.
Host evidence and independent review are required before any implementation
or release claim. No new milestone or PR is proposed.
