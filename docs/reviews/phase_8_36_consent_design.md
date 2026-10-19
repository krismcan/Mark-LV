# Phase 8.36 — Model-ready conversation, consent-bound OFFLINE preview

**Design v0.2 — independent rereview requested, not approved.** 19 October 2026.  
**Draft review PR only. DO NOT MERGE.** No executable product code or release change.  
**Protected product commit:** `b0490cd9e72104a74a32dc5315cbc55bc4034676` (Phase 8.34 fake-only reply lifecycle).  
**Exact remote annotated tag:** `nayeon-v1-phase-8-34-fake-reply-lifecycle-01`; Git tag object `b503ce088ee4a787990534ea862be2936fa55767` peels to that commit.

## Scope and deliberately narrow product claim

Phase 8.36's **first increment** shall provide a user-visible **OFFLINE request review** with an exact, bounded proposed prompt, optional cached provider/model **informational metadata**, and a complete "NO MESSAGE SENT" disclosure. Completing a review returns a fixed **NON-AUTHORIZING offline receipt**. This phase does **not** activate live AI, verify remote model support, establish the presence or correctness of API credentials, authorise data transmission, or produce a real AI response. There is no future-live permission hidden in a saved review ticket.

The existing Save Offline / Reset / Simulate Reply behaviour is unchanged. Never convert offline history into provider input, never forge AI replies, and never turn user/model-generated text into action permissions.

**Required future live-request phase:** separately designed atomic transmission authority and network lifecycle. Any provider-connection metadata, candidate transcript bytes and outbound consent must be re-observed under that future trust boundary, not inherited from this offline-only phase.

## Trusted sources and reviewed exact paths

- `nayeon/desktop_alpha/application.py`, `workspace_window.py`: creator-thread Tk root, pane/window, explicit callback route, lifecycle.
- `nayeon/desktop_alpha/conversation_session.py`: ephemeral OFFLINE/UNSENT status; never implicitly included in a transmission.
- `nayeon/desktop_alpha/reply_owner.py`, `reply_worker.py`, `reply_contracts.py`: sealed fake-only reply worker, fixed status and physical lifetime, not transport authority.
- `nayeon/brain/connection_service.py`, `connection_document.py`, `connection_readiness.py`, `connection_persistence.py`: provider **cached metadata only**, no secret or remote availability proof.
- `nayeon/brain/service.py`, `connection_composition.py`, `providers/openai.py`, `providers/openai_client.py`: existing lazy provider authority. **Forbidden by design in the new offline review ownership graph.**
- Existing tests for callback ordering, reset, undo, thread identity, real root Destroy, and original 8.30–8.34 history/source/tag/index/alias tamper injection.

## Two-stage presentation-before-arm protocol (remediation to P2)

**Stage A, unarmed preview proposal:**
1. The genuine current application's owned Tk callback initiates **Review** on creator thread; mere `human_clicked=True` input is NOT proof of a gesture.
2. Validate the exact NFC prompt (512 codepoints, 2048 UTF-8 bytes; no Unicode control/format/surrogate), root/pane/generation/session/epoch/revision identity, current fake worker fully retired/idle, monotonic clock and optional cached metadata.
3. Create **display-only data**. The review owner is **UNARMED**: it cannot confirm even if a nested callback or directly invoked confirmation method supplies the data or an opaque token.
4. Keep Confirm disabled while rendering the **entire** exact prompt + cached provider/model label (if any) + **explicit NO SEND** disclosure. After **each** potentially reentrant Tcl or callback boundary, revalidate exact root/pane/session/prompt and verify no cancellation, Reset, model/metadata change within owned snapshot, unknown widget state or partial display.
5. If and only if full disclosure is visibly published and final eligibility survives, the trusted owner **arms a new single-use confirmation ticket** and enables Confirm. If enabling has an uncertain before/after effect, revoke the ticket and fail closed. No ticket issued before complete successful presentation can authorise confirmation.

**Stage B, subsequent user-visible offline confirmation:**
6. Confirmation can be reached only from the exact current, root-owned Confirm widget/callback identity and current creator thread; it consumes the **armed** ticket before any reentrant effect.
7. Recheck exact rendered proposal identity, current pane/context, prompt, provider/model **informational snapshot**, expiry, no in-flight worker and all owner generations. A Cancel/Reset/Destroy, changed input or changed internal cached document revokes A. Uncertainty fails closed.
8. Return fixed **REVIEWED OFFLINE / NO AI REQUEST SENT**, without accepting the ticket as network/action authority, creating an AI transcript entry or touching WinCred. Never publish A's status over successor B after nested Save/Reset/Cancel/Close.

**Human-origin boundary:** Tk `button.invoke()` and synthetic UI events are indistinguishable from some programmatic actions to same-process Python code. The first increment can establish **trusted application-owned callback provenance within a non-compromised process**, not cryptographic proof of a physical human. Do **not** call an unvalidated Boolean a human proof. Physical human verification against malicious same-process code is out of scope and must not be asserted as the guarantee behind live transmission.

## Cached configuration validity (remediation to P1)

