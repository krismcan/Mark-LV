# BYOK C1 P215 — Actual Windows Store Principal and Credential Persistence Ownership

**14 November 2026 · OM v2.1 · exact P214 baseline
`707e591417aa81b61ad9d97c6c90c0f5e7dec5ac`.**

**Classification:** source-linked native Windows engineering observation / fail-closed C1
admission, **NOT** an approved service-owned credential vault, real-key pilot
or production release.

## The unresolved security decision

Existing P132/P133 source-mode desktop Python can call
`WindowsCredentialBackend.put/delete`, which invokes live Win32
`CredWriteW` and `CredDeleteW` for the user's fixed target. That
path is *not* regulated by the existing native C1 service-hold logic.

Microsoft's `CRED_PERSIST_LOCAL_MACHINE` value (2) is explicitly a
credential scoped to logon sessions of **the same user** on that computer,
NOT a machine-wide credential accessible to LocalSystem or a new
dedicated service principal. A LocalSystem service is not associated with
the logged-in user. An administrator or service running under a distinct
token does not automatically access the interactive user's vault. Using
impersonation alone would reintroduce the same-user direct-client threat.

Microsoft source references:
- [CREDENTIALW Persist and current-user visibility](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw)
- [CredGetSessionTypes read-only maximum per-logon-session capability](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credgetsessiontypes)
- [LocalSystem is not associated with an interactive user](https://learn.microsoft.com/en-us/windows/win32/services/localsystem-account)
- [Windows service-user account/token and loaded profile](https://learn.microsoft.com/en-us/windows/win32/services/service-user-accounts)

**EXTERNAL DECISION REQUIRED**: choose either the deliberately reduced
P132 user-scoped U1–U6 model, or a separately reviewed **actual service-owned
credential target/store** with an explicitly chosen service account,
per-user association and broker authentication. Do not combine their
approval or use the phrase "machine-persistent" to imply shared-vault access.

## P215 actual Windows integration

The additive native `P215WindowsStorePrincipalReadOnlyAdmission.cs` is
compiled only into `C1_REVIEW_ISOLATED_ASSEMBLY` and directly:

1. Reuses the unchanged original P214 Windows pipe-to-existing
   `CustodyService` integration and its actual P113/P114/P115/P116
   OS impersonated peer, PID, token session/integrity and WinVerifyTrust
   source code.
2. Obtains the **current running process's actual token SID** through
   native `WindowsIdentity.GetCurrent(false)`; compares it against the
   OS LocalSystem well-known SID and (when connected) the actual OS pipe
   impersonated-client SID. Raw SIDs are never retained in result/logs.
3. Calls **only** Win32 `CredGetSessionTypes` to observe the current
   logon session's **maximum generic-credential persistence capability**.
   This does not report a credential's existence, target, owner, password
   or value. It never invokes `CredReadW`, `CredWriteW`,
   `CredDeleteW`, `CredEnumerateW` or `CredGetTargetInfo`.
4. Invokes the existing C1 terminal/request refusal for forged operations
   and demonstrates that even a genuine OS client SID equal to this
   unprivileged **test runner** process is insufficient to establish an
   independently protected service vault, signed human consent or
   authorised migration. P215 cannot create a true effect receipt.

**Important limitation:** the hosted Windows runner is an unprivileged
current user, **not** LocalSystem and **not** an installed service. Its
observed generic persistence is a per-session capability, not the
actual storage/lifetime/readback of any user key. These tests cannot
prove cross-principal isolation without an approved separate service
account and actual protected storage. This is *negative* architecture
evidence, not a solution to the release gate.

## Proposed store/effect architecture needing external G0/R3 approval

| Decision | Required external specification | Current |
| --- | --- | --- |
| Principal | Dedicated least-privilege service user vs LocalSystem, reason, service SID and token, logon/profile semantics, privilege minimisation | OPEN |
| Store | Protected service-owned target, exact account scope, filesystem/HKLM/DPAPI/WinCred model, image code integrity and backup policy | OPEN |
| Existing user key | No automatic P132 key migration or deletion; explicit local consent and operation-bound migration ceremony if approved | HOLD |
| Isolation | Prevent P132 Python/same-user direct WinCred writes against **the selected high-assurance target** via protected OS store or code policy, not a Python flag | OPEN |
| Broker | Signed installed UI, authenticated endpoint, session and loaded-image identity, actual user-presence proof, challenge and durable one-use grant | OPEN |
| Native effect | Single service-owned atomic actor replacing original P96 approval/effect race, no alternate Python or old pending transaction route | OPEN |
| Recovery | Independently protected monotonic anchor, safe unknown-result recovery without replay, security-reviewed ACL/volume/FileId authority | OPEN |
| Deployment | Signed installer/service/UI/dependencies, enterprise WDAC/SAC/App Control policy owner decision and installed content provenance | OPEN |
| Review | GOV-01/02 SEC-03/04 REL-05/06/07 independently named source-bound signed GO decisions; G0–G6 and R0–R4 | 7 OPEN |

A `LocalSystem` process is highly privileged and cannot be chosen by
default to close this issue. A service-scoped secret target might require a
dedicated identity, but policy and principal ownership must be decided by
independent Windows platform and security reviewers first.

## Source preservation and genuine native Windows evidence

P215 adds exactly **five paths** on P214, leaving historical P49/P96,
P113–P116, existing C1 service, P132/P133, P208–P214 and frozen
signing/installer holds unchanged. Source-bound `windows-2025` hosted CI
requires exact SHA/event/branch/P214 ancestor and original source Git
blob pins unchanged before/after. It compiles the original C1/P113–116
source plus the P214 host integration and new P215 test-only observer;
executes **16** genuine Windows native cases (including real separate
process pipe, actual user SID equivalence, LocalSystem distinction,
read-only generic persistence capacity, forged/migration claims,
replay, revocation and fault), and preserves OS exit codes/log SHA.

Re-executes previous P132–P214 **233** selected cases before P215.
Expected total is **249 selected genuine Windows tests**, not three
complete unfiltered product regressions (**0/3**). P96's original race,
P135/P175/P178/P179/PERF-P187-01 findings and machine Code Integrity
test hold remain unwaived. No real key, native credential effect,
service installation, protected store, signer enrollment, provider
C2 call, release merge or Drive MASTER release record update.

## P216 substantive recommendation

Produce an independently reviewable **service-account + target store
decision RFC** with a concrete account/token comparison, protected
target namespace, no-direct-Python-bypass proof requirements and a
separate signed service code-admission plan. Once external G0/R3
approval arrives, implement an actual production-shaped protected
storage/IPC candidate (synthetic only initially), with native Windows
fault and adversarial process tests. Do not claim R0–R4 or release
P0–P5 GO until real OS boundaries and signed approvals exist.
