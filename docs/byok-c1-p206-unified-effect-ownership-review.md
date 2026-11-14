# P206 — Legacy Python Credential Effect-Entry Ownership & Unified Admission Gate

**Source baseline:** exact P205 `94b8b457cc99c111bf444d89529ddcb861af7fd9`.  
**Disposition:** isolated dormant engineering candidate. Real-key **NO-GO**; production **HOLD**. This is not an independent Windows review, real credential test, service integration, or release.
**Scope:** no source changes to existing Python backend/lifecycle/desktop UI, native C1, frozen P49, P96 or Phase 10/P76.

## 1. Grounded entrypoint inventory (current source, NOT inferred authority)

| Entry/edge | Actual source function | Capability and classification | Trust gap / disposition |
| --- | --- | --- | --- |
| Direct Python WinCred storage | `nayeon/secrets/windows_credential.py::_Advapi32Adapter.write/delete` calls `CredWriteW/CredDeleteW`; `WindowsCredentialBackend.put/delete` | Real OS effects when an actual native adapter is lazily created | **Bypass-capable** without native C1 admission; backend accepts any syntactically valid `SecretIdentifier` under its Nayeon prefix. No trusted native owner; **HIGH, HOLD** |
| Direct Python storage observation/read | same module `_Advapi32Adapter.read/contains`, `WindowsCredentialBackend.get/is_available` | Real local OS retrieval/availability, not a signed read-only authority | Key bytes can enter the Python process; future protected-read gating needed |
| Lifecycle mutation | `nayeon/secrets/lifecycle.py::BoundCredentialLifecycle.connect/replace/_put/remove` | Calls arbitrary injected `SecretBackend.put/delete` | `_approval_live=None` is expressly accepted for direct legacy callers. Presence rechecks not an atomic compare-and-swap. **HIGH if real WinCred is injected** |
| Onboarding wrapper | `nayeon/brain/credential_onboarding.py::OpenAICredentialOnboarding.connect/replace/remove` | Delegates to lifecycle, fixed `openai.api_key` | Fixed credential ID at this layer does not constrain direct backend callers or grant service provenance |
| Trusted composition | `nayeon/brain/credential_onboarding_composition.py::compose_openai_credential_onboarding` | Injects caller-supplied backend and a validator | Validator can contact provider if explicitly called: **C2 consent missing**. Composition does not instantiate a protected native service |
| Host approval | `nayeon/brain/credential_operation_host.py::TrustedCredentialOperationHost.approve` | Re-observes consent, then calls onboarding operations | In-process approval/clock checks do not bind a native one-use effect actor. No inherited OS authority |
| Coordinator | `nayeon/brain/onboarding_coordination.py::CooperativeOnboardingCoordinator.approve_ui/_approve_recovered` | UI ticket, mutex, journal and recovery-oriented in-process operations | Historical P96 approval-to-effect race comparator remains binding; no native secure IPC or final terminal effect admission |
| Desktop UI | `nayeon/desktop_alpha/first_run_credential_management_window.py::approve_from_button` | Calls `coordinator.approve_ui` using a human-operated Tk window | UI masking and local ticket are **not** independently signed UI provenance or authority for WinCred effects |
| Separate first-run owner | `nayeon/desktop_alpha/first_run_connection_owner.py::TrustedFirstRunConnectionOwner.confirm` | Delegates to injected coordinator | No production-factory/real native service trust proof. Read-only composition/reachability study, not necessarily a live user path |
| Read-only AI service composition | `nayeon/brain/connection_composition.py::compose_provider_ai_service`, `nayeon/secrets/resolver.py::BoundSecretResolver.resolve` | Reads bound backend credential, may be used by a provider | Not a credential mutation path, but secrets can leave storage for provider use. C2 provider validation remains unauthorised |
| Native candidate | `native_c1_candidate/CustodyService.cs`, `ServiceOwnedAdmissionBoundary.cs`, `CandidateCredentialEffectHold.cs` | Denial-only; no trusted WinCred effect adapter; no installable service `Main` | Cannot prevent separately invoked Python DLL calls; **no production GO** |
| Historical original P49 | `tests/p99_original_native_c1_denial/*` | Frozen native effect/service denial baseline | Preserve untouched and SHA-pinned. Never enable legacy disabled flags |

### Observed reachability, not assumed reachability

A source AST inventory of the `nayeon/` product tree at P205 found no executable product-side constructors of `WindowsCredentialBackend`, `compose_openai_credential_onboarding`, `TrustedCredentialOperationHost`, `CooperativeOnboardingCoordinator` or `FirstRunCredentialManagementWindow`. The functions/classes exist, and test harnesses instantiate them with injected fakes. Separate `first_run_connection_window.py` constructs `TrustedFirstRunConnectionOwner` with an injected coordinator; this does **not** demonstrate production composition of a real credential store. A future dynamic installer/runtime authority inventory must repeat this assessment. AST non-reachability is **not** isolation from arbitrary Python imports, plugins, reflection or a malicious process.

### Synthetic negative comparator

`tests/test_p206_unified_effect_ownership.py` uses a `FakeNative` object, **never `WinDLL`**, to show:

