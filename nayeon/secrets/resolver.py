"""Bind one credential's read authority; no backend management surface.

This is a least-authority interface, not cryptographic isolation from code
executing in the same Python process. Private state remains introspectable.
"""

from __future__ import annotations

from nayeon.secrets.contracts import (
    SecretBackend, SecretIdentifier, SecretNotFoundError, SecretStorageError,
    SecretValue,
)


class BoundSecretResolver:
    """Immutable binding of one backend to one exact safe identifier."""

    __slots__ = ("__backend", "__identifier")

    def __init__(self, backend: SecretBackend, identifier: SecretIdentifier) -> None:
        if hasattr(self, "_BoundSecretResolver__backend"):
            raise AttributeError("Secret resolver is immutable")
        if type(identifier) is not SecretIdentifier:
            raise TypeError("Identifier must be an exact SecretIdentifier")
        # Only the read operation is needed. Do not probe management methods or
        # perform any storage operation during construction.
        try:
            valid = callable(getattr(backend, "get", None))
        except Exception:
            raise TypeError("Backend must provide a callable get") from None
        if not valid:
            raise TypeError("Backend must provide a callable get")
        object.__setattr__(self, "_BoundSecretResolver__backend", backend)
        object.__setattr__(self, "_BoundSecretResolver__identifier", identifier)

    @property
    def identifier(self) -> SecretIdentifier:
        """Return the exact bound immutable safe metadata."""
        return self.__identifier

    def resolve(self) -> SecretValue:
        """Read only the bound credential, without retaining the result."""
        try:
            value = self.__backend.get(self.__identifier)
        except (SecretNotFoundError, SecretStorageError):
            raise
        except Exception:
            raise SecretStorageError("Secret resolution failed") from None
        if type(value) is not SecretValue:
            raise SecretStorageError("Secret resolution failed")
        return value

    def __repr__(self) -> str:
        return "BoundSecretResolver(<redacted>)"

    def __str__(self) -> str:
        return "BoundSecretResolver(<redacted>)"

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Secret resolver is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Secret resolver is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Secret resolver cannot be serialized")

    def __getstate__(self) -> object:
        raise TypeError("Secret resolver cannot be serialized")
