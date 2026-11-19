# P279 — Real Windows running-service token custody observation

**19 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | OM v2.1**

**Development-only review candidate — production HOLD, real API keys NO-GO.**

## Provenance and immutable source scope

Parent: P278 a4b221745e274c0c73bcd9a8d5e938f1aef3911b.
Branch: byok-c1-p279-scm-runtime-token-readonly-20261119.
Review worktree: D:\Nayeon\CODEX_P279_SCM_RUNTIME_TOKEN_20261119.
Codex was sole C# implementation, native harness, source-test and workflow author. Nayeon independently reviewed source/interop, compiler outputs, risk boundaries and this report and owns draft publication.

Expected bounded revision: exactly five new regular paths:
- native_c1_candidate/P279RunningServiceTokenReadOnly.cs
- tests/p279_service_runtime/RuntimeServiceTokenTests.cs
- tests/test_byok_c1_p279_runtime_token_source.py
- .github/workflows/p279-windows-service-runtime-token.yml
- docs/byok-c1-p279-running-service-token.md (this report)

All 1,122 inherited Git blobs remain byte-identical, including original P261 and P215, original CustodyService, ServiceGate, ProtectedAcl, original P96, P275, P276/P277/P278 and all historic security tests. A final accepted candidate contains exactly 1,127 files. Git HEAD, branch, parent, checkout and native source hashes must be independently reconciled before publication. No old acceptance or service policy is modified.

## Actual security defect and bounded native advancement

P261 observes the actual Windows Service Control Manager *configured* account and SERVICE_SID_TYPE_RESTRICTED policy, but does not bind the *running process* to a kernel token. P215 observes the review executable's own token and session persistence capability, not the installed service's running token. Configuration, process status and token must never be treated as interchangeable evidence.

P279 is a read-only, nondeployable C# observation. It calls the unchanged P261 SCM probe and refuses everything unless P261 has actually observed a configured account matching NT SERVICE plus the frozen ServiceGate.ServiceName, with restricted service-SID policy. It then independently opens the named SCM service with status-query rights and calls QueryServiceStatusEx. The fixed nine-DWORD SERVICE_STATUS_PROCESS structure is accepted only when SERVICE_WIN32_OWN_PROCESS, SERVICE_RUNNING and a nonzero process ID all agree. Shared processes, drivers, pending/stopped states, malformed response, missing services and query denials are refusal statuses.

For suitable configured/running evidence only, P279 uses OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION), OpenProcessToken(TOKEN_QUERY), WindowsIdentity(token).User and bounded LookupAccountNameW for NT SERVICE plus the frozen ServiceGate.ServiceName. It compares SID objects (not account text) and re-queries the SCM process status while the process/token handle remains open. Both snapshots must agree. All P/Invoke APIs are read-only SCM/process/token/lookup/handle operations; **no WinCred read, write, delete, enumeration or migration is present.** The observer never logs or returns PID, SID, username, account, binary path, credential target or material. All allocations and native handles are finally cleaned, and cleanup failure downgrades status.

Matching OS data is not approval. Every qualified decision, approved service principal, protected credential owner, trusted consent, native effect, real-key and production authority property is literally false, including RuntimeTokenObserved. Untrusted account and approval strings are discarded. Source cannot be compiled without C1_REVIEW_ISOLATED_ASSEMBLY and deliberately emits P279_RUNTIME_TOKEN_REVIEW_ONLY_NONDEPLOYABLE otherwise. This is not a launcher, service installation, broker, signer, loaded image attestation or credential actor.

**Source limitation:** QueryServiceStatusEx returns an SCM snapshot, not an atomic service execution lease; a requery while holding the process handle reduces PID/restart ambiguity but cannot guarantee race-free identity. A hostile same-user process, altered SCM configuration, unapproved signatures, profile changes, reparse/handle substitutions or OS code-integrity bypasses remain outside P279. A running service need not exist during this test. Status RuntimeTokenObserved is only a coarse observation, never a release gate.

Windows documentation: https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryservicestatusex, https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_status_process, https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info and https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocesstoken.

## Review and test evidence contract

