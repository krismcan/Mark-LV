"""Offline preview controller: no executor, model, credential or side effects."""
from dataclasses import dataclass
from enum import Enum

class ChatOutcome(str, Enum):
    PREVIEW = "preview"
    BLOCKED = "blocked"
    PENDING = "pending"
    EXECUTED_UNVERIFIED = "executed_unverified"
    VERIFIED = "verified"

@dataclass(frozen=True, slots=True, repr=False)
class ChatReply:
    message: str
    outcome: ChatOutcome

    def __post_init__(self):
        if type(self.message) is not str or not 1 <= len(self.message) <= 512:
            raise ValueError("Bounded display message required")
        if type(self.outcome) is not ChatOutcome:
            raise TypeError("Exact outcome required")

class PreviewOnlyController:
    """Default launch mode. All requests remain local and nonacting."""
    mode = "OFFLINE PREVIEW"

    @property
    def has_pending(self) -> bool:
        return False

    def send(self, text: str) -> ChatReply:
        if type(text) is not str or not text.strip() or len(text) > 512:
            return ChatReply("Enter a non-empty request of up to 512 characters.", ChatOutcome.BLOCKED)
        return ChatReply("Offline preview only. No action has been executed.", ChatOutcome.PREVIEW)

    def approve(self) -> ChatReply:
        return ChatReply("No action is awaiting approval.", ChatOutcome.BLOCKED)

    def reject(self) -> ChatReply:
        return ChatReply("No action is awaiting rejection.", ChatOutcome.BLOCKED)
