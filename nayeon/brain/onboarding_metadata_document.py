"""Phase 8.12: pure canonical OpenAI metadata document preview.

Construction neither persists non-secret configuration nor confers credential
binding, validation, permission, confirmation, or provider activation authority.
"""
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.onboarding_configuration_proposal import OpenAIConfigurationProposal
from nayeon.secrets.contracts import SecretIdentifier


def compose_onboarding_metadata_document(
    proposal: OpenAIConfigurationProposal,
) -> ProviderConnectionDocumentV1:
    """Create one fresh canonical document, never storage or connection owner."""
    if type(proposal) is not OpenAIConfigurationProposal:
        raise TypeError("Exact onboarding proposal required")
    if proposal.provider != "openai" or proposal.requires_new_observation is not True:
        raise ValueError("Proposal is not eligible for metadata preview")
    configuration = ProviderConnectionConfiguration(
        provider="openai",
        model=proposal.model,
        credential=SecretIdentifier("openai.api_key"),
    )
    return ProviderConnectionDocumentV1(connection=configuration)
