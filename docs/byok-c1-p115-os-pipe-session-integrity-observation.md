# BYOK C1 P115 — Windows pipe-client session / integrity observation (REVIEW ONLY)

Date: 9 November 2026 | OM v2.1 | Starting point: P114 exact `5e4267a55d46a9f3e190884020fed6f28fce92e1`.

## Objective and threat model

P113 proved the account SID of the real pipe client; P114 independently derived kernel pipe-client process ID, process-token SID, loaded executable path, and process creation time. These are **provenance observations, not trust decisions**. P115 adds a narrowly scoped, read-only Windows OS session and token mandatory-integrity observation for the **same existing, connected** named-pipe instance.

An attacker under the same account may send the same claimed SID, request/session/operation IDs or app name. None are accepted as authority. P115 invokes `GetNamedPipeClientSessionId` against the OS pipe handle and reads `TokenSessionId` / `TokenIntegrityLevel` with `GetTokenInformation` from an actual `TOKEN_QUERY` process-token handle. It compares OS pipe session with OS token session, and revalidates the P114 PID, creation time and token SID under an independent `PROCESS_QUERY_LIMITED_INFORMATION` handle. Recheck pipe PID and session before returning. All inaccessible, stale, malformed or ambiguous observations => `Unavailable`.

Session 0 is not automatically rejected; it is an OS identity observation, and a proper interactive desktop/broker binding has not yet been implemented. Observing an integrity RID (S-1-16-*) is **not** a trusted publisher, desktop-verification, code-signing result or consent decision. P115 reopens a process handle after P114 returns; even when creation time matches, this is NOT yet a single atomic process-to-loaded-image signed-file attestation. Never reuse metadata as a later authorization.

## Exactly what remains false

For EVERY outcome, including valid OS session/mandatory-integrity evidence:
- `TrustedInteractiveDesktopVerified=false`
- `SignedTrustedConsentImageVerified=false`
- `ExplicitHumanConsentVerified=false`
- `ProtectedOneUseGrantIssued=false`
- `NativeCredentialEffectAllowed=false`

No new signed UI, production service, IPC listener, key, credential write, WinCred operation, protected journal/HKLM write, privileged host launch or signing workaround. Production release **HOLD**.

## Test scope

New unprivileged Windows native driver `tests/p115_real_windows_session_integrity/NativeSessionIntegrityTests.cs` exercises random current-account-only local pipe fixtures and a genuine distinct child process (same temporary test executable), with nonsecret one-byte handshake. It asserts OS pipe/token session agreement, OS process session readback, OS mandatory-integrity RID retrieval and the permanent no-authority flags. It also covers null/disconnected inputs, identification-only client, no caller-supplied PID/session/authority and direct PInvoke mutation bans.

On hosted Windows runner only, require 14 new P115 + prior 184 P114/P113/P112/P110/P109/P108/P106/P99/P96 named native cases = **198**. Preserve P96 15/15 legacy race-reproducing fake-only negative comparator. Pin 11/11 original P49 source hashes plus all prior review sources. No unsigned executable launch on Kristian (Smart App Control stays enabled).

## Security findings and excluded acceptance gates

- **G0 OPEN:** No qualified independent security review or signed broker architecture approval.
- **G1 OPEN:** No signed installed consent UI, publisher thumbprint / trust-anchor pin, verified signer chain / revocation policy, handle-to-loaded-image byte identity, tamper-resistant install path, interactive desktop/user presence, authenticated service-owned pipe endpoint, exact operation display/click, durable server-owned one-use grant, or anti-replay proof. Session / integrity identity does NOT cure this.
- **G1 adversarial follow-up OPEN:** Wrong-user/wrong-session, lower-integrity, app-container, protected process, remote-client, cross-desktop, stalled process, disconnected peer, image replacement, path reparse/symlink, signer substitution and consent race scenarios require separately controlled native testing/review. No production approval inferred from a happy-path runner.
- **G2 OPEN:** P96 legacy `StillCurrent()` then effect race reproduced; original P49/P61 coordinator remains deliberately excluded. No private service-owned atomic native WinCred actor.
- **G3–G5 OPEN:** Durable protected journal, antirollback, native pending-only credential lifecycle and production trusted signing/SAC acceptance incomplete.
- **G6 OPEN:** Three complete Windows product regressions and independent release approval, GitHub release/accounting, original Drive workbook first then dashboard not performed.

Microsoft reference APIs: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientsessionid ; https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation ; https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_mandatory_label .

**P115 is a review-only OS provenance increment. The absence of a genuine production trusted consent window is an explicit open gate; never treat its test pass as G1 or C1 release approval.**
