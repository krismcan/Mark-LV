# P207 — Trusted Native Admission and Consent: Design Acceptance Dossier

14 November 2026 · OM v2.1 · Parent P206 `d2e31ecc53e7e4c115b00bb527dcc7eb9723d2e9`
**Disposition: DESIGN REVIEW PACKAGE / ENGINEERING TEST CANDIDATE ONLY. NOT independent acceptance, trusted-service admission, real-key pilot or production release.**
Real-key R0–R4 NO-GO · Production P0–P5 HOLD · G0–G6 OPEN · 0/3 complete unfiltered Windows regressions.

## Source-grounded architectural finding requiring a formal policy decision

P132 `nayeon/brain/local_byok_user_scope.py::compose_user_scope_local_byok`
constructs `WindowsCredentialBackend`; `LocalByokController.approve` directly
delegates SAVE / REPLACE / REMOVE to the backend's real `CredWriteW` /
`CredDeleteW` capability after only local in-process review. P133 exposes that
route from `workspace_window.py` Connection-page button, `application.py`
`_open_local_byok`, `local_byok_launch_bridge.py` and
`local_byok_window.py`. Source launch uses `sys.executable -B -m`.
P140 frozen-launch pin gate currently refuses unsigned/unapproved builds.

P132 is a **separately authorised reduced current-user design direction**, not
itself a production approval or a privileged C1 service. It is fixed to
`SecretIdentifier("openai.api_key")` at its controller, and its mutex +
re-checks are useful cooperative protections. They cannot establish signed
consent provenance, OS isolation from other same-user processes, an immutable
service-owned terminal effect actor or persistent recovery after power loss.
The controller enforces **exact WindowsCredentialBackend type**, so the P206
`P206LegacyEffectHoldCandidate` cannot simply be injected. Its in-memory
`_uncertain` latch is lost on restart. Real executable source route and a direct
independent general Python backend API coexist.

The privileged high-assurance C1 candidate separately has
`native_c1_candidate/CustodyService.cs` and
`ServiceOwnedAdmissionBoundary.cs`: native terminal admission **always
denies**. There is no deployable service Main, signed consent agent,
authenticated pipe, durable one-use admission or authorised effect adapter.
P49 original and P96 race comparators must remain frozen.

## Proposed ownership decision, to be signed by external GOV/SEC policy owner

- **Option A — High-assurance BYOK C1 (recommended for R0–R4):** one signed
  service owns the target and WinCred effects; signed local UI conveys only
  explicit operation intent over authenticated, tightly constrained IPC.
  Package must remove or deny *all* independent Python direct CredWrite/
  CredDelete reachability: P132 controller + its factory and launcher,
  general `WindowsCredentialBackend`, legacy `BoundCredentialLifecycle` paths,
  plugins/action surfaces and unsanctioned runtime interpreters. The native
  service enforces exact source identity, UI peer, target, consent issuance,
  one-use transaction, durable no-retry journal, and an exclusive terminal actor.
  Same-user WinCred access not mediated by the service must be addressed by
  actual OS/application policy or migration to a protected service-owned store;
  a Python bool/optional permit does not establish isolation.
- **Option B — Separate reduced user-scope release:** complete independent
  P132/P133 U1–U6 external threat-model acceptance, approved code signer and
  installer, native synthetic tests on isolated test profile, documented
  same-user malicious-process/ABA/restart uncertainty risks and three full
  product regressions. Such a release is not the privileged C1 R0–R4 GO,
  must be distinctly named, signed and represented, and cannot inherit any G0–G6
  proof. This branch remains a DRAFT.
- **Mutual-exclusion requirement:** no bundle may silently offer both effect
  paths as alternatives under a single high-assurance C1 approval. The signer,
  installer, policy owner and reviewers must enumerate all machine images,
  Python/script sources, child processes and backend import paths and approve
  one complete effect boundary before a real-key pilot.

**Engineering can prepare both documents and fake adapters, but cannot choose
release trust policy or certify the machine Code Integrity controls.**
Option A remains the target for P208–P210 synthetic engineering unless the
responsible human security/governance owner authorises a different architecture.

## Proposed Option A trust-boundary contract for reviewer response

