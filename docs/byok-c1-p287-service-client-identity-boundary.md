# P287 service-owner / trusted-client identity boundary — 19 November 2026

**NONDEPLOYABLE synthetic review candidate. Architectural admission HOLD;
production, real key, WinCred, provider and service installation NO GO.**
Approvals **0/7**; full product regressions **0/3**. No seal is requested.

Initial custody: clean branch `byok-c1-p287-service-client-pipe-boundary-20261119`,
exact parent `bf96a2a5d6570da7397770445967fa2434dd9008`, 1,157 tracked files,
no tag at HEAD. Parent draft PR #206/status and completed P286 hosted evidence
are user-supplied, not independently retrieved here. `.codex/CURRENT_STATE.md`
describes older Phase 10.2 work and disagrees with this Git checkpoint. It is
preserved under the explicit inherited-file freeze. Exactly five additive paths;
no inherited source, tests, workflow, P270, prior PR, workbook or dashboard edit.

## Open Failures & Prior-Issues Review

| Issue / source / severity | Cause, affected route, evidence, containment and disposition |
| --- | --- |
| P286 callback lifetime / prior HIGH development blocker | User reports 3 hosted x64 + 3 x86 passes: unchanged P284 128 cases, 1,542 assertions and 129 safe roots each, six text receipt sets, no crash. Historical callback/event ownership repair remains in frozen P286; no copy or promotion. P287 compiles that exact source and executes its unchanged managed completion tests only on hosted runners. No new native runtime closure claimed. |
| P287 service/client identity gap / material architectural HOLD | P265/P286 select current developer for pipe peer and owner. P267 StartDevelopment rejects virtual service SIDs. P282 ObserveProtectedService compares executing token to canonical virtual-service SID and SCM PID, but returns diagnostic evidence, not a reusable role-bound capability. P271 OpenProtectedService still throws LedgerBlocked. A single-user pipe is not service/client separation. P287 live admission unconditionally refuses; synthetic role/continuity/ACL adversaries provide containment tests, not a production repair. Independent review OPEN; admission HOLD. |
| P96 original / HIGH OPEN | Unrepaired by P287; original transaction, consent, recovery and effect paths remain frozen. No credential or production progression. |
| P76 / P211 / P216 / unwaived | No closure, downgrade or deferral approval inferred. Earlier acceptance/package/store issues still block production. |
| Local compiler orchestration / tooling, corrected | First relative-path compilation failed raw exit 1 on both architectures with CS1504 (source path resolution). Logs preserved under `nayeon-p287-local-076777ebe5ea450ebf0f35998bd0b84a` in Windows Temp. Absolute Resolve-Path inputs compiled successfully. No source/test weakening or executable run. |

Disposition: **HOLD** for architectural admission and all security-sensitive
seals. The user-authorized work here is isolated fail-closed containment and
synthetic modeling only. It does not waive the failure gate or move a milestone.
No new HIGH finding identified in this bounded implementation; independent
review is still required.

## Source and actor trust map

| Actor / source | Role and authority |
| --- | --- |
| Frozen P267 development entry -> P286 adapter | Current developer principal; development denial transport only. Cannot start as virtual service or become the P287 service-owner implementation. |
| Frozen P282 -> P261/P279 -> kernel executing-process token + SCM QUERY | Read-only executing-service observation; store/profile/SEC03/04 remain unproven. P287 does not reinterpret its status as approval or add name resolution. |
| Separately trusted interactive-client provenance | **Missing live issuer.** No wire SID, GUI identity, environment value, display name, caller bool or caller-created observation can fill this role. |
| P287 private synthetic fixture issuers | Fixed generated service/user SIDs represented by Windows SecurityIdentifier, never an assertion of installed principals or actual virtual-service execution. Distinct nonexported service and client issuers produce immutable observations for TEST ACL MODEL ONLY; even equal snapshots from another fixture are untrusted. |
| P287 classifier / PipeSecurity builder | Re-evaluates binding, role, identity and lease state; produces only detached in-memory ACL data. No real pipe, profile, store, service or credential operation exists. Forging BoundaryEvidence cannot feed the builder. |
| P286 completion callback | Owns End* and event cleanup after Framework signaling. It is not a client identity source; no callback thread can borrow the P287 fixture's binding. |

The service model requires exact virtual-service SID shape and equality with its
verified expected service SID, primary token, session 0, and executing PID equal
to SCM PID. The separately issued client requires bounded account SID shape,
nonzero session, primary token and distinct SID, process, token and logon IDs.
Shape alone never admits input. All modeled PID/birth, token/authentication/
modified IDs and sessions must remain equal to the initial observations.
Missing, swapped, shared, substituted, expired, revoked, cancelled or
impersonating evidence refuses. Snapshots are immutable; current binding is
checked before supplied observations, preventing old snapshots from reviving it.

