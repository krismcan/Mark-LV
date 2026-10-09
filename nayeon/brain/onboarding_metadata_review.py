"""Phase 8.13: pure non-secret canonical metadata review.

A review neither grants confirmation nor authorizes a credential operation,
connection persistence, or provider activation.
"""
from dataclasses import dataclass

from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.onboarding_configuration_proposal import OpenAIConfigurationProposal
from nayeon.brain.onboarding_metadata_document import compose_onboarding_metadata_document
from nayeon.brain.onboarding_status_view import OnboardingDisplayState


@dataclass(frozen=True, slots=True, repr=False)
class OnboardingMetadataReview:
    provider: str
    model: str
    credential_reference: str
    source_state: OnboardingDisplayState
    requires_reobservation: bool = True
    requires_explicit_confirmation: bool = True

    def __post_init__(self) -> None:
        if type(self.provider) is not str or self.provider != "openai":
            raise ValueError("Only canonical OpenAI metadata is allowed")
        if type(self.model) is not str or not 1 <= len(self.model) <= 128:
            raise ValueError("Invalid model metadata")
        if self.model != self.model.strip() or not self.model.isprintable():
            raise ValueError("Invalid model metadata")
        if type(self.credential_reference) is not str or self.credential_reference != "openai.api_key":
            raise ValueError("Canonical non-secret reference required")
        if type(self.source_state) is not OnboardingDisplayState:
            raise TypeError("Exact source state required")
        if self.requires_reobservation is not True or self.requires_explicit_confirmation is not True:
            raise ValueError("A review never grants authorization")


def present_onboarding_metadata_review(
    proposal: OpenAIConfigurationProposal,
    metadata_preview: ProviderConnectionDocumentV1,
) -> OnboardingMetadataReview:
    """Match an exact proposal to the canonical preview and project safe data."""
    if type(proposal) is not OpenAIConfigurationProposal:
        raise TypeError("Exact configuration proposal required")
    if type(metadata_preview) is not ProviderConnectionDocumentV1:
        raise TypeError("Exact provider connection document required")
    if metadata_preview != compose_onboarding_metadata_document(proposal):
        raise ValueError("Metadata preview does not match proposal")
    connection = metadata_preview.connection
    return OnboardingMetadataReview(
        provider=connection.provider,
        model=connection.model,
        credential_reference=connection.credential.value,
        source_state=proposal.source_state,
    )
