"""Phase 8.14: pure, non-authorizing OpenAI onboarding metadata change preview.

Caller-supplied metadata is NOT a fresh observation, evidence of consent, or a
permission to persist configuration or activate a provider.
"""
from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.onboarding_configuration_proposal import OpenAIConfigurationProposal
from nayeon.brain.onboarding_metadata_review import present_onboarding_metadata_review
from nayeon.brain.onboarding_status_view import OnboardingDisplayState


class MetadataChangeKind(str, Enum):
    CREATE = "create"
    UNCHANGED = "unchanged"
    MODEL_CHANGE = "model_change"


@dataclass(frozen=True, slots=True, repr=False)
class OnboardingMetadataChangePreview:
    kind: MetadataChangeKind
    proposed_model: str
    current_model: str | None
    source_state: OnboardingDisplayState
    provider: str = "openai"
    credential_reference: str = "openai.api_key"
    requires_reobservation: bool = True
    requires_explicit_confirmation: bool = True

    def __post_init__(self) -> None:
        if type(self.kind) is not MetadataChangeKind:
            raise TypeError("Exact metadata change kind required")
        for item in (self.proposed_model, self.current_model):
            if item is None:
                continue
            if type(item) is not str or not 1 <= len(item) <= 128:
                raise ValueError("Invalid model metadata")
            if item != item.strip() or not item.isprintable():
                raise ValueError("Invalid model metadata")
        if type(self.source_state) is not OnboardingDisplayState:
            raise TypeError("Exact source state required")
        if type(self.provider) is not str or self.provider != "openai":
            raise ValueError("Only canonical OpenAI metadata is supported")
        if (type(self.credential_reference) is not str or
                self.credential_reference != "openai.api_key"):
            raise ValueError("Only the canonical non-secret key reference is supported")
        if self.requires_reobservation is not True or self.requires_explicit_confirmation is not True:
            raise ValueError("A preview never authorizes an action")
        if self.kind is MetadataChangeKind.CREATE and self.current_model is not None:
            raise ValueError("CREATE requires absent current metadata")
        if self.kind is MetadataChangeKind.UNCHANGED and self.current_model != self.proposed_model:
            raise ValueError("UNCHANGED requires matching models")
        if (self.kind is MetadataChangeKind.MODEL_CHANGE and
                (self.current_model is None or self.current_model == self.proposed_model)):
            raise ValueError("MODEL_CHANGE requires differing existing model")


def preview_onboarding_metadata_change(
    proposal: OpenAIConfigurationProposal,
    proposed_preview: ProviderConnectionDocumentV1,
    current_snapshot: ProviderConnectionDocumentV1,
) -> OnboardingMetadataChangePreview:
    """Compare typed metadata only; never read storage or infer live freshness."""
    if type(current_snapshot) is not ProviderConnectionDocumentV1:
        raise TypeError("Exact current metadata snapshot required")
    review = present_onboarding_metadata_review(proposal, proposed_preview)
    existing = current_snapshot.connection
    if existing is None:
        kind = MetadataChangeKind.CREATE
        current_model = None
    else:
        if existing.provider != "openai" or existing.credential.value != "openai.api_key":
            raise ValueError("Cannot preview replacement of unsupported existing metadata")
        current_model = existing.model
        kind = (MetadataChangeKind.UNCHANGED if current_model == review.model
                else MetadataChangeKind.MODEL_CHANGE)
    return OnboardingMetadataChangePreview(
        kind=kind,
        current_model=current_model,
        proposed_model=review.model,
        source_state=review.source_state,
    )
