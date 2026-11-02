# Phase 10.1 — Vision / Perception Foundation (offline candidate)

Date: 1 November 2026
State: **IMPLEMENTED CANDIDATE / RELEASE HOLD**, not an approved production capture milestone.

## Grounding

The original master workbook **Build Plan** places Phase 10 as *Vision / Perception*,
with dependencies **3, 4, 6**, goal: independent visual-state observation
across model providers. Intended components are screen/camera capture,
Vision Service, UI metadata, privacy controls and verification evidence.

This 10.1 milestone is a proposed sub-increment, not a pre-existing numbered
roadmap item. It introduces **pure, non-capturing contracts only**. It does not
add new execution authority, a UI, provider API integration, persistence,
hardware access, network communication, memory, or autonomous vision.

Source:
`nayeon/perception/contracts.py` and package `__init__.py`.
Tests: `tests/test_phase10_perception_contracts.py`.

## Ownership and trust boundaries

- **Permission / Policy / Confirmation** remain authoritative in the existing
  trusted runtime. An `ObservationRequest` is a *declaration*, never a permit.
- **Capture / OS authority:** no Phase 10.1 capture implementation. A future
  controlled service must validate active, scoped, revocable permission at
  the OS/service boundary before requesting a screen or camera sample.
- **Redaction and content provenance:** `RedactionClaim.REDACTED` is merely
  producer-supplied metadata; neither the schema nor the digest proves pixels
  were redacted, private data removed, or the producer trusted. A future
  trusted adapter must attest those facts; do not accept LLM assertions.
- **Observation request binding:** request, session, source and purpose must
  match. Mismatches, missing redaction claim, stale or future timestamps
  fail closed. Caller-supplied timestamps must come from a trusted clock.
- **Evidence vs outcome:** a `CANDIDATE` assessment establishes only a
  bounded structural and freshness predicate. It never means VERIFIED,
  authorized, acted on, trustworthy, repeat-safe or privacy-safe.
- **Privacy / data minimization:** the schema has no dedicated raw image,
  screenshot, OCR, audio, credential or prompt fields. It carries producer-
  controlled ID strings and a digest which could themselves leak information;
  syntactic validation alone cannot establish their confidentiality.
  Future trusted capture adapters MUST generate non-secret opaque IDs, protect
  or scope the digest, and avoid automatic dataclass repr/logging or persistence.
  Never place raw content, sensitive prompts, API keys or user text into IDs.
- **Replay resistance:** per-request ID binding reduces cross-session mixups
  but does not stop replay using the same ID. Real anti-replay demands a trusted
  one-use grant/nonce store, authority proof, revocation and clock origin.
- **Resource ownership:** this module neither allocates OS capture handles nor
  persists frames. Future services must own cleanup, cancellation, window/
  app boundary validation and revocation.

## Bounded negative cases

1. Missing/oversize/injection-like identifiers, wrong enum types, digest format,
   dimension overflow, boolean-as-integer and invalid clocks are rejected.
2. Session, request, source or purpose mismatch refuses candidate promotion.
3. Unknown/unredacted producer claim refuses promotion; so do stale or
   future timestamps and out-of-range age windows.
4. Immutable dataclasses cannot be modified after creation.
5. Valid redacted-claim metadata is only a *candidate* for an independent
   trusted reviewer, never permission or outcome truth.
6. Current module has no screen, camera, microphone, filesystem, networking,
   subprocess, provider or credential API imports.

## Prior issues and release impact

- **Phase 9:** separate 7-added/20-modified candidate remains isolated and on
  release HOLD. Do not copy its disputed historical fixture changes or attempt
  to complete its blocked repair in Phase 10.
- **BYOK C1 and PRC:** remain on hold. No real credential material or
  provider calls should be activated by Phase 10.1.
- **Legacy source provenance gate:** a live native preflight on this isolated
  branch failed `test_phase8_byok_b_scope_integrity.ExactBYOKBTests.
  test_literal_exact23_parent_manifest_and_live_admission` with
  `AssertionError: Wrong BYOK B product branch` and exit 1. This is the
  *expected, correct* rejection of a new branch by the sealed old gate.
  Do not disable the original guard or edit immutable historical tags.
- **Candidate release sequence:** design and independent security approval
  for a new exact Phase 10 successor gate; test its raw Git/index/disk/
  branch/ancestry/tag allowlist with tamper cases; preserve historical 8.x
  fixtures using authenticated sealed snapshots; obtain focused, affected,
  and three complete native Windows unstaged/staged/one-child regressions,
  independent source review, human seal review, annotated GitHub release
  and same-ID macro-enabled master workbook/dashboard updates.
- **OM v2.1 efficiency:** no full native discovery on known-failing branch.
  Preflight the historical admission route before starting expensive suites.
  Set process-local PYTHONDONTWRITEBYTECODE=1 in authoritative native runs
  (child interpreters may not inherit parent -B).

## Out of scope / not implied by these tests

Production camera/microphone consent, screenshots, redaction correctness,
window-specific capture, privacy quality, vision model interpretation, screen
automation, speaker verification, fake UI evidence as successful outcome, BYOK
or service activation. Additional design and permissions required first.

Status: **10.1 source/focused test candidate only; all release gates open**.
