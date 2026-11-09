# BYOK C1 P118 — simultaneous OS file ID and native WinTrust on one opened handle

Date: 9 November 2026 | OM v2.1 | Direct exact baseline P117: `929e94a4a53805aa3234f7749591d18b74f01a6e`

## Security boundary and rationale

P113 observed the actual pipe client token SID; P114 obtained OS pipe client PID / process creation time / executable path; P115 compared pipe client session with process-token session and mandatory-integrity RID. P116 performed native WinVerifyTrust file-signature policy evaluation against an open read-only file handle. P117 obtained 128-bit `FileIdInfo` using a separate file inspection.

**P118 combines the Windows file ID checks and native WinVerifyTrust OS policy invocation inside the lifetime of the SAME read-only file handle**, with before/after FileIdInfo (volume serial + 128-bit file ID) consistency. For connected named-pipe review, it also holds an actual `PROCESS_QUERY_LIMITED_INFORMATION` process handle while the native file probe runs; the queried PID and creation timestamp must match P114's OS observation before and after. P115 session/integrity and pipe client PID must agree with P114 before invoking the file query.

`WinVerifyTrust` receives the same already-opened file HANDLE via `WINTRUST_FILE_INFO.hFile` and a required path. Revocation network fetches are disallowed using `WTD_CACHE_ONLY_URL_RETRIEVAL`, UI disabled, whole-chain revocation policy requested. The native policy result, **even when success is exact zero**, is only an UNPINNED file signature check. The API/provider may still use a pathname in implementation: the caller cannot infer a cryptographically verified identity of the process's live loaded image section from the API call alone.

## Non-authority boundary (absolute)

P118 is NOT trusted consent provenance. None of the following is implemented:

- approved service-owned publisher/certificate thumbprint, trust-anchor enrollment or revocation-response lifecycle;
- immutable verified installation location / file system ACLs and signed installed broker;
- actual kernel mapping of process executable IMAGE SECTION to the opened handle and signed contents;
- trusted interactive desktop/window that displayed the exact user-facing target/operation;
- authenticated service-owned IPC request with nonce/challenge binding or genuine user click;
- durable cryptographically bound single-use consent with protected consumed/revoked state;
- permission to call WinCred, privileged service, HKLM or protected credential journal.

For every outcome (including any `NativePolicyAccepted`):
`ApprovedPublisherTrustAnchorConfigured=false`,
`RunningMappedImageIdentityProven=false`,
`TrustedConsentApplicationVerified=false`,
`TrustedInteractiveDesktopVerified=false`,
`HumanApprovalVerified=false`,
`ProtectedOneUseGrantIssued=false`,
`NativeCredentialEffectAllowed=false`.

Holding a process handle prevents PID reuse while that instance is held, but not exit or mutation of what user saw; FileIdInfo is file-system-specific and can be reused over time. Rereading the **same open handle** helps bound accidental path replacement during the file probe but still cannot prove that the process executed that file object. No production authorisation decision is emitted.

## Genuine native hosted Windows tests

14 new unprivileged cases: null/blank/relative/missing/directory/empty fail-closed; native unsigned binary and masquerading executable extension rejected; actual compiler-built unsigned test executable; before/after same-handle ID; same file stable across two independent open handles; two concurrent different file IDs; null/disconnected pipe; real same-process named-pipe client; real distinct child process pipe client. Ephemeral test files and an unsigned test executable run only on the hosted Windows runner. No native executable launched on Kristian.

Preserve the previous **226** P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 native focused cases exactly, including original P96 fake-only 15/15 negative test that must continue reproducing the original effect/revocation race. Expected **240 = 14 + 226** native focused cases. Frozen original 11 P49 files, previous candidate source hashes and all preceding native test drivers are pinned in CI.

## Remaining G0–G6 security work

G0: qualified independent Windows security review of original source, threat/attack surface and signed broker absent.
G1: real publisher-pinned installed consent client, mapped-image trust, interactive desktop provenance, authenticated pipe service and exact operation user consent with durable one-use grant absent.
G2: original P49/P61 PendingCustodyTransaction still has the P96 revocation-to-effect race; it remains excluded and no native service-owned replacement exists.
G3: protected journal/antirollback/recovers after crash not ready.
G4: native pending-only privileged WinCred real effect lifecycle not approved or tested.
G5: trusted signed app/service, Smart App Control production acceptance absent; SAC must stay enabled.
G6: qualified independent release approval, 3 complete Windows product regressions and official Google Drive master-first/dashboard release reconciliation not done.

No real API key, no privileged service installation, native credential effect, GitHub merge/release, Smart App Control change, unsigned Windows executable launched on Kristian or P62 blocked safety operation retry.

Microsoft API references:
- https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_file_info
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info
- https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust

**P118 is a review-only native observation increment. G1 human approval remains absent and BYOK C1 PRODUCTION RELEASE HOLD.**
