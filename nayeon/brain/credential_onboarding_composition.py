"""Trusted, lazy composition of a canonical OpenAI credential lifecycle.

No backend reads, validation requests, provider activation, or startup wiring
occur on import or construction. Only the trusted caller supplies the backend.
"""

from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.providers.openai_validation import OpenAICredentialValidator
from nayeon.secrets.contracts import SecretBackend, SecretIdentifier
from nayeon.secrets.lifecycle import BoundCredentialLifecycle


def compose_openai_credential_onboarding(
    backend: SecretBackend,
) -> OpenAICredentialOnboarding:
    """Bind one trusted backend to the constant supported credential identity."""
    validator = OpenAICredentialValidator()
    lifecycle = BoundCredentialLifecycle(
        backend, SecretIdentifier("openai.api_key"), validator,
    )
    return OpenAICredentialOnboarding(lifecycle)
