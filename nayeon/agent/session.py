"""Process-local, sequential ownership of one conversational request lifecycle."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from nayeon.agent.dispatch import DispatchKind, IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionResult, ExecutionStatus
from nayeon.agent.orchestration import PendingStructuredAction, StructuredOrchestrationBridge
from nayeon.intent.model import IntentContext
from nayeon.intent.resolver import IntentResolver
from nayeon.registry import CapabilityRegistry


class ConversationSession:
    """Coordinate open_app without acquiring execution or approval authority.

    Approval/rejection methods are for the trusted caller/UI, never model tools.
    A new action cannot replace a pending one. No history or persistence is kept.
    Use one instance sequentially with the same executor for its entire lifetime.
    """

    def __init__(
        self, *, resolver: IntentResolver, registry: CapabilityRegistry,
        executor: ActionExecutor,
    ) -> None:
        self._resolver = resolver
        self._dispatcher = IntentDispatcher(registry=registry)
        self._bridge = StructuredOrchestrationBridge(registry=registry, executor=executor)
        self._executor = executor
        self._pending: PendingStructuredAction | None = None

    @property
    def has_pending(self) -> bool:
        """Whether local state is retained; expiry is handled on the next operation."""
        return self._pending is not None

    def request(self, text: str) -> ExecutionResult:
        """Resolve, plan, and submit one request; text can never approve an action."""
        if self._pending is not None and datetime.now(timezone.utc) > self._pending.expires_at:
            self.reject_pending()
        if not isinstance(text, str) or not text.strip():
            return self._deny("A non-empty user request is required.")

        resolution = self._resolver.resolve(
            text, context=IntentContext(pending_confirmation=self.has_pending),
        )
        plan = self._dispatcher.plan(resolution)
        if plan.kind is DispatchKind.SYSTEM_CONTROL:
            if plan.intent == "cancel_pending":
                return self.reject_pending()
            # Routed undo uses the legacy executor/UndoCapability lifecycle.
            # Do not bypass it with a direct UndoService or UndoAction call.
            return self._deny("This system control is not supported by the session.", plan.intent)
        if self.has_pending:
            return self._deny("Approve or reject the pending action before starting another.")
        if plan.kind is not DispatchKind.CAPABILITY:
            return self._deny("No supported action was resolved.", plan.intent)

        outcome = self._bridge.execute_with_pending(plan, original_request=text)
        if outcome.result.status is ExecutionStatus.REQUIRES_CONFIRMATION:
            self._pending = deepcopy(outcome.pending)
        return outcome.result

    def approve_pending(self) -> ExecutionResult:
        """Submit only the saved candidate; the executor rechecks all authority."""
        pending = self._pending
        if pending is None:
            return self._deny("There is no pending action to approve.")
        self._pending = None
        return self._executor.approve_and_execute_structured(
            pending.token, capability=pending.capability, request=pending.request,
        )

    def reject_pending(self) -> ExecutionResult:
        """Consume the pending token through the executor without execution."""
        pending = self._pending
        if pending is None:
            return self._deny("There is no pending action to reject.")
        self._pending = None
        return self._executor.reject(pending.token, capability=pending.capability)

    @staticmethod
    def _deny(message: str, intent: str | None = None) -> ExecutionResult:
        return ExecutionResult(ExecutionStatus.DENIED, intent or "", message)
