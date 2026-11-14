# BYOK C1 P205 — Real-Key Gate vs Production Release Gate: Independent Approval Decision Package

**14 November 2026 | OM v2.1 | H/C/R = HOLD / native reality and external approval package / HOLD**

## Two genuinely separate milestones

**R — Real-key pilot admission (NO-GO today).** This authorises ONE explicit local Windows trusted UI operation with a real provider key on a reviewed signed, installed candidate, *not* a production release or provider validation. It requires approved independent signer/trust root and target machine install policy; authenticated distinct service/UI principals and IPC; nontransferable user approval bound to exact key bytes/operation/target; durable one-use consumption and revocation; single service-owned terminal dispatch with verified journal/HKLM protected anchor; sticky uncertain-outcome recovery, exactly-once attempt and manual recovery policy; readback/absence semantics; original source trust including modern Phase10/P76 and ADS; scoped test logs with no secrets; qualified G0–G5 review. Permission cannot be inferred from a signed interpreter, a source SHA, same-user SID, a local fake token or selected CI tests. Real key is entered **only in local approved UI after explicit user's local action**. Do not place the key in ChatGPT, test artifacts, GitHub or email.

**P — Production release admission (NO-GO today).** This happens AFTER R and requires complete integrated source, signed product main/helper/installer and actual Code Integrity/WDAC/SAC evidence for Kristian's authorised Windows policy, threat model and qualified independent GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 written positive signoffs, privileged G0–G6 GO, no unresolved product regression failures, and 3 *complete unfiltered* genuine native Windows product regression passes, not selected subset tests. Exact final release commit/manifest/tag/HCR, GitHub published release and original same-ID Google Drive MASTER workbook write/readback **before** dashboard. No automatic release from a test count.

**C2 provider validation is separate**; it is not enabled merely because a real key could eventually be stored.

## Source-specific current facts, not future promises

Exact final P204 source Git commit: 3d91358aa49b31b76db1bb130cf6fef22a800ac6, PR #129 draft/unmerged. Genuine exact-head Windows Actions 43584885068 SUCCESS, artifact 14110110651. ZIP SHA256 1D53C003E87303155A61142D2629888B73B5637C79357C00A09337AD1335CA2D, two original members CRC valid: p204_real_windows_source_set_9.log SHA 4C92E128DF0293266796581784B4B3D9A2906C17E43CA73C2A9CC501EDB8D9F2 and p204_readonly_source_set_HCR_ledger.json SHA 809A0EF1346D75C1C1AA6A655B041378EA2B618E9A786FE2A57C72B1FEBE8098. Selected actual Windows tests 9/9, source before==after, original full product 0/3, H/R HOLD.

**Native reality:** original frozen 11 P49 C# service source remains denied by ServiceGate.LiveEligible, original PendingServiceState.LegacyEffectEntryDisabled and original PendingWinCredStore.NativeMutationAdmissionPending. The current nondeployable native_c1_candidate/CustodyService.cs still has no Main or installed-service startup path; ServiceOwnedAdmissionBoundary.cs has no trusted issuer or native effect dispatcher. Original P96 post-approval-to-effect race is demonstrated by its historical negative; replacing bools with "true" is forbidden. P110/P111 artificial integer-effect synthetic cases are not native WinCred writes or a real trusted approval.

**Python legacy reality:** nayeon/secrets/windows_credential.py contains actual CredWriteW/CredDeleteW/ReadW capable code; it is **NOT automatically governed by the native C1 service denial gate**. The historical Tk UI uses a coordinator and has simulated tests, but real-key admission cannot assume it is an independently signed, trusted broker. A full product effect-entry inventory and retirement/containment of legacy direct backend calls is required before any integrated real-key pilot. Failing to integrate the Python and native paths would make a "ready" claim misleading.

**G0 current source reality:** the modern public route B → Phase10.1 → 10.2 → 10.3 → P76 offline prototype is branch-bound and does not grant effect authority. The historical full B original named NTFS ADS admission gap remains unpatched, while P201/P202 and P204 physical-source guards are dormant candidates only. P204 demonstrates two lasting unsafe findings: post-HANDLE-close path substitution and self-selected bytes plus re-pinned hash accepted merely as observation.

## Required decisions and ownership (no fake reviewer names)

