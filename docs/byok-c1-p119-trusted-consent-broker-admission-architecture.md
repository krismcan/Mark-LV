# BYOK C1 P119 — G1 trusted consent broker admission: architecture for qualified external review

Date: 9 November 2026 | OM v2.1 | Source baseline P118 `e12c7b2c8c8a1049c2e636a528391c57619b488e`

**Status: DRAFT ARCHITECTURE / REVIEW REQUEST, NOT G0/G1 APPROVAL.** No positive human consent, signing key, API credential, native effect, or privileged service is available.

## Why this checkpoint is essential

P113–P118 established **OS observations**, not trust:
1. Real named-pipe impersonated client token SID, never consent (P113).
2. Pipe kernel client PID, process create time, path, token SID (P114).
3. Pipe session, token session and mandatory-integrity RID (P115).
4. Native WinVerifyTrust file signature policy with no approved publisher root (P116).
5. OS opened file-object volume and 128-bit FileIdInfo (P117).
6. FileIdInfo before/after native WinTrust using the same open file handle with a process handle held across inspection (P118).

A file may be signed by an arbitrary publisher, a path may be redirected, a PID may become stale, a caller handle may be transferred, a malicious same-user process may spoof ordinary UI, and a Windows user SID alone is never a positive consent event. None of these evidence classes attests the process's actual loaded kernel image section or proves that a human intentionally approved the exact pending-only operation.

## Proposed trust-root ownership and acceptance sequence (DESIGN ONLY)

**Authority:** A separately security-reviewed privileged C1 service would be the sole owner of the pending credential target, challenge generation, admission policy, approvals, grant consumption and eventual custody transaction. It must never accept caller-supplied booleans like `Signed`, `TrustedWindow`, `HumanApproved`, `CanWriteCredential`, claimed PID, claimed image path or claimed SID as authority.

**Signed installed broker:** The eventual interactive consent broker must be a production-signed executable installed in a protected machine-wide location with an independently validated ACL and tamper-controlled updater. The exact signing chain, policy, key lifecycle, approved publisher/public key, certificate rollover/revocation checks, version and rollback controls must be formally approved. Authenticode success without a **service-owned pinned trust anchor** is insufficient. User-writable paths and side-loaded DLL dependencies must be excluded/mitigated; Smart App Control must remain enabled.

**Connection identity:** Use a service-created pipe listener with verified least-privilege ACL, attack-resistant name/instance design and security descriptor. Bind each accepted connection to real Windows OS peer account and process evidence, process lifetime, session, token integrity, installed-broker provenance and per-request challenge. Treat pipe handle passing/duplication and process replacement as threats. Repeated PID/path/file-ID observations alone are insufficient for exact mapped-image attestation; a separate, independently reviewed Windows image attestation or service-controlled broker launch strategy is required before any admission method can ever become positive.

**Interactive human approval:** Service generates a fresh high-entropy one-use challenge with short service-clock expiry and immutable canonical operation payload (operation kind, fixed pending target, request identity, digest, display text, expiry, transaction version). Broker must render the exact immutable operation on an appropriately trusted interactive surface, then bind a fresh response to **the same connection/session/process and request**. A returned signature or message from a broker does NOT itself prove a physical click on a trustworthy desktop. The qualified reviewer must decide and document whether an ordinary user desktop can meet the adversary model, or whether a secure Windows system interaction / separate protected user-presence mechanism is required. A generic UAC elevation prompt is NOT approval of the exact credential operation.

**Grant custody:** Service validates freshness, origin and user presence and issues an independently protected, durable, single-use, operation-bound decision with an unambiguous consumed/revoked terminal state. Failed/ambiguous verification must become sticky refusal, not a reusable pending positive. G1 success cannot dispatch actual native effects until a separately reviewed G2 service-owned atomic transaction actor replaces the original P96-vulnerable check-then-effect design. The old `PendingCustodyTransaction.Apply()` remains excluded.

## Mandatory explicit blockers

- No trusted production signer/publisher root, signed installed UI executable or approved ACL-managed installer.
- No approved immutable mapping between connected process **loaded image section** and exact verified signed file.
- No independently accepted assurance of real, intentional human interaction with exact operation; same-user malicious UI spoof / injected input / switched desktop unresolved.
- No service-owned authenticated IPC listener deployed, session-matched challenge protocol, nonce anti-replay or protected one-use decision.
- No independent Windows security reviewer named/approved; G0 cannot be cleared internally.
- P96 original effect/revocation race remains reproduced in native fake-only negatives; G2 cannot pass with original coordinator.

## Proposed G1 acceptance criteria for independent reviewer

The reviewer must explicitly sign off on the threat model, signed broker identity and certificate rotation/revocation policy, protected install and process-image binding, OS broker/pipe trust, user-presence mechanism, exact pending target display, replay/downgrade controls, failure/recovery behaviour and compatibility with SAC. Evidence must include separate genuine native negative tests against untrusted same-user clients and adversarial session/process/image replacement, plus explicit production signed component validation. Without signed production artefacts and approval, positive acceptance stays **NOT IMPLEMENTED**.

**Test boundaries:** New work may develop fail-closed architecture, pure synthetic tests, isolated unprivileged Windows test executables on GitHub-hosted runners, source integrity checks and draft PRs. Never test real keys, install privileged service, disable SAC, enable old WinCred effects or merge/release without new authority and independent review.

## Gate ledger

G0 — qualified independent native security review OPEN.
G1 — signed consent broker, app provenance, user intention, durable one-use approval OPEN.
G2 — atomic native credential dispatch/revocation successor OPEN (P96 race persists).
G3 — protected journal/HKLM antirollback/crash recovery OPEN.
G4 — privileged pending-only WinCred lifecycle OPEN.
G5 — production signing and Smart App Control acceptance OPEN.
G6 — three complete Windows product regressions, independent release approval and original Google Drive master workbook then dashboard synchronization OPEN.

P119 is documentation/review-preparation. The existing focused native P118 result **240/240** is unchanged, not an approval or a new test run.

**BYOK C1 PRODUCTION RELEASE HOLD.**
