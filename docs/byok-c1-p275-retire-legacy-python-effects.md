# P275: retire bundled Python native WinCred effects and plaintext reader

Nayeon v1 / Mark-LII BYOK C1, OM v2.1. Date: 2026-11-18.
**Product source hardening candidate; production HOLD.** Independent review
and hosted runtime evidence PENDING. This is an authorized containment repair
to the user-approved P258 read-only default, not a new production architecture,
service qualification, historical acceptance waiver or sealed milestone.

Exact parent: `f388e69d31dbc8f1dc02230597c2b45deb5b1e60` (P274).
Branch: `byok-c1-p275-retire-legacy-python-native-effects-20261118`.
Initial Git verification found that exact branch/HEAD, clean index and worktree,
and no tag pointing at HEAD. `AGENTS.md` and the engineering failure gate were
read. `.codex/CURRENT_STATE.md` still describes historical Phase 10 work and
does not describe this parent. Git is authoritative; the explicit P275 scope
preserves that file. No completed-product context refresh is claimed.

## Exact source envelope

One inherited product modification:

- `nayeon/secrets/windows_credential.py`

Four additions:

- `tests/test_byok_c1_p275_native_effect_retirement.py`
- `scripts/p275_product_effect_entrypoint_inventory.py`
- `.github/workflows/p275-windows-legacy-native-effect-retirement.yml`
- `docs/byok-c1-p275-retire-legacy-python-effects.md`

The parent contains **1,109** tracked regular blobs. Exactly 1,108 inherited
blobs must remain unchanged: 1,103 other pre-P274 blobs plus all five P274
additions. This reconciles the requested 1,103 count with actual Git custody.
No prior test, review, witness, P96/P268/P274 source, immutable SHA pin or tag
is edited. No staging, commit, tag, push, PR creation, workbook/dashboard
operation or publication is authorized in this writer session. Nayeon owns
independent review and any later commit/publication.

Reviewed backend SHA-256:
`9FFB136A73E4277B966FAE025A3962123433745B6BA8907AB3B8C4137F4A21B3`.
CI records the five-path SHA inventory, all inherited raw Git blob custody,
the product Python source SHA inventory, and unchanged frozen source pins.

## Product behavior and limits

The private `_Advapi32Adapter` now configures/resolves only `CredReadW` and
`CredFree`. Its native write/delete methods, `CredWriteW`/`CredDeleteW`
bindings and calls, write-buffer construction, and native plaintext
dereference/copy are physically removed. The credential ABI structure remains
for the read API; declaring its blob fields does not inspect them.

`read` remains an **inert denial-only shim** solely to preserve the original
P258 `patch.object(..., "read", ...)` semantics. Its only executable statement
raises fixed `SecretStorageError(_FAILURE)`. It does not initialize a DLL,
obtain a buffer, dereference fields or return plaintext,
even when invoked on an instance made without running `__init__`.

The pointer-returning `_acquire` method is removed. Only `__init__`, `read`
and `contains` remain on the native adapter; no method returns a pointer.
Presence acquisition and cleanup are inline within `contains`. The unchanged public
backend constructs a target from an exact typed identifier and the fixed
`nayeon-v1/secret/` namespace; the actual P258 controller uses only the fixed
`openai.api_key` identifier. `contains` returns a boolean and never inspects
the returned credential or blob. A `finally` owner frees every non-null output
exactly once, including when the native read returns false or raises after
setting the output pointer. Only false plus `ERROR_NOT_FOUND` and null output
returns `False`; other failures, inconsistent success/null output, and
false/non-null output fail with the fixed storage error. A free error is
attempted once and fails closed, with no retry or success claim. The pointer
is never returned, dereferenced or copied by product code.

There is no new public native target selector, runtime mode, environment
override, auto-migration or legacy-vault deletion. Existing private methods
are still introspectable; this change adds no claim of private-target security.
Default `WindowsCredentialBackend.get/put/delete` semantics are unchanged:
denial before setup or secret reveal, including after explicit presence refresh.
Explicitly injected deterministic FakeNative fixtures retain backend
get/put/delete and local SAVE/REPLACE/REMOVE controller behavior. Injecting an
actual `_Advapi32Adapter` cannot restore native mutation or plaintext read.

The actual P258 factory, P132/P133 UI status composition, lifecycle and launcher
are untouched. Default begin/approve still refuse forged pending reviews and
never obtain a mutex or reveal a candidate. The trace is source/manual module
or bridge -> local window -> `compose_user_scope_local_byok` ->
`LocalByokController` -> `WindowsCredentialBackend`; the separate lifecycle
depends on the typed backend protocol. Validation remains distinct from effect
authority. Source inventory lists these dependency paths and source hashes;
it does not assert that the lifecycle/UI source has been rewritten or that
every possible Python execution can be statically analyzed.

