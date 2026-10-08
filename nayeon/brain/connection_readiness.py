"""Pure, non-secret readiness of one initialized provider connection owner.

READY_FOR_COMPOSITION proves metadata eligibility only, not that a credential
exists, is valid, that a model is available, or that a request can succeed.
"""

from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.secrets.contracts import SecretIdentifier


class ProviderConnectionReadinessStatus(str, Enum):
    UNCONFIGURED = "unconfigured"
    UNSUPPORTED = "unsupported"
    READY_FOR_COMPOSITION = "ready_for_composition"


class ProviderConnectionReadinessError(RuntimeError):
    """Metadata cannot be assessed safely using a fixed, non-secret message."""


@dataclass(frozen=True, slots=True, repr=False)
class ProviderConnectionReadiness:
    status: ProviderConnectionReadinessStatus

    def __post_init__(self) -> None:
        if type(self.status) is not ProviderConnectionReadinessStatus:
            raise TypeError("Status must be an exact readiness status")


def assess_provider_connection_readiness(
    owner: ProviderConnectionService,
) -> ProviderConnectionReadiness:
    """Assess only cached metadata; never probe secrets or activate a provider."""
    if type(owner) is not ProviderConnectionService:
        raise TypeError("Owner must be an exact provider connection service")
    if not owner.is_initialized:
        raise ProviderConnectionReadinessError("Connection owner is not initialized")

    connection_document = owner.current
    if type(connection_document) is not ProviderConnectionDocumentV1:
        raise ProviderConnectionReadinessError("Connection document has an invalid type")
    configuration = connection_document.connection
    if configuration is None:
        return ProviderConnectionReadiness(ProviderConnectionReadinessStatus.UNCONFIGURED)
    if type(configuration) is not ProviderConnectionConfiguration:
        raise ProviderConnectionReadinessError("Connection configuration has an invalid type")
    if (configuration.provider != "openai"
            or type(configuration.credential) is not SecretIdentifier
            or configuration.credential != SecretIdentifier("openai.api_key")):
        return ProviderConnectionReadiness(ProviderConnectionReadinessStatus.UNSUPPORTED)
    return ProviderConnectionReadiness(ProviderConnectionReadinessStatus.READY_FOR_COMPOSITION)
