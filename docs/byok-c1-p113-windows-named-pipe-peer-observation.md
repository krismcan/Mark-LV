# BYOK C1 P113 — Windows OS pipe-peer observation, not human consent

Date: 8 November 2026 | OM v2.1 | **G1 authentic client-token observation increment; G1 production human consent still NOT implemented**

## What is real in P113

The earlier P102 `ServiceBoundRequestIdentity` contains caller-controlled session ID, request ID, request digest, expiry and delete acknowledgement. Those values can validate *shape*, not trusted application or human identity. To avoid treating claimed metadata as authenticated, P113 introduces a separate **real Windows named-pipe peer-impersonation observer** in `native_c1_g1_peer_review/WindowsPipePeerObservation.cs`. It does **not** modify the existing P112 strictly read-only candidate service or original P49 source.

The actual implementation takes **only a pre-existing, connected `NamedPipeServerStream` handle**. It never creates/listens on a pipe, chooses a connection identity, accepts a claimed SID/PID or process image, handles an API key, performs P/Invoke or launches a privileged service. After a client has written at least one bounded nonsecret byte (enforced by the test fixture), it calls Windows/.NET Framework `NamedPipeServerStream.RunAsClient`. Inside the impersonated thread it obtains `WindowsIdentity.GetCurrent(true)`—*not* the service process's own token—requires authenticated client token and `Impersonation`/`Delegation` level, and records the **OS-observed** client SID only in private in-memory test data. Invalid/missing/disconnected handles, inadequate impersonation level, token ambiguity, and all exceptions lead to `Unavailable`.

Microsoft's documentation states that the client must write at least once for its impersonation token to become available; `RunAsClient` uses the connecting client's Windows permissions on the server thread. References: https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.namedpipeserverstream.runasclient ; https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.namedpipeclientstream.-ctor

### Distinguish exactly what token evidence can and cannot prove

**CAN:** Establish an OS-reported Windows account SID and impersonation level from a particular connected pipe client in an unprivileged test environment, independent of caller-supplied name/digest/SID. This is a foundational peer-identity signal for future authenticated IPC.

**CANNOT:** Verify the signed installed caller executable and exact user-desktop application provenance; prove the user was presented the exact pending operation and pressed Approve; authenticate a trusted elevated human-consent broker; verify active desktop/session/integrity or pipe-server provenance; create a server-originated durable single-use approval or bind it to the fixed target/hash/transaction; establish a historical antirollback witness; or authorize native WinCred. **The OS SID alone MUST NEVER be used as consent or a release gate.** Reused user SID across arbitrary processes is not human confirmation. The `OsPipePeerObservation` object always has `TrustedClientImageVerified=false`, `HumanConsentVerified=false`, `OneUseGrantIssued=false`, `CanAuthorizeCredentialEffect=false` regardless of OS token success. SID not logged or included in `ToString()`.

## Native executable test scope and limitations

`tests/p113_real_windows_pipe_peer/NativePipePeerIdentityTests.cs` creates a fresh random-name **temporary local unprivileged pipe fixture** with Windows `PipeSecurity` allowing the runner account. It accepts a one-byte *nonsecret* handshake and uses `NamedPipeClientStream(...TokenImpersonationLevel.Impersonation)` to provide real OS client token to server. Fourteen focused cases assert null/disconnected fail-closed, real OS impersonation vs actual runner user token, no trusted signed UI, no human click or single-use grant, identification-level inadequacy not authorizing, no caller-supplied peer ID arguments, no WinCred/issuance APIs, no production listener, original service/effect holds, and exact separation between OS peer identity and untrusted request identity. **This is real Windows IPC execution but not a real privileged service, signed UI or legitimate user consent.**

Run on isolated, non-LocalSystem GitHub-hosted Windows 2025 runner only. No pipe server is created in P113 candidate library itself. Pin exact source SHA-256/commit and original P49 source identities. Also preserve the existing **156/156 P112/P110/P109/P108/P106/P99/P96** native regressions unchanged; total expected **14 + 156 = 170** genuine Windows native tests. The 15-case original P96 fake-only negative comparator remains explicit proof of the legacy check-to-effect vulnerability, not a fix.

## Next production G1/G2/G3 requirements

A qualified independent Windows security reviewer must approve a signed installed interactive human broker; an authenticated IPC endpoint with least-privilege ACLs, independently verified client binary signing and exact application origin, user session/integrity provenance, request/operation/nonce binding and protection from same-user malicious peers; explicit human review/consent to a fixed pending-only operation; service-issued, independently durable and one-use consumed approval; and G2 atomic terminal dispatch with the trusted OS custody mutex/WinCred effect path. The new real OS token observation is **necessary context but not sufficient** for any of this. Real UI and the privileged service are not activated, installed or simulated as "approved".

P113 adds **no actual API key, real WinCred, protected journal/HKLM write, broker executable, privileged listener, Windows security change, production release, GitHub merge or Google Drive master/dashboard edit**. Kristian Smart App Control remains enabled; never rerun original P62 blocked tool operation. Original 17 product dirty paths preserved and exact P112 read-only source baseline retained.

**P113 = real local OS peer-identity observation foundation only. G0–G6 and C1 production release HOLD.**
