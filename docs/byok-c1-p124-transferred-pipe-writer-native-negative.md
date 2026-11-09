# BYOK C1 P124 — real Windows duplicated named-pipe client handle: OS peer PID versus actual message writer

Date: 9 November 2026 | Operating Model OM v2.1
Direct P123 exact source baseline: `e90ba1f9dfe43726d88672ee8ed821b43c77288e`

## Goal: demonstrate the actual G1 message-authorship gap

P113–P123 observe a real OS named-pipe client account/process PID/creation/session/integrity and exchange a bounded P120 challenge with the connected client. That provides useful Windows provenance, **but not proof that the process which originally CONNECTED the pipe is the process that wrote each response**. Microsoft documents that duplicated or inherited handles can refer to the same underlying object; `GetNamedPipeClientProcessId` returns the connecting pipe client process identifier, not a signed per-message authorisation token or immutable human-presence assertion.

P124 is a **TEST-ONLY NATIVE RED-TEAM PROOF**, not a fix. It uses ordinary Windows `OpenProcess(PROCESS_DUP_HANDLE)`, `DuplicateHandle(DUPLICATE_SAME_ACCESS)`, and `WriteFile` on an **unprivileged synthetic local Windows named-pipe client handle**. The test runs a test server, a separate connecting process that sends the inert initial handshake, and a distinct third process that receives a duplicated client handle, sends the 32-byte synthetic nonce response using Win32 and exits. The connecting process remains alive and never writes the response bytes. Real Windows OS process and session re-observation on the server therefore may report the opener, even when the response was written by another process.

**Expected negative proof:** The P123 review exchange can still return `EchoObservedWithoutConsent` when the reply is authored by a different process through the duplicated client handle. This result is a **vulnerability demonstration**, not authority. Every `TrueHumanConsentVerified`, `ActualSignedInstalledBrokerAuthenticated`, `DurableOneUseGrantIssued`, `NativeCredentialEffectAllowed` etc. remains FALSE. A real production service must never promote peer PID, pipe-token SID, OS image path, a nonsecret challenge echo, or WinTrust file success to human-approved credential mutation.

Additional native test cases ensure a tampered nonce and truncated response remain refused, even with the transferred handle, and that ordinary non-transfer pipe flow still works. There are no privileged processes, real secrets, real WinCred, network services, protected-state writes, executable signing, installed consent UI or changes to Smart App Control.

## Scope and reviewer decisions

This P124 increment adds only a new hostile-native Windows test driver, corresponding GitHub-hosted Windows CI workflow and a report; **no production code is modified**. The test driver has a compile-time `#error` unless `C1_REVIEW_ISOLATED_ASSEMBLY` is defined. Native Windows code uses only synthetic review-only 32-byte nonsecret challenges and ephemeral local current-user ACL pipe instances. All other historical source remains frozen; the original P96 15 fake-only negative tests must continue reproducing the known revocation-to-effect check race.

Real Windows hosted focused test target: **12 new P124 tests + 313 prior P123/P122/.../P96 native tests = 325 total**. The three Windows processes and native DuplicateHandle call must execute in a real GitHub-hosted unprivileged Windows runner; never launch an unsigned compiled EXE on Kristian.

The qualified independent Windows security reviewer must decide a defensible endpoint-authorship strategy:
- A service-controlled broker launch/protected trust root may restrict permitted callers, but a transferred handle can still allow a different same-user process to write through the same named-pipe object.
- A nonce reply is not proof of a verified user click. OS client PID identifies a connection, not each writer. A broker attestation, protected producer/consumer channel, actual secure user presence, and operation-specific one-use service-owned grant must be independently designed and defended against same-user malicious processes.
- It may be necessary to **narrow the same-user adversary model** or adopt stronger OS-protected user-presence/consent mechanisms; do not manufacture an impossible guarantee.

## Microsoft documentation

- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid
- https://learn.microsoft.com/en-us/windows/win32/sync/object-duplication
- https://learn.microsoft.com/en-us/windows/win32/fileio/file-handles
- https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle

## Mandatory release-hold gates

G0 independent qualified Windows security review OPEN.
G1 signed installed consent broker, service-owned approved publisher/live image binding, message authorship / trusted user presence, protected durable bound one-use grant OPEN. P124 demonstrates an additional real OS G1 threat rather than clearing G1.
G2 P96 original native revocation/effect race OPEN, legacy effect coordinator excluded.
G3 protected journal/antirollback/crash recovery OPEN.
G4 privileged pending-only real WinCred lifecycle OPEN.
G5 trusted signed binaries and Kristian Smart App Control acceptance OPEN.
G6 three complete Windows product regressions, independent release approval, GitHub release and Google Drive master workbook-first/dashboard reconciliation OPEN.

No real credentials, WinCred/protected HKLM writes, unsigned Windows binary on Kristian, privileged installs, SAC changes, GitHub merge/tag/release or historical blocked P62 replay.

**P124 negative G1 provenance investigation; BYOK C1 PRODUCTION RELEASE HOLD.**
