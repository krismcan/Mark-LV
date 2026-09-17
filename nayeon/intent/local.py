"""High-confidence local intent interpretation for Nayeon."""

from __future__ import annotations

from nayeon.agent.controls import (
    ConversationContext,
    ConversationControlAction,
    ConversationControlResolver,
)
from nayeon.agent.router import TaskRouter
from nayeon.intent.model import (
    IntentContext,
    IntentResolution,
    IntentSource,
)


class LocalIntentInterpreter:
    """
    Resolves intent without semantic AI reasoning.

    It uses:
    1. context-aware conversational controls;
    2. capabilities already known by the TaskRouter.

    Anything that cannot be understood confidently is left unresolved so the
    system-wide IntentResolver can pass it to semantic interpretation.
    """

    def __init__(
        self,
        *,
        router: TaskRouter,
        controls: ConversationControlResolver | None = None,
    ) -> None:
        self._router = router
        self._controls = controls or ConversationControlResolver()

    def resolve(
        self,
        request: str,
        *,
        context: IntentContext,
    ) -> IntentResolution:
        control_decision = self._controls.resolve(
            request,
            context=ConversationContext(
                pending_confirmation=context.pending_confirmation,
                undo_available=context.undo_available,
            ),
        )

        if (
            control_decision.action
            is ConversationControlAction.CANCEL_PENDING
        ):
            return IntentResolution(
                intent="cancel_pending",
                source=IntentSource.LOCAL,
                confidence=1.0,
                reason=control_decision.reason,
            )

        if control_decision.action is ConversationControlAction.UNDO_LAST:
            return IntentResolution(
                intent="undo_last",
                source=IntentSource.LOCAL,
                confidence=1.0,
                reason=control_decision.reason,
            )

        route = self._router.route(request)

        if route.capability is not None:
            return IntentResolution(
                intent=route.capability.name,
                source=IntentSource.LOCAL,
                confidence=0.95,
                arguments={
                    "request": request,
                },
                reason=(
                    "Matched a registered capability using "
                    "deterministic routing."
                ),
            )

        return IntentResolution(
            intent=None,
            source=IntentSource.NONE,
            confidence=0.0,
            reason=(
                "No high-confidence local interpretation was available; "
                "semantic interpretation is required."
            ),
        )