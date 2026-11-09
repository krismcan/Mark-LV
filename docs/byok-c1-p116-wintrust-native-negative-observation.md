# BYOK C1 P116 — Native Authenticode file-policy negative observation (not trusted UI)

Date: 9 November 2026 | OM v2.1 | Direct baseline: `a72d6d76c5a3d6941b3ef80966053014d28d4b4e` (P115).

## Purpose

P113 established actual Windows named-pipe client token/account evidence. P114 established kernel client process PID, creation time and loaded image path. P115 recorded Windows pipe/token session agreement and token mandatory integrity label. **None establishes signed trusted consent application provenance.**

P116 adds an isolated review-only native Windows code-signing policy probe using `WinVerifyTrust(WINTRUST_ACTION_GENERIC_VERIFY_V2)`, an **already opened read-only file handle**, `WTD_UI_NONE`, `WTD_REVOKE_WHOLECHAIN` and **`WTD_CACHE_ONLY_URL_RETRIEVAL`** to prevent uncontrolled revocation URL/network retrieval. Native success requires exact status code 0, not an HRESULT sign check. Native provider state is closed after verification. Unsigned or malformed files are expected to be rejected by the actual Windows OS policy. The file probe has no privilege elevation, native credential API, service listener, writable protected state or provider network call.

`ObserveConnectedClientFilePolicyOnly` first invokes the real P114 process-image-path and P115 session/integrity readbacks on the same **preconnected existing pipe**. It compares observed process PID and creation time across these independent results, then uses a read-only file handle to query signature policy for P114's observed path. This is **not** an atomic image-section / signing-file binding: image paths may be replaced/reparsed, P114/P115 hold different short-lived process handles, and signatures of arbitrary other signed executables do not prove this app was an approved consent broker.

## Mandatory denial-only trust scope

A `NativePolicyAcceptedButUnpinned` finding would only report that the OS accepted the inspected file's Authenticode policy in that environment. **It is NOT an approved trusted signer, installed application or human consent.** There is NO production service-owned trusted publisher pin, chain/policy specification, immutable approved installation root, handle-to-image-section proof, desktop/user click, protected one-use grant, or native credential effect authority. These flags stay false for ALL native outcomes:

- `ApprovedPublisherPinConfigured`
- `LoadedProcessImageFileIdentityBound`
- `SignedTrustedConsentImageVerified`
- `TrustedInteractiveDesktopVerified`
- `ExplicitHumanConsentVerified`
- `ProtectedOneUseGrantIssued`
- `NativeCredentialEffectAllowed`

Never treat a valid Authenticode result, matching SID/session/integrity, image filename, or supplied PID as permission to write WinCred. **No positive G1 production acceptance path exists.**

## Native Windows tests

14 NEW P116 cases: null/empty/whitespace/unrooted/missing/directory/zero-length fail-closed; native OS rejection of unsigned temporary data and EXE-extension forgery; actual compiler-produced unsigned test EXE rejection; no publisher pin; null/disconnected pipe; actual same-process and separate child-process OS pipe/image-policy observations. The temporary executable is launched only by unprivileged GitHub-hosted Windows tests; never on Kristian. A test-created current-user ACL local pipe transports only an inert one-byte handshake. No real credential, privileged listener, key, WinCred, HKLM, protected journal, signing bypass, or Smart App Control change.

Retain **198** earlier native regression cases unchanged, including P96 15 fake-only negative tests still reproducing the revocation-to-effect flaw. Expected native focused test inventory: **212 = 14 + 198**. Pin P49 originals, P112 no-effect candidate, and P113–P115 review-only source hashes.

### Security and release hold

G0: independent qualified native security assessment absent.
G1: signed consent broker and approved service-owned publisher/trust anchor not enrolled; code-signature revocation policy and trusted installation image-section binding require design + external review. Real session/integrity does not prove interactive desktop trust or an actual approving user action. Durable one-use service-owned grant absent.
G2: P96 race unchanged; old vulnerable original credential-effect coordinator remains excluded.
G3/G4: protected antirollback journal, crash recovery and real pending-only privileged WinCred lifecycle incomplete.
G5: approved signed app/service and Kristian Smart App Control acceptance incomplete.
G6: independent release approval, 3 full Windows product regressions, master Drive workbook and dashboard release reconciliation pending.

Microsoft native API guidance:
- https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust
- https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_data
- https://learn.microsoft.com/en-us/windows/desktop/SecCrypto/example-c-program--verifying-the-signature-of-a-pe-file

**P116 review-only native negative work, G1 still OPEN; BYOK C1 PRODUCTION RELEASE HOLD.**
