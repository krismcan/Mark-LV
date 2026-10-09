"""Phase 8.11: non-secret canonical OpenAI onboarding configuration proposal.

A proposal is a preview only: not a provider connection object, token, validated
model entitlement, persistence authorization, or evidence of live credentials.
"""
from dataclasses import dataclass

from nayeon.brain.onboarding_status_view import OnboardingDisplayState, OnboardingStatusView


_ALLOWED = frozenset((
    OnboardingDisplayState.NEEDS_SETUP,
    OnboardingDisplayState.SAVED_KEY_NEEDS_REVIEW,
    OnboardingDisplayState.NEEDS_CREDENTIAL,
    OnboardingDisplayState.NEEDS_EXPLICIT_VALIDATION,
))


@dataclass(frozen=True, slots=True, repr=False)
class OpenAIConfigurationProposal:
    model: str
    source_state: OnboardingDisplayState
    provider: str = "openai"
    requires_new_observation: bool = True

    def __post_init__(self) -> None:
        if type(self.model) is not str or not 1 <= len(self.model) <= 128:
            raise ValueError("Invalid model selection")
        if self.model != self.model.strip() or not self.model.isprintable():
            raise ValueError("Invalid model selection")
        if type(self.source_state) is not OnboardingDisplayState or self.source_state not in _ALLOWED:
            raise ValueError("Configuration proposal requires an eligible observation")
        if self.provider != "openai" or type(self.provider) is not str:
            raise ValueError("Provider may not be changed")
        if self.requires_new_observation is not True:
            raise ValueError("Proposal never authorizes persistence")


def propose_openai_configuration(
    status_view: OnboardingStatusView, model: str,
) -> OpenAIConfigurationProposal:
    """Propose bounded non-secret metadata for a trusted *future* human flow."""
    if type(status_view) is not OnboardingStatusView:
        raise TypeError("Exact trusted status view required")
    if status_view.state not in _ALLOWED:
        raise ValueError("Cannot propose configuration from unsafe status")
    return OpenAIConfigurationProposal(model=model, source_state=status_view.state)
