# P216 — Service-Owned Credential Store, Principal and Effect-Route Decision RFC

**Nayeon v1 / Mark-LII · BYOK C1 · 14 November 2026 · OM v2.1**

**Source baseline P215:** `4143ec9faa9a41c2a4991f93916f2b6bc760e04e`.

**STATUS: ENGINEERING ARCHITECTURE CANDIDATE FOR EXTERNAL G0/R3 REVIEW — NO REAL-KEY OR PRODUCTION AUTHORITY.**

This RFC is an actual source-linked independent review request and staged
implementation contract. It is not a qualified reviewer response, signed
service, installed protected store, machine Code Integrity approval, or
permission to use real API keys.

## 1. Architecture decision requiring a real owner

**Proposed, NOT approved: high-assurance service-owned store under a
dedicated least-privilege Windows virtual service account**, provisionally
named `NT SERVICE\NayeonByokCustody`, with restricted service SID and
strict service-owned file/registry ACLs. The service would run only a
signed, protected, independently approved install tree and own all
credential effects for a *separate* high-assurance target.

**Protection proposal:** a service-account-user-scoped DPAPI envelope,
encrypted and decrypted only while running under that dedicated service
identity, with the profile/load/unload/restart semantics proven on the
actual approved Windows machine. The ciphertext would be accessible only
from an ACL-protected service directory and registered custodian; a
*separately protected monotonic journal/anchor* must bind issuer, source
version, operation, target, exact single-use consumption and terminal
recovery. No sensitive value may appear in logs, review, Git, IPC metadata,
dumps or email.

**Critical rejection:** do NOT merely change a Python/C# flag to
`CRYPTPROTECT_LOCAL_MACHINE` or rely on the machine-scoped DPAPI
encrypted blob as the boundary. Microsoft documents that other users on
the same computer can decrypt that blob if they can obtain it. Its
protection is machine-wide, not service-account-only. On the other hand,
user-scoped DPAPI normally restricts decryption to the same user, with
backup/recovery/domain policy exceptions, and user profile availability
is a first-order service risk.

**Credential Manager limitation:** P132 uses
`CRED_PERSIST_LOCAL_MACHINE`, which means available across logon
sessions of **the same user on the same computer**, not that a
LocalSystem or a distinct virtual service account automatically shares
the existing interactive-user credential. A user-scope key cannot be
silently promoted, read, migrated or deleted by a new service. A
separate user-initiated re-enrolment ceremony could avoid insecure
cross-account transfer, but must still be reviewed under G1/R1–R4.

**Why avoid LocalSystem as the default:** running a privileged credential
owner under LocalSystem increases blast radius and does not solve
user-present consent. A virtual service account is only a *candidate*
until the platform security owner verifies it is supported on this
Windows edition, can load its DPAPI profile, has a stable service SID,
does not gain unneeded network access, can be recovery-restored without
key exposure and is protected by installed image and service ACL policy.

Microsoft authorities for review:
- CREDENTIALW same-user persistence:
  https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw
- CryptProtectData user/machine decryption semantics:
  https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
- .NET ProtectedData / impersonated profile caveat:
  https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata
- Windows service accounts and virtual account semantics:
  https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/service-accounts
- SERVICE_SID_TYPE_RESTRICTED:
  https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info

## 2. Existing *actual* source effect paths to eliminate/isolate

P216's `nayeon/brain/p216_service_store_decision.py` reads **actual
Git-tracked Python files**, AST parses them, lists source-level
imports/native `CredWriteW` / `CredDeleteW` references and
review-needed dynamic-import patterns, and re-authenticates the P211
original source-risk witness. It emits a non-secret source inventory.
It does not import or call any credential backend or accept a caller-
provided manifest as execution authority.

| Source path | Actual capability and impact |
| --- | --- |
| `nayeon/secrets/windows_credential.py` | Original `_Advapi32Adapter` has real `CredReadW`, `CredWriteW`, `CredDeleteW`; `WindowsCredentialBackend` exposes get/put/delete and uses current-user `CRED_PERSIST_LOCAL_MACHINE` |
| `nayeon/brain/local_byok_user_scope.py` | P132 `compose_user_scope_local_byok` instantiates the backend; `LocalByokController.approve` calls `_backend.put` or `_backend.delete` after its *user-scope*, in-process/manual confirmation |
| `nayeon/desktop_alpha/local_byok_launch_bridge.py` | P133 launches Python source module `nayeon.desktop_alpha.local_byok_window`; frozen mode's P140 path has no approved signing/pins |
| `native_c1_candidate/CustodyService.cs` | Actual native candidate has no `Main` and refuses `OnStart` and terminal effect; its refusal does NOT gate a different same-user Python process |
| P213/P214/P215 | Native OS signer, genuine pipe/account principal and read-only WinCred persistence evidence; no approved owner, trusted broker, installed service or effect |

**P0 retirement contract, which is NOT complete:**
1. Enumerate *all actual product* paths including Python import graphs,
   native P/Invoke, reflection, executable launch, dynamic plug-ins,
   independently installed siblings, update path and recovery tools.
   P216 AST scanning is an **incomplete source inventory** and may miss
   dynamically computed names or native code.
2. Under high-assurance release packaging, reject *all* direct
   user-scope credential mutation consumers and the existing
   P132 source-mode launcher from the signed product/installer. No
   Python source interpreter, untrusted plug-in or debugger in the
   trusted effect process. The old user-scope path may remain in
   archived source for review; its mere absence from the signed package
   does NOT prevent another same-user program accessing the user's
   old WinCred target.
