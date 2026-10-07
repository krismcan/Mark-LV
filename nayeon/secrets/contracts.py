"""Provider-neutral secret contracts, separate from presentation and authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SecretNotFoundError(RuntimeError):
    """A credential is absent; callers must use fixed, secret-free messages."""


class SecretStorageError(RuntimeError):
    """Storage failed; callers must use fixed, secret-free messages."""


@dataclass(frozen=True, slots=True)
class SecretIdentifier:
    """Canonical safe metadata, never a credential or a provider allowlist."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise TypeError("Secret identifier must be an exact str")
        if not 1 <= len(self.value) <= 128:
            raise ValueError("Invalid secret identifier length")
        initial = "abcdefghijklmnopqrstuvwxyz0123456789"
        if self.value[0] not in initial or any(
            character not in initial + "._-" for character in self.value[1:]
        ):
            raise ValueError("Invalid secret identifier syntax")


class SecretValue:
    """Opaque immutable holder with identity equality and explicit reveal.

    Redaction prevents accidental display, not introspection. Python and provider
    SDK use necessarily leave plaintext transiently in process memory; this is
    not cryptographic in-memory secrecy or guaranteed memory erasure.
    """

    __slots__ = ("__value",)

    def __init__(self, value: str) -> None:
        if hasattr(self, "_SecretValue__value"):
            raise AttributeError("Secret value is immutable")
        if type(value) is not str:
            raise TypeError("Secret value must be an exact str")
        if not value or value.isspace():
            raise ValueError("Secret value must not be blank")
        object.__setattr__(self, "_SecretValue__value", value)

    def reveal(self) -> str:
        """Explicitly return the original plaintext for a bounded consumer."""
        return self.__value

    def __str__(self) -> str:
        return "SecretValue(<redacted>)"

    def __repr__(self) -> str:
        return "SecretValue(<redacted>)"

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Secret value is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Secret value is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Secret value cannot be serialized")

    def __getstate__(self) -> object:
        # Python's inherited slot-state helper would otherwise expose plaintext.
        raise TypeError("Secret value cannot be serialized")


class SecretBackend(Protocol):
    """Bounded per-identifier storage; no enumeration or export authority."""

    def get(self, identifier: SecretIdentifier) -> SecretValue: ...

    def put(self, identifier: SecretIdentifier, value: SecretValue) -> None: ...

    def delete(self, identifier: SecretIdentifier) -> bool: ...

    def is_available(self, identifier: SecretIdentifier) -> bool: ...
