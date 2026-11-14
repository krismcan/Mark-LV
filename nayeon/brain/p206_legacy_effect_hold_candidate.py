"""P206: DORMANT, permanently refusing legacy Python credential-effect adapter.

This is a review/test integration seam, not a production security boundary.
It intentionally accepts NO native adapter, transport, dispatcher, callback,
consent token, credential value, or backend factory. It never imports WinCred.
Inserting this adapter in a Python graph can demonstrate failure isolation;
it DOES NOT restrict direct access to legacy WindowsCredentialBackend.
A future accepted native service must own the effect, and production must
remove/restrict the legacy direct WinCred route at OS/packaging authority.
"""
from __future__ import annotations

from nayeon.secrets.contracts import (
    SecretIdentifier, SecretStorageError, SecretValue,
)

_DENIED = "Credential effect owner unavailable; operation refused"


class P206LegacyEffectHoldCandidate:
    """No authority state and no delegated effect; even reads are refused.

    Exact SecretBackend protocol shape for composition with existing lifecycle.
    There is intentionally no configuration bit, allowlist extension, callback,
    synthetic privilege, reset, or authorise method.
    """

    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("P206 candidate cannot be subclassed")

    @staticmethod
    def _refuse(identifier: object) -> None:
        # Do not format the identifier or inspect a value (possibly a secret).
        # Neither a correct identifier nor a forged one conveys approval.
        raise SecretStorageError(_DENIED)

    def get(self, identifier: SecretIdentifier) -> SecretValue:
        self._refuse(identifier)

    def is_available(self, identifier: SecretIdentifier) -> bool:
        self._refuse(identifier)

    def put(self, identifier: SecretIdentifier, value: SecretValue) -> None:
        # Do not even call value.reveal(); no WinCred backend is held.
        self._refuse(identifier)

    def delete(self, identifier: SecretIdentifier) -> bool:
        self._refuse(identifier)

    def __reduce_ex__(self, protocol: int):
        raise TypeError("P206 hold cannot be serialized")
