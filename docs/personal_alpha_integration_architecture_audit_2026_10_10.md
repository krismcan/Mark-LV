# Nayeon v1 - Integration architecture audit (Personal Alpha milestone 1)

## Baseline and purpose
Audited clean `nayeon-v1` HEAD `21c3eba76687a5d1fae192e24fe15cfa3bd22589`
after sealed Phase 8.14: **1,970/1,970** deterministic regression.
This is a *read-only architecture decision and verification milestone*.
It adds no runtime authority and does not close a formal end-user release gate.

## Actual reusable components
- `nayeon.agent.session.ConversationSession`: owns sequential request and
  saved pending action; explicit `request`, `approve_pending`,
  `reject_pending` methods. Natural language never approves an action.
- `nayeon.intent.local.LocalIntentInterpreter` with `TaskRouter`,
  `IntentResolver`, `IntentDispatcher` and
  `StructuredOrchestrationBridge`: deterministic local-first dispatch.
- `nayeon.registry.CapabilityRegistry` and
  `nayeon.capabilities.open_app.OpenAppCapability`: existing structured
  `open_app` tool, no generic model-selected executable authority added.
- `PermissionService` (default deny), `PolicyService`, the executor-owned
  `ConfirmationService`, `ActionExecutor`, `AuditService`,
  `VerificationService`, and `UndoService`: existing action trust path.
- `ApplicationService` and `resolve_notepad_definition`: trusted Windows
  App Paths read, exact file check, observed process executable identity and
  bounded observation.
- Python 3.12 Windows runtime has Tkinter 8.6: no new pip dependency required.
  Legacy root `main.py` and `ui.py` must NOT be wired in.

## Identified boundaries and blockers
1. A `LaunchResult.success=True` means the launch call returned, **not**
   that a target was verified. Only `VerificationStatus.VERIFIED` with
   matching identity is a verified outcome; otherwise show indeterminate or
   failed without invented success.
2. `ApplicationService.launch` accepts general targets; the alpha UI must
   not directly expose it. Trusted host wiring shall register *only*
   `open_app` and default-deny permissions except explicitly scoped
   `open_app`; additionally constrain the GUI command to the exact local
   Notepad wording and reject all other prefixes/targets before session
   dispatch. Approval uses `ConversationSession.approve_pending` only.
3. Application identity can be unavailable without trusted App Paths. In
   such a case a local alpha run must fail closed before launch, and cannot
   claim end-to-end demonstration evidence.
4. The current 8.10-8.14 onboarding contracts are read-only projections,
   not secure consent, credential persistence, live entitlement or a
   configured provider. This tranche is **offline/local only**; no keys,
   SDK requests or provider activation.
5. The UI must not show confirmation tokens, arbitrary execution output,
   platform errors, user secrets or raw provenance. Use only bounded
   `ExecutionStatus` / `VerificationStatus` for messaging.
6. Tkinter widgets must be created and touched on the owning main thread;
   no background actions, timers, orchestration loops or auto approval.
   Session actions are explicitly user-triggered buttons.
7. Refuse a second request while a pending confirmation exists; enforce
   button state from `session.has_pending`. No model request can invoke
   accept/reject.
8. The existing historical regression guards freeze broad production trees.
   If new alpha modules require explicit scope additions, amend only exact
   file inventories or observed typed consumer graphs. Never relax live
   authority checks.

## Approved bounded implementation milestones
### Milestone 2: minimum local chat GUI
A new isolated `nayeon/desktop_alpha/` package, standard-library Tkinter
window, with a narrow injected session-style UI controller. The controller
sanitizes results to stable statuses and safely separates execution from
verification; Tk widgets never instantiate permissions, action executors or
tools. Start in an **offline, non-acting preview mode**, allowing user
requests to be displayed as non-executing messages. Show explicit disabled
or unavailable action status. Tests should use fake controller and Tk-free
headless contracts. This stage is *not* a functional release gate.

### Milestone 3: verified, approval-bound Notepad
A dedicated trusted host factory creates the existing `ConversationSession`,
with only Notepad, explicit permission, mandatory confirmation, local-only
resolution, existing services, audit and verification. It must reject any
non-Notepad command or missing trusted App Paths before submission. No
generic launch, raw path, shell, arbitrary executable or model-selectable
route; approval/rejection via a real GUI button. Fakes must demonstrate:
no launch before confirmation, cancel, single approval, rejection of
substituted target, deny/no configured path, launch failure, unavailable
observation, and **verified only with exact executable identity match**.
A controlled real Windows smoke is optional and must never operate without
explicit user action; report its status separately.

## Acceptance and tracking
Milestone 1: report + clean full regression + doc-only sealed commit/tag,
remote refs, Codex state and master workbook. Milestone 2 and 3 use their
own exact scoped commits, full pre/post-commit regression and remote
verification. Formal readiness remains **5/19 phase exits and 0/12
verified release gates** until reproducible complete user journeys qualify.
