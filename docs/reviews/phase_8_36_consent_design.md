# Phase 8.36 — Model-ready conversation, consent-bound OFFLINE preview

**Design v0.3 — independent rereview requested, not approved.** 19 October 2026.  
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
5. **TWO SEPARATE NON-OVERLAPPING TRANSITIONS:** (a) After complete preview and final owner/context checks, the owner remains **UNARMED** while the Tk Confirm widget is changed from disabled to enabled. The owner is not capable of confirming before or **during** the `configure(state="normal")` call, including any nested or before/after-effect callback. Any nested Confirm attempt during enable **poisons** the proposal and it must not subsequently arm. (b) Only after the enable call returns successfully, a separate **pure, callback-free, creator-thread state transition** checks all tokens, clock, no poison, widget state, current prompt, pane/session and disclosure snapshot, then issues/arms a fresh one-use ticket. **No Tk call and no user callback is permitted inside this arm transition.** If anything fails, revoke; clear/disable the widget using the existing safe deferred/invalidation path. A nested Confirm triggered by enable can never consume an armed ticket. The UI is not claiming it can detect malicious same-process manipulation.

**Stage B, subsequent user-visible offline confirmation:**
6. Confirmation can be reached only from the exact current, root-owned Confirm widget/callback identity and current creator thread; it consumes the **armed** ticket before any reentrant effect.
7. Recheck exact rendered proposal identity, current pane/context, prompt, immutable provider/model **informational snapshot**, expiry, no in-flight worker and all owner generations. A Cancel/Reset/Destroy or changed input revokes A. A changed upstream metadata cache is **not** guaranteed detectable here; this receipt never authorises transmission and the preview must say it may be stale. Uncertainty fails closed.
8. Return fixed **REVIEWED OFFLINE / NO AI REQUEST SENT**, without accepting the ticket as network/action authority, creating an AI transcript entry or touching WinCred. Never publish A's status over successor B after nested Save/Reset/Cancel/Close.

**Human-origin boundary:** Tk `button.invoke()` and synthetic UI events are indistinguishable from some programmatic actions to same-process Python code. The first increment can establish **trusted application-owned callback provenance within a non-compromised process**, not cryptographic proof of a physical human. Do **not** call an unvalidated Boolean a human proof. Physical human verification against malicious same-process code is out of scope and must not be asserted as the guarantee behind live transmission.

## Metadata snapshot boundary and no writable graph (remediation to second-round P2)

- The **trusted application composition layer**, not a consent owner or Tk review widget, may **once** inspect existing cached provider metadata for display. If it has no current eligible metadata, use a fixed "not configured/unsupported" label. Do not initialize a store or load a file on the preview path; do not resolve credentials or compose a provider.
- Transfer into the review owner/renderer ONLY an **exact frozen primitive display snapshot** (bounded provider string, model string, descriptive source label). The review owner and renderer **must not retain**, even indirectly, `ProviderConnectionService`, `ProviderConnectionFileStore`, a revision observer with a closure to one, `ProviderConnectionConfiguration` holding a `SecretIdentifier`, secret resolver/backend, filesystem path, writable callback, or arbitrary object graph.
- Do **not** send a live owner to the review graph under the label "cached metadata owner": the existing `ProviderConnectionService` retains `_store` with `save()`/file write methods. A merely *read-only use* of a writable service is still a latent capability. A direct object-graph negative test must reject a service/store or a closure that captures either, before presentation/arming; constructor signatures should accept only exact primitive/frozen display types.
- This strict separation intentionally **does not attest cross-process freshness**. Display must say **SNAPSHOT / CACHED METADATA / MAY BE STALE / NOT API VERIFIED**. The review confirmation only proves that the same displayed snapshot was reviewed and returns **no send authority**. An independent writer can perform A→B→A while old in-memory bytes remain identical; a synthetic Windows reproduction confirms this. Do not promise prompt/config freshness beyond the trusted UI snapshot.
- A future *live network* phase requires an independently reviewed authoritative multi-writer revision/provenance protocol (OS coordination or equivalent covering every writer) and a distinct explicit outbound-approval authority; if out-of-band writers are possible, **HOLD live send**. The offline review receipt and informational metadata cannot be reused.

## Direct denial of composition and latent capability (remediation to first-round P1)

The offline review owner/renderer must contain only exact primitive/frozen display values, opaque root/pane token identities and in-memory review lifecycle state. It shall not **call, capture or retain** `compose_provider_ai_service`, `AIService`, `OpenAIProvider`, `BoundSecretResolver`, `create_openai_client`, SDK clients, `SecretBackend`, `ProviderConnectionService`, `ProviderConnectionFileStore`, filesystems/paths, WinCred handlers, HTTP/sockets, network/process executors, tool/action dispatchers, message writers/history loaders or functions/closures pointing to any of them.

The only metadata transfer is via a strict **data-only** constructor; no service/store/read-only revision observer remains reachable from the review object graph. Tripwires must cover provider composition, provider/resolver/client construction, secret resolution, SDK/network and file writes **plus a causal graph-reachability test**, not merely absence of calls in the happy path.

The application trust layer may independently own previously constructed services outside the review graph, but no delegation of those capabilities is permitted through review callbacks. Direct Tk widget references in the renderer do not confer permission to transmit.
 
## Adversarial acceptance matrix before product integration

| ID | Case | Required test result |
|---|---|---|
| A01 | Nested Confirm before full disclosure **and specifically inside Confirm-enable `configure(state=normal)`** | **UNARMED** throughout enable; poison on nested call; never arm late |
| A02 | Enable throws before/after effect; reentrant Cancel/Reset; pure arm after successful enable | No armed ticket on uncertainty; pure arm has zero callbacks/Tk; no stale status |
| A03 | Confirm after entire disclosure from distinct valid current callback | One *offline* non-authorizing receipt |
| A04 | Foreign, copied, expired, repeated ticket / wrong thread / root/pane | Reject without consuming successor B |
| A05 | Prompt changed, Unicode invalid, model changed, session reset/navigation | Refuse, no status leakage |
| A06 | Source snapshot is copied to UI and upstream cache changes after capture | No claim of live freshness; review holds only immutable displayed snapshot; never authorises network |
| A07 | External store writes B→A while local cache remains A | Reproduce limitation; do **not** assert external-freshness guarantee or grant live authority |
| A08 | Provider unconfigured/mismatched credential identifier/uninitialised | Fixed local refusal, **no secret read** |
| A09 | Provider/resolver/composer/SDK/socket/action/file-writer constructors or alternate network path reachable from review graph | Explicit negative tripwire and graph-reachability refusal, including exact writable service/store as constructor argument |
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

**Pending reviewer decision:** `DESIGN_HOLD` and `SCOPE_HOLD` until v0.3 risks and mandatory tests are independently accepted. Experimental v0.2 tests are not proof of the redesigned v0.3 arm/data graph; v0.3 focused tests remain required. Draft PR cannot be merged as a release.
