"""Explicit, least-authority credential operations for trusted onboarding callers.

Not a UI, agent capability, or ambient startup service. Validation may contact the
provider ONLY when a trusted caller explicitly invokes a validation operation.
"""

from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)
from nayeon.secrets.lifecycle import (
    BoundCredentialLifecycle, CredentialLifecycleStateError,
    CredentialValidationStatus,
)


class CredentialOnboardingStateError(RuntimeError):
    """Safe, fixed lifecycle precondition failure."""


class OpenAICredentialOnboarding:
    """Wrap an exact, canonically bound lifecycle without exposing credentials."""

    __slots__ = ("__lifecycle",)

    def __init__(self, lifecycle: BoundCredentialLifecycle) -> None:
        if type(lifecycle) is not BoundCredentialLifecycle:
            raise TypeError("Lifecycle must be an exact BoundCredentialLifecycle")
        if (
            type(lifecycle.identifier) is not SecretIdentifier
            or lifecycle.identifier != SecretIdentifier("openai.api_key")
        ):
            raise ValueError("Credential identifier is not supported")
        object.__setattr__(self, "_OpenAICredentialOnboarding__lifecycle", lifecycle)

    def _call(self, operation: str, *args: object) -> object:
        """Delegate a fixed internal operation, sanitizing backend failures."""
        try:
            if operation == "is_connected":
                return self.__lifecycle.is_connected()
            if operation == "test_candidate":
                return self.__lifecycle.test_candidate(*args)
            if operation == "test_stored":
                return self.__lifecycle.test_stored()
            if operation == "connect":
                return self.__lifecycle.connect(*args)
            if operation == "replace":
                return self.__lifecycle.replace(*args)
            if operation == "remove":
                return self.__lifecycle.remove()
            raise ValueError("Unsupported onboarding operation")
        except SecretNotFoundError:
            raise SecretNotFoundError("Credential is not available") from None
        except SecretStorageError:
            raise SecretStorageError("Credential storage operation failed") from None
        except CredentialLifecycleStateError:
            raise CredentialOnboardingStateError(
                "Credential operation is not permitted in the current state"
            ) from None

    def is_connected(self) -> bool:
        """Explicit storage availability check, not proof of provider validity."""
        return self._call("is_connected")

    def test_candidate(self, value: SecretValue) -> CredentialValidationStatus:
        """Explicit validation probe; never saves a candidate."""
        if type(value) is not SecretValue:
            raise TypeError("Candidate must be an exact SecretValue")
        return self._call("test_candidate", value)

    def test_stored(self) -> CredentialValidationStatus:
        """Explicitly retrieve and validate one bound stored credential."""
        return self._call("test_stored")

    def connect(self, value: SecretValue) -> CredentialValidationStatus:
        """Only persist a validated candidate if none is already present."""
        if type(value) is not SecretValue:
            raise TypeError("Candidate must be an exact SecretValue")
        return self._call("connect", value)

    def replace(self, value: SecretValue) -> CredentialValidationStatus:
        """Preserve old credential unless candidate validates and rechecks pass."""
        if type(value) is not SecretValue:
            raise TypeError("Candidate must be an exact SecretValue")
        return self._call("replace", value)

    def remove(self) -> bool:
        """Explicit deletion; never mutate non-secret connection metadata."""
        return self._call("remove")

    def __repr__(self) -> str:
        return "OpenAICredentialOnboarding(<redacted>)"

    __str__ = __repr__

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Credential onboarding is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Credential onboarding is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Credential onboarding cannot be serialized")

    def __getstate__(self) -> object:
        raise TypeError("Credential onboarding cannot be serialized")
