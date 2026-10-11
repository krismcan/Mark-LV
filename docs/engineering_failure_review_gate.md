# Nayeon v1 — Mandatory Failure & Architectural Regression Gate

**Authority:** Engineering governance; applies to every new product phase and every security-sensitive seal. This rule does not reopen, move or modify existing product tags.

## Principle

**No forward phase progress while a material failure, unresolved incident, security finding, or unexplained regression in an affected trust path remains open.** A green test count alone is insufficient: determine what failed, *why*, which architectural paths share the assumption, and whether the repair is verified.

## Pre-phase retrospective (mandatory)

Before proposing or starting the next product phase:

1. Read the latest sealed milestone review, current Codex state, recent test/review results, incident checkpoints, any STOP conditions, and relevant open issues or workarounds. Do not assume that a prior green run proves the whole architecture is safe.
2. Build a bounded failure ledger with **issue ID, date/source, severity, affected components and callers, observed symptom, reproduction, root cause, repair/containment, regression evidence, independent-review outcome and disposition**. Include historical failures or near-misses affecting the new phase, not just current test failures.
3. Identify architectural dependencies and alternate paths into the affected capability. For permissions, credentials, provider connections, computer control, secrets or audit, trace the full trusted call path and potential bypasses across windows, services, processes, restarts and threads. Include formerly sealed modules where reachable, without indiscriminately reopening unrelated phases.
4. Rank findings as critical/high/medium/low, distinguish confirmed from suspected, and reproduce confirmed issues with deterministic fakes wherever possible. Where real Windows semantics matter, use controlled read-only or fake-only host smoke; **never** introduce live credentials or external provider calls without separate explicit approval.
5. **Gate decision:** stop if critical/high/medium findings affecting the proposed phase remain unresolved, root cause is unknown, behavior conflicts with trust contracts, or verification is incomplete. Low-risk issues may be carried only with documented evidence and explicit user-approved deferral. Never silently waive a failed test or unsafe route.

## Failure response and verification

- On any material test, security-review, tool, build, integration, deployment or smoke failure: **STOP forward progression**. Preserve HEAD, tags, logs, relevant outputs and uncommitted changes. Record the exact symptom and first failing command.
- Classify **product defect versus test expectation versus environment/tool failure** with evidence, not assumption. Investigate cause and impact before trying fixes; do not retry indefinitely or mask errors through timeouts or weakened checks.
- **Five-minute progress watchdog:** if a process shows no clear meaningful progress for five minutes, inspect live output, process identity/state and logs; stop or pivot if stuck. Do not count repeated reasoning/status chatter as implementation progress.
- For architecture/trust failures, create an adversarial test that would fail on the original defect, then demonstrate the repaired behavior; check adjacent callers, shared objects, restart/crash/abandoned-lock conditions, fault injection, UI consent and the Permission -> Policy -> Confirmation -> Execution -> Verification chain as applicable.
- Never weaken sealed invariants, remove tests, use broad exception swallowing, add approval bypasses or label an issue fixed simply to make regression green. **Test-contract migrations** must explicitly document the obsolete expectation, replacement security property, and independent review of frozen source/hash guards.
- Rerun focused, affected, cross-phase and full regressions (no unexplained failures/skips); perform `compileall`, staged diff checks and an independent security review. A successful unit suite is necessary but **not sufficient** to close a systemic issue.
- If a repair creates further findings, repeat investigation and verification. Do not start the next phase until the repaired architecture is independently cleared and the current milestone is sealed, pushed/verified where approved, documented in Codex and logged in the same-ID master workbook.

## Evidence and sign-off

Every phase plan and phase-close review must contain an **Open Failures & Prior-Issues Review** section with: reviewed prior issues and checkpoints, dependency paths checked, severity/disposition, tests added, independent-review result, remaining limitations and a clear **GO / HOLD** decision. Treat missing evidence as **HOLD**, not as implicit success.

**STOP precedence:** security concerns and explicit user stop rules override delivery schedules, phase batching and any earlier approval to continue several phases. New phases require the user-requested approvals; a GO outcome is not permission to use live credentials or provider services.
