"""Presentation-only names and preference references; no runtime authority."""

from __future__ import annotations

from dataclasses import dataclass


def _validate_string(value: str, maximum: int) -> None:
    if type(value) is not str:
        raise TypeError("Presentation value must be an exact built-in str")
    if not 1 <= len(value) <= maximum:
        raise ValueError("Presentation value length is outside the allowed range")
    if value != value.strip():
        raise ValueError("Presentation value must not have surrounding whitespace")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("Presentation value must not contain control characters")


def _validate_optional_string(value: str | None, maximum: int) -> None:
    if value is not None:
        _validate_string(value, maximum)


@dataclass(frozen=True, slots=True, repr=False)
class AssistantPresentationIdentity:
    """Assistant display and wake names, distinct from trusted action identity."""

    display_name: str = "Nayeon"
    wake_name: str = "Nayeon"

    def __post_init__(self) -> None:
        _validate_string(self.display_name, 64)
        _validate_string(self.wake_name, 64)


@dataclass(frozen=True, slots=True, repr=False)
class UserPresentationProfile:
    """Optional user display name with no personal production default."""

    display_name: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_string(self.display_name, 64)


@dataclass(frozen=True, slots=True, repr=False)
class PresentationPreferences:
    """Opaque presentation references without provider interpretation."""

    personality_ref: str | None = None
    voice_ref: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_string(self.personality_ref, 128)
        _validate_optional_string(self.voice_ref, 128)