The native harness uses a deliberately disposable GitHub-hosted Windows-2022 x64/x86 runner. Pure parser negatives cover 36-byte STATUS_PROCESS bounds, nonrunning, pending, stopped, shared, driver and invalid service types, zero/mismatched process IDs and deny-only evidence. The actual SCM query must return Missing because no Nayeon service has been installed. It must not open a token or report positive authority. Ten untrusted claimant combinations have no influence.

The source-only Python module has 10 deterministic tests and 21 mutation canaries, including original raw hash guards, narrow native API allowlist, P261-first observation ordering, fixed service SID comparison, second actual SCM snapshot, complete native handle cleanup, permanent authority denial, sanitised native stdout and hosted-only execution guard. These do not substitute for runtime Windows proof. Original protected-source hashes for P261, P215, ServiceGate, ProtectedAcl, CustodyService, P275 backend and P216 old tests must be preserved.

Local compiler validation on Kristian, using actual .NET Framework v4.0.30319 and absolute source paths:
- Warning-as-error x64 guarded C# build: raw exit 0.
- Warning-as-error x86 guarded C# build: raw exit 0.
- Missing C1_REVIEW_ISOLATED_ASSEMBLY x64/x86: both expected native compile exit 1, with two P279 and one preserved P261 CS1029 guard diagnostics and no output assembly.
- No newly built native EXE or Python was executed on Kristian under Windows Application Control.

The pinned same-repository draft PR workflow must validate exact parent/child Git topology, five additive paths, all 1,127 Git/disk identities, actual PR event, exact runner architectures and source hashes. It runs new source-only 10 tests plus preserved P278 10, P277 10 and P276 12, then both the new and original P261 read-only native SCM harnesses on hosted Windows only. Capture native compiler/exe exit codes, stdout/stderr, source custody and SHA-256 text-only artifacts without uploading binaries.

The original unchanged P216 18-test suite remains a separate historical step. Original test02 and test06 have previously genuinely failed because P275 correctly retired direct Python CredWriteW/CredDeleteW; those failures must remain unwaived, with the native exit preserved as 1. Overall CI RED/HOLD is required until qualified versioned test-contract migration. No scoped current-source/native read-only proof counts toward 3 full unfiltered Windows product regressions.

## Open Failures & Prior-Issues Review

| Issue | Severity and disposition |
| --- | --- |
| Configured SCM principal versus actual running process token | HIGH previously unproven; P279 implements read-only evidence under an exact frozen name, no positive admission; hosted runtime result and independent review required |
| Original LocalSystem host gate versus proposed NT SERVICE virtual account | HIGH architecture contradiction; original P49/P261 sources preserved; qualified SEC-03/SEC-04 security owner decision absent |
| Protected service-owned vault, per-principal DPAPI profile, independent antirollback and ACLs | HIGH OPEN; source observation adds none |
| Signed installed service image, authenticated IPC and trusted user-present one-use consent | HIGH OPEN; P214/P215 observation is not a signed consent issuer |
| Original P96 pending operation revoke/effect race | HIGH OPEN in production original; P268 successor development gate and P274 disposable actual effect experiment cannot close it |
| P216 original test02/test06 | UNWAIVED historical RED, contract requiring retired native Python effects; qualified versioned acceptance decision needed |
| P211 original test02, P76 original four modern fails, P275 old adapter two fails/five errors | UNWAIVED original acceptance debts; no test edits or invented passes |
| Whole-product release regression | 0/3 complete accepted unfiltered native Windows product runs |
| Qualified external governance/security/release decisions | 0/7 approved; source author and assistant cannot self-approve |
| Local Python/native execution availability on Kristian | Application Control denies normal Python; no policy bypass, alternate binary or native runtime was attempted |

## Decision

**GO for bounded development/source review only if hosted tests and independent evidence are authentic; HOLD for service installation, credential operations, real API keys and production.** Do not merge or seal this draft. No credential material, provider calls, actual service installation/start/stop, OS policy changes or machine ACL changes were performed.

Next implementation should seek the qualified service-owner/security architecture choice and deliver the production-owned, signed and authenticated service/IPC/consent/credential store with independent protected antirollback, along with original P96 production race remediation and full native Windows product regressions. Do not update the Google Drive master workbook or dashboard until BYOK C1 is fully completed.