1. Original `WindowsCredentialBackend.put/delete` directly delegate a write/delete without a native C1 authority.
2. An arbitrary syntactically valid `other.api_key` reaches the fake store's `nayeon-v1/secret/other.api_key`.
3. `OpenAICredentialOnboarding.connect/replace/remove` can call the fake store without `_approval_live`, demonstrating legacy source capability, not a production execution route.
4. Existing lifecycle and composition fail closed when injected with the dormant refusing P206 adapter.
5. Missing owner, wrong target, forged approval fields, repeated calls, restart/new hold instance and backend faults do **not** create an effect in the candidate.

These are security **findings plus synthetic tests**, not evidence a real key was used.

## 2. Dormant P206 candidate

`nayeon/brain/p206_legacy_effect_hold_candidate.py::P206LegacyEffectHoldCandidate` implements the existing `SecretBackend` shape, but permanently rejects **get, is_available, put and delete**. It owns no storage/transport/native adapter, accepts no caller-selected namespace/approval callback, and provides no `enable`, `authorize`, `reset`, `retry` or dispatch method. It never reveals any candidate secret. This can be injected into existing onboarding for **fail-closed integration tests only**.

**Critical limitation:** The P206 object is **not** wired to production; direct Python calls to the original `WindowsCredentialBackend` remain possible. Even wiring one in-process guard could not secure arbitrary Python code with access to WinCred. Thus P206 is a deny-only integration candidate and design input, not a complete unified admission implementation.

## 3. Required future unified effect-owner architecture (design for external reviewer)

1. **Trusted modern source:** pre-bound Windows file/volume/ancestor identities, signed verified manifests and protected loader; unify Phase 10.1/10.2/10.3/P76 and historical BYOK-B ADS protections under modern authority, never old self-repin.
2. **Trusted launch and IPC:** independently signed/authorised machine-policy-compliant native service and explicit approved native UI; validate both peers through authenticated OS identity, signed executable/loader and secure local transport. UI/IPC messages contain no caller-selected backend or arbitrary credential target.
3. **Single effect actor:** fixed service-owned WinCred target `nayeon-v1/secret/openai.api_key`; only CONNECT, REPLACE and REMOVE with exact operation binding. The native service, **not Python**, owns the WinCred mutation API and memory lifetime. A caller-provided approval boolean or token cannot confer authority.
4. **One-use consent:** service creates candidate/session/operation identity, approved local UI reviews exact action/target, and a protected durable transaction binds peer, candidate and one-use consent. Bind final authorisation and exactly one effect attempt atomically in a service-owned terminal critical section. No stale/replayed/forged/cross-target approval may act.
5. **Crash/uncertainty:** durable pending/inflight/terminal evidence survives restart with ACL/protected source/monotonic identity. Unknown effect outcomes mean RECONCILIATION REQUIRED, not automatic retries or falsified success.
6. **Legacy closure:** remove/restrict Python's direct WinCred write/delete route in production packaging and enforce confinement with approved OS/application policy. Python UI can request operation metadata only through the authenticated service. Any retained Python backend must be read-only under explicitly reviewed policy or unavailable; *do not simply add an optional permission argument or toggle a denial boolean*. Search/trace all direct imports, adapters, plugin/extension launch surfaces and packaging outputs before a real-key pilot.
7. **Test progression:** P207 qualified-design package, P208 pure synthetic service-owned one-attempt actor, P209 durable on-disk custody/recovery candidate, P210 authenticated Windows negative tests and full-path synthetic integration, then externally authorised deployment and three unfiltered product Windows regressions. Preserve P96 and the existing unwaived failures.

## 4. External decisions P206 cannot self-approve

- GOV-01/02 and SEC-03/04 independent qualified Windows-native service, source, authenticated peer, consent, terminal actor, WinCred direct-path elimination and recovery acceptance.
- REL-05/06/07 independent release evidence including installer, rollback, integrity and complete Windows regression acceptance.
- Approved code-signing authority, installed UI/service provenance, Windows Code Integrity/WDAC/Smart App Control policy administrator approval on actual deployment machine.
- Actual local user's explicit, bounded real-key pilot consent **only after R0–R4 GO**, never via chat. BYOK C2 real provider validation remains separate and unauthorised.
- Production P0–P5 and privileged G0–G6 remain OPEN. Full unfiltered accepted Windows product regressions remain **0/3**.
- P135, P175, P178, P179 and PERF-P187-01 are unwaived.

## 5. Genuine Windows evidence and H/C/R recording

`.github/workflows/p206-windows-unified-effect-ownership.yml` runs on genuine GitHub-hosted `windows-2025` event source. The collector authenticates the P205 ancestor, asserts exactly the five additive P206 files, hashes original Python/native source identities, and records the original Windows OS exit and raw log SHA-256 for the 12 synthetic original-Python tests plus frozen P49 20 and current native C1 24 denial cases. All outputs, original C# compiler logs and before/after source custody are archived. Any mismatch is HOLD; failed runs remain evidence. This is **selected** Windows evidence only, not 3/3 regression acceptance.

**Kristian original branch/worktree:** `D:\Nayeon\BYOK_C1_PRODUCT_20261028`, HEAD `e3612279cb972e68e2487702183d5bf5b8f6c4a1` and 17 pre-existing modified/untracked paths. Read-only verification confirmed baseline, and no original worktree mutations are authorised for this checkpoint.

**H/C/R:** H = HOLD (legacy direct effect risk); C = isolated fail-closed candidate pending tests; R = HOLD. Real-key NO-GO; production HOLD; C2 NOT AUTHORISED.

**Review caution:** Passing selected denial tests does not constitute a trustworthy integrated credential effect boundary or permission to enter an API key.
