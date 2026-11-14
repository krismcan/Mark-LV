# P218 — Independent G0/R3 Windows Owner Intake and Read-Only Platform Evidence

Nayeon v1 / Mark-LII · BYOK C1 · 14 November 2026 · Operating Model v2.1

**Status: REVIEW PACKET PREPARED; EXTERNAL DECISION NOT RECEIVED. REAL-KEY NO-GO. PRODUCTION HOLD.**

## 1. Immutable source and predecessor evidence

P218 exact parent: f9da67040141f242b2132ad545a13f85e0bf3cb7 (P217 draft PR #142, open/unmerged at intake).
P217 genuine hosted Windows run 43617847433, artifact 14123270020, ZIP SHA-256 DBE2E032637DDD1297F17A24C329EE3988D1BB79FB6B64CFFC42F288FFB90559; original focused P216 security cases 18/18 PASS, but not a full-product regression. P216 earlier selected Windows security tests 267/267 PASS. Three accepted unfiltered whole-product regressions remain 0/3.

P218 permits exactly three additive paths: this decision record, scripts/p218_windows_readonly_store_owner_preflight.ps1, and .github/workflows/p218-windows-store-owner-readonly.yml. Original P132/P133/P96/P113–116/CustodyService/P216/P217 source, frozen security assertions and original Kristian worktree are not modified.

## 2. Genuine Kristian Windows read-only results

Device: Kristian; original Git worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028, branch nayeon-v1, HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, 17 pre-existing modified/untracked entries. Inspection performed through authorised Desktop Commander, read-only, with process exit 0.

| Actual OS observation | Result |
|---|---|
| Windows OS | Microsoft Windows 11 Pro, build 26300, version 10.0.26300 |
| Proposed service name NayeonByokCustody registered | No |
| advapi32.dll in Windows System32 | Present; does not prove authorised service-owned vault |
| CiTool.exe available | Yes |
| Read-only command | CiTool.exe --list-policies --json |
| Actual OS command exit | 0 |
| Raw joined CiTool output SHA-256 | AC16D757E4F5CA6F51E2053070C0FEC46A3DF7CBD187EB7E1D472221A6AB005C |
| JSON policy records | 15 |
| IsEnforced=true | 7 |
| IsEnforced=false | 8 |
| IsSystemPolicy=true | 15 |

Only policy counts and enforcement booleans are recorded; raw IDs, certificate details and token/account information are not uploaded. CiTool's native IsEnforced field is the basis for counts, not an invented IsActive field. Code Integrity records do not imply the proposed Nayeon image would be allowed by any policy, nor ownership of an installed signer/consent broker. The old Windows Code Integrity block remains relevant and unresolved.

**Not proven by any of this:** registered Nayeon service account, service SID/restricted token, profile loading, stable service-identity DPAPI, credential target isolation, backup/recovery, signed installed image, trusted IPC, user-presence, native effect ownership or independent approval.

## 3. Source-controlled, repeatable *read-only* probe

The P218 script queries OS version, exact Windows service-name presence, native API library availability, and CiTool policy counts. It runs only read-only CiTool --list-policies --json and never performs a credential read/write/delete, account creation, ACL change, registry mutation, service install, policy refresh/disable, key enrolment or native terminal effect.

It outputs minimal non-secret JSON. Unavailable CiTool, parsing failures or missing enforcement fields must be represented as UNPROVEN, never interpreted as no policy or permission to run. All real-key, production, signer, DPAPI profile, P132 isolation and independent-approval flags are fixed to false.

GitHub Windows-hosted runner observations are runner-specific, not substituted for the Kristian OS policy inventory.

## 4. Explicit independent sign-off matrix

| ID | Qualified independent owner required | Binding decision | P218 status |
|---|---|---|---|
| GOV-01 | Security governance | Threat model, admin/kernel attacker scope and exact G0 trust boundary | UNISSUED |
| GOV-02 | Data/credential lifecycle governance | Separate high-assurance namespace; re-enrolment, deletion, recovery and backup | UNISSUED |
| SEC-03 | Windows identity, service token and DPAPI/platform authority | Virtual account versus LocalSystem; actual restricted service SID, profile, privileges, Credential Manager vs service-owned native store and user DPAPI | UNISSUED |
| SEC-04 | Windows Code Integrity, signed image, IPC and consent security authority | Interprets actual policies; approves signer, installer, loaded-image trust, authenticated pipe, user-present consent and P96 original race closure contract | UNISSUED |
| REL-05 | Independent release security assessor | G0–G6 and R0–R4 security acceptance after implementation | UNISSUED |
| REL-06 | Independent Windows QA | Three unfiltered whole-product Windows regressions with native OS exit/log/hash evidence | UNISSUED |
| REL-07 | Production release owner | P0–P5 authorised release and deployment | UNISSUED |

Each real approval must bind reviewer identity/independence and authority basis, exact source commit and binaries, target OS/policy/signer, supported threat model, evidence considered, explicit GO/HOLD, date and signature. No assistant-authored document, CI result, or unsigned reviewer claim is approval. No qualified external reviewer or Windows policy/signing owner was named in the connected GitHub P217 PR #142 reviews/request metadata. This is an external blocker, not a reason to nominate an invented person.

## 5. Approved disposable Windows trial *plan*, NOT an authorised experiment

The proposed NT SERVICE\NayeonByokCustody virtual service account, restricted service SID and service-identity user-scoped DPAPI remain candidates, not provisioned configurations. LocalSystem is not a default because of excess privilege. Existing P132 current-user CRED_PERSIST_LOCAL_MACHINE persistence is not a service vault. Machine-scope DPAPI alone cannot provide cross-user isolation of copied ciphertext.

Before *any* trial involving a service account, credential effect, signing policy or protected store, require all of:
1. SEC-03/SEC-04 qualified source-bound positive written approval of test-only principal, account, profile, Windows edition/build, signer and installer policy, target store and recovery plan.
2. Disposable, owned, snapshotted, independently authorised Windows VM, never Kristian. Written administrator/operator authority, rollback and no-real-secret test-data policy.
3. Approved signed service executable and complete transitive image list, protected install paths/ACL, precise Code Integrity and runner policy evidence; never disable WDAC or Smart App Control to achieve a pass.
4. Native CustodyService real terminal-effect integration design proving exactly one native effect actor, service-only target and exclusion of the P132/P133 Python effect path from signed high-assurance package.
5. Original P96 approval/effect race and stop/revoke crash tests as negative comparators, durable one-use consent consumption and sticky recovery-required outcome, no automatic effect retry.

Only when those decisions have genuinely been given may an authorised operator run harmless fixed synthetic payload experiments for service SID/token/profile, restart, service-only DPAPI/WinCred, denied cross-token reads, protected store ACLs, crash/reboot recovery, signed broker named-pipe peer and actual P96 race closure. Source records and failures must remain immutable; no automatic user vault migration, real API key, provider validation or production promotion.

Microsoft authoritative review material:
- https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/deployment/use-code-signing-for-better-control-and-protection
- https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/feature-availability
- https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info
- https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata

## 6. Original source route remains reachable and security holds remain

P132 UI local_byok_window.py -> LocalByokController.approve -> WindowsCredentialBackend.put/delete -> CredWriteW/CredDeleteW, with P133 independently launched Python child still active in source; P140 frozen signed-helper pins remain empty; original native C1 CustodyService is denial-only. This is a concrete legacy effect bypass until the actual signed installer excludes that path and service-owned target is OS-isolated. Static scan and feature flags are NOT runtime isolation. Do not modify historical source merely to make tests green.

P96, P135, P175, P178, P179 and PERF-P187-01 remain unwaived for production.

**G0–G6 OPEN; R0–R4 NO-GO; P0–P5 HOLD; external GOV/SEC/REL 0/7; full Windows regressions 0/3; C2 not authorised.**

The original Google Drive MASTER (.xlsm) remains authoritative; a draft engineering checkpoint is not a release. Do not convert/recreate/replace macro content without a safe, tested original in-place update path. Master first then dashboard only when authorised.

**P219 next implementable task:** obtain a named qualified platform/Code Integrity reviewer and source-bound G0/R3 decision, or remain on explicit HOLD while refining safe source-linked design and read-only evidence. No privileged VM/service/real-key action without new external authority.
