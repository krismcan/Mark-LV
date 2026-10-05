"""Versioned presentation document and pure, strict mapping codec."""

from __future__ import annotations

from dataclasses import dataclass, field

from nayeon.config.presentation import (
    AssistantPresentationIdentity,
    UserPresentationProfile,
    PresentationPreferences,
)


PRESENTATION_CONFIGURATION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True, repr=False)
class PresentationConfigurationDocumentV1:
    """Immutable presentation data; version one has no migration semantics."""

    schema_version: int = PRESENTATION_CONFIGURATION_SCHEMA_VERSION
    assistant: AssistantPresentationIdentity = field(default_factory=AssistantPresentationIdentity)
    user: UserPresentationProfile = field(default_factory=UserPresentationProfile)
    preferences: PresentationPreferences = field(default_factory=PresentationPreferences)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise TypeError("Schema version must be an exact built-in int")
        if self.schema_version != PRESENTATION_CONFIGURATION_SCHEMA_VERSION:
            raise ValueError("Unsupported presentation schema version")
        if type(self.assistant) is not AssistantPresentationIdentity:
            raise TypeError("Assistant must be an exact presentation identity")
        if type(self.user) is not UserPresentationProfile:
            raise TypeError("User must be an exact presentation profile")
        if type(self.preferences) is not PresentationPreferences:
            raise TypeError("Preferences must be exact presentation preferences")


def _validate_mapping(data: object, keys: tuple[str, ...]) -> None:
    if type(data) is not dict:
        raise TypeError("Presentation section must be an exact built-in dict")
    if any(type(key) is not str for key in data):
        raise TypeError("Presentation keys must be exact built-in str")
    if len(data) != len(keys) or any(key not in data for key in keys):
        raise ValueError("Presentation section has missing or unknown keys")


def parse_presentation_configuration_document(data: object) -> PresentationConfigurationDocumentV1:
    """Parse an exact mapping without coercion or retaining mutable input."""
    _validate_mapping(data, ("schema_version", "assistant", "user", "preferences"))
    assistant = data["assistant"]
    user = data["user"]
    preferences = data["preferences"]
    _validate_mapping(assistant, ("display_name", "wake_name"))
    _validate_mapping(user, ("display_name",))
    _validate_mapping(preferences, ("personality_ref", "voice_ref"))
    return PresentationConfigurationDocumentV1(
        schema_version=data["schema_version"],
        assistant=AssistantPresentationIdentity(
            display_name=assistant["display_name"], wake_name=assistant["wake_name"]
        ),
        user=UserPresentationProfile(display_name=user["display_name"]),
        preferences=PresentationPreferences(
            personality_ref=preferences["personality_ref"], voice_ref=preferences["voice_ref"]
        ),
    )


def presentation_configuration_document_to_mapping(
    document: PresentationConfigurationDocumentV1,
) -> dict[str, object]:
    """Encode fresh canonical mappings without exposing mutable internal data."""
    if type(document) is not PresentationConfigurationDocumentV1:
        raise TypeError("Document must be an exact presentation configuration document")
    return {
        "schema_version": PRESENTATION_CONFIGURATION_SCHEMA_VERSION,
        "assistant": {
            "display_name": document.assistant.display_name,
            "wake_name": document.assistant.wake_name,
        },
        "user": {"display_name": document.user.display_name},
        "preferences": {
            "personality_ref": document.preferences.personality_ref,
            "voice_ref": document.preferences.voice_ref,
        },
    }
