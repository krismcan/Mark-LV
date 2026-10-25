# Phase 8.36 independent design + exact scope request — v0.4

**Review exact doc-only commit on draft PR #1, not v0.3.** Product at sealed Phase 8.34 parent `b0490cd9e72104a74a32dc5315cbc55bc4034676`. **DO NOT MERGE OR START LIVE AI.**

This review addresses Codex v0.3 findings from **19:18:44–45Z**:

1. **P2 DESIGN_HOLD: pure arm widget-state contradiction.** New design keeps owner **UNARMED** while Configure runs and through a separate real Tk `instate(("!disabled",))` observation. The creator-thread pure arm transition happens only after that state query successfully returns and all exact identities/context are revalidated. The pure transition performs NO Tk call. Critical canary: instrumented `configure(state="normal")` returns normally but leaves Confirm DISABLED; cannot arm. Query callback reentrancy canary also required.
2. **P2 DESIGN_HOLD: callback closure captures application/writable service.** Instead of passing a provider metadata owner into an app that is reachable from widget callbacks, v0.4 **removes all optional provider metadata inspection from the initial increment** and prohibits composition/retention of ANY provider connection/file store/service/resolver/client in the application and new review graph. Display is literal "MODEL NOT CONNECTED — OFFLINE PREVIEW ONLY". A09 closure/bound-object/partial graph test must find a deliberately injected provider service/store even when reachable via application callback, and refuse before arm. The existing presentation profile path is separate and unchanged.
3. **P2 SCOPE_HOLD: unspecified file envelope.** v0.4 explicitly enumerates increment A (2 files), B (4 files), C (13 files), exactly **19 distinct approved-path candidates**, MODIFIED or NEW, and enumerates exclusions. No products/tests may be edited outside the approved per-increment envelope. Reviewer must inspect existing 8.30–8.34 source/integrity guards and decide whether every path is sufficient; if not, **SCOPE_HOLD with exact additions and tests**, not a wildcard.

Please return **SEPARATE DESIGN_GO/DESIGN_HOLD** and **SCOPE_GO/SCOPE_HOLD** with numbered findings, severity, exact causal source evidence and bounded test canaries. Evaluate whether the narrowed feature has meaningful minimum offline-user value without implying it is real AI. Do not grant an implementation GO based on off-repository v0.3 prototype tests, and do not treat sealed 8.34 historical docs' obsolete PRESEAL text as proof the remote annotated tag is missing.

Future outbound consent, multiwriter provider freshness, real credentials/network, model action and app installer are **outside 8.36**. Reject any attempt to reuse the offline review receipt as send authority.

No live calls. No merge. No product commit yet. Historical Git tags, user primary checkout, canonical same-ID Drive master workbook and public product metrics remain unchanged.
