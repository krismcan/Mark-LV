# P301 dispatcher / development owner composition

22 November 2026; OM v2.1; Codex is the sole source writer.
**NONDEPLOYABLE. REAL-KEY NO-GO. PROD HOLD. Hosted evidence PENDING.**
Qualified approvals remain **0/7**; full original Windows regressions **0/3**.
This is bounded test-only source preparation, not a new product-phase seal.

## Custody and exact four-file scope

Git is authoritative: inherited P298 HEAD is
`635f3443ceab17230ed8586ef7b869fa40b092a5`, with 1,212 tracked paths.
The working branch is
`byok-c1-p301-dispatcher-owned-synthetic-composition-20261122`.
The inherited `.codex/CURRENT_STATE.md` still describes Phase 10.2 on 3 November;
that mismatch is recorded, not repaired within this explicitly additive scope.
No completed product phase or new regression baseline is asserted here.

Exactly these four new paths form the eventual one-child candidate:

1. `native_c1_successor/P301DispatcherOwnedSyntheticService.cs`
2. `tests/p301_dispatcher_owner/P301SourceReviewTests.cs`
3. `.github/workflows/p301-windows-dispatcher-owner-review.yml`
4. `docs/byok-c1-p301-dispatcher-owner-integration.md`

The two C# files already existed untracked and remain byte-for-byte fixed.
This authoring task creates only the workflow and this document.
No inherited file, index entry, historical tag, test or report is changed.
No staging, commit, tag, push, local executable generation or execution occurs.
No Python, C#, SCM, WinCred, DPAPI, key or provider operation is run locally.
Local PowerShell parsing is static verification only.

The fixed service SHA256 is
`5D129C8FB908A281B493587F850E2A4012078EA03B4A4948C66AACE8E380B48D`.
The fixed source-review SHA256 is
`9A70F5EA989E36AB0C901C9EFFB876E5C8BBC644653CDD305C85F8F692DD1A61`.
Workflow/document custody uses Git blobs and before/after source manifests;
there is no circular workflow self-hash pin.

## Architecture and bounded dependency audit

P301 combines P294's dispatcher-first idea with the actual development-only
P269 composed owner, P268 pending-transaction owner and P267 denial-only worker.
P265 and the frozen P95/P96 fixtures supply existing synthetic dependencies.
The old P269 entrypoint remains disabled; inherited sources are not migrated.
The service entry's Main guard precedes the genuine `ServiceBase.Run` call.
OnStart reads the exact `NT SERVICE` virtual SID and requires a restricted,
nonimpersonated token before owner construction or worker startup.
`IsTokenRestricted` is a read-only token check, not an authority grant.
The test callback is explicitly cleared to null before development startup.
No TestPrepare/Submit, approval issuance, client admission or credential effect
path is introduced. Capability and production eligibility getters remain false.
Stop, shutdown and disposal transfer ownership once and terminate the lifecycle;
cleanup uses stop/finally-dispose with no rearm. Runtime proof remains absent.

Model output is untrusted. Permission -> Policy -> Confirmation -> Execution ->
Verification remains required; a service identity or synthetic result cannot
substitute for consent, protected provenance, custody or qualified approval.
The compiled IL review inspects methods; its single-argument mode does not
construct the service, call OnStart or invoke its dispatcher.

## Proposed hosted evidence envelope

The workflow admits only a same-repository draft pull request against
`byok-c1-p298-current-effect-retirement-20261122` at the exact P298 SHA above,
with the exact P301 head branch and a checked-out head having that sole parent.
It requires four ADD paths, all 1,212 inherited raw blobs unchanged and 1,216
regular current files whose disk bytes match unfiltered Git blob hashes.
Read-only permissions, pinned Actions, credential persistence disabled and
submodules/LFS disabled bound checkout; no other downloads are authorized.
`core.autocrlf=false` preserves raw UTF8 LF source on hosted Windows.
Both jobs use Windows-2022, one Framework64 x64 and one Framework x86 compiler,
with an eight-minute job limit and bounded child processes without retries.
Build output and sanitized receipts live outside the source checkout.
Clean index/untracked/ignored checks and identical full pre/post SHA256 manifests
detect source changes; both fixed new C# hashes are literal admission pins.

