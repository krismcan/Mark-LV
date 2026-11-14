# BYOK C1 — P214 Actual Windows Peer→CustodyService Integration and Independent G0 Decision

**14 November 2026 · OM v2.1 · exact verified P213 SHA**
`3d9314625ae9417b440f5eb3b3101281216f97e5`

**State: IMPLEMENTATION IN PROGRESS — REAL-KEY NO-GO / PRODUCTION HOLD.**

This is the source-grounded **high-assurance native C1** track.
It does not absorb the alternative P132/P133 *reduced user-scope*
U1–U6 consent model. No independent trustee, Windows machine policy
owner, code signing service or qualified reviewer has approved a pilot.

## A. Concrete architecture finding: Windows credential user identity

The existing *reachable* P132 source:
`nayeon/brain/local_byok_user_scope.py` calls
`WindowsCredentialBackend.put/delete`, which directly calls native
`CredWriteW/CredDeleteW` in `nayeon/secrets/windows_credential.py`
with `CRED_PERSIST_LOCAL_MACHINE = 2`.

**LOCAL_MACHINE is not a machine-wide shared credential namespace.**
Microsoft defines it as persistence across subsequent logon sessions
*of this same user* on this computer. A new LocalSystem account service
does **not** automatically operate in the current user's vault.
Windows LocalSystem is not associated with a logged-on interactive
user. <https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw>
<https://learn.microsoft.com/en-us/windows/win32/services/localsystem-account>

This is a **critical unresolved R3/G4 architecture decision**, not a
mere test failure. Reviewer/owner must choose in writing, before new
service effect code:
- Option **USER-SCOPE:** preserve P132/P133 with explicitly narrower
  threat model, local human UI, own U1–U6 review, controlled key ownership;
  NEVER inherit privileged C1 release claims.
- Option **SERVICE-SCOPE:** new service-owned named target and protected
  store (service identity, least-privilege permissions, key isolation,
  explicit one-time *consented* migration/deletion of any earlier P132
  user credentials). Specify exactly which principal accesses secrets,
  how it handles per-user scope, cross-logon, backup/recovery, process
  access and decommissioning. Impersonating a user is not by itself
  proof of human consent or a defence against same-user hostile code.
  Never assume LocalSystem provides the desired security model by default.

No P132 migration, new actual WinCred target or real secret storage
was implemented in P214.

## B. P214 executable source integration (real Windows, no fake trust)

The new
`native_c1_candidate/P214ActualWindowsHostReadOnlyIntegration.cs`
is compiled **only** under `C1_REVIEW_ISOLATED_ASSEMBLY`
and combines these **unchanged real Windows modules**:

- P113: Windows named-pipe client impersonation token/SID (OS-observed)
- P114: actual kernel client PID, process creation time and image path
- P115: actual kernel session/token session/integrity observations
- P116: real read-only opened-handle `WinVerifyTrust` file-policy
  inspection with cache-only revocation
- P101/current native C1 `CustodyService.cs`, including
  `ServiceOwnedAdmissionBoundary` and
  `ServiceBoundRequestIdentity`.

This is *not* a new detached mock gate. P214 directly invokes the
existing `CustodyService.RefuseUnreviewedTerminalEffect()` and, for
caller-claimed metadata,
`CustodyService.RefuseBoundPendingOperation()`. Both continue to
refuse every real effect. Its immutable review observation cannot
create signed publisher trust, approved service image, desktop
provenance, actual intentional human click, one-use protected approval,
real WinCred grant or release eligibility.

Original P116's file WinTrust can return a negative for genuinely
signed OS files under offline cache-only revocation conditions;
even a positive result without the **independently enrolled Nayeon
publisher/loaded process image identity** is not an IPC grant.
P113 observed SID/session and P114 OS PID do not prove
nontransferable trusted consent. P124's transferred-handle issue remains.

The **new 14 native Windows tests**, executed unprivileged under hosted
`windows-2025`, include:
null and unconnected pipe, original service-held flags, real same-
process OS peer/process/session matching, actual unsigned native file
policy, genuine *separate OS process* named-pipe handshake and identity,
a structurally valid forged P102 request sent alongside genuine OS
observations, replay, malformed request, revoked service, sticky
faulted service and no authorised WinCred effects. Real process exit
codes, compiler original stdout, test stdout and SHA-256 are preserved.

No key, payload, person SID, secret, approved signer, actual installer,
service Main, named-pipe production listener, protected kernel state,
real user approval or credential effect can be created here.

## C. Required **external** independent G0 decision matrix

