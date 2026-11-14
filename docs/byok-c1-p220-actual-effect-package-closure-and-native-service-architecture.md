# BYOK C1 — P220 Real Package Credential-Effect Exclusion & Native Service Implementation Boundary

Nayeon v1 / Mark-LII · 14 November 2026 · Operating Model v2.1

**IMPLEMENTATION READINESS ONLY — G0/R3 INDEPENDENT WINDOWS OWNER DECISION MISSING.**

## Source custody / exact parent

- P219 parent commit: d05d2373d9e4fc8c96b6c09d201086dff9afecdc; draft PR #144 (unmerged, no reviewer approval).
- Genuine original P219 Windows run 43621333751 (SUCCESS), artifact 14124112661, SHA-256 51328FB8D54BAB1FB4D5D4E0792AC4C954CC4837B28AB0B7DCFD6DA5D64FE0EA.
- P219 compilers + original negative native cases: 15/15 x64 and 15/15 x86; Python focused cases: 18/18. Original P96 security flaw **reproduced**, not fixed.
- P220 additive scope: this document, a standalone bounded ZIP member inspector under nayeon/brain/p220_artifact_effect_closure.py, its source-linked original-P132 regression tests, and a Windows CI source-custody workflow. No production installer or service.
- No old credential API, native P96 coordinator, P132/P133 product, P216/P217/P218/P219 security source, denial-only CustodyService, original test, historical Git seal or user's local Kristian worktree is edited.

## Actual effect routes and proposed security model

**Current real interactive-user legacy path (P132):**
nayeon/desktop_alpha/local_byok_window.py -> nayeon/brain/local_byok_user_scope.py LocalByokController.approve -> nayeon/secrets/windows_credential.py WindowsCredentialBackend.put/delete -> Windows CredWriteW/CredDeleteW. This operates under the *interactive user's* Credential Manager namespace. P133 local_byok_launch_bridge.py can launch a separately selected child. These direct source paths are real and currently reachable; an in-process deny flag or a GitHub static scan is not a Windows credential effect isolation boundary. **Never delete or migrate historical user credentials automatically.**

**Current native service candidate:** native_c1_candidate/CustodyService.cs remains denial-only. It has no ServiceBase.Run/Main, OnStart always throws and its ServiceOwnedAdmissionBoundary refuses native terminal requests. Source file native_c1_candidate/CandidateCredentialEffectHold.cs also keeps mutation admission disabled. This is deliberately not a working installed privileged service.

**Historical original P96 race:** tests/p96_native_transaction_negative/PendingCustodyTransaction.cs (original SHA-256 D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB) checks approval then lease ownership, but invokes the fake native effect interface without a shared lock with revocation/fault/stop. Original fake-only native harness deterministically revokes between those operations on a separate OS thread and records one effect after revocation. The 30 passing native tests are negative proof, not correction.

**Production-shaped proposed solution (requires external platform and security approval):**
1. Standalone signed native *service principal* owns the only new high-assurance pending credential target, never a current-user P132 target. SEC-03 must choose token/service SID, profile loading, WinCred vs service-user DPAPI protected file, lifecycle and authenticated antirollback witness.
2. Native service admission and terminal mutation share the exact same service-owned synchronization and process-scoped authenticated Windows custody mutex. All trusted consent/revoke/stop/fault transitions linearize with one terminal-effect attempt; durable IN_FLIGHT and independent witness verified before effect.
3. Trusted installed signed user-interaction broker authenticates the actual interactive user/session, client loaded image and its named-pipe peer identity; only one immutable operation/candidate/version-bound consumed consent is accepted. No caller-provided bool, process name, WinTrust file hash alone or model suggestion is authority.
4. The *actual* signed installer/package manifest has no P132/P133 direct credential effect implementation, Python interpreter, arbitrary plugin code or unreviewed dynamic/nested package. The service-owned target must be inaccessible to old interactive-user processes by OS credential principal/ACL; old user-owned vault remains separate. Signing/Code Integrity applies at *loaded runtime*, not simply a static copied ZIP or source scan.
5. Terminal effects remain exactly one pending-only native Save/Replace/Delete with no automatic retry. Any uncertain effect/journal/anchor/stop/reboot yields sticky RecoveryRequired, even if the WinCred API reported success; distinguish unverified submission from provider validation.
6. P96 original negative comparator stays frozen, while the *separate successor* must prove revoke-before-effect yields zero genuine effect calls under the same lock and revoke-after-committed attempt cannot report “no effect”; crash/ABA/replay/rollback require native platform evidence.

## P220 concrete source addition — actual ZIP member closure audit