- `READY_FOR_COMPOSITION` proves only configured metadata eligibility; NOT a valid key, supported model or request consent. No backend or resolver may enter the offline review object graph.
- Within **one** `ProviderConnectionService` instance, a proposal may pin the exact `ProviderConnectionDocumentV1` identity and reject changed/replaced cached docs, including A→B→A with equal string values. This covers **process-local** mutations only.
- **External-writer limitation:** A second `ProviderConnectionFileStore` can write B then A to the same file while the first owner's cached A object remains unchanged. This exact scenario was reproduced with synthetic data on Windows. Neither in-memory object identity nor rereading equal bytes proves that an external write never happened.
- Accordingly, the v0.2 offline UI must disclose **CACHED METADATA / MAY BE STALE / NOT API VERIFIED** and must never claim cross-process freshness or use it as consent/network authority. If metadata cannot be validated even as cached information, display "not configured/unsupported" or refuse preview.
- Any *future live-network approval* requires a separately reviewed authoritative multi-writer coordination/freshness protocol (one shared owner and trusted durable write revision under an OS process lock, or equivalent verifiable revocation tracking). Every permitted writer must participate. A read-before/send without external-write detection is insufficient for byte-identical A→B→A; if an out-of-band writer cannot be accounted for, **HOLD live send**.

## Direct denial of composition and latent capability (remediation to P1)

The offline owner/bridge shall not call **or retain** any of:
- `compose_provider_ai_service`, `AIService`, `OpenAIProvider`, `BoundSecretResolver`, `create_openai_client`, SDK clients, `SecretBackend`, WinCred handlers, HTTP/sockets, process/network executors, tool/action dispatcher, persisted message writer or history loader.
- Review constructor parameters must be exact plain immutable display records, trusted non-secret cached owner and bare Tk widgets/callback identities **on creator thread only**. Reject injected callables, subclassed owner instances and arbitrary responders.
- **Tripwires must cover construction as well as execution**: patch composer entry, provider/resolver/client constructors, secret resolution, SDK loader, HTTP/socket creation, native actions and persistent-file operations; all remain uncalled in the review flow. Audit object graph for latent retained capability; deny worker creation.
- Merely patching `AIService.generate()` does not prove the absence of lazy provider creation; review must assert the stricter denial above.

## Adversarial acceptance matrix before product integration

| ID | Case | Required test result |
|---|---|---|
| A01 | Nested Confirm before full disclosure, during first/last Tcl `configure`, after a partial display | **UNARMED**, no completion; preview revoked |
| A02 | After-effect exception or reentrant Cancel/Reset when arming | No armed ticket, no stale status |
| A03 | Confirm after entire disclosure from distinct valid current callback | One *offline* non-authorizing receipt |
| A04 | Foreign, copied, expired, repeated ticket / wrong thread / root/pane | Reject without consuming successor B |
| A05 | Prompt changed, Unicode invalid, model changed, session reset/navigation | Refuse, no status leakage |
| A06 | Cached in-process metadata A→B→A | Refuse by object identity |
| A07 | External store writes B→A while local cache remains A | Reproduce limitation; do **not** assert external-freshness guarantee or grant live authority |
| A08 | Provider unconfigured/mismatched credential identifier/uninitialised | Fixed local refusal, **no secret read** |
| A09 | Provider/resolver/composer/SDK/socket/action constructors or alternate network path invoked | Explicit negative tripwire FAIL |
| A10 | Save/Simulate Reply/Reset normal paths | Never submit a provider request/review implicitly |
| A11 | Child/Root Destroy during publication/confirmation | No worker/Tcl orphan/cross-thread graph use |
| A12 | Existing 8.30–8.34 historical guard tags, trees, worktree, index and injection seams tampered | Original tests fail closed and reach injected path |
| A13 | Attempt to reuse REVIEWED_OFFLINE receipt for future live transmission | Deny: receipt lacks network authority |
| A14 | Unsupported external mutation detection for actual network send | **Separate future design HOLD**, no implicit support |

## Read-only prototype observations, NOT implementation/security GO

- Selected existing native Windows baseline: **170/170** PASS (7 affected suites plus 8 existing review tests).
- Synthetic pure consent: **19/19**; actual Tk review: **15/15**; cached-metadata owner: **21/21** including direct composition/provider/resolver/SDK/socket tripwires; actual Tk+cached metadata: **10/10**; strict sealed Phase 8.34 input equivalence **1,129/1,129**.
- Most recent combined off-repo candidate test run: **65/65** PASS plus **1,129/1,129** parity cases. These are NOT release regressions. External-writer A→B→A weakness separately **reproduced by synthetic filesystem test**. Tests do not establish full consent security.
- An earlier native Tk research prototype exposed/fixed a stale confirmation status after nested Reset. This remains a required direct-source review concern.

## Git baseline and required release gates

**Actual GitHub tag fact:** `refs/tags/nayeon-v1-phase-8-34-fake-reply-lifecycle-01` is an annotated tag object `b503ce088ee4a787990534ea862be2936fa55767` and peels to `b0490cd9e72104a74a32dc5315cbc55bc4034676`; `refs/heads/nayeon-v1` points to that commit. Older files within the sealed product tree still contain PRESEAL/HOLD text and the tag message references pending postcommit work: those are **documentation/evidence reconciliation questions**. Their text alone does not prove the remote tag is missing. Reviewer must separately validate postcommit regression evidence.

**No product change authorised by this doc:** independent `DESIGN_GO`, specific `SCOPE_GO`, source/test/staged review; exact staged hash inventory, compile/whitespace, true native Tk/adversarial, three full authoritative Windows pre-stage/staged/postcommit runs (not weakened), immutable Git commit+annotated tag, non-force remote verification, original same-ID 16-sheet macro-enabled Drive workbook update/readback and then sanitised dashboard publication. Historical tags/old primary checkout are protected. Phase 8.35 Git batching proposal remains separate security HOLD.

**Pending reviewer decision:** `DESIGN_HOLD` and `SCOPE_HOLD` until v0.2 risks and mandatory tests are independently accepted. Draft PR cannot be merged as a release.
