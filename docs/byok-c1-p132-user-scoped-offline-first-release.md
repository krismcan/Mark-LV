# Nayeon v1 — BYOK C1 user-scoped first-release rescope (P132)

**9 November 2026 | OM v2.1 | DRAFT / NOT RELEASED**

## Authorised scope change

The user selected a **narrower first local BYOK C1**: save/replace/remove an OpenAI API key in the *currently signed-in Windows user's* Generic Credential Manager slot, by a deliberate local UI, without a privileged credential-writing service or live provider validation. Provider validation/connection remains a separate BYOK C2 milestone.

This is a **different threat model**, not a claim that the high-assurance privileged BYOK C1 architecture and its G0–G6 production holds have been cleared. Preserve original P49/P96 frozen code and independent-review evidence. Do not silently merge privileged service, protected journal, local admin/HKLM, signing or trust-root privileges into this first release.

## Existing code reused instead of reinvented

- `nayeon/secrets/windows_credential.py`: already implements a fixed internal generic target `nayeon-v1/secret/openai.api_key`, `CredWriteW`/`CredDeleteW`/`CredReadW` adapter with current-user local-machine persistence and lazy native setup. Existing backend and its previous test suite are not changed.
- `nayeon/brain/windows_onboarding_mutex.py`: existing cooperative Windows logon-session single-writer mutex, holding its kernel handle around each operation. Does NOT block external same-user processes or guarantee cross-store atomicity; no trusted-signer or privileged security root implied.
- Existing Phase 8.27 first-run credential-management UI and `BoundCredentialLifecycle` require a candidate to be provider-validated. P132 intentionally **does not** call them because this first offline local-store milestone must not send a real API key to any provider before C2.
- The default Nayeon offline Personal Alpha CLI and `__main__.py` remain byte-identical. A separate explicit *manual* setup window is added, not started automatically.

## P132 concrete product-facing implementation

**Controller** `nayeon/brain/local_byok_user_scope.py`:
- Exact `WindowsCredentialBackend`, fixed `SecretIdentifier("openai.api_key")`, existing `WindowsOnboardingMutex`. No arbitrary key name/target, model tool, credential export, network, provider validator, HKLM or service.
- `begin(SAVE/REPLACE/REMOVE)` performs only an explicit metadata presence observation and creates an **ephemeral, one-use operation-specific review object**. No candidate is retained and no backend write or delete occurs at review time.
- `approve(exact_review, confirmed=True)` consumes review **before** effect. SAVE requires absent, REPLACE and REMOVE require present; REMOVE also requires explicit destructive acknowledgment; SAVE/REPLACE require exact `SecretValue`. Under one existing cooperative kernel mutex, re-observe slot presence, perform only the exact user-scoped `put` or `delete`, then re-observe **presence only**, never plaintext. Same-presence ABA/external writers are not detected.
- After successful native submission, report `SUBMITTED_UNVALIDATED` or `SUBMITTED_REMOVAL`, not provider-connected, verified secret content or guaranteed persistence. Storage/OS errors, abandoned mutex and unknown outcomes return `RECONCILIATION_REQUIRED` and halt this controller's further mutation. Reconciliation flag is **in process only**, lost after restart; no protected journal or native effect atomicity is claimed.
- On import, construction, default startup or passive display, NO WinCred access. A status check only runs on explicit Refresh.

**User-facing Tk window** `nayeon/desktop_alpha/local_byok_window.py`:
- Launch ONLY by a manual command `python -m nayeon.desktop_alpha.local_byok_window` on Windows after testing/review; separate from normal preview startup.
- Displays current-user and offline/no-validation status, masked key entry that is disabled outside an active SAVE/REPLACE review, and explicit **Review** then separate **Approve**.
- Requires an affirmative confirmation checkbox for every operation; REMOVE additionally requires destructive deletion acknowledgment. Reject/close clears the entry and current review. No key may be read back from WinCred, printed, logged or included in status.
- UI injects exact controller and only creates `SecretValue` transiently after the user presses Approve. Python/Tk plaintext remains memory-resident transiently; masking and best-effort cleanup are **not memory zeroisation or malware resistance**. No cryptographic hardware human-presence proof.
- A local application under the same user security context can still programmatically invoke the controller; this is an intentionally narrower first release, **not a G1 signed trusted-consent broker**.

## Security boundaries and explicit non-goals

1. Windows current-user Generic Credential storage, not a privileged LocalSystem escrow, is the *only* proposed first-release persistent effect. Windows Credential Manager's security isolation depends on the signed-in user's profile and host integrity. It is not immune to malicious processes under the same account.
2. No actual provider validation, API request, startup reading, secret export, telemetry, model-facing tool or background key handling. A saved key is **stored but unvalidated**, not a connected account.
3. No automatic retries after ambiguous error. Direct same-user WinCred mutation can race other applications. The presence check cannot detect replacement ABA or guarantee content/durability.
4. No high-assurance protected journal, independent TPM/HKLM antirollback witness, privileged one-use grants or native service process. G0–G6 for the original privileged route remain **OPEN**, including P96's frozen race and P124's pipe-handle trust gap. Do not reuse or enable that adapter.
5. This branch DOES NOT contain any real key, make native credential writes during testing, or ask the user to paste credentials into ChatGPT. All tests use synthetic non-key fixtures and an injected fake Windows Credential Manager adapter.
6. Do not run unsigned setup binaries on Kristian while Smart App Control is enforced. Do not invoke manual setup with a real key until the signed package/user-scope risk review and release acceptance are complete.

## User-scoped release acceptance / next tasks

P132 is the first implementation slice, not release:
- **U1:** Independent review of user-scope threat model, explicit consent, fixed slot, user-profile storage, reentrancy, deadlock, crash/error and in-memory handling; define residual risks accepted by user.
- **U2:** Windows CI suite with synthetic fake native, genuine Windows Tk callbacks + actual unprivileged OS mutex with fake store; prevent any test write to live WinCred.
- **U3:** Integrate manual setup with the intended consumer product UX in an explicit and reviewable way; protect default offline startup and ensure no hidden backend access or auto-upload.
- **U4:** Separately authorised, signed test build on an isolated/sacrificial Windows user profile for *actual synthetic* `CredWriteW` / `CredReadW` / `CredDeleteW` lifecycle, confirming current-user visibility, replace/delete and failure handling; not on Kristian's real credential slot without explicit approval. API keys not necessary for this acceptance.
- **U5:** Production package signed, Smart App Control accepted, and full end-to-end application testing, including the OM v2.1 three Windows product regressions. Only after security review and explicit release approval should a real key be entered LOCALLY. Never submit it to a chat.
- **U6:** On a genuine completed release, first reconcile the **original Google Drive master workbook**, then dashboard. Draft PRs/source tests are not releases and do not trigger workbook update.

**Disposition: P132 production-facing OFFLINE user-scoped functionality in review. High-assurance BYOK C1 production release HOLD and all historic G0–G6 gates unchanged.**