**No OS policy isolation is established.** Hostile/re-entrant same-user or
same-SID callers can independently import ctypes, invoke Advapi32, replace
Python objects, inject a different adapter or run older code. This patch
removes capabilities bundled in the current product adapter; it does not
prevent those independent actions or revoke already deployed old Python
artifacts, copies or running children. A presence-only native call still
causes Windows to allocate its credential buffer; P275 proves no application
plaintext inspection/copy, not that the OS avoided handling credential data.
No OS isolation, CODE INTEGRITY, trusted consent, release or real-key GO is
established by this in-process source API minimization.

## Deterministic tests and inventory

The new stdlib suite has 18 tests. Its counter DLL exposes all four WinCred
symbols but records symbol resolution and invocation separately. Every actual
adapter construction patches `_load_advapi32`; a second `ctypes.WinDLL` guard
prevents accidental real loading. The fake credential has no stored plaintext.
Tests cover exact read/free ABI binding; absent native mutation methods;
the inert read shim; default denial before/after presence; injected native
adapter denial; actual factory/controller forged reviews; no `SecretValue`
reveal; poisoned pointer dereference and copy; exact single free ownership;
absent/read/free failures; partial output on false/error (including cleanup
failure), unexpected success/null output; pointer escape rejection; and
original injected backend/controller fixtures.

The read-only inventory imports no product code, executes no ctypes or
subprocess, and writes only a JSON receipt to stdout. It enumerates current
`nayeon/**/*.py`, SHA-256s, native presence call sites, dependency paths and
existing ctypes owners. A bounded AST contract freezes native executable
bodies and rejects native effect symbols, extraction, computed aliases,
unexpected methods/imports and DLL function aliases. Native returns are
restricted to boolean literals in `contains`; restored `_acquire` and new
pointer-returning methods fail the source contract. Mutation tests parse
syntactically valid candidates, then demand rejection of restored bindings,
native methods, plaintext copy/dereference, computed DLL symbols, ctypes
aliases, missing/duplicate free, and read-shim acquisition. Temporary source
trees verify rejection of new ctypes owners/import aliases without executing
their contents. These are source review guards, not a general Python sandbox.

Successful inventory says `SOURCE_NATIVE_EFFECTS=NONE` and
`SOURCE_NATIVE_PLAINTEXT_RETURN=NONE` in its structured
receipt, with production `HOLD` and real keys `NO-GO`. It never emits a
production GO. Unchanged historical scanners contain native symbol *strings*
as evidence predicates; those strings are not executable native effects.
Other established ctypes owners remain frozen by complete Git custody.

## Hosted verification and authentic historical impact

CI admits only a same-repository **draft** `pull_request` in `krismcan/Mark-LV`,
from the exact P275 branch to `byok-c1-p274-real-os-effect-gate-20261118`,
at the fixed P274 base SHA above, with exactly one direct child and no merge
parent. It validates actual event JSON, exact one-modification/four-addition
scope, regular modes, raw disk Git blobs and frozen SHA pins before testing.
Checkout/setup-python/upload-artifact are pinned to full action commits.
The matrix is GitHub-hosted `windows-2022`, x64 and x86 **Python 3.12.8**;
runtime verifies Python version and pointer width. Event/source checks are
misuse/custody controls, not trusted-runner attestation.

