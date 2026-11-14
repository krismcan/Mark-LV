# P217 — Independent Windows Store Ownership, Code Integrity & Credential Effect Architecture
Nayeon v1 / Mark-LII · BYOK C1 · 14 November 2026 · OM v2.1

**P217 STATUS: EXTERNAL DECISION PACKET PREPARED; QUALIFIED G0/R3 DECISION NOT RECEIVED.**
**No engineering artifact in this document is a security approval or proof of runtime isolation.**

## 0. Immutable review identity and evidence
- Repository: krismcan/Mark-LV
- P217 parent: P216 commit 7fae895ee4b91849e1f572a60b8db5d740878579.
- Parent P216 draft PR #141: https://github.com/krismcan/Mark-LV/pull/141 (open, draft, unmerged when reviewed).
- P216 genuine Windows run 43616096798 (success), artifact 14121677988.
- Original Actions artifact digest SHA-256 407D48970EE711C853169E0B11D8A8B97A99A798D5A81CF4C030DC67509EC634.
- Original H/C/R ledger SHA-256 632341BDD27229B6BFA89BB3DB46863F28E593262D7DC816E8704A532F55EAAA.
- P216 267 selected Windows security and integration tests PASS (249 retained + 18 new); NOT any of 3 accepted whole-product unfiltered Windows regressions (still 0/3).
- P216 identified 177 tracked Python source files and 32 review-needed findings. The 32 are **not** proof of exhaustiveness; additional compiled, dynamic, process, update, recovery or third-party paths could exist.
- Original Kristian worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028 at e3612279cb972e68e2487702183d5bf5b8f6c4a1 on nayeon-v1, 4 modified + 13 untracked; read-only observed, never reset/stashed/modified for P217.
- P216 first failed CI run from incorrectly rejecting 14 zero-byte __init__.py files is preserved. The subsequent run passed; neither run proves G0/R3.
- The seven external GOV/SEC/REL decisions are unissued and PR #141 has no submitted independent reviews at P217 intake.

A reviewer must bind any verdict to the exact P217 commit after submission, source blobs, measured binary/package artifacts when available, specific Windows version/policy and a stated threat model. GitHub PR review, Windows CI, WinVerifyTrust observation and a signed PDF are distinct evidence, not interchangeable authority.

## 1. Required threat model and operational boundary

**In scope:** ordinary local interactive users including a compromised same-user Python process; untrusted app plug-ins, imported modules, user-controlled search paths and adjacent executables; unauthenticated or impersonating IPC clients; attacker-controlled files under a writable install/update path; crashes, journal rollback, retry/ABA, process and service restarts; concurrent revoke/stop/effect; and lost/unavailable account-profile data.

**Explicit constraints:** an elevated administrator, kernel compromise or privileged process with debugging rights may exceed service-user DPAPI and ACL guarantees. Independent Windows security owner must state which privileged attacker classes are out of scope, how tampering is detected, whether tamper-resistant rollback requires TPM/hardware-backed anchoring, and what recovery promises are defensible. Never label service-user DPAPI as protection against a fully compromised administrator.

Trust zones:
1. Interactive untrusted Nayeon app / Python extension / old P132 source-mode tool.
2. Separately signed, installed, verified, *interactive* consent UI broker.
3. OS authenticated named-pipe boundary and live peer token/image binding.
4. Privilege-minimized native Windows service process, exact installed image, service-specific identity.
5. Service-only store and protected durable custody/monotonic witness with explicit recovery owner.

Secret bytes must never cross into zones 1, untrusted logs, PRs, CI, model prompts or an unbound third-party process. User input in trusted broker can reach only exact authenticated service endpoint under approved design. Existing P132 is a separate, lower assurance user-scope workflow, not part of zone 4.

## 2. Source-to-effect route matrix (real source; no effect executed by P217)