Each architecture compiles the exact nine-source frozen set for both entries,
with DEBUG, TEST_ONLY, isolated-assembly and P265/P267/P268/P269/P301 symbols.
Explicit framework references, /noconfig, /debug+, /warn:4, /warnaserror+ and
the exact platform/main selections require raw exit0 and zero diagnostics.
Four guard negatives per entry remove P301, remove DEBUG, add RELEASE or remove
P269; each requires original raw exit1, only CS1029 and no binary/debug output.
Only the review executable runs, with one absolute checkout-path argument.
Its exact stdout is `P301_SOURCE_CHECKS=17; runtime refusal=NOT RUN`, raw exit0,
and empty stderr. The optional service executable refusal is deliberately omitted.
No valid four-argument service mode, ServiceBase.Run invocation, native SCM
create/start/stop/delete, credentials or provider effects occur in this workflow.
Receipts retain compiler/binary hashes, raw exits, bounded sanitized streams and
source manifests; executable artifacts are not uploaded.

The user reports independent source review and Kristian x64/x86 compilation
of both fixed entries: raw exit0, warnings-as-errors, diagnostics0; no executable
was run. This is supplied compile evidence, not a fresh author execution result.
Actual P301 hosted source/IL results remain **PENDING** until receipts exist.
Even a future hosted PASS is source/IL evidence, not SCM runtime acceptance,
P292 service runtime PASS, cleanup proof, security approval or production release.

## Open Failures & Prior-Issues Review

Sources: engineering failure gate, P298 retirement review, P292-DIAG review,
P295 preflight review and the user's supplied current evidence and limitations.
No original failure is waived, downgraded or closed by this additive preparation.

| Issue / severity | Root cause, reproduction and impacted boundary | Repair, tests, independent review and disposition |
| --- | --- | --- |
| Original P96 / HIGH unchanged | StillCurrent/final IsOwned is separate from SAVE/REPLACE/DELETE; revoke, shared objects, older callers and restart atomicity remain unproved. | P298 default retirement contains an effect route, not this race. Original repair/adversarial cross-route proof and qualified review absent; HOLD. |
| Original P292 / HIGH evidence gap | Original third run 3/6; metadata errors and child timeouts have distinct unknown causes. Original x86 postdelete absence remains unverified. | Preserve original receipts; delete success cannot prove absence. No SCM rerun or cleanup repair here; independent causal closure pending; HOLD. |
| P292-DIAG / material limitation | Read-only diagnostic 6/6 does not reproduce or close original startup/cleanup failures. | Native/CIM observations remain distinct from runtime owner/token evidence; original x86 absence still unverified; HOLD. |
| P295 / HIGH launch qualification gap | Local Smart App Control enforcement, Code Integrity 3033/3077, affects executable launch custody. Compile success does not establish permission to execute. | No bypass, policy change or local execution. Preserve enforcement evidence; independent launch/provenance qualification pending; HOLD. |
| P294/P301 / material runtime gap | Dispatcher-first source and IL shape cannot prove real SCM scheduling, exact token identity, owner lifecycle or cleanup. | P301 composes the real development owner; fixed entries independently reviewed/compiled per supplied report. Hosted and qualified runtime review still pending; HOLD. |
| Historical regressions / material OPEN | P275 WindowsCredentialBackend 2 fails/5 errors, P211 14 failures, P216 2 failures; P76 and older acceptance routes remain unwaived. | No frozen expectations edited or skipped; no full original suite run or replacement acceptance claimed; independent reconciliation pending; HOLD. |
| Principal/provenance/consent/store/restart / HIGH OPEN | A virtual SID and restricted token do not prove protected installed code, client custody, one-use consent, store ownership or recovery. | No production wiring or credentials. External security decisions and adversarial integration proof remain absent; HOLD. |
| Qualified approvals and full regressions / missing evidence | 0/7 qualified approvals; 0/3 full original Windows regressions. Source-only evidence cannot substitute. | No signed approval invented, no release seal; qualified independent acceptance remains OPEN; HOLD. |

**Disposition: bounded test-only preparation only; security/runtime/product HOLD.**
This explicitly authorized investigation does not advance a held product phase.
No workbook or dashboard update until BYOK C1 is complete.
Real keys remain forbidden; production remains held regardless of hosted outcome.