The new reviewer tool inspects **real bytes** of bounded ZIP archives (max 24 MiB archive, max 256 entries, max 8 MiB uncompressed total, max 2 MiB member) without extraction or execution. It bounds and verifies CRC, disallows path traversal/drive syntax/ADS/backslashes/percent names/Unicode NFKC aliases/casefold duplicates/symlinks/encryption. It searches for four known Python route modules under any archive prefix and Python or cached-bytecode suffix:

- nayeon/secrets/windows_credential
- nayeon/brain/local_byok_user_scope
- nayeon/desktop_alpha/local_byok_window
- nayeon/desktop_alpha/local_byok_launch_bridge

When any is present, result is LEGACY_CREDENTIAL_ROUTE_PRESENT_HOLD. When an executable DLL/EXE/PYD, nested wheel/ZIP/PYZ or other unreviewed executable-like member appears, result is OPAQUE_RUNTIME_OR_NESTED_CODE_UNPROVEN_HOLD. A bounded plain-source archive with no named module is **still** NO_NAMED_LEGACY_SOURCE_IN_BOUNDED_ZIP_STILL_HOLD. Invalid/incomplete data is INVALID_ARCHIVE_HOLD.

All four dispositions are **NO-GO**; all seven boolean approval/release fields are always false and cannot be changed through caller claims. No approved high-assurance package/binary has yet been produced. This audit cannot see packed Python module tables, compiled/native alternate WinCred calls, dynamic imports, a live installed service, nested installers, actual signed loaded images, a modified ACL, DPAPI isolation or publisher trust. **It is not a complete transitive installed-build closure proof.**

Windows CI proves the test parses actual original P132 files and rejects their inclusion, as opposed to inventing a clean production manifest. Actual production acceptance later must use a separate independent signer-owned install-tree and loaded-image inventory with Win32 file IDs, signer/hash, complete dependency closure, ACLs, native behaviour and OS Code Integrity enforcement. No security reviewer may promote a P220 static clean outcome to GO.

## Required qualified sign-offs (none issued)

| Gate | Independently qualified role | Required recorded decision |
|---|---|---|
| GOV-01 | Security governance owner | Threat model, local user, admin, kernel and update-rollback adversary scope |
| GOV-02 | Credential lifecycle authority | Separate target, re-enrolment, old vault retention, deletion, restore, no automatic migration |
| SEC-03 | Windows service identity/store authority | Exact user/service token/SID/profile; service WinCred or user DPAPI, protected ACL and antirollback |
| SEC-04 | Windows signing/Code Integrity/IPC authority | Actual installed signed service and broker image, loaded image/code integrity, authenticated named-pipe consent and native P96 fix |
| REL-05 | Independent release security reviewer | Security gate G0–G6, R0–R4 evidence bound to exact binary/source hashes |
| REL-06 | Independent Windows QA | Three full unfiltered native Windows product regressions + native exit/log/hash receipts |
| REL-07 | Authorised production release operator | P0–P5 deployment/rollback/incident handling authorisation |

An independent reviewer must be an actually identifiable qualified person/team with authority, scope, source SHA, platform build, official signer/policy, risk acceptance, signed dated GO/HOLD and evidence chain. A Github draft PR, assistant-authored architecture note and passing test are **not** independent security sign-off. At P220 intake, PR #144 listed **no requested external reviewer and no review**; no reviewer decision is issued. No authorised disposable test VM/operator is named.

## Implementable P221 path, distinct from further fake-only gate inflation

**Prerequisite:** obtain SEC-03/SEC-04 written exact-target design choice and authorised owned test VM. Then produce new isolated native-service implementation candidate (never modify frozen P96 original) with a *single effect actor*, durable service-private journal, trusted signer/broker and real OS principal. Only on reviewed disposable VM, fixed harmless synthetic test material first; no real user API key, vendor validation or native credential mutation on Kristian. Add tests for service-user/interactive-user cross-principal refusal, native pipe peer and loaded-image identity, revocation linearization, reboot recovery/rollback, negative legacy package closure, and fresh full Windows product regressions.

Until then, remaining blockers are **real external approval and actual native/installer implementation**, not failing Python packaging tests.

G0–G6 OPEN · R0–R4 REAL-KEY NO-GO · P0–P5 PRODUCTION HOLD · 7 signoffs 0/7 · full Windows unfiltered regressions 0/3 · BYOK C2 NOT AUTHORISED.

Kristian original authoritative branch and modifications must remain untouched. Original Drive MASTER .xlsm must not be replaced by a duplicate Google Sheet; current unfinished P220 is not a release and cannot be logged as one. No service install, policy toggle, secret read/write/delete, key migration, real provider call, merge/tag/release or production promotion.
