# Personal Alpha Milestone 3 - Verified Notepad Action via Human Approval

## Implemented
Opt-in trusted Windows command: `python -m nayeon.desktop_alpha --notepad`.
Default `python -m nayeon.desktop_alpha` remains offline-only.
The command activates an existing Nayeon UI and registers exactly one
`OpenAppCapability` via trusted `ApplicationService`, using pinned Windows
App Paths registration and the existing no-PATH-fallback behavior when
Notepad is available. The only accepted user text is `open notepad`.
No shell/argument parsing, arbitrary executable path, provider prompt,
LLM semantic fallback, external tool or model-selected route exists.

The trusted controller constructs a new process-local
`ConversationSession`, `PermissionService(default_allowed=False)` with
only `open_app` granted, `PolicyService`,
`ConfirmationService`, `ActionExecutor`, `AuditService`, and
`VerificationService` (through the executor). The UI never directly
calls the low-level launcher or executor. The `open_app` metadata is
locally overridden to require explicit confirmation; it is
required even for the harmless Notepad demonstration.

## Lifecycle and proof obligations
The UI send button creates a pending confirmation without OS effects.
The reject button consumes the token via `session.reject_pending`.
The approve button invokes `session.approve_pending` with the saved
request and policy recheck; no reconstruction or semantic resolution.
The Notepad service must report an exact trusted Windows registration
before a request or approval proceeds. A missing registration fails
closed. Successful launch alone is **not** verified success:
the controller requires `VerificationStatus.VERIFIED` plus matching
non-secret Notepad executable-identity evidence from the existing
`OpenAppCapability.verify_result`.

No on-device action is initiated automatically by starting the UI or
by testing; a person explicitly clicking Approve is required for a
real Notepad launch. No API key, credential validation, provider call,
voice, memory, general purpose pointer, OS automation, or filesystem
write is in scope. Neither offline GUI nor the Notepad path supports
arbitrary new capabilities.

## Acceptance evidence and limitations
Tests use trusted fake `ApplicationService` values and full real
`ConversationSession` pipeline: no launch before approval,
single-use approve, reject/cancel, whitelist, missing registration,
failed launch receipt, absent/unmatched identity, no LLM and default
permission deny. Full pre/post-seal regression and Codex/master workbook
update follow. The real Windows host was read-only checked and
reported App Paths registration present; **no live GUI click has been
completed by the user** unless separately documented with captured
evidence. Not a release gate. Formal planned phase closures 5/19
and end-user verified acceptance gates 0/12 remain unchanged.

## Further scope
The next milestone must be separately authorized. A production-ready
installer, onboarding UI, AI-backed conversation, accessible keyboard
focus/ARIA analogue, crash recovery, real human acceptance and
general-purpose desktop actions are **not** implemented here.
