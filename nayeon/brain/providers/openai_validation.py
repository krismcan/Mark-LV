"""Bounded OpenAI credential validation without storage or lifecycle authority."""

from nayeon.secrets.lifecycle import CredentialValidationStatus
from nayeon.secrets.contracts import SecretValue
from nayeon.brain.providers.openai_client import (
    create_openai_client, OpenAIClientConstructionError,
)


class OpenAICredentialValidator:
    """Probe once; provider failures cannot establish an invalid credential."""

    __slots__ = ()

    def validate(self, value: SecretValue) -> CredentialValidationStatus:
        if type(value) is not SecretValue:
            raise TypeError("Value must be an exact SecretValue")
        try:
            client = create_openai_client(value, timeout_seconds=5.0, max_retries=0)
        except OpenAIClientConstructionError:
            return CredentialValidationStatus.INDETERMINATE
        except Exception:
            return CredentialValidationStatus.INDETERMINATE

        status = CredentialValidationStatus.INDETERMINATE
        try:
            client.models.list()
            status = CredentialValidationStatus.VALID
        except Exception:
            pass
        finally:
            try:
                client.close()
            except Exception:
                status = CredentialValidationStatus.INDETERMINATE
        return status
