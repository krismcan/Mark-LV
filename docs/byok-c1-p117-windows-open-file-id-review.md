# BYOK C1 P117 — Native Windows opened-file object identity (128-bit), no trusted consent

Date: 9 November 2026 | OM v2.1 | Direct exact base: P116 `909c260fecc087fd6600fb1e758dbc327492879e`.

## Scope

P117 narrows a specific unresolved G1 ambiguity: a *reported executable path* is not a stable identity of a file, and a valid Authenticode signature for some path would not demonstrate that the same file object backs the executable section already running in the peer process.

The new `WindowsPipeClientFileIdentityReview` queries a **read-only file handle**, using genuine Windows `GetFileInformationByHandleEx(FileIdInfo)` to obtain an OS **128-bit file ID** plus volume serial number, and `GetFinalPathNameByHandleW` to observe the final resolved file path. The result stores file ID/volume in test-only in-memory data and does not log paths or account SIDs. FileIdInfo avoids a 64-bit file identifier truncation problem on ReFS. This identifies an *opened file object*, not an application publisher or running memory-mapped image.

`ObserveConnectedClientFileOnly` derives an untrusted current executable path from P114's actual connected pipe OS PID and P115's process-token session/integrity observation; it checks matching PID and process creation timestamp before opening the file. It **cannot** prove that the opened file handle is the same kernel image-section file mapping still executing in the client. The process may exit, the path may be replaced/reparsed, files may be hardlinked, IDs may be reused over time, and separate P114/P115 handles create additional races. Therefore this module **NEVER** turns an OS file ID into authorisation.

## Absolute denials

For every result, even valid OS file ID:
- `MappedImageSectionBoundToInspectedFile=false`
- `ApprovedPublisherTrustAnchorConfigured=false`
- `SignedTrustedConsentImageVerified=false`
- `ExplicitHumanConsentVerified=false`
- `ProtectedOneUseGrantIssued=false`
- `NativeCredentialEffectAllowed=false`

P116 native WinVerifyTrust negative evidence is unchanged and not combined to issue any actual positive consent decision. Signed publisher pin, independently reviewed file identity attestation, approved immutable installation root, trusted interactive desktop and specific human-click-to-one-use grant all remain unavailable.

## Native test scope

14 new unprivileged hosted Windows tests cover null/empty/relative/missing/directory rejection; genuine 128-bit OS file ID readback on temporary files; stable identity across reopening the *same* file; distinct identities for simultaneous different files; zero-byte identity without signature authority; OS resolved-handle-path observation; null/disconnected pipe; real same-process and distinct child-process pipe clients. Temporary files are created ONLY in isolated GitHub-hosted runner temp and removed. The child EXE is unsigned and executes only on hosted Windows; Smart App Control on Kristian is untouched.

Require all earlier **212/212 native focused P116/P115/.../P96 cases** unchanged; new total **226**. Retain P96 15/15 fake-only reproduction of original revocation-to-credential-effect race. Frozen 11 P49 native C# source SHA-256 plus review candidate/driver pins must remain intact. No privileges, real keys, WinCred, HKLM or protected journal writes.

## Open production gates

G0 independent qualified Windows native security review absent.
G1 signed installed consent UI with service-owned publisher/trust root, binding real loaded executable image to verified signer *and* protected installation/file object, authenticated service-owned IPC and safe session/desktop assurance, exact approved operation and user click, durable consumed one-use permission absent.
G2 P96 vulnerable effect coordinator still excluded, no atomic service-owned native replacement.
G3 protected antirollback/journal enrollment + recovery open.
G4 privileged pending-only real WinCred lifecycle open.
G5 signed production binary + Smart App Control review open.
G6 full triple Windows product regressions, independent release approval and Drive master workbook-first release reconciliation open.

No GitHub merge/release, original worktree edits, unsigned host executable run or settings change. P117 is **review-only OS file identity**, not production G1 acceptance.

Microsoft references:
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandleex
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-file_id_info

**BYOK C1 PRODUCTION RELEASE HOLD.**
