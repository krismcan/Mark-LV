# P223 — Actual Native CustodyService No-Effect Request Port & External Security Hold

14 November 2026 · Nayeon v1 / Mark-LII · BYOK C1 · OM v2.1

**This is a source-linked native host DENIAL integration, not a real terminal-effect service, a P96 remediation, an independent Windows G0/R3 decision or BYOK C1 release authority.**

## Ground truth and exact parent

- Parent P222: 4cd6878394efe2a8a6e3e5f719edca566360a700, draft PR #147, unmerged. P222 contains independent SEC-03 and SEC-04 decision forms with no actual independent review.
- Last verified genuine Windows native baseline: P221 commit 429694ca64b38a3957fab462d53afeddcdb298d2, Actions run 43632484551, artifact 14128691879, SHA-256 5ECD5536270DD9BBE8D3A90F03F1A191A2E2ACD6DE20A569002357259D401FAB. Original P96 negative race still reproduced and open.
- Original native P96 coordinator raw Git SHA-256 D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB; original ledger raw Git SHA-256 93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B.
- P223 only adds this document, native_c1_candidate/P223ActualHostNoEffectPort.cs, tests/p223_actual_native_host_denial/P223ActualHostNoEffectTests.cs, and .github/workflows/p223-windows-actual-host-no-effect.yml. No historical source/guard/test has been edited. In particular, native_c1_candidate/CustodyService.cs and ServiceOwnedAdmissionBoundary.cs remain byte-unchanged.
- User's Kristian worktree must remain unchanged: D:\Nayeon\BYOK_C1_PRODUCT_20261028, branch nayeon-v1, HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, original 4 modified + 13 untracked entries.

## Meaningful native integration achieved in source

P223ActualHostNoEffectPort is a **review-only typed admission port bound to an instance of the existing CustodyService**, NOT a detached synthetic coordinator. It accepts only the exact CustodyService and ServiceBoundRequestIdentity (untrusted metadata). It invokes *the current* CustodyService.RefuseBoundPendingOperation and CustodyService.RefuseUnreviewedTerminalEffect and never invokes PendingCustodyTransaction.Apply or WinCred. Revocation and fault delegate to the original real candidate's RevokePendingAdmission / FaultPendingAdmission, rather than simulating new authority. Actual original OnStart and OnStop are tested through reflection in the review assembly, not installed or executed under Windows SCM. No user credential or provider call is touched.

The class has no byte[] candidate, no caller-configured effect callback, no generic WinCred adapter, and every authority field stays false. It is gated by #if !C1_REVIEW_ISOLATED_ASSEMBLY #error, so attempting to include it in a normal shipping build fails. Ordinary builds have no execution entry point, service installer, native effect port, UI consent, authenticated IPC or Windows identity.

### What this does NOT demonstrate

- It does not integrate an authorised *terminal effect* into the actual service. This is a refusal-only port; no code exists to arm it through any flag or reviewer claim.
- It does not fix original P96's check-to-effect revoke race: original source still invokes its old fake effect interface after an interposed revocation. P221's separate wrapper does not close it in the real service.
- It cannot prove protected Windows profile, genuine DPAPI/WinCred service ownership, durable journal/anchor, process-shared mutex, loaded signed image or Code Integrity enforcement. Ordinary same-user Python P132/P133 source remains reachable and must be excluded from a future verified installed high-assurance product.
- A passing Windows native CI run is scoped engineering evidence, **not** qualified independent G0/R3 authority.

## Genuine Windows native verification

- Exact parent SHA and exactly four additive paths are source-bound. Every original critical native candidate source, P96 coordinator, P95 ledger and Python P132/P133 effect source is checked against HEAD and before/after hash.
- Frozen original P96/P95 source digests are computed from raw **Git blobs**, not Windows-translated CRLF checkout bytes.
- Genuine Windows .NET Framework x64 and x86 compile the *unchanged actual native candidate CustodyService and ServiceOwnedAdmissionBoundary* with the new P223 test-only port and 12 new focused native test cases per architecture.
- A second deliberate attempt to compile P223 without C1_REVIEW_ISOLATED_ASSEMBLY must fail with the source-defined #error. This tests *ordinary build refusal*, not OS Code Integrity.
- 12 cases cover exact host identity, release-hold observation, typed untrusted requests, replay, null, original revoke/fault/stop, actual OnStart refusal, separate-thread denied request, and reflection audit of callback/credential inputs.
- Historical C1 P96 negative and P216/P220 focused security evidence remains applicable; do not re-label these 24 P223 native cases as 3 full unfiltered product regressions. Those remain 0/3.
- The exact original Windows compiler and executable exit codes, generated log SHA-256 and failure artifacts are recorded.

## Decision owner blockers

SEC-03 must decide actual Windows service logon identity/token/SID/profile, service-owned new target or DPAPI CurrentUser protected file, ACL, protected journal/antirollback witness, independent backup/recovery and genuinely separate same-user P132 store access. SEC-04 must decide signed installed service/broker, loaded-image CI enforcement, full dependency closure, authenticated named-pipe user/session provenance, immutable one-use consent and the actual native P96 final-effect critical section. Neither decision can be invented or accepted from a self-authored GitHub issue/PR or passing native test.

GitHub Issues are disabled on this repository (API 410), so P222's draft PR #147 is the existing review intake surface. No independent reviewer was assigned or submitted a positive decision at P223 intake. Request real qualified independent decisions from the relevant owners; not another synthetic sign-off.

GOV-01/02, SEC-03/04 and REL-05/06/07: 0/7 genuine reviews. G0–G6 OPEN, R0–R4 REAL-KEY NO-GO, P0–P5 PRODUCTION HOLD, full unfiltered Windows regressions 0/3, BYOK C2 NOT AUTHORISED.

## Next engineering decision

If a genuine SEC-03/SEC-04 response arrives, bind their signed choices to exact binaries, Windows OS build and source hashes; implement a *separate actual service-owned native successor* whose final native effect is private to the same service mutex/monitor, authenticated immutable consent and protected IN_FLIGHT journal. Only then proceed to a platform-owner approved disposable no-secret VM test. No privileged service installation, real credential mutation or policy change on Kristian.

If no qualified independent owner is available, record a blocking review status; do not convert P223 code into a production service, and do not generate repetitive fake-only security gates to substitute for external approval. Production remains HOLD; original Google Drive MASTER macro workbook and dashboard are unchanged.