| Gate | Required written artifact and actual responsible party | Current decision |
| --- | --- | --- |
| R0 — original current release/source authority | Product engineering + qualified independent Windows code-integrity reviewer: modern Phase10 release-root proof, trusted signed manifest, atomic or independently protected source custody, executable content identity | OPEN |
| R1 — signed UI/service/IPC and actual OS principal | Windows security reviewer: trusted publisher/revocation, enrolled service binary and approved UI, secure IPC/SDDL, token/session/impersonation/code-content identity and anti-spoof evidence | OPEN |
| R2 — one-use consent and atomic effect actor | Native security review: exact operation/target/bytes, service-owned revocation and terminal monitor, no legacy Apply bypass, crash/fault and no-retry proof | OPEN |
| R3 — protected durable custody and safe key lifecycle | Windows platform admin/security: installer enrollment and protected journal/HKLM independent witness, rollback, restart/manual recovery, WinCred pending-only target and user scope | OPEN |
| R4 — signed disposable pilot and human local consent | Windows machine policy owner + authorised local user: approved signed test install, reviewed UI, reversible/synthetic tests before any real key, explicit local operation | OPEN |
| P0 — integrated product source and effect-route inventory | Engineering and reviewer: all potential legacy Python/backend/native paths locked to approved gate and source | OPEN |
| P1 — all release security reviews | Independent GOV-01/02, SEC-03/04, REL-05/06/07 positive source-bound written decisions | OPEN |
| P2 — genuine full native Windows product regressions | Engineering/testing: fix original P135/P175/P178/P179/PERF-P187-01 failures; run 3 unfiltered complete acceptable product regressions | 0/3 |
| P3 — approved code signing + deployment | Windows policy owner: Code Integrity/WDAC/SAC allowlist and signed main/helper/installer/service/provenance, no bypass | OPEN |
| P4 — custody, recovery and no-secret release review | Security/release management: exact signed release branch SHA, readback, zero secret leakage, rollback/recovery tested | OPEN |
| P5 — publish, repository and Drive release reconciliation | Authorised release owner: final merge/tag/GitHub release; same-ID Drive MASTER workbook update/readback before dashboard | HOLD |

## Executable evidence created in P205

On genuine hosted Windows (without accessing the user's credential store), source-owning P205 collector reauthenticates the P204 exact ZIP hashes and selected 9 native cases and verifies Git ancestry with exactly three additive review paths. It also compares the **11 frozen original P49 C# source SHA-256 pins**, compiles the original P49 full service under actual native x64 C# compiler and runs its original 20 denial tests, then compiles the contemporary candidate host with 10 original P49 units plus five actual native C1 candidate modules and executes its original 24 denial tests. Additional source audit cases explicitly distinguish the Python Credential Manager API from any absent native C1 trusted effect gate. All C# compilations and native executions run under ordinary hosted Windows user and write bounded nonsecret logs, actual OS exit and log hashes; original frozen code/Phase10/current native candidate remain untouched. H/C/R must remain HOLD even when these selected tests pass.

**Disallow:** any attempt to force a current C1 permit by toggling release booleans, disabling Smart App Control/WDAC, installing unreviewed service, altering frozen tests, self-minting security review GO, claiming P96 solved, writing real credentials, calling providers, or treating 44 native selected source-denial cases as a full product regression.

## Next implementation steps that do not require dangerous privilege

1. Build an explicit **native-versus-Python effect-entry ownership inventory** and a dormant, fail-closed product integration seam; no direct legacy key writes via an unreviewed UI.
2. With independent design approval, implement successor signed consent broker, protected one-use approval, same-actor terminal lock/effect state and durable recovery using **synthetic only**, with actual Windows source, OS exit and crash tests.
3. Prepare machine-specific signed pilot acceptance for authorised Windows policy owner; do not deploy to Kristian before approval.
4. After external reviewers respond, resolve their line-specific findings and repeat current native tests, then three complete unfiltered full product regressions, then separately open R and P.

**Decision package prepared, not externally submitted or approved.** Qualified reviewer identities and machine signing authority have NOT been supplied; no assistant-generated markdown substitutes for those decisions. P205's own automated verdict must remain real-key **NO-GO**, production **HOLD**.
