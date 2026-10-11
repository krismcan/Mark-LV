# Phase 8.28 — Trusted metadata confirmation, cooperative persistence, conservative recovery

**Date:** 11 October 2026. **Protected starting HEAD:** `8d46efddbb06db55ca97cc6b1f48b1fc7312eee2` on `nayeon-v1`, clean, prior full regression 2,111/2,111.

## Approved architecture and bounded implementation

- The new `TrustedMetadataCommitHost` (separate from `TrustedCredentialOperationHost`) creates a single-use, expiring, process-local confirmation review of **SAVE** canonical OpenAI provider/model metadata or **CLEAR** only that metadata. It holds no pending secrets; confirmation is entered only by a trusted human UI callback. Review does no persistence.
- Typed canonical record is created through existing `parse_provider_connection_document`. Saved metadata must reference exactly `openai` and `openai.api_key`; model identifiers must satisfy the existing schema. Unsupported, malformed, changed or unreadable metadata cannot be overwritten by this workflow.
- Approval **consumes** the pending review before side effects. Deadline is checked with an injectable monotonic clock, finite bounded timeout maximum 300 s; wrong type, expired review, missing review and repeated approvals fail closed.
- Approval acquires the **same exact Windows-session named mutex** as credential coordination, and uses the **same in-flight marker path**; a credential action cannot safely overlap with this cooperating metadata write. No lock is held through human think-time. It compares a typed, non-secret document and file identity before and after the human review, then rechecks under lock before any mutation.
- The previously sealed `ProviderConnectionFileStore.save` persists a single typed document via same-directory temporary file, file fsync and replacement. Post-save the host re-reads the typed metadata twice and rechecks the file identity under lock. Only a verified target document and successful marker removal return `VERIFIED`, meaning the **immediate metadata reread** alone, not disk durability, provider connection, credential state, token validity or transaction atomicity.
- A prior recovery marker blocks new requests. Abandoned mutex, uncertain save (including after-effect exceptions), post-save mismatch or marker cleanup error preserve a marker and demand separately authorised human reconciliation. No auto retry, deletion or rollback.
- CLEAR replaces the metadata record with an explicit empty connection document. **It does not delete any credential**. No Windows Credential Manager functions, secret lifecycle methods, provider SDK or live API calls are imported or invoked from this phase.
- The standalone `FirstRunMetadataManagementWindow` is injected with an exact trusted metadata host; it offers explicit Review save, Review metadata-only clear, Reject, and separately Approve buttons. CLEAR requires a distinct acknowledgement that the key will be retained. No action runs on launch; invalid/expired/conflict cases show fixed safe messages. No model-callable route.
- Both coordination and persistence are cooperative-only, without external-writer protection, credential CAS, general filesystem CAS, cross-store transaction, atomic directory durability or guarantees of catching same-state ABA. The existing 8.27 credential interface remains unchanged.

## Required verification before product seal

1. Focused fake-only tests for canonical creation/model change/idempotence, explicit clear, no credential effects, review reject/replay/expiry, mutex busy/abandoned, marker recovery, metadata ABA conflict, malformed/unsupported state, interrupted/after-effect failures, post-save re-read mismatch, failed marker operations, and non-secret receipt restrictions.
2. Genuine local Windows Tk withdrawn-root callback acceptance for save and clear with explicit acknowledgement. No live credentials, real provider calls or native Windows Credential Manager writes.
3. Review diff for authority boundaries; update historic exact-source inventories only for the two added production modules, and preserve all prior frozen production hashes.
4. Focused/affected tests, full test discovery, compileall, diff check, exact staged scope, seal-time and post-commit suite, product commit and immutable annotated tag, GitHub branch/tag peeled verification, Codex handoff.
5. Update original same-ID master Google Drive `.xlsm` in place, preserve 16 sheets, verify fetched bytes. Formal Phase 8 IN PROGRESS, 5/19 formal phase exits and 0/12 release gates until independently completed.

No phase is closed or production-ready until every required seal and master workbook gate is verified.

## Second-pass trust-boundary review and pre-seal evidence

Source and AST review: the metadata confirmation host has no import or call path into a credential backend, resolver, key-value secret contract, validator, provider SDK, application dispatcher or model-callable capability. The presentation layer has no file persistence or native Windows API path; its only write path is `TrustedMetadataCommitHost.approve(human_approved=True)`, only from an explicit Tk button callback. The shared `WindowsOnboardingMutex` class and `.nayeon-onboarding-inflight` marker name match the sealed Phase 8.26 credential coordinator. A test exercises an in-flight credential marker blocking metadata review.

Defensive model input check additionally rejects recognizable secret-token prefixes in the model field before document parsing (defence in depth only, not a universal secret classifier). Key-backed state is never read. Immediate post-save typed rereads detect many conflicts but cannot provide true compare-and-swap, atomic directory durability or protection against arbitrary external writers. A synthetic exception raised *after* a successful file replacement is correctly quarantined with the recovery marker left in place.

Focused Phase 8.28: 31/31 passed, including two genuine Windows Tk callback cases, exclusively with temporary metadata and fake locks. Affected metadata/credential guards passed after adding only the two new module paths and exact document/store consumer. First full host Python regression: 2142/2142 passed. Exact staged-seal and post-commit reruns, remote refs and original master workbook remain separate, mandatory gates.

No external independent human/Codex reviewer opinion is claimed by these tests; source inspection and separate verification layers provide bounded evidence only.