| Boundary | Invariant / acceptance evidence | Current proof |
| --- | --- | --- |
| Source admission R0/G0 | Signed image and manifest tied to protected, immutable source + loader and pre-bound Windows FileId/volume/ancestor including ADS refusal and Phase10/P76 | P201/P202/P204 review candidates only; not integrated |
| Signed UI G1/R1 | Locally explicit, installed/signed UI; authenticated SID/session/image/process provenance; operation/target presented unambiguously | P132 Tk is not signed provenance |
| IPC R1 | Trusted Windows peer identity from kernel, no caller-selected credential namespace, freshness + channel binding and impersonation safety; reject duplicate/session cross-use | No production IPC |
| Service G2/R2 | Service owns candidate, approval issuance and final one-use decision; exact immutable operation/target; no Python mutation | P49/C1 native candidate denial only |
| Effect actor R2 | Commit protected IN_FLIGHT once under same native terminal lock as revoke/fault/stop; invoke fixed WinCred call max once; unknown OS outcome never auto-retried | Synthetic P110 evidence only |
| Durable G3/R3 | Protected ACL+integrity, crash-safe journal, restart antirollback, pending/attempted/terminal recovery and one-way reconciliation | P132 in-process `_uncertain` lost on restart |
| Packaging R4/P3 | Qualified Windows signer and code-integrity policy administrator approves signed binaries and source execution on actual target machine | Unapproved |
| Product P0/P2 | All legacy/direct WinCred routes closed or separately excluded by enforced OS/installer boundaries; three unfiltered Windows product regressions accepted | No: 0/3 |
| External review P1 | GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 independent positive decisions and G0–G6 | All open |

The chosen actor must distinguish CONNECT/SAVE, REPLACE, DELETE only at its fixed
`nayeon-v1/secret/openai.api_key` identifier; destructive acknowledgement is
mandatory on delete. The UI must never pass a raw secret or bearer approval via
a model/tool/chat interface, and provider validation is C2, not C1. Atomic
consumption and first effect attempt must be service-owned; a provisional
`approved` boolean returned to Python is not an effect permission.
After an uncertain effect, return RECOVERY_REQUIRED, preserve protected state
and perform no automatic retry. Review and approve every state transition,
including reconnect and service process restart, under the same original source
authority. Every future test must preserve P96's approval-to-effect race negative.

## P207 actual-source synthetic negative package

`tests/test_p207_user_scope_native_consent_review.py` executes P132 real
controller methods with an injected `FakeNative` adapter and fake mutex.
No Advapi32, Windows Credential Manager, real key, provider, service or signed
installation is invoked. It proves review-only is inert, explicit confirmation
can reach the fake store, stale/replayed reviews refuse, deletion requires
acknowledgement, post-fake-effect errors latch only the existing instance,
a fresh controller loses the uncertainty latch, the P206 holder cannot replace
the P132 exact type, and the direct old backend attempts broader namespace
mutations. These are source-grounded risk observations; don't convert a
known-negative into an acceptance pass by weakening test assertions.

The hosted Windows collector pins the P206 parent, all unchanged original
source via Git tree custody, exact P207 changed paths, and runs the original
P132 fake-native functional suite, P206 fake-path/hold suite, P207 source
negative suite, original P49 native 20 and current C1 host native 24. Preserve
genuine Windows OS exit codes, SHA256 member logs, before/after Git source
identities, H/C/R with archives on success **and** failure. Selected tests do
not count as full product regressions.

## Reviewer questions and nondelegable decisions

1. Which *mutually exclusive* threat model is intended as **the** upcoming
   real-key pilot? Who signs acceptance of legacy same-user risks?
2. Can actual managed Windows image policy prevent arbitrary same-user Python
   processes from calling WinCred, or must sensitive credentials move into
   separately access-controlled native service custody? Show proof, not design.
3. What documented trusted signer, service identity, UI image provenance,
   named-pipe ACL/peer check, replay barrier and authorisation source implement G1?
4. What protected journal, atomic terminal effect actor and restart recovery
   prevent P96-like approval-to-effect transfer and ambiguous automatic retries?
5. Which independent reviewers own GOV-01/02, SEC-03/04, REL-05/06/07, and
   what precise evidence will constitute their formal signed positive decision?
6. Has the authorised machine administrator accepted installer/Code Integrity/
   WDAC/SAC policy on Kristian or an approved separate pilot profile?
7. Has the original Google Drive MASTER workbook been read back, and only
   after actual release approval? Draft P207 must not mutate production records.

## Outcome classification

P207 can close as **review-package engineering** after its honest
source-bound Windows tests. It CANNOT close as independent design acceptance
until qualified reviewers sign those decisions. Engineering continues to P208
with strictly synthetic service-owned terminal admission; no real credentials,
no native effects, no service activation, no production merge.
