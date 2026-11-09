# BYOK C1 P119 — G1 independent security review agenda and adversarial acceptance matrix

Date: 9 November 2026 | OM v2.1 | **Review requested; NO independent reviewer has accepted or approved it.**

This is a **source-driven review pack**, not a native test execution and not a completed G0/G1 gate. Baseline: P118 `e12c7b2c8c8a1049c2e636a528391c57619b488e`, focused hosted-Windows evidence 240/240; draft PR #43 remains open. P96 still reproduces the original revocation-to-effect flaw.

## Explicit threat boundary

**Adversary classes:** (A) arbitrary process under same Windows account, (B) different-account/remote/low-integrity or AppContainer process, (C) attacker with write/replace access to user-controlled executable path or DLL, (D) stale/reused process or transferred pipe handle, (E) malicious or compromised UI in the same interactive session, (F) process termination, reboot, replay or concurrent terminal transitions.

**High-priority research question:** Can an ordinary interactive app on the user's regular desktop provide an independently defensible confirmation of exact credential operation against a malicious process already running as the same user? If not, the architecture must use stronger OS-controlled user presence or explicitly narrow the adversary assumption. **Do not implement a fake guarantee or treat process image metadata as a substitute for this answer.**

## Review matrix — every positive grant remains disabled until signed evidence and external acceptance

| ID | Attack / ambiguity | Required negative test or evidence | Gate |
|---|---|---|---|
| R01 | Same-user unsigned binary opens IPC | Must never be accepted merely by account SID/session | G1 |
| R02 | Same-user arbitrary signed Microsoft binary connects | Authenticode OS success without *approved publisher/app pin* refuses | G1 |
| R03 | Caller forges PID, SID, path, session, signature boolean or operation hash | Only OS/service-originated authenticated fields considered | G1 |
| R04 | Pipe handle inherited, duplicated or passed to new process | Connecting PID must not be assumed to identify message author; independently prevent/deny transfers | G1 |
| R05 | Process exit, PID reuse or late disconnect | Fail closed with bounded process lifetime and connection proofs | G1 |
| R06 | Path junction, symlink, hardlink, reparse or on-disk replacement | Signed inspected file object must be bound to approved installed image, not merely string path | G1 |
| R07 | P118 holds one file handle for OS file ID and WinTrust | Must not be misrepresented as attesting the running image-section file object | G1 |
| R08 | Signed executable loads untrusted DLL / side-load | Broker's full trusted deployment + dependency policy independently reviewed | G1/G5 |
| R09 | Signer chain revoked, expired, test signed, wrong EKU, wrong certificate or timestamp abuse | Approved offline/online revocation policy and pin validation; refuse ambiguity | G1/G5 |
| R10 | Certificate/key rotation or signed binary rollback | Authorized enrollment, version/rollover/antirollback witness and rollback refusal | G1/G3/G5 |
| R11 | Different account, wrong Windows session or mismatched integrity | Explicitly refuse unapproved principals/sessions/integrity/app-container | G1 |
| R12 | Secure desktop switch, RDP session switch, session lock/unlock | User-presence model must bind exact current authorised desktop/action | G1 |
| R13 | Window spoofing, overlaid click, simulated input or consent response forged by same-user process | Reviewer-approved human presence, no unchecked click boolean | G0/G1 |
| R14 | UAC elevation prompt appears without exact operation display | UAC is **not** a one-use credential consent grant | G1 |
| R15 | UI renders different target/hash than service-accepted request | Fixed canonical operation bytes and display digest must match | G1 |
| R16 | Challenge replay, concurrent approval, close/reopen, expiry or out-of-order response | Service-issued challenge bound to one request/session/connection, consumed exactly once | G1 |
| R17 | Service crashes between durable grant and dispatch/revoke | Protected intent/terminal outcome and crash recovery, fail-closed | G1/G2/G3 |
| R18 | User revokes after old coordinator StillCurrent() then before effect | Preserve actual P96 negative race; replace with service-owned atomic actor | G2 |
| R19 | Real WinCred save/delete attempted in isolated runner or Kristian | Forbidden until separately authorised signed privileged integration | G4/G5 |
| R20 | Independent source review, 3 complete product Windows regressions or Drive master reconciliation missing | Refuse release and preserve exact historical source/evidence | G0/G6 |

## Reviewer deliverables

1. Signed threat model explicitly naming the attack classes and same-user malicious process guarantee.
2. Documented Windows supported mechanism for exact live image / signed installed executable binding, including image-section-to-file evidence or an alternative service-controlled launch and trust mechanism. Cite exact Windows API semantics and known TOCTOU windows.
3. Concrete G1 signer trust anchor configuration/rotation/revocation mechanism and protected installation identity independent of caller claims.
4. Account/session/desktop/UI authenticity and *actual human intent* design, with exact displayed operation-to-one-use grant binding and refusal semantics.
5. Independent critique of source in P113–P118; identify any security-sensitive P/Invoke marshalling, process/token handle leaks, path follow, WinTrust provider-state, file-system identity and network-revocation issues.
6. Required safe native Windows hostile tests, signing prerequisites, gating strategy, distinct G2/G3/G4 implementation contract and independent release approval path.

## Evidence source index

- P113 PR #38, real pipe client token (170/170).
- P114 PR #39, OS client process provenance (184/184).
- P115 PR #40, pipe/session and token integrity (198/198).
- P116 PR #41, actual unsigned WinVerifyTrust denial (212/212).
- P117 PR #42, actual file object FileIdInfo (226/226).
- P118 PR #43, same-handle FileIdInfo + WinTrust (240/240).
- All PRs remain review-only draft; previous numbers are successive **focused** test totals, NOT full product release regression certifications.
- Original P96 fake-only negative coordinator 15 cases MUST remain reproducing the known defect.

**No reviewer is named, accepted, or has independently certified the design. No signed production UI, protected one-use grant, privileged service, real key, WinCred, release or master Drive update has occurred. G0–G6 remain OPEN.**
