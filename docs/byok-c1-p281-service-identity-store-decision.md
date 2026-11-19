# P281 — Exact service principal and user-scoped DPAPI preflight

**19 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1**

**DEVELOPMENT-ONLY ARCHITECTURE CANDIDATE. REAL KEYS NO-GO. PRODUCTION HOLD. No independent SEC03/04 approval.**

## Proven conflicts in original source

The frozen P49 tests/p99_original_native_c1_denial/ServiceGate.cs defines ServiceGate.ServiceName as NayeonV1ByokCustody and requires LocalSystem in EligibleForService and LiveEligible. It does not currently grant service startup or native credential access.

The historical P216 service-owned store RFC proposes NT SERVICE\NayeonByokCustody (missing V1), and favours a dedicated low-privilege virtual service account with SERVICE_SID_TYPE_RESTRICTED and user-scoped DPAPI rather than LocalSystem. P261 actual SCM configuration observation and P279 running-process token observation instead bind to the real frozen ServiceGate.ServiceName. The P280 hosted Windows evidence validates their absent-service denial on x64 and x86; it does not prove a running installed service.

Two independent conflicts therefore remain: the historical proposal uses a different **account name** and the frozen service startup gate requires a different **security principal**. These cannot be fixed by changing a boolean or claiming user consent.

**Provisional recommendation, subject to qualified independent Windows security approval:** NT SERVICE\NayeonV1ByokCustody under an explicitly signed, reviewed, restricted-SID own-process service. Its data ACL and user-profile DPAPI scope would be separate from the interactive user, with protected independent monotonic recovery custody. The original LocalSystem-only startup gate needs a versioned independent security decision before production repair. LocalSystem is the higher-privilege alternative and remains HOLD. The exact name must match the actual frozen service name. Machine-scoped DPAPI is not an acceptable substitute for service-account isolation: another user with ciphertext on the same machine may decrypt it.

Microsoft references:
- Virtual Windows accounts: https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/service-accounts
- SERVICE_SID_TYPE_RESTRICTED: https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info
- Virtual service account name configuration: https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-changeserviceconfigw
- User versus machine DPAPI scope: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
- Profile requirement: https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata

## Actual bounded native implementation

Codex, as sole native C# source writer, created exactly two additive review-only files:

- native_c1_candidate/P281SyntheticCurrentUserDpapiReview.cs
- tests/p281_synthetic_dpapi/SyntheticDpapiReviewTests.cs

The source cannot compile without C1_REVIEW_ISOLATED_ASSEMBLY; missing-symbol builds deliberately produce P281_DPAPI_REVIEW_ONLY_NONDEPLOYABLE. No production service, installer, backend, credential API, approval issuer, IPC listener or key actor is created.

The only crypto exercise, executed solely on disposable GitHub-hosted Windows x64/x86 runners, creates a random 32-byte synthetic payload and independent random entropy under the CURRENT RUNNER USER. It calls .NET Framework ProtectedData.Protect / Unprotect with DataProtectionScope.CurrentUser entirely in memory, tests round-trip, changed-entropy refusal and tampered ciphertext refusal, and clears all buffers in finally. It never uses DataProtectionScope.LocalMachine, WinCred, a real credential, persistent file, network or OS policy modification. This is a synthetic capability test, not a protected store implementation.

The test harness binds the exact frozen ServiceGate.ServiceName, proves the P216 short name is different, and asserts that original LocalSystem-only admission refuses virtual-account claims. It checks every approval and effect property remains false, even after a successful synthetic DPAPI result.

**If the runtime passes:** only the ordinary current GitHub runner user-scoped DPAPI cryptographic operation is validated. It does NOT prove NT SERVICE profile load, separate-principal negative access, installed service identity, protected vault ACL, backup/restart semantics, real-key safety or production readiness.

## Source identities and genuine Windows evidence contract