| Boundary | Explicit decision needed | Responsible party | Current state |
| --- | --- | --- | --- |
| Architecture | P132 U1–U6 **or** high-assurance privileged C1 R0–R4. Store principal, target namespace, secret migration and alternative effect-route retirement. | Product security owner + independent reviewer | **OPEN** |
| Service privilege | LocalSystem vs dedicated least-privilege service account; protected storage, Windows profile/vault semantics; protected installed path/ACL, no user-writable executable/DLL dependencies. | Windows platform security administrator | **OPEN** |
| Code signing | Enterprise-approved publisher, thumbprint/policy anchor, revocation/rotation, hashes of *every* executable (service, broker, installer, scripts, updater, DLLs), version/anti-downgrade. | Qualified code-signing / App Control owner | **OPEN** |
| Loaded image | Exact actual broker process loaded-image identity vs verified opened-file identity, handle transfer, replacement/race/ABA, signed process create/exit, no PID-only authorisation. | Independent Windows native security reviewer | **OPEN** |
| Local IPC | Source-owned named-pipe ACL/SDDL, service-controlled listener and user session matching; no untrusted caller SID/PID/signer/client boolean; challenge/replay/timeout/downgrade rules. | Windows service/IPC security reviewer | **OPEN** |
| Actual human intention | Explicit signed interactive broker presenting *exact* target, operation and immutable candidate identity; approved mechanism for actual user presence; UAC/SID alone insufficient. | Security/HCI reviewer + product owner | **OPEN** |
| Terminal effect | Single service-owned actor/lock; approval consume under lock; durable prepare/attempt/uncertain sticky recovery; zero old P96 Apply bypass and zero Python direct effect route in high-assurance installation. | Independent native security reviewer | **OPEN** |
| Durable custody | Protected independent monotonic antirollback/ABA witness, crash-safe on-disk state, verified ACL/FileId/volume, OS failure injection, no automatic retry. | Windows security and incident recovery owner | **OPEN** |
| Machine policy | Actual enrolled Code Integrity/WDAC/Smart App Control user-mode enforcement, no forced executable test bypass. Original Kristian Code Integrity blocks preserved. | Real endpoint policy owner | **OPEN** |
| Release evidence | G0–G6 + R0–R4 + P0–P5, GOV-01/02 SEC-03/04 REL-05/06/07 approvals, 3 complete unfiltered Windows product regressions, release source seal. | Independent GOV/SEC/REL and quality owners | **OPEN** |

Microsoft's App Control signing guidance requires a full executable
inventory and signing verification; a signed installer by itself
does not make each loose installed file trusted:
<https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/deployment/use-code-signing-for-better-control-and-protection>.

Named-pipe access requires explicitly reviewed security descriptors
and impersonation must be bounded to the intended OS client context:
<https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights>
<https://learn.microsoft.com/en-us/windows/win32/ipc/impersonating-a-named-pipe-client>.

**Do not self-certify independent security review**: tests can
demonstrate *failure modes*, not confer authorised real-key release.

## D. Exact Windows evidence and original source custody

P214 contributes **five additive paths only**:
`native_c1_candidate/P214ActualWindowsHostReadOnlyIntegration.cs`,
`tests/p214_native_host_integration/P214RealWindowsHostIntegrationTests.cs`,
`scripts/p214_windows_real_peer_service_admission.py`,
this review document and
`.github/workflows/p214-windows-real-peer-service-denial.yml`.

Runner demands authentic push SHA/branch/repo, exact P213 ancestor and
only those paths. It verifies unchanged frozen P49/P96, P113–P116,
P132/133, native service/P208–P213 source identities before and after.
Compiles original P49/C1 and P113–P116 OS observer sources with
new P214 TEST-only bridge, executes 14 genuine Windows cases, captures
real native compiler and process OS exits + SHA-256, and re-executes
the previous 219 selected Windows security cases. **Expected 233
selected**, *not* three completed full-product regressions (still
**0/3**).

Original P135/P175/P178/P179/PERF-P187-01 failures and P96
approval/effect race remain unwaived. P132 direct Python CredWrite/Delete
remains unmodified and reachable. Kristian's original 17
modified/untracked paths must remain untouched. All new GitHub PR work
is isolated/draft/unmerged, not production.

## E. Actionable P215 engineering after P214

Produce a source-specific **service-owned store/principal decision
and single-effect-owner replacement specification** using the existing
native C1 source (not another isolated fake). Clarify whether a
high-assurance service/privileged target is materially defensible
given the existing P132 same-user backend; obtain actual independent
review and Windows signing-policy owner decisions, then implement
a test-only production-shaped successor service seam under verified
controlled native Windows admission with NO keys. Do not claim
real-key READY until R0–R4 have been independently granted.

**Absolute restrictions:** no real key entry, WinCred mutation on
Kristian, signing certificate use, disabling Smart App Control/WDAC,
unauthorised service installation, provider C2, GitHub merge/tag/release,
or Drive MASTER production-release ledger/dashboard update.