The immutable upstream refs were checked against the
[checkout commit](https://github.com/actions/checkout/commit/11bd71901bbe5b1630ceea73d27597364c9af683),
[setup-python action at its commit](https://raw.githubusercontent.com/actions/setup-python/ece7cb06caefa5fff74198d8649806c4678c61a1/action.yml),
and [upload-artifact commit](https://github.com/actions/upload-artifact/commit/ea165f8d65b6e75b540449e92b4886f43607fa02).

Hosted CPython first parses and compiles the three relevant Python sources
without executing their bodies and retains the native adapter AST/method
list in `source-parser.json`, stderr and raw exit. The source inventory then
checks the bounded executable AST contract. Each parser, suite and inventory
invocation prints START/END progress and its authentic exit status.

The focused job runs these original controls independently from P275:

- P258 `DefaultCompositionTests`, `DefaultBackendDenialTests`,
  `EntryAndBridgeTests` (original non-Tk fake/status/entry controls).
- Original `tests.test_windows_credential_backend.BackendTests`.
- Original P132 `LocalOfflineControllerTests` with explicit FakeNative/mutex.

All unittest invocations additionally guard the real native loader. Original
test-local fake patches remain effective inside that guard. No real CredRead,
CredWrite, CredDelete, credential enumeration, provider, service, policy or
credential operation runs on Kristian **or hosted Windows** for P275.
There is no C# compilation/execution or P274 real-native harness invocation.
P134's real-WinCred suite is deliberately not invoked and no P134 native opt-in
is supplied. Full discovery is not invoked or claimed to pass.

Historical acceptance is invoked in separate processes, retaining original
code and raw stdout/stderr/exit for each suite:

| Original acceptance | P275 impact / disposition |
|---|---|
| Backend `NativeAdapterTests` used by the historical P132/P134 acceptance path | Requires native write/delete binding and calls, real plaintext read-copy/free, invalid-read handling and native decode acquisition. Those requirements conflict with retirement. Presence/free contract remains; the original suite is expected RED. Actual raw result PENDING, unwaived HOLD. |
| P134 ephemeral real native writes/reads/deletes | Legacy default backend mutations are already refused by P258, and P275 removes underlying native implementations. No P134 native execution authorized here; original source unchanged, acceptance not credited. |
| P211 original source witness tests | Original witness requires `_Advapi32Adapter.write/delete` and `.CredWriteW`/`.CredDeleteW` to exist; that predicate is false on P275. Original positive witness assertions are expected RED. No witness or packaging-policy migration; raw evidence PENDING, HOLD. |
| P216 original source/store inventory tests | Original inventory requires the legacy direct effect source/witness, including native mutation symbol strings. It can no longer claim that witness and may raise in `setUpClass`. No test is edited to manufacture closure; raw evidence PENDING, HOLD. |

The separate historical step runs even if focused tests fail, provided source
custody and Python setup succeeded. It does **not** use `continue-on-error`,
`expectedFailure`, exit coercion, failure suppression or test replacement.
Any nonzero raw result is labeled **HISTORICAL RED/HOLD; UNWAIVED** and makes
that step fail after all three suites' evidence is retained. An unexpected
green result is only its authentic narrow raw result, never a full-product or
release PASS. Infrastructure/import errors must be investigated from the raw
logs; they are not accepted as proof of a particular historical failure.

Artifacts include text `.log`, `.exit` and `.json` only: raw stdout/stderr,
source hashes/custody, individual exits/dispositions and evidence SHA-256s.
No binaries or provider payloads are uploaded. No installer is produced.

## Open Failures & Prior-Issues Review

Reviewed the engineering gate, P258 decision/current implementation/tests,
original backend/native ABI tests, P134 native-only confinement, P211/P216
source witnesses and service decision, and P274 workflow/review/frozen pins.
P275 is bounded repair work under explicit user authorization despite ongoing
production HOLD; it does not advance or seal the next product phase.

| Issue / source / date | Severity, root cause, callers and reproduction evidence | Repair/containment and regression evidence | Independent review / GO-HOLD |
|---|---|---|---|
| Residual native effects/plaintext, P258/P274 source, 2026-11-18 | HIGH: public denial left executable private Python native write/delete/read-copy in the shipped adapter, reachable by direct same-process callers. Confirmed by initial source inspection; runtime reproduction not run locally. | Physically remove native mutation and plaintext extraction; fake DLL resolution/call tests plus source reintroduction canaries. Default/fake semantics unchanged. Hosted evidence PENDING. | Independent source review PENDING; source-hardening verification HOLD. |
| Pointer escape/partial-output cleanup, corrective P275 review, 2026-11-18 | HIGH: initial retirement retained callable `_acquire`, returning a raw credential pointer; false/error paths could abandon non-null partial output. Direct source reproduction confirmed the escape and missing cleanup owner. | Delete `_acquire`; inline acquisition/finally cleanup in boolean-only `contains`; fixed failure on inconsistent outputs. Add pointer-return AST canaries and fake false/exception/cleanup tests. Static surface/statement checks PASS; hosted runtime PENDING. | Corrective source pass completed; runtime/security qualification HOLD. |
| Invalid checkout pin, corrective P275 review, 2026-11-18 | CRITICAL CI blocker: initial checkout pin contained 42 hex characters and could not resolve the intended action. | Replace with exact known checkout commit `11bd71901bbe5b1630ceea73d27597364c9af683`; all three pins match exact approved lowercase 40-hex refs. Recompute backend hash only after source repair. Four native PowerShell parser/compile checks PASS. | Static correction verified; actual hosted workflow run PENDING, HOLD. |
| Historical ABI/source witness acceptance, P132/P134/P211/P216 | Material regression/contract conflict: original tests positively require the retired capability or witness. Source predicates inspected; no local runtime result fabricated. | Preserve all original blobs, run safe fake/source suites separately, retain raw RED/HOLD; do not run real P134. No waiver or governance migration supplied. | Unwaived HOLD even if focused suite is green. |
| P96 original production race, frozen negative source | HIGH: approval/revocation can race original final ownership/effect path. P274 review records original expected-vulnerable proof; no P275 repair. | P96/P268/P274 preserved with unchanged SHA pins. P268 development timing evidence does not qualify original production architecture. | Original production race **OPEN**, HOLD. |
| P76 original four current-branch FAIL, P273/P274 | Material governance failures remain unwaived; current-source admission does not close original failures. | No P76 or successor source changed; no full-suite green claim. | Original four FAIL **OPEN**, HOLD. |
| SEC03/04 service/store/signed IPC ownership, P216 | HIGH: qualified approvals absent; LocalSystem versus virtual-account identity conflict unresolved. Consent/signing/independent antirollback missing; same-user code is not an OS trust boundary. | No service account, store, ACL, policy, signing, credential migration or native trusted consent implementation. Source removal cannot supply owner decisions. | Required qualified Windows/service/store/IPC owner acceptance absent; HOLD. |
| Legacy deployed copies, processes and restarts | HIGH residual threat: source repair cannot revoke installed/copied Python or stop hostile independent same-SID native calls. Presence cannot detect same-presence ABA; re-entrant Python remains untrusted. | No auto-delete/migration, kill/revoke mechanism, or OS-isolation claim. Default restarts still compose read-only status; older deployed artifacts need separately qualified disposition. | No closure claimed; production HOLD. |
| Stale context / blocked interpreter, 2026-11-18 | Environment/handoff evidence gap: state file disagrees with Git; approved Python path `Test-Path` returned access denied. | Preserve state and exact parent; no install/copy, alternate executable or network workaround. Static checks only locally. | Hosted runtime and independent review PENDING; no runtime GO. |

## Current validation and handoff

Local inspection confirms the requested clean starting branch/parent and the
residual capability's source root cause. The approved Python path is sandbox
access-denied; no Python test, syntax execution or compileall is claimed.
No alternative interpreter, package download/copy or executable workaround
is used. Local static checks completed with exit 0: all four workflow
PowerShell blocks parsed; all 15 inherited frozen SHA-256 pins and the reviewed
backend SHA matched; all 1,108 other inherited files matched their raw Git
blob SHA-1 framing; all 1,109 index modes/OIDs/stages matched HEAD. The only
delta is the one product modification and four listed additions. An exact
source-suffix comparison confirms `WindowsCredentialBackend` is unchanged.
The native-class lexical check found no mutation methods/symbols or plaintext
copy/dereference, exactly `__init__/read/contains`, only boolean return
literals and the single guarded `CredFree(pointer)` call. Normalized
executable statement text for all three methods matches the expected AST
contract text. The four workflow blocks each produced a native
`System.Management.Automation.Language.ScriptBlockAst` with zero parser
errors and compiled via `ScriptBlock.Create` without execution (token counts
996/328/204/139). All three action pins passed exact known-ref and
40-lowercase-hex checks. The corrected backend SHA above matches CI's literal.
These are
static custody/source observations, not execution of the Python AST inventory,
its mutation tests, the focused suites or historical acceptance suites.
Hosted CPython parser/AST/compiler evidence is configured but remains PENDING;
the local native PowerShell AST is not Python AST evidence.
Tracked `git diff --check` and all four additive whitespace checks passed
with zero diagnostics (new-file diff status 0/1 is handled explicitly).

**Full Windows product regressions 0/3. P76 original four current-branch FAIL
unwaived. Original P96 production race OPEN. Real keys NO-GO. Production HOLD.
No releasable installer.** No Google workbook/dashboard update until C1 is
fully complete. No keys/credentials are inspected; no provider call, service
installation, security-policy mutation or live credential operation occurs.

Next: Nayeon independently reviews the exact unstaged five-path candidate,
including historical acceptance impact, then owns any later exact one-child
commit and same-repository draft publication. Inspect both architecture jobs'
raw focused and historical results; explain every failure without waiver.
Missing/failed evidence remains HOLD. Stop here before commit.