| Route | Actual P216 source | Reachability / required P0 retirement |
|---|---|---|
| User interactive UI | nayeon/desktop_alpha/local_byok_window.py | LocalByokWindow.approve_from_button calls controller.approve after a user interaction; in-process confirmation is **not** OS-attested human presence. |
| Controller to credential backend | nayeon/brain/local_byok_user_scope.py | compose_user_scope_local_byok instantiates WindowsCredentialBackend; LocalByokController.approve calls _backend.put or _backend.delete, and inspect/begin use availability reads. |
| Python native credential effect | nayeon/secrets/windows_credential.py | _Advapi32Adapter calls CredReadW, CredWriteW and CredDeleteW; WindowsCredentialBackend.get/put/delete and is_available expose current-user target operations. |
| Python child process | nayeon/desktop_alpha/local_byok_launch_bridge.py | Source mode launches python -B -m nayeon.desktop_alpha.local_byok_window via subprocess.Popen; child is a separate same-user process, outside native service control. |
| Frozen helper | nayeon/desktop_alpha/frozen_signed_byok_companion.py | P140 signer/hash/release pins remain empty/false, frozen helper must refuse; this is not a signed installed source identity. |
| Existing native service | native_c1_candidate/CustodyService.cs | OnStart always throws; no service Main or installed host, terminal methods delegate to denial-only ServiceOwnedAdmissionBoundary. Refusal cannot block unrelated same-user WinCred writes. |
| Broader dynamic surface | P216 Git-tracked AST inventory | 177 .py files/32 review findings require manual trace through entry points, imports, subprocesses, P/Invoke, DLL loading, installer, update/repair/recovery. Static absence ≠ OS isolation. |
| Original P96 comparator | P96 historical original Apply approval/effect race | Remains unresolved and unwaived; new owner must prove revoke, stop, crash and effect share a serialized, durable terminal transition, not use original Apply as production path. |

**Mandatory retirement decision:** high-assurance installer must exclude all legacy Python credential-effect code, child launcher, source interpreter, unsafe extensions, unpinned native helpers and uncontrolled recovery tools. The original audited source stays intact on historical branches. Excluding code from a package alone does not stop a separate same-user process from using a pre-existing **user** WinCred target. The NEW service-owned target must be inaccessible to the ordinary interactive user even when that user separately launches the P132 code. That cross-principal boundary must be proven under an authorised Windows policy and test VM; do not use P216 AST or Python flags as proof.

No implicit migration: existing P132 credentials remain current-user owned; future high-assurance enrolment is separate, user-present and explicitly authorised. Never copy, impersonate, decrypt, export or delete the user's old credential to initialize the service.

## 3. Competing principal and store designs — independent G0/R3 choice

| Option | Benefits | Material unresolved cost/risk | P217 recommendation |
|---|---|---|---|
| Dedicated virtual service account + restricted service SID; service identity user-scope DPAPI + service-ACL-only ciphertext | Separates new store from interactive user's WinCred, less ambient privilege than LocalSystem, OS-managed service identity | Actual service profile availability, DPAPI master-key lifecycle, registry/profile ACLs, network token behavior, user/administrator separation, recovery/restore, Windows edition/service SID/token behavior unverified | **Preferred for independent test only**, NOT production-approved |
| LocalSystem + ACLs and user-scope system DPAPI | Service execution/restart and access to machine resources commonly straightforward | Very broad OS privilege, larger lateral impact, harder blast-radius argument, no built-in user-present consent | Reject as default; require exceptional written justification |
| Same interactive user + current WinCred target | Legacy P132 compatibility, no new service provisioning | Same-user Python route can manipulate vault; does not meet independent high-assurance owner boundary | Reject for high-assurance C1, retain separately only under lower-assurance model |
| Service-owned Credential Manager under dedicated account | Native Windows API storage lifecycle, familiar credential semantics | Noninteractive/service account availability, persistence and profile behavior MUST be proven; legacy CRED_PERSIST_LOCAL_MACHINE does not share across principals | Candidate; compare on actual approved Windows test VM |
| Native service-owned encrypted file/registry store + service user-scope DPAPI + service-SID ACL | Explicit fixed namespace and journal coupling; possible atomic service-store writes | Must design robust crash atomicity, backup/restore, ciphertext replacement, antirollback anchor, ACL inheritance and data destruction | Candidate if service account WinCred fails threat model/restart/recovery |
| Machine-scope DPAPI ciphertext as primary boundary | Cross-principal availability after restart | CRYPTPROTECT_LOCAL_MACHINE allows any machine user with ciphertext to decrypt; ACL secrecy alone is inadequate if blob copied | Reject as sole service-isolation boundary |

