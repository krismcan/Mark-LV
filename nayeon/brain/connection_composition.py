"""Compose an AI service from validated, initialized connection metadata."""

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.brain.providers.openai import OpenAIProvider
from nayeon.brain.service import AIService
from nayeon.secrets.contracts import SecretBackend, SecretIdentifier
from nayeon.secrets.resolver import BoundSecretResolver


_OPENAI_CREDENTIAL = SecretIdentifier("openai.api_key")


class ConnectionCompositionError(RuntimeError):
    """Connection metadata cannot safely select the supported provider."""


def compose_provider_ai_service(
    connection_service: ProviderConnectionService,
    backend: SecretBackend,
) -> AIService:
    """Construct a lazy AI service after completing all metadata checks."""
    if type(connection_service) is not ProviderConnectionService:
        raise TypeError(
            "connection_service must be an exact ProviderConnectionService"
        )
    if not connection_service.is_initialized:
        raise ConnectionCompositionError("Connection service is not initialized")

    connection_document = connection_service.current
    if type(connection_document) is not ProviderConnectionDocumentV1:
        raise ConnectionCompositionError("Connection document has an invalid type")

    config = connection_document.connection
    if config is None:
        raise ConnectionCompositionError("No provider connection is configured")
    if type(config) is not ProviderConnectionConfiguration:
        raise ConnectionCompositionError("Connection configuration has an invalid type")
    if config.provider != "openai":
        raise ConnectionCompositionError("Provider is not supported")
    if (
        type(config.credential) is not SecretIdentifier
        or config.credential != _OPENAI_CREDENTIAL
    ):
        raise ConnectionCompositionError("Credential identifier is not supported")

    resolver = BoundSecretResolver(backend, SecretIdentifier("openai.api_key"))
    provider = OpenAIProvider(resolver, model=config.model)
    return AIService(provider)
