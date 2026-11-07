# P103 — Genuine Windows Local IPC Peer-Identity Negative Proof (Nondeployable)

**Date:** 7 November 2026 | **Project:** Nayeon v1 BYOK C1 | **Model:** OM v2.1
**Disposition:** unprivileged OS-primitive experiment and review-only native C# evidence, **NOT** a trusted approval implementation; **C1 production HOLD**.

## Why P103 exists

The P100 independent security review gate G1 is **HIGH**: a privileged local Windows service must only accept operation-bound, one-use, elevated user consent from a trusted approval UI via authenticated IPC. The original P49 service's eleven C# source files have no concrete `ITrustedPendingApproval` implementation and no service IPC listener. P102's immutable session/operation/request/digest/expiry metadata is explicitly **untrusted caller input** and never a consent ticket.

P103 experiments with **real Windows local named pipes and native Windows peer impersonation on Kristian**, rather than purely simulated IPC. The experiment is intentionally **not connected** to the Nayeon v1 Windows service, P49 transaction coordinator, WinCred adapter, persistent journal/registry anchor, secure key entry, or provider. Its purpose is to prove the limits of low-level OS peer identity and to obtain reproducible source for qualified independent review.

## Exactly what the native Windows code does

The additive C# file `native_c1_candidate/DisposablePipePeerEvidence.cs` creates a unique, randomly named **unprivileged per-test local** `NamedPipeServerStream`. Its Windows DACL protects the pipe with a current-user allow rule and protected inherited rules. A short-lived test client connects locally with `TokenImpersonationLevel.Impersonation` and transmits exactly **one synthetic byte**, never a credential or API key. The server uses Windows `RunAsClient` and `WindowsIdentity.GetCurrent().User` to observe **the real OS impersonated peer SID**, then returns **only a denial byte**, regardless of whether the SID matches the current user or the client sends a fabricated “trusted UI” sentinel `0x54`. Neither the SID, username nor claimed message is logged.

The type `DisposablePeerObservation` records only nonsecret `bool` results indicating whether the Windows token was observable, whether it matched the current user, whether the synthetic sender asserted a fake trusted-UI claim, and whether an OS security exception arose. It has **four immutable NEVER-TRUE authority flags**: `VerifiedTrustedUi`, `ElevatedConsentGranted`, `CanDispatchNativeEffect`, `ProductionEligible`. There is no method which grants trusted consent or native effects.

Native x64 test cases cover Windows peer token observation with exact same-user SID, protocol sentinel forgery, benign/zero/max byte payloads, no secret/log disclosure, distinct disposable sessions, concurrent real named-pipe pairs, original native P49 release/legacy/WinCred denial switches, existing P102 bound-request refusal and no service `Main`. This is a negative OS-identity proof, **not** authentication of an application or a consent ceremony.

## Threat-model and security limits

1. **Same-user is not same-app.** A malicious process running under the same SID can connect to a user-accessible pipe. Matching `WindowsIdentity` alone cannot distinguish the trusted key-entry UI or grant an operation-bound elevated user approval.
2. **A synthetic byte is never authority.** A caller-supplied string or one-byte value claiming trusted status is trivially forgeable; the server always returns denial.
3. **A protected user-only pipe is not a production LocalSystem service security design.** The disposable current-user DACL and process do **not** prove the correct installed service principal, peer/app attestation, deployment signing, DACL/ancestor ownership, elevation or consent provenance.
4. **The observed Windows SID is personal metadata.** It is not copied into reports, printed to CI or surfaced as a file; only booleans are retained.
5. **No secret or effect path.** No real API key, credential bytes, Windows Credential Manager `CredReadW/CredWriteW/CredDeleteW` execution, registry mutation, service install/start, provider request or privileged user approval.
6. **Do not promote this helper to production.** Its only safe purpose is a read-only, local negative peer-identity experiment. A real G1 design requires qualified independent review of trusted Windows service/client identities, signed UI provenance, one-use consent issuer, replay/expiry/operation binding and authenticated IPC. G2 actual revocation-to-effect dispatch and G3 protected recovery are still absent.

## Existing security/release holds

The original P61 **MEDIUM** native `PendingCustodyTransaction` check-to-effect race remains OPEN and reproduced in P96 fake-only Windows C# adversarial tests, even though P97 separately models a corrected lock. P101/P102 candidate remains nondeployable and unconditional refusal. The original P49 service's three hardcoded denial switches remain unchanged, as does the branch-specific historical P85 source-admission gate. Windows x86 executable execution was refused by Kristian's genuine Code Integrity enterprise signing policy in P97 (3077/3033); P103 must **not** attempt an x86 execution or workaround. The historical OpenAI P62 platform restriction must not be reconstructed or bypassed.

Independent qualified reviewer request and acceptance gates: [P100 G0–G6 review contract](https://github.com/krismcan/Mark-LV/pull/24#issuecomment-6709413936). No qualified reviewer has been assigned. GitHub repository Issues and Discussions are disabled, and publicly visible historical contributors alone do not establish qualified review authority.

**P103 expected disposition:** Windows local named-pipe peer observation and same-user spoof negative proof; G1 review evidence strengthened, **G1 still HOLD**, BYOK C1 production **HOLD**. No API key is required and no release/dashboard update is authorised.
