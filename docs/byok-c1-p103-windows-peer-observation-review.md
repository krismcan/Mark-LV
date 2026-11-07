# P103 — Actual Windows Named-Pipe Peer Identity Observation (NO C1 AUTHORITY)

**Date:** 7 November 2026 | **Operating model:** OM v2.1
**Status:** Nondeployable native Windows identity-observation review component. BYOK C1 production **RELEASE HOLD**.

## Engineering objective and exact scope

P102 added an immutable nonsecret **caller-supplied** request identity (operation, session/request identifiers, *claimed* candidate digest, expiry, delete acknowledgement) to a nondeployable, denial-only native C# host. This is not user consent. **P103 adds one real Windows OS boundary**: a disposable, access-controlled named-pipe server used only in a native test assembly, which observes the connected client's OS-issued SID using `NamedPipeServerStream.RunAsClient`. The server **only sends the literal ASCII `DENIED`** and is not used to issue approval or receive candidate key bytes.

All original P49 service/WinCred source files, P99 source pins, P101 nondeployable host source, P102 request binding and P85 historic exact-source gate remain unchanged. P103 adds a separate `native_c1_candidate/ReadOnlyWindowsPeerObservation.cs` and `tests/p103_os_peer_identity/WindowsReadOnlyPeerObservationTests.cs`, this review note, and an x64-only CI workflow. It does not edit the P101 candidate host, actual protected ledger, credential adapter, UI, installers or active product.

## Actual native Windows OS mechanisms exercised

- Test creates a fresh random `NayeonP103ReadOnly_<32 lowercase hex>` named pipe via a `NamedPipeServerStream` with Windows `PipeSecurity`; rejects arbitrary pipe names before creating any listener. There is no stable shared product endpoint.
- Pipe security contains **exactly three deliberately defined allow SID entries**: current test user's Windows SID, LocalSystem and BuiltinAdministrators. Never adds `Everyone` or `AuthenticatedUsers` group access. This test ACL **does not constitute a production LocalSystem service IPC policy**, and built-in administrators can access the test pipe by design.
- Actual temporary Windows named-pipe test client connects using Windows OS client impersonation level and reads only six bytes: `DENIED`. It sends no API key, consent ticket or data.
- Server uses `RunAsClient` to query the client-associated Windows security token's SID; detects whether the test user identity is observable. It never turns that SID into a one-time approval. A client with the *same* SID (including same-user malware) remains untrusted.
- The test feeds the observation to the separate P102 native service-host candidate and proves a structurally valid request still returns `Denied`, with `NativeEffectEnabled=false`, `AuthenticatedConsentAvailable=false`, `ProductionReleaseEligible=false`.
- Any failure to observe peer identity cannot mint authority, and the only possible wire response from a successful session is `DENIED`. This is not an authenticated production request dispatcher.

### Explicit limitations (not solved by P103)

1. **Same-user malicious client:** Windows SID identity alone does not establish interactive user intent, an approved UI ceremony, a trusted client process, integrity level, process signer, or unforgeable user-consent event. An attacker running as the same Windows user might connect to a permitted pipe. **G1 HIGH remains OPEN.**
2. **Pipe lifetime and namespace:** disposable random test names, test-user ACL, one connection and basic impersonation do not establish secure LocalSystem installation, name squatting resistance, client PID/session signer integrity, user elevation boundaries, trusted service restart or an operational authenticated named-pipe protocol.
3. **Input and authentication:** P103 accepts **no** user message or key. It does not bind the OS SID to a P102 session/request identity, an operation, candidate hash or one-use signed approval. Metadata remains untrusted.
4. **Race/credential custody:** original P49 `PendingCustodyTransaction.Apply` still contains the real P61 MEDIUM post-consent-revocation check-to-effect race, demonstrated by P96 fake-effect native tests; P97 model does not fix production. The actual WinCred adapter, protected journal/HKLM anchor/recovery and all three literal native admission denial guards remain untouched and disabled.
5. **Platform security:** Kristian's P97 x86 test binary was denied by enterprise Windows CodeIntegrity policy events 3077/3033; P103 **must not** use any x86 execution, repackaging or policy bypass. Historical OpenAI Support P62 restricted operation remains untouched.
6. **Independent review/release:** no real, qualified external native Windows security reviewer has provided the G0–G6 source-specific GO. Native test results, even on GitHub Windows machines, are not independent source security approval. Three full native product regressions and original same-ID Drive master/dashboard updates are release-only work after qualified GO.

## Native x64 acceptance evidence and future review questions

Compile the **ten exact unchanged original P49 native source units**, the P101/P102 review-only host, service-owned denial boundary and immutable request class, plus P103 read-only observer and tests. Test genuine Windows ACL SID rules, reject invalid names, real OS token observation across disposable pipe sessions, untrusted same-user peer denial, no credential authority, and unchanged native safeguards. Run repeated x64 Windows cases and affected Python3.12/3.14. External CI pins exact source identity/parent and repeats the actual named-pipe test.

A real independent reviewer must evaluate proposed **LocalSystem** ACL and elevated trusted UI design, malicious same-user process/handle/token attack model, client process PID vs token identity, session switching/UAC, impersonation level, pipe namespace and ACL parent objects, one-use consent issuer, replay persistence and lock ordering. This test does not settle any of them.

**P103 complete criteria:** actual OS identity observed and **always denied**, zero native credential effects, original source unchanged, x86 held and C1 release HOLD. Do not merge/install or request a real API key.
