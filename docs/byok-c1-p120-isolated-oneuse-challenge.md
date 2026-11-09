# BYOK C1 P120 — compile-gated one-use challenge transcript, with no human consent authority

Date: 9 November 2026 | OM v2.1 | exact direct P119 parent `c4be1976fc2d1dbd3c63b73d16afb48e99311c72`

## Task

Implement the first **nonprivileged, review-only executable prototype** of the P119 operation-bound challenge admission model; **do NOT build a positive trusted consent broker** without qualified review and real OS trust root.

`ReviewOnlyOperationChallenge` is compile-time prohibited outside the isolated `C1_REVIEW_ISOLATED_ASSEMBLY` test definition. It requires P102's immutable `ServiceBoundRequestIdentity` with a 5-minute maximum untrusted-request clock window and a 64-character lowercase hexadecimal **untrusted** peer observation claim. The review-only issuer generates a new OS CSPRNG 256-bit nonce and computes SHA-256 over length-prefixed canonical immutable request fields: exact operation, session ID, request ID, candidate digest / deletion acknowledgement, expiry, and untrusted peer claim.

The in-memory review transcript uses a **maximum 60-second synthetic TTL** (or earlier request expiry) and one synchronized terminal transition on first attempted response, even if malformed or mismatched. It checks a mock host time against issue time and deadline; stale, clock rollback, callback exception, unknown/changed identity, incorrect peer and bad nonce all fail closed. Concurrent response/revocation attempts can end in at most one terminal diagnostic echo; no replay and no reissue of that state. Returned nonce and digest are defensive copies. ToString never logs IDs or digests.

### Critical limitation and security controls

**This is not a service.** A `Func<long>` injected clock and the peer fingerprint are **synthetic caller-controlled test inputs**, not authenticated Windows service-owned identity. A challenge can be observed or relayed by an attacker. A matching echo proves **only a matching in-memory transcript** — it is not cryptographic proof of a signed installed broker, actual human click, trusted desktop, OS-backed IPC caller, or approval.

There is **no positive approval API**: the highest result is exactly `EchoMatchedWithoutConsentAuthority`. `AuthenticatedServiceListenerInstalled`, `ApprovedSignedConsentBrokerVerified`, `TrustedHumanInteractionVerified`, `ProtectedDurableGrantIssued` and `NativeCredentialEffectAllowed` are immutable **FALSE** for all outcomes. Memory state is intentionally NOT durable; a real G1 durable grant and G3 crash recovery require independently approved protected service-owned implementation.

This does not touch original P49, P112 candidate, prior P113–P118 or P96 native race comparator. No real secrets, WinCred, HKLM/protected journal, installed privileged service, signed app, Smart App Control setting, Kristian unsigned binary launch, hardware user presence, network or credential effect.

## Hosted Windows focused tests

27 new C# native x64 hosted Windows isolated cases:
- malformed/missing input and peer, expired or overlong request TTL, missing and faulting mock clock;
- random distinct 256-bit challenge nonces, defensive copies of nonce and canonical binding digest;
- matching echo remains diagnostic only and cannot authorise human approval or WinCred;
- exact replay refusal; incorrect nonce, changed peer fingerprint, session ID, request ID, candidate digest, operation, or expiry all sticky terminal refusals;
- reply exactly at expiry refused, rollback refused, clock exception burns attempt;
- revoke and synthetic fault terminal refusal;
- 16 concurrent echo attempts yield at most one diagnostic marker, and 64 races between concurrent echo vs revoke produce exactly one terminal result;
- deletion vs save operation binding and real P49/P112 effect-gate denial.

Previous **240** P118/P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 focused Windows cases MUST be preserved unchanged, including P96 15 fake-only cases reproducing original revocation/effect race. Expected native focused total: **267 (27 + 240)**. Tests must run exclusively on hosted unprivileged Windows; use exact GitHub SHA and pinned historical candidate and original SHA checks, no unsigned native EXE on Kristian.

## G0–G6 and next true integration

G0 external qualified Windows security review not received.
G1 true authenticated service IPC, trusted signed production installed UI/publisher pin, OS-verified live loaded image, defensible interactive human presence, service-owned clock and challenge, protected durable one-use operation grant not implemented. This synthetic challenge is only a candidate protocol state-machine starting point.
G2 atomic service-owned protected native WinCred effect transaction absent; P96 original check-to-effect race OPEN.
G3 protected antirollback journal/HKLM and reboot/crash recovery absent.
G4 separately authorised real pending-only WinCred validation absent.
G5 production signed artefacts and Kristian Smart App Control validation absent.
G6 qualified independent release, three full Windows product regressions and original Google Drive master workbook-first/dashboard release sync absent.

**P120 development focused native test checkpoint does not clear any production gate. BYOK C1 PRODUCTION RELEASE HOLD.**
