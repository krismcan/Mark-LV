# Phase 8.34 — Fake-Only Reply Lifecycle: Independent Review & Release Evidence

Date: 18 October 2026. Branch: `nayeon-v1`. Protected parent: `1a972d1d292597239c938d53437218c536b5bf3f`. Immutable Phase 8.33 tag: `nayeon-v1-phase-8-33-offline-delayed-completion-01`, tag object `0b5bb13d0ea8847ead6e05d4cd12af57a891d5a0`.

## Product boundary

Only an explicit human click can initiate bounded **SIMULATED / NO AI REQUEST** fake-only reply. No real OpenAI or other provider requests, keys, Windows credential writes, autonomous desktop action, arbitrary model text or network transport. The native worker produces fixed allowlisted output with exact request/context/ticket ownership; Tk root creator thread alone polls, joins and renders. Cancel, Reset, pane navigation, root destruction and stale/reentrant callbacks fail closed. Physical worker retirement and strong graph ownership are mandatory. Offline Save, Reset and settings retain their separate sealed authorities.

## Design and bounded source evidence

Independent DESIGN_GO and SCOPE_GO for RFC v0.2 preceded implementation. Pure owner/worker Increment A independent SOURCE_GO after two confirmed MEDIUM repairs (public worker import alias and failed Thread.start retirement); native 42/42 focused PASS. Tk Increment B lifetime read-only SOURCE_GO; source UI reviewer initially found one MEDIUM: cancellation-notice publication fault after displaying a preview could leave previous-session text through confirmed Reset. A first scoped repair added precommit preview invalidation and eight adversarial tests, Windows host 231/231 affected PASS.

Independent rereview identified two further MEDIUM reentrant callback interleavings: a before-effect reply publication could reenter Reset and paint old output after new-session commit; and Cancel during B admission could leave previously displayed A. Bounded scoped repair added serial/pane-bound deferred invalidation, busy-reset refusal and fresh-review requirement, plus two native Tk adversaries. Independent rereview issued SOURCE_GO for those two findings (report `C:\Users\krist\AppData\Local\Temp\834_m2m3_independent_source_result.txt`). Native host Windows Python 3.12.10 compiled source/tests successfully and ran 233/233 focused and affected tests PASS, exit 0; two initial repair-iteration test/static contract failures were corrected without weakening the historical guard.

## Scope and security gates

Exactly 20 revised-RFC paths: 10 added and 10 modified; see `tests/phase_8_34_scope_migration.py` for literal manifest and raw SHA-256 pins. Frozen 8.33 branch/HEAD/tag object/tree and predecessor 8.30–8.33 adversarial guard paths remain active; public production admission routes through exactly one 8.34 successor, fail-closed on stale/alias/disk/index/tree/commit deviations.

**PRESEAL CHECKPOINT, NOT A RELEASE CLAIM.** Final independent exact 20-path staged review, whole-suite native Windows prestage/staged/postcommit passes, new immutable commit and annotated tag, GitHub remote verification, original same-ID 16-tab Drive macro-enabled workbook append/readback and public dashboard deployment all remain required as of authoring. Do not infer any of these from a successful focused test. Stop on HIGH/MEDIUM, failed test, native Tcl stderr warning, changed scope or stale remote evidence.

Formal overarching architecture completion remains 5/19 and user release acceptance remains **0/12**. Phase 8.34 is fake-only product-level, not a live conversational assistant or consumer release.

## Final Save-boundary security repair (18 October 2026)

An independent cross-component review found a MEDIUM stale simulated-reply preview on accepted Offline Save: A could survive cancellation-notice failure, or nested Save could commit B while A was being published. A first scoped repair introduced serial-bound preview invalidation and nested-publication refusal. Native Windows run: 236 PASS and one preserved 8.33 regression FAILED (nested offline Save during no-worker destroy timer cancellation). The next independent source review found a further MEDIUM: committing B before clearing its predecessor could leave A displayed if both clear and hide failed.

The final scoped repair separates the sealed worker-free destroy-hook Save from prohibited reply-publication reentrancy, requires successful clear/hide BEFORE successor commit, rechecks issuing owner/root/view/serial/snapshot identity after reentrant seams, and revokes the issuing-owner ticket on exit. Double-fault preserves A and poisons reply admission without committing B. Native Tk adversarial tests cover final widget effect, notice failure, double-fault, historical destroy-hook, stale identities and rejected input.

Authoritative Windows Python 3.12.10 compileall PASS; 241/241 focused and affected PASS, exit 0. Historical 8.33 files remain unchanged. Independent bounded source rereview SOURCE_GO, no remaining HIGH/MEDIUM in Save repair. Reviewed SHA256: application.py 035F5C8D6EA131B1DD4BB3AA061FF96662D1B926C4321E9A1BFE2EEF700181E7; test_phase_834_tk_reply.py D0971F1E6FF6D5AE6444F10E2DA0903E6A1F02B51F8D677F34B0E427394DCE94.

SOURCE_GO is not a release GO. Exact 20-file manifest pinning, adversarial and whole-suite pre-stage/staged/postcommit regressions, independent exact staged review, annotated commit/tag, GitHub verification, canonical same-ID Drive update and public dashboard validation remain required. No live model/provider calls.
