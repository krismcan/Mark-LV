"""Immutable presentation read model without configuration-owner authority."""

from __future__ import annotations

from dataclasses import dataclass

from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.config.presentation import (
    AssistantPresentationIdentity,
    UserPresentationProfile,
    PresentationPreferences,
)


@dataclass(frozen=True, slots=True, repr=False)
class PresentationConfigurationView:
    """Presentation values only, distinct from trusted action identity."""

    assistant: AssistantPresentationIdentity
    user: UserPresentationProfile
    preferences: PresentationPreferences

    def __post_init__(self) -> None:
        if type(self.assistant) is not AssistantPresentationIdentity:
            raise TypeError("Assistant must be an exact presentation identity")
        if type(self.user) is not UserPresentationProfile:
            raise TypeError("User must be an exact presentation profile")
        if type(self.preferences) is not PresentationPreferences:
            raise TypeError("Preferences must be exact presentation preferences")


def presentation_configuration_view(
    document: PresentationConfigurationDocumentV1,
) -> PresentationConfigurationView:
    """Project fresh presentation values without retaining the source document."""
    if type(document) is not PresentationConfigurationDocumentV1:
        raise TypeError("Document must be an exact presentation configuration document")
    return PresentationConfigurationView(
        assistant=AssistantPresentationIdentity(
            display_name=document.assistant.display_name,
            wake_name=document.assistant.wake_name,
        ),
        user=UserPresentationProfile(display_name=document.user.display_name),
        preferences=PresentationPreferences(
            personality_ref=document.preferences.personality_ref,
            voice_ref=document.preferences.voice_ref,
        ),
    )