P217 does **not** assert a virtual service account profile is loaded, stable, DPAPI-capable, or recovery-safe. Windows platform owner must approve the exact service registration, required privileges, SID type, logon token, service profile path, registry/file DACL inheritance, restart and rollback semantics. Service SID is a token/ACL principal, not by itself code integrity or key custody.

Review-specific observations must include user/service/admin token SIDs, service account profile state, fixed target-name ownership, API error codes with no secret bytes, service account logon/restart after machine reboot, key-loss recovery/refusal and denies from a different interactive user. None have been executed here.

Microsoft references:
- https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw
- https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
- https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info
- https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/service-accounts

## 4. Code Integrity, installed image and trusted human consent — G0/G1/G4/G5

The signed installed trust root is a machine-policy and signer-owner decision, NOT a file hash computed by the Python app or a Python feature flag. Require:
1. Exact verified build provenance, pinned trusted publisher and certificate policy, signed installer/service/broker and all transitive native DLLs and plug-ins; no user-writable PATH, side-load or search-order ambiguity; immutable installed ACLs and safe update/repair/uninstall behaviour.
2. Windows policy owner explicitly tests App Control for Business (WDAC), Smart App Control and actual Code Integrity event evidence on the target Windows edition. Treat previous Kristian Code Integrity block as relevant and preserved; do not bypass or loosen it.
3. Verify loaded process identity from OS handles (not caller-supplied path strings), file/volume identity and verified signer under an approved race-resistant load mechanism; preflight signature alone does not solve TOCTOU. Bind a peer to live process token, PID plus creation identity, session/logon LUID, expected publisher and loaded-image evidence.
4. Named-pipe endpoint: restricted DACL, service-owned server identity, authenticated client token and one-to-one operation nonce; prevent pipe squatting, process-ID reuse, cross-session impersonation, reconnect swapping and spoofed approval messages. Verify OS peer under authoritative host; do not trust Python fields.
5. User-present consent broker in the legitimate interactive session: immutable display of exact target/provider, operation (save/replace/remove), destructive consequence, one-use expiry and no ambient permission. Strong user-interaction guarantee needs explicit independent review of desktop spoofing, accessibility/remote session, untrusted UI automation and code integrity.
6. Durable service-owned consent issuance and consumption: bind operation ID/target/source version/peer/session, store consumed state **before** any effect, reject mismatches/replay and never auto-replay after crash. Partial or unknown effect outcome means terminal reconciliation-required until authorised independent recovery.

Relevant prior P113–P116 and P213–P215 OS observations are **read-only evidence**, not a signed loaded consent broker, service registration, working pipe or policy approval.

Microsoft code-signing and policy guidance:
- https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/deployment/use-code-signing-for-better-control-and-protection
- https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/wdac-and-applocker-overview

## 5. One native effect owner and source-specific P96 race closure — G2/R2

**Original target of integration:** native_c1_candidate/CustodyService.cs and ServiceOwnedAdmissionBoundary, not a new detached fake service. Before replacing current denial path, reviewer must approve a change plan that:
- Adds a native service executable / ServiceBase.Run only as a separate authoritatively signed/installable candidate, under approved identity in authorised VM; keeps the original P49/P101 denial comparator sealed.
- Implements exactly one service-private credential-effect interface (no Python direct effect entry, script hook, debug IPC, alternate helper or privilege-bearing updater). The owning terminal actor is the only place that may call CredWrite/CredDelete or equivalent protected store mutation.
- Uses a single explicit lock/serial transaction across prepare, consent consume, dispatch, stop, revoke and fault. P96 original Apply race requires a **real source-specific regression** before approval, not merely passing synthetic race cases.
- Persists durable intent/consumption and a separately protected monotonic witness in an order reviewed for crash points. States: PREPARED -> CONSUMED -> IN_FLIGHT -> COMMITTED, or RECOVERY_REQUIRED. No automatic retry on ambiguous API return, power loss or unmatched journal and anchor.
- Separately exercises cancellation before consumption, conflict in-flight, crash during effect, rollback, journal tamper, restart, cross-principal denial and re-enrolment on a disposable authorised system; secret values only fixed synthetic harmless data until real-key R0–R4 approvals.
- Retains old user-scope P132 code in its historical repository context without advertising it as trusted/isolated.

