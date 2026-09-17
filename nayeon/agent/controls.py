"""Context-aware conversational controls for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class ConversationControlAction(str, Enum):
    NONE = "none"
    CANCEL_PENDING = "cancel_pending"
    UNDO_LAST = "undo_last"


@dataclass(frozen=True)
class ConversationContext:
    """Current conversational state relevant to control decisions."""

    pending_confirmation: bool = False
    undo_available: bool = False


@dataclass(frozen=True)
class ConversationControlDecision:
    """Result of deterministic conversational-control resolution."""

    action: ConversationControlAction
    reason: str

    @property
    def matched(self) -> bool:
        return self.action is not ConversationControlAction.NONE


class ConversationControlResolver:
    """
    Resolves only high-confidence conversational controls locally.

    This is intentionally NOT a complete natural-language interpreter.
    Anything that is not clear enough for deterministic handling should
    continue through Nayeon's normal routing / AI interpretation layer.
    """

    _UNDO_PATTERNS = (
        re.compile(r"^(please )?undo( that| it| this)?$"),
        re.compile(r"^(please )?revert( that| it| this)?$"),
    )

    _CANCEL_PATTERNS = (
        re.compile(r"^(please )?cancel( that| it| this)?$"),
        re.compile(r"^(please )?stop( that| it| this)?$"),
        re.compile(r"^(never ?mind)$"),
    )

    _CONTEXTUAL_PATTERNS = (
        re.compile(r"^(actually )?scratch that$"),
        re.compile(r"^(no|nah),? scratch that$"),
    )

    def resolve(
        self,
        request: str,
        *,
        context: ConversationContext,
    ) -> ConversationControlDecision:
        normalized = self._normalize(request)

        # Explicit undo/revert while something is still waiting for approval
        # means cancel the not-yet-executed action rather than undoing an
        # earlier completed action.
        if self._matches(normalized, self._UNDO_PATTERNS):
            if context.pending_confirmation:
                return ConversationControlDecision(
                    action=ConversationControlAction.CANCEL_PENDING,
                    reason=(
                        "The referenced action is still pending, "
                        "so it should be cancelled rather than undone."
                    ),
                )

            if context.undo_available:
                return ConversationControlDecision(
                    action=ConversationControlAction.UNDO_LAST,
                    reason="The user explicitly requested an undo.",
                )

            return ConversationControlDecision(
                action=ConversationControlAction.NONE,
                reason="There is no completed reversible action to undo.",
            )

        # Explicit cancellation applies only to work that has not yet run.
        if self._matches(normalized, self._CANCEL_PATTERNS):
            if context.pending_confirmation:
                return ConversationControlDecision(
                    action=ConversationControlAction.CANCEL_PENDING,
                    reason="The user explicitly cancelled the pending action.",
                )

            return ConversationControlDecision(
                action=ConversationControlAction.NONE,
                reason="There is no pending action to cancel.",
            )

        # Common contextual reversal phrases depend entirely on state.
        if self._matches(normalized, self._CONTEXTUAL_PATTERNS):
            if context.pending_confirmation:
                return ConversationControlDecision(
                    action=ConversationControlAction.CANCEL_PENDING,
                    reason=(
                        "The user reversed a request that has not executed yet."
                    ),
                )

            if context.undo_available:
                return ConversationControlDecision(
                    action=ConversationControlAction.UNDO_LAST,
                    reason=(
                        "The user reversed the most recent completed "
                        "reversible action."
                    ),
                )

            return ConversationControlDecision(
                action=ConversationControlAction.NONE,
                reason="There is no pending or reversible action to change.",
            )

        # Important: unknown wording is NOT treated as failure.
        # It simply continues to the normal router / semantic AI layer.
        return ConversationControlDecision(
            action=ConversationControlAction.NONE,
            reason=(
                "No high-confidence local control was detected; "
                "continue normal interpretation."
            ),
        )

    @staticmethod
    def _matches(
        request: str,
        patterns: tuple[re.Pattern[str], ...],
    ) -> bool:
        return any(pattern.fullmatch(request) for pattern in patterns)

    @staticmethod
    def _normalize(request: str) -> str:
        normalized = request.strip().lower()

        normalized = re.sub(
            r"[^\w\s',]",
            "",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized