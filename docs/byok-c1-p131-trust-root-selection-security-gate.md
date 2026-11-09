# Nayeon v1 / BYOK C1 P131 — Independent G3 antirollback trust-root selection gate

**9 November 2026 | OM v2.1 | SECURITY-REVIEW PACKET — NOT APPROVED**
Direct exact verified P130 baseline: `f39c233e3287d86951438ef5993d7160badf0afa`.

## Reviewer decision: none has been approved

**NO production antirollback root has been selected. G0 and G3 are OPEN.**

P128–P129 proved actual nonsecret local file staged persistence and process death observations (but NOT power-loss atomicity). P130 proved that a separate unprotected file detects journal-only rollback if it remains intact, yet simultaneous rollback of both files remains undetectable and a deleted witness can be re-enrolled by the same principal.

The key security decision is **who can irreversibly change history, and who cannot roll it back**. Different file paths, different registry keys, unkeyed SHA-256 chains or even two ACL-protected records that are both writable by one compromised privileged service do NOT automatically establish an independent trust root. No positive service or credential admission is possible until independent qualified native Windows review establishes a defensible historical witness for the actual specified attacker model.

### Read-only Kristian platform observation

An explicitly **read-only** `Get-Tpm` status query on Kristian on 9 November 2026 observed `TpmPresent=True`, `TpmReady=True`, `TpmEnabled=True`. No index was created, read, written or incremented; no TPM command was submitted; no protected registry entry, WinCred, secret or service state was touched.

**This does NOT prove TPM 2.0 counter availability or that the intended signed application/service can access, define or increment an appropriate TPM NV index under Windows permissions.** TPM firmware command implementation, TBS access, driver command filtering, NV-index attributes/authorization, counter persistence, capacity, rate limits and device/firmware policy are different claims. A state-changing `TPM2_NV_Increment` is NOT authorised or attempted here. A future controlled capability test would need a dedicated signed test environment and explicit new approval for actual provisioning/mutation; an invalid-command probe cannot substitute for authorised valid increment evidence.

Relevant documentation:
- Microsoft TBS overview: https://learn.microsoft.com/en-us/windows/win32/tbs/tpm-base-services-portal
- Microsoft TBS shared resource/counter virtualization caveats: https://learn.microsoft.com/en-us/windows/win32/tbs/resource-virtualization
- Windows TPM status vs NV increment support/authorization discussion: https://learn.microsoft.com/en-us/answers/a/13023576
- Reference TPM2 NV increment semantics: https://github.com/microsoft/ms-tpm-20-ref/blob/main/TPMCmd/tpm/src/command/NVStorage/NV_Increment.c
- Event log security/access: https://learn.microsoft.com/en-us/windows/win32/eventlog/event-logging-security

## Independent trust-root options and explicit no-go conditions

| Candidate | Possible role | Critical limitations / verdict |
|---|---|---|
| Second local file, hash chain, HKLM value, normal Windows Event Log | Ordinary diagnostic / operational audit | **NOT independently rollback resistant** when controlled by the same principal or privileged local admin. Reject as sole G3 root. Local event logs can be cleared by appropriately privileged principals |
| Signed protected local journal only | Tamper detection against users without signing authority | Signatures do **not** by themselves detect rollback of an old valid signed file; separate monotonic history required. NOT sufficient alone |
| TPM 2.0 authorised NV monotonic counter + an authenticated journal-digest binding | **Conditional offline-first candidate** if actual target hardware, Windows APIs, NV permissions, ownership, provisioning, resets, wear/rate, and recovery can be supported | Kristian merely reports a ready TPM. No NV authorization, policy, index provisioning, counter rate/clear/replacement or signed service design validated. NOT selected or approved |
| Independently administered external append-only signed receipt/witness | **Conditional candidate** if truly outside the local service/admin rollback domain | Must have authenticated signing identity, append/read monotonic semantics, durability, time/ordering, idempotent replay rejection, secure enrollment, offline policy, cost/network availability and external operator; unknown/timeout means DENY. NOT selected or connected |
| TPM-bound anchor plus external witness | Defence in depth if properly independent | Complexity, operational dependencies and two-phase crash recovery require more independent review. Not assumed safer merely because it uses two components |

For an offline desktop assistant, **TPM-based historical indexing may deserve a qualified feasibility study first**, but that is not a production selection or a finding of API support. If the required TPM operation/authorization cannot be proven on a supported signed Windows target without weakening system protections, reject that option and review an independently operated external witness with strict offline denial. Do NOT silently downgrade to local hashes, writable HKLM or logs.

## P131 model — only a policy oracle for negative testing

`native_c1_g3_review/G3ThirdDomainWitnessReviewPolicy.cs` adds a deliberately compile-gated, unprivileged review-only *comparison contract*, not a TPM or external-service client. It receives:
- the existing P128/P130 disposable nonsecret journal + local unprotected witness observation;
- a **caller-provided synthetic** supposed external issuer ID, enrollment ID, service generation, monotonic counter, checkpoint stage and SHA-256 journal digest;
- equally **caller-provided** supposed pre-existing issuer/enrollment/generation/counter baseline.

The model classifies absent or invalid enrollment/root, missing/invalid local or external records, wrong issuer, enrollment, service generation, rollback or unexpected-future counter, local/external stage disagreement, digest fork, or a structurally consistent but **entirely UNTRUSTED** tuple. A test-supplied `ClaimedSignatureVerified=true` is **never** trusted as a cryptographic proof. No external signature, TPM attestation, protected monotonic counter, user click, real credential operation, protected storage or production service exists.

