# BYOK C1 P114 — Windows pipe client process provenance, no trusted consent authority

Date: 8 November 2026 | OM v2.1 | **G1 review-only process origin signal — NOT approved signed consent window**

## Purpose and exact security limit

P113 added REAL Windows named-pipe impersonated client-token observation, but a Windows account SID shared by multiple applications cannot identify a particular signed trusted interactive consent window. P114 adds a separate review-only Windows kernel **process-origin observation** on that same preconnected pipe: `GetNamedPipeClientProcessId`, `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)`, `GetProcessId`, `QueryFullProcessImageNameW`, `GetProcessTimes`, and `OpenProcessToken(TOKEN_QUERY)` plus `WindowsIdentity`. Before reporting any source metadata, it obtains P113's real impersonated client SID from the pipe, compares that SID to the OS-reported process-token SID, uses a held process handle across PID/image/creation-time comparisons to prevent PID reuse while inspecting, and obtains the pipe client PID a second time before completion.

There is **no** client-supplied PID, image path, SID, signature flag or approval boolean in the observer API; the only input is a **connected `NamedPipeServerStream`** that has already received a bounded nonsecret byte. No pipe listener, service installation, IPC server deployment, UI window, user approval, WinCred, registry writes, journal writes, network request, real key or executable signing is introduced in the new source. Process metadata and raw SID are not included in `ToString()` or logs.

**This is NOT a trusted signer verification.** A Windows-reported executable path may change on disk, does not establish a publisher signature, cannot pin exact loaded image bytes, and does not prove interactive desktop/session provenance or user intention. P114 does **not** call WinVerifyTrust; it deliberately leaves `SignedTrustedConsentImageVerified=false`, `InteractiveUserSessionVerified=false`, `ExplicitHumanConsentVerified=false`, `ProtectedOneUseGrantIssued=false`, `NativeCredentialEffectAllowed=false` for every outcome. The process handle is closed after observation: a stale recorded path/PID must never become authorization for a later transaction. Image provenance requires an independently reviewed signed publisher + installed app identity + handle-to-image-file binding, OS session/integrity checks, anti-TOCTOU controls and genuine human confirmation before any positive grant.

Microsoft source API reference:
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew
- https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust

## Source composition and native tests

New `native_c1_g1_peer_review/WindowsPipeClientProcessProvenance.cs` is independent of the strict no-mutation P112 candidate assembly and its P113 IPC observer. New `tests/p114_real_windows_client_process/NativeProcessProvenanceTests.cs` uses a **random current-account-ACL local pipe** on ephemeral unprivileged GitHub-hosted Windows; it tests the real kernel PID/path/token/creation-time for both same-process and **separate short-lived child EXE** pipe clients (the child is the very same unprivileged unsigned test program, not a service or UI). The test parent keeps the child alive until OS observations are complete, then sends an inert one-byte acknowledgment and requires clean exit.

Fourteen focused native C# cases cover null/disconnected fail-closed; actual same-process PID; cross-process genuine different OS PID; OS loaded image path; creation time; OS SID agreement; identification-level no authority; reflection proof that no caller PID/path/approval parameter exists; immutable no-signature/no-human-click/no-one-use-grant booleans; OS query-only P/Invoke inventory; and original P49/P112 permanent release guards. All tests run solely on hosted unprivileged Windows. Real named-pipe connection is exercised, but **no code signature/publisher trust or signed human-consent window is tested or certified**.

Retain all previous **170 P113/P112/P110/P109/P108/P106/P99/P96** native cases unchanged and require 14+170=**184 actual named native tests** for focused CI. Original P96 negative fake-only test still proves original P49 consent-to-effect race and remains an open production G2 risk. Historical C1 PRs preserved as review-only draft branches. Original 11 P49 source SHA-256 pins and P112 strict no-effect candidate read-only composition remain unchanged.

## G0–G6 production holds, required next

G0/G6: external qualified native Windows security review, code/image signing design and positive G1 trust approval **not received**.
G1: trusted signed installed consent UI + process signing/publisher binding, OS broker/session/integrity/actual human approval, protected durable one-use server-issued consent and authenticated IPC **not implemented**. A valid OS PID/path/SID is NON-AUTHORITY.
G2: original P49 mutable effect coordinator still has P96 reproducible check-to-effect TOCTOU; real sealed private WinCred dispatch actor absent.
G3: independently protected journal/HKLM antirollback and crash recovery not approved.
G4: fixed pending-only native LocalSystem WinCred lifecycle not tested.
G5: publisher-signed protected Kristian Smart App Control acceptance not performed; Smart App Control stays enabled.
G6: three full Windows product regressions, approved GitHub release and original Google Drive master workbook/dashboard sync pending.

No P62 safety block retry, no real key/credentials, provider call, host unsigned EXE execution, protected mutation, product workspace modification or production release. Original 17 historically dirty product paths are preserved. **P114 is read-only OS process origin evidence, not a human-consent implementation.**