The only actual OS identity check in P287 is read-only
`WindowsIdentity.GetCurrent(true)` to reject any ambient thread identity;
query failure refuses, with no process-identity fallback. Modeled thread-token
adversaries do not impersonate or adjust privileges. No SCM operation is added.

The synthetic protected DACL has service SID owner, service FullControl, client
ReadWrite plus Framework-added Synchronize, and Network FullControl deny. Client
CreateNewInstance, ChangePermissions and TakeOwnership are absent. Exact
OS-normalized owner/access SDDL comparison rejects any changed, broad, inherited,
extra or missing ACE. A returned PipeSecurity is mutable detached test data;
validation rechecks binding and never creates a pipe or applies an ACL.

`ObserveLiveAdmission` always returns MissingTrustedLiveProvenance;
`DemandBeforeRealPipeCreation` always throws before resource creation.
CredentialAllowed, StoreAllowed, ProtectedStoreAllowed and ProductionEligible
are always false, including for synthetic success or caller-forged evidence.

## Composition preconditions still missing

A future separately approved design must issue nonforgeable client provenance
from an authenticated kernel peer/token observation, bound to the connection,
process lifetime, token/logon/session, intended service and endpoint. It must
define revocation, expiry, impersonation/revert failure and revalidation at every
use, including reconnect, callback, process restart and PID reuse. P282 would
separately need a reviewed executing-service role issuer based on trusted SCM
configuration/process comparison and stable token evidence. P287 does not invent
either issuer or accept arbitrary caller-supplied SID strings as substitutes.

Only after those proofs and independent architecture approval could a future
transport compose role separation with P286's completion lifecycle. It must
preserve connect/read/write callback-owned cleanup, total deadline, cancellation,
replay bounds and identity restoration. P286 must not be renamed or its
current-user constructor reused as a service-principal admission path.

Protected profile ownership, DPAPI CurrentUser service-store scope/ACL/handle
custody, qualified SEC03/04, explicit consent and recovery/P96 proof remain
separate prerequisites. Observing a service identity grants none of these.

## Verification boundary and actual results

Focused suite: exact P286 SHA256 pin and mutation canary; unchanged P286
managed completion suite; immutable observation fields and OS SID roundtrip;
role/issuer spoofing; SID swap and same-SID refusal; SCM mismatch; PID/token/
logon/modified-ID/session continuity; wrong and well-known accounts; null,
revocation, expiry and cancellation; stale ACL/evidence; broad/missing/expanded
ACE and owner tampering; 128 callback-thread/cancellation schedules. Live pipe
creation denial is an unconditional preflight test, **not a native kernel ACL
denial test**. No real virtual-service token or actual client admission is claimed.

Final-source local Framework64/Framework builds with `/warn:4 /warnaserror+`:
**2 positive raw exits 0**, **14 expected negative raw exits 1**, named CS1029
and no negative binary. These are compilation results, not test passes.
Compilation input SHA256 manifests match before/after. Hosted manifest AST
parses with zero errors; all 1,157 inherited raw disk blobs match parent HEAD.
No generated EXE, hosted PowerShell manifest or policy bypass runs locally.
Full Python/native product regressions are not run or inferred from compilation.

Final compiler receipts (earlier iterations remain preserved separately):
`C:\Users\krist\AppData\Local\Temp\nayeon-p287-final-d15dd4a40b264844bbf6f7d71c355798\final-source`.
`raw-exits.txt` SHA256
`7E43D9D642EA50B86128F25AEC9FAC280160065A92A7A591ACBCD7D6829D1302`;
`binaries.sha256` SHA256
`460049192E9ED0C13195466717570FC64DA2F32244C4C1A25423DDF4ED53CCA1`.
The parent evidence directory holds inherited before/after manifests and the
final five-file `source-sha256.txt`, including this document. No binaries are
delivered or scheduled. Final Git check must show only these five untracked
additions, zero tracked/index changes and unchanged parent HEAD.

Prepared Windows-2022 workflow: exact P286 parent above, same-repository DRAFT
PR with exact P286 base and P287 head branches, immutable checkout/upload action
SHAs, contents:read only, no persisted credentials. Three trials per x64/x86;
only one focused test executable built and run. No P284 128-case rerun. All 1,157
inherited tree/disk blobs plus all five added files must match the exact PR head
before and after; bounded linear additive history is checked. Seven negative
compile configurations per job (ALL, RELEASE+DEBUG, each of five missing defines)
require raw exit 1, named CS1029 and no binary. Runtime requires raw exit 0,
bounded exact receipt shape, architecture, case/assertion floor and HOLD gates;
any failure stays red. Native child deadline 60 seconds; job limit 10 minutes.
Artifacts are eight explicitly allowed text receipts; no binaries, secrets or
private identity values. Environment flags are accident barriers, not identity
or production authority. No workflow launch/publication is authorized here.

Hosted runtime trials **0/6 run by Codex**, independent review OPEN. Approvals
**0/7**, full regressions **0/3**; production and real credentials **NO GO**.
