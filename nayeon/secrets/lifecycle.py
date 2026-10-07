"""One credential's least-authority lifecycle, without a plaintext read API.

This application boundary is not cryptographic isolation inside one Python
process: private state remains introspectable. No memory erasure is claimed.
"""

from enum import Enum
from typing import Protocol

from nayeon.secrets.contracts import (
    SecretBackend, SecretIdentifier, SecretNotFoundError, SecretStorageError,
    SecretValue,
)


class CredentialValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    INDETERMINATE = "indeterminate"


class CredentialValidator(Protocol):
    """Validation alone grants no lifecycle or storage authority."""

    def validate(self, value: SecretValue) -> CredentialValidationStatus: ...


class CredentialLifecycleStateError(RuntimeError):
    """Lifecycle preconditions failed, using fixed safe state messages."""


_FAILURE = "Credential lifecycle operation failed"


class BoundCredentialLifecycle:
    """Permanently bind one backend, exact identifier and validator.

    Availability rechecks detect state changes during validation, but SecretBackend
    has no compare-and-swap. An external actor can race the final check and put
    for both connection and replacement. There is no rollback or readback claim.
    """

    __slots__ = ("__backend", "__identifier", "__validator")

    def __init__(self, backend: SecretBackend, identifier: SecretIdentifier,
                 validator: CredentialValidator) -> None:
        if hasattr(self, "_BoundCredentialLifecycle__backend"):
            raise AttributeError("Credential lifecycle is immutable")
        if type(identifier) is not SecretIdentifier:
            raise TypeError("Identifier must be an exact SecretIdentifier")
        try:
            valid_backend = all(callable(getattr(backend, name, None)) for name in
                                ("get", "put", "delete", "is_available"))
        except Exception:
            raise TypeError("Backend must provide callable lifecycle operations") from None
        if not valid_backend:
            raise TypeError("Backend must provide callable lifecycle operations")
        try:
            valid_validator = callable(getattr(validator, "validate", None))
        except Exception:
            raise TypeError("Validator must provide a callable validate") from None
        if not valid_validator:
            raise TypeError("Validator must provide a callable validate")
        object.__setattr__(self, "_BoundCredentialLifecycle__backend", backend)
        object.__setattr__(self, "_BoundCredentialLifecycle__identifier", identifier)
        object.__setattr__(self, "_BoundCredentialLifecycle__validator", validator)

    @property
    def identifier(self) -> SecretIdentifier:
        """Return only exact immutable safe metadata."""
        return self.__identifier

    def is_connected(self) -> bool:
        try:
            result = self.__backend.is_available(self.__identifier)
        except SecretStorageError:
            raise
        except Exception:
            raise SecretStorageError(_FAILURE) from None
        if type(result) is not bool:
            raise SecretStorageError(_FAILURE)
        return result

    def test_candidate(self, value: SecretValue) -> CredentialValidationStatus:
        if type(value) is not SecretValue:
            raise TypeError("Value must be an exact SecretValue")
        try:
            result = self.__validator.validate(value)
        except Exception:
            # Credential/provider validation failures are contained as a tri-state
            # result. Process-control exceptions are deliberately not swallowed.
            return CredentialValidationStatus.INDETERMINATE
        if type(result) is not CredentialValidationStatus:
            return CredentialValidationStatus.INDETERMINATE
        return result

    def test_stored(self) -> CredentialValidationStatus:
        try:
            value = self.__backend.get(self.__identifier)
        except (SecretNotFoundError, SecretStorageError):
            raise
        except Exception:
            raise SecretStorageError(_FAILURE) from None
        if type(value) is not SecretValue:
            raise SecretStorageError(_FAILURE)
        return self.test_candidate(value)

    def connect(self, value: SecretValue) -> CredentialValidationStatus:
        if type(value) is not SecretValue:
            raise TypeError("Value must be an exact SecretValue")
        if self.is_connected():
            raise CredentialLifecycleStateError("Credential is already connected")
        status = self.test_candidate(value)
        if status is not CredentialValidationStatus.VALID:
            return status
        if self.is_connected():
            raise CredentialLifecycleStateError("Credential state changed")
        self._put(value)
        return status

    def replace(self, value: SecretValue) -> CredentialValidationStatus:
        """Keep the old credential untouched through validation and recheck."""
        if type(value) is not SecretValue:
            raise TypeError("Value must be an exact SecretValue")
        if not self.is_connected():
            raise CredentialLifecycleStateError("Credential is not connected")
        status = self.test_candidate(value)
        if status is not CredentialValidationStatus.VALID:
            return status
        if not self.is_connected():
            raise CredentialLifecycleStateError("Credential state changed")
        self._put(value)
        return status

    def _put(self, value: SecretValue) -> None:
        try:
            self.__backend.put(self.__identifier, value)
        except SecretStorageError:
            raise
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def remove(self) -> bool:
        try:
            result = self.__backend.delete(self.__identifier)
        except SecretStorageError:
            raise
        except Exception:
            raise SecretStorageError(_FAILURE) from None
        if type(result) is not bool:
            raise SecretStorageError(_FAILURE)
        return result

    def __repr__(self) -> str:
        return "BoundCredentialLifecycle(<redacted>)"

    def __str__(self) -> str:
        return "BoundCredentialLifecycle(<redacted>)"

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Credential lifecycle is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Credential lifecycle is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Credential lifecycle cannot be serialized")

    def __getstate__(self) -> object:
        raise TypeError("Credential lifecycle cannot be serialized")