No service actor has been implemented or installed under P217. Until approved, CustodyService remains denial-only.

## 6. Exact independent decisions requested (no self-approval)

| ID | Proposed qualified independent owner — assignment NOT confirmed | Decision and required output | Current |
|---|---|---|---|
| GOV-01 | Project security governance authority | Signed threat model, accepted privileged-adversary boundary and G0 source scope | UNASSIGNED / HOLD |
| GOV-02 | Credential lifecycle/data owner | Separate namespace, opt-in re-enrolment, backup, retention, deletion/recovery decision | UNASSIGNED / HOLD |
| SEC-03 | Windows platform/security principal owner | Exact account type, service SID/token, profile and DPAPI, WinCred vs native store and cross-user evidence; R3 | UNASSIGNED / HOLD |
| SEC-04 | Code Integrity/signing/IPC security reviewer | WDAC/SAC policy, signed loaded binary, installer, peer/broker, source-bound consent and P96 race remedy | UNASSIGNED / HOLD |
| REL-05 | Independent release security assessor | G0–G6 and R0–R4 source-specific verdict after actual implementation | UNASSIGNED / HOLD |
| REL-06 | Independent Windows QA/release verifier | 3/3 complete unfiltered Windows product regression evidence, native OS exits, log/sha receipts | UNASSIGNED / HOLD |
| REL-07 | Authorised release/deployment owner | P0–P5 production admission, machine-policy and release control | UNASSIGNED / HOLD |

The decision record MUST include reviewer legal/organisational identity, authority basis, independence conflict, exact Git commit/blobs and binary hashes, OS build/edition/policy ID, reviewed threat model, tested evidence/artifacts, alternative and risk accepted/rejected, explicit GO or HOLD, signature/date and conditions. No assistant-authored packet, CI result, GitHub merge or routine user approval constitutes this signature.

**Reviewer submission status:** P217 packet made available in a draft PR for qualified external review; no named authorised independent Windows security/policy owner was identifiable from connected repository PR metadata. Do not claim delivery to such a reviewer or invent an approver.

## 7. Decision questions requiring explicit answers before any safe pilot

1. Is restricted virtual service account NT SERVICE\NayeonByokCustody supportable on the approved target Windows edition and service configuration? Show actual token, profile, SID, privileges and recovery proof.
2. Is service-user DPAPI reliable across restart and approved recovery, or is service-owned WinCred preferable? Demonstrate cross-token access denial, without real keys.
3. Where are protected journal/antirollback monotonic anchor and encryption data kept so local users cannot replace/replay? Specify scope against administrators/restore.
4. What exact installed signer, binary set, DLL loading graph, WDAC/SAC policy and read-only verification prove the trusted effect process? Who owns signing credentials?
5. Can consent broker be OS-attested to the live interactive user, logon session and signed loaded image, not merely UI text? What is the named-pipe peer authentication design?
6. Which original P96 Apply / effect entry and stop/revoke race fixes will be made in the actual native source, with crash/restart atomicity and no auto retry?
7. How are legacy P132/P133 effect processes excluded from the *signed high-assurance product* and the new target protected, without silently deleting or migrating old user vault contents?
8. Which authorised disposable Windows machine, operator, change ticket, backup plan, test data policy and rollback authority permits the controlled no-secret service-account experiment?

## 8. Gates and permissible next checkpoint

**G0–G6: OPEN. R0–R4: NO-GO. P0–P5: HOLD. GOV-01/02, SEC-03/04, REL-05/06/07: UNISSUED. Windows whole-product unfiltered passes: 0/3. BYOK C2: NOT AUTHORISED.** P96, P135, P175, P178, P179, PERF-P187-01 remain open/unwaived.

P217 authorised output is a source-bound independent-review submission and accurate explicit HOLD. No real API keys, Windows secret read/write/delete, service account installation, signing policy edit, binary deployment, release tag, production merge or source custody modification.

**Next implementable checkpoint:** P218 — qualified G0/R3 owner response intake and authorised disposable Windows synthetic store-principal trial plan (or continued documented HOLD if no external authority is available). Do not perform system-changing trials until exact independent platform and security authorisation exists.