Exact parent: P280 commit 466c978458f4cc056e2f161b4c9b4c862bd48e63. Work branch: byok-c1-p281-virtual-principal-dpapi-synthetic-20261119. Candidate is one direct child with exactly four additive paths: the two C# files above, this document, and .github/workflows/p281-windows-synthetic-dpapi-review.yml. All 1,129 inherited regular Git blob/source bytes must remain unchanged; candidate total 1,133 files.

Frozen new C# raw SHA256:
- P281 native source: ABD3B3F42DAB242970E33622EFCF735D66A283E82C1DE03A33588163D6BACE4D
- P281 native test harness: 5044C780EE29D9CC65AE65B6D43B08694D442DDF8F48973DD0DE1822911324DC

Codex compiled actual new C# sources with Windows .NET Framework compiler, x64 and x86 warning-as-error guarded builds raw exit 0; both unguarded builds raw exit 1 with exactly two expected CS1029 review-only diagnostics. No compiled executable or local Python was run on Kristian due Windows Application Control.

Hosted draft-only GitHub Windows-2022 x64/x86 workflow must preserve exact head/base topology, four additive paths, all 1,133 Git/disk hashes before/after, source/action pins and actual raw execution exits, stdout/stderr and SHA256 text artifacts only. It runs 42 preserved P279/P278/P277/P276 current-source tests, the actually hosted P279/P261 read-only SCM missing-service tests and the new P281 synthetic DPAPI harness. No native artifacts or secret material are uploaded. An unexpected result or host policy denial remains HOLD, not implied acceptance.

Original unchanged historical P216 18-suite remains separated, with genuine old test02/test06 failures and raw exit 1 unwaived. Its old expectations of Python native credential writes are obsolete after P275 effect retirement, but cannot be removed, skipped, xfailed or replaced without qualified versioned security acceptance. Overall CI RED/HOLD accurately retains that debt. Full native product regressions remain 0/3.

## Open Failures & Prior-Issues Review

| Finding | Severity and disposition |
| --- | --- |
| Historical virtual-account spelling versus frozen ServiceGate name | HIGH OPEN; canonical exact service name is candidate, external SEC03 source-bound approval required |
| LocalSystem startup gate versus virtual-account proposal | HIGH OPEN; do not alter original gate without separate qualified service-principal decision |
| Service-user DPAPI profile load, restart, ACL and cross-token negative proof | HIGH OPEN; runner user test is NOT service profile proof |
| Protected vault, monotonic antirollback/recovery, signed install, trusted IPC and user presence | HIGH OPEN; no production store or consent issuer exists |
| Original P96 effect/revocation race | HIGH OPEN; synthetic successor development does not close original production race |
| Original P76 four failures, P211 test02, P216 test02/test06, old native adapter tests | UNWAIVED historical acceptance debts |
| GOV01/02, SEC03/04, REL05/06/07 independent qualified approvals | 0/7; no reviewer-signed decision |
| Full unfiltered native Windows product regression passes | 0/3 |

## Decision needed from a qualified external Windows security owner

Name the approved exact installed principal (proposed NT SERVICE\NayeonV1ByokCustody or explicitly reasoned alternative), restricted service SID, profile and DPAPI user-scope semantics, protected installation code-signing and descriptor policy, per-principal vault ACL, backup/recovery, independent antirollback, trusted consent and signed IPC, treatment of legacy interactive-user keys, and explicit source-bound GOV/SEC/REL verdict on the exact commit. An assistant-authored design, user routine engineering authorisation or a synthetic unit test is not that external sign-off.

After a qualified owner decision, a distinct controlled authorised synthetic service installation/test on a permitted Windows host can prove service-owned profile and cross-principal isolation. **P281 does not authorise service installation, change Windows security policy, use real keys or merge a release.**

**P281 DEVELOPMENT-ONLY; REAL-KEY NO-GO; PRODUCTION HOLD.** Main Google Drive workbook and dashboard remain untouched until BYOK C1 is fully completed.