Every response has immutable `ActuallyIndependentWitnessAuthenticated=false`, `ActuallyProtectedHistoryVerified=false`, `GenuineRollbackResistanceEstablished=false`, `ApprovedHistoricalEnrollmentVerified=false`, `SignedServiceOrHumanAuthenticated=false`, `DurableOneUseGrantVerified=false`, `NativeCredentialEffectAllowed=false`, and `ProductionAdmissionAllowed=false`.

The policy does not solve TOCTOU between two independently read ordinary files; a positive structural result must never issue a grant. Its receipt fields are **test data only**, not an implementation of independent attestation.

## Reviewer-mandated contract before real implementation

A qualified, genuinely independent Windows security reviewer should approve an exact protocol and independent root, addressing all of:

1. **Threat boundary:** ordinary user, admin, compromised privileged writer/service, physical disk copy/restore, stolen signing key, remote witness operator, TPM reset/clear, motherboard replacement, VM cloning, offline mode. Explicitly list threats outside scope.
2. **Bootstrap and first enrollment:** immutable issuer identity, service installation/public key pin, owner SID, approved interactive enrollment ceremony, historic device generation and source of a trusted non-resettable root. Never allow ordinary first-run `create-if-missing` to declare security.
3. **Canonical external receipt:** version, issuer, enrollment, service generation, exact request identity/operation, authoritative monotonic counter, journal checkpoint stage, hash of canonical protected journal bytes, previous-receipt hash, immutable signer or TPM-certified binding, and expiration/revocation policy. Define signature verification and actual trust chain on opened handles; test model here implements NONE.
4. **Atomicity across media:** propose and reason about order of protected intent flush, independent monotonic advance, issuance/consumption of G1 consent, irrevocable pending-only G2 WinCred call and terminal checkpoint. Crash at each possible boundary must be **RECOVERY REQUIRED or DENIED** unless actual independently reviewed evidence proves safe. Do not claim hardware counter and disk files update atomically.
5. **Single writer:** service-owned OS mutex and same revocation/Stop lock through effect; signed service identity and hardened IPC, protected ACLs, no arbitrary effect callbacks. P124 duplicated pipe handles prove PID/session/nonce echo is not human consent.
6. **Compromised service:** identify whether a compromised LocalSystem writer can increment/forge/delete witness, reset index, change service generation or enroll a new root. If yes, specify residual risk and whether the trust root truly satisfies required model.
7. **Unavailable witness:** no implicit fallback to plain SHA256, same-user file, HKLM, Event Log or cached receipt. Network outage/TPM read error/permission denial/rate limit -> no new native effect.
8. **Recovery and rollback:** journal older/newer than witness, both journal and local witness restored, receipt rollback, missing/deleted witness, forked signatures, device clock rollback, reset/backup restore, TPM clear/replacement, software downgrade, signed binary replacement, concurrent instances.
9. **Operational readiness:** exact supported Windows build and OEM TPM/Pluton behaviour, TBS or documented TPM API command permissions, provisioning, user consent, maintenance/update/rollback SOP, offline policy, escalation and break-glass authority.
10. **Release gate:** independent reviewer signs the threat matrix, protocol, verified test plan and explicit NO-GO list; tests must then validate real protected trust root in an authorised sacrificial environment. P96 original negative comparator, original SHA pins and triple full Windows product regressions remain mandatory.

## P131 native focused test scope

34 new C# hosted Windows native focused negative/policy cases including missing/malformed issuer/enrollment/counter/digest, unexpected future/rollback counters, wrong generation, local/external stage mismatch, same-stage digest fork, false `ClaimedSignatureVerified` never authorising, immutable digest copies, dual local rollback with an intact separate synthetic receipt, **all local/external counter baselines rolled back together still consistent-but-untrusted**, and original P49/P112 actual no-effect denials.

The existing **440** P130/P129/.../P96 native focused cases are unchanged, including P124/P125 live pipe handle-transfer and P96 15 fake-only race reproduction. **Expected 474/474 focused native tests = 34 + 440**, NOT the three full product regressions. Compile ONLY with BOTH `C1_REVIEW_ISOLATED_ASSEMBLY` and `C1_SYNTHETIC_TEST` on an unprivileged hosted Windows runner; never run unsigned code on Kristian. No remote trust service calls and no TPM state changes.

## Mandatory gate ledger and disposition

- **G0 OPEN:** no qualified independent Windows security-review approval has been obtained.
- **G1 OPEN:** signed installed broker, trusted live mapped image, authenticated actual human exact-operation approval, protected durable one-use grant absent; duplicated HANDLE authorship attack confirmed.
- **G2 OPEN:** original frozen P96 revocation/effect check-to-call race still reproduces; fixed native approved WinCred actor absent.
- **G3 OPEN:** no selected, independently protected monotonic root, signed/authenticated external receipt, actual protected journal/HKLM, crash/reboot/power-loss recovery.
- **G4 OPEN:** separately authorised privileged pending-only native WinCred validation not performed.
- **G5 OPEN:** signed production binary/installer and Kristian Smart App Control admission not verified.
- **G6 OPEN:** three complete Windows product regressions, independent release and original Google Drive master workbook FIRST then dashboard reconciliation outstanding.

No real API keys, protected Windows writes/registry, actual TPM NV provisioning/increment, privileged service install, real WinCred, SAC policy modification, unsigned EXE on Kristian, historical P62 safety retry, GitHub merge/tag/release or nonrelease Drive master/dashboard edit.

**P131 = REVIEW CONTRACT AND HARDWARE STATUS OBSERVATION, NOT AN INDEPENDENT SECURITY SIGNOFF. BYOK C1 PRODUCTION RELEASE HOLD.**