3. Service-owned high-assurance target must be in a security principal's
   store that the old user process cannot access. Confirm with real
   cross-token negative trials under approved admin/test policy.
   If old P132 keys exist, they remain under original user scope
   pending explicit consented deletion or re-enrolment.
4. Product callers must use authenticated service-owned IPC and a
   signed, locally trusted consent broker. The service must issue and
   consume a durable one-use operation-bound decision, with a single
   locked native terminal effect actor and sticky uncertainty.
   Existing P96 `Apply` race remains a frozen *negative* comparator,
   never a production execution path.

## 3. Concrete implementation contract (after owner decisions)

| Sequence | Required actual deliverable and evidence | Gate |
| --- | --- | --- |
| 1 | Security owner signs approved threat model, exact service account principal and separate target-store namespace; independent reviewer records source hashes and G0/R3 verdict | G0/R3 |
| 2 | On disposable authorised Windows image, create/test the account and protected install tree, service SID, profile, ACL, App Control / SAC / WDAC identity; separate actual OS user, service, admin and restart identities | R0/R3/G5 |
| 3 | Implement a **test-only** installed native service-store adapter under exact chosen principal; read/write only synthetic fixed harmless data, exercise DPAPI user scope and denied cross-user unprotect, loaded-profile and reboot/rollback loss | R3 development |
| 4 | Build independently signed UI broker and service-owned secure IPC, immutable display text, exact target/operation, user presence, nonce and one-use consent issue/consume; explicitly assess user desktop spoofing | G1/R1 |
| 5 | Replace P96 effects with a single service-owned terminal actor, durable prepare → consumed → in-flight → committed/recovery-required, same lock for stop/revoke/fault, no uncertain retry | G2/R2 |
| 6 | Eliminate service-store access from P132 and all other external/native routes in **actual signed product**, prove original user vault and new service vault separation, reject PATH/dll side load/rollback and forged signer | G4/P0 |
| 7 | Native crash/restart and ACL/antirollback adversarial tests, original full product tests **three unfiltered passes**, qualified GOV/SEC/REL source-bound positive reviews | G6/P1/P2 |
| 8 | Only then: authorised local real-key pilot R0–R4 separate from production P0–P5; no C2 provider call without its own consent | R/P |

**Do not** configure a service account, change ACL/WDAC/SAC,
install a signed component, enable any real credential effect or
use a real API key before independent approval. P216's pure design
candidate intentionally cannot implement any of these steps.

## 4. Required external decisions and explicit HOLD record

All these stay **unissued** until a qualified, separate actor signs
the source-bound verdict. No assistant-generated review text counts:

`G0:independent_windows_native_security_review`,
`R3:actual_service_account_and_profile_token_semantics`,
`R3:service_owned_separate_target_and_secret_isolation`,
`R3:user_scoped_DPAPI_not_machine_scoped_and_acl_evidence`,
`R3:independently_protected_monotonic_rollback_witness`,
`R3:recovery_migration_deletion_and_backup_plan`,
`R0:approved_signed_source_and_install_tree`,
`R1:loaded_signed_UI_image_authenticated_pipe_and_user_presence`,
`R2:oneuse_atomic_original_service_owned_terminal_effect_actor`,
`P0:legacy_user_scope_P132_P133_effect_elimination_or_OS_isolation`,
`P1:GOV01_GOV02_SEC03_SEC04_REL05_REL06_REL07`,
`P2:three_unfiltered_native_Windows_product_regressions`,
`P3:Windows_Code_Integrity_WDAC_SAC_signing_policy_owner`.

The independent decision must name the reviewer/identity, product
scope, exact source commit, threat model, approved Windows policy/version,
approved service account and store choice, alternative considered,
discovered source failure, required edits and explicit GO/HOLD for
G0–G6/R0–R4/P0–P5. Signing and OS policy owner decisions are separate.
**User's routine engineering approval does not substitute for external
security authority.**

## 5. P216 actual evidence scope

P216 creates 5 additive paths only:
- `nayeon/brain/p216_service_store_decision.py`
- `tests/test_p216_service_store_decision_inventory.py` (18 focused cases)
- `scripts/p216_windows_service_store_review_evidence.py`
- this RFC
- `.github/workflows/p216-windows-source-store-review.yml`

Actual GitHub-hosted Windows source-bound CI verifies P215 exact
parent, all expected files and original P49/P96/P132/P133/P113–P116
and native C1 source identities unchanged before/after.
It reads `git ls-files -z` (not caller-supplied paths) and hashes the
actual tracked file-list stream, reports original direct native
credential effect and all source risk findings, runs the 18 P216 source
decision tests and retains the previous 249 selected original Windows
security tests, native compiler and process exits. **Expected 267
selected** if genuine CI succeeds; zero of three accepted complete
unfiltered product regressions. Static scans and synthetic/native
negatives do not grant deployment, protect an existing secret or prove
the absence of other dynamic effect routes.

**G0–G6 OPEN · R0–R4 NO-GO · P0–P5 HOLD · seven GOV/SEC/REL
decisions OPEN · three full product regressions 0/3 · C2 NOT AUTHORISED.**

Next P217 should depend on qualified reviewer **design decision**,
or remain a nondeployable, no-secret controlled OS experiment. Avoid
substituting another simulated credential service for the
signed/installed/independently approved trust root.
