"""Pure local request data. Construction/encoding is never consent or dispatch.

No caller is wired in Increment A. Receipts describe local data only; they do
not attest a human gesture and cannot authorize any future effect.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json

from nayeon.desktop_alpha.conversation_session import validate_offline_text


DISCLOSURE = (
    "LOCAL REQUEST DRAFT — MODEL AVAILABILITY UNCHECKED — NOTHING SENT"
)
RECEIPT_TEXT = "NO REQUEST WAS SENT"
MAX_MODEL_CHARACTERS = 80
MODEL_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
)


def _validate(provider: str, model: str, prompt: str) -> None:
    # Exact types precede all comparisons, iteration and encoding. Never call
    # user-supplied __str__, equality, iteration or JSON conversion hooks.
    if type(provider) is not str or provider != "openai":
        raise ValueError("DRAFT_PROVIDER")
    if (type(model) is not str or not 1 <= len(model) <= MAX_MODEL_CHARACTERS
            or any(character not in MODEL_CHARACTERS for character in model)):
        raise ValueError("DRAFT_MODEL")
    validate_offline_text(prompt)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class OfflineRequestDraft:
    """Immutable metadata and one literal prompt, with no authority fields.

    Model syntax is an ASCII allowlist, not proof of provider availability.
    Only the exact class is an encoding source, including unbound to_json use.
    """

    provider: str
    model: str
    prompt: str

    def __post_init__(self) -> None:
        if type(self) is not OfflineRequestDraft:
            raise ValueError("DRAFT_SOURCE")
        _validate(self.provider, self.model, self.prompt)

    def to_json(self) -> str:
        """Return fresh deterministic JSON text; never execute or send it."""
        if type(self) is not OfflineRequestDraft:
            raise ValueError("DRAFT_SOURCE")
        # Recheck even objects forged via low-level Python construction. Python
        # immutability is a data contract, not isolation from hostile Python.
        _validate(self.provider, self.model, self.prompt)
        return json.dumps(
            {"model": self.model,
             "input": [{"role": "user", "content": self.prompt}]},
            ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        )


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class OfflineDraftReceipt:
    """Local NO_SEND data bound to a draft, never a confirmation ticket."""

    draft: OfflineRequestDraft
    status: str = field(default=RECEIPT_TEXT, init=False)
    disclosure: str = field(default=DISCLOSURE, init=False)
    permits_network: bool = field(default=False, init=False)
    permits_action: bool = field(default=False, init=False)
    permits_persistence: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self) is not OfflineDraftReceipt:
            raise ValueError("RECEIPT_SOURCE")
        if type(self.draft) is not OfflineRequestDraft:
            raise ValueError("DRAFT_SOURCE")
        _validate(self.draft.provider, self.draft.model, self.draft.prompt)
