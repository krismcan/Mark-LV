"""Windows credential storage; default native access is presence-only."""

from __future__ import annotations

import ctypes

from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)


_TARGET_PREFIX = "nayeon-v1/secret/"
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_USERNAME = "nayeon-v1"
_MAX_BLOB_BYTES = 2560
_ERROR_NOT_FOUND = 1168
_FAILURE = "Secret storage operation failed"
_MISSING = "Secret is not available"


# Explicit Windows-width integers keep this layout inspectable on other hosts.
class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_uint32),
                ("dwHighDateTime", ctypes.c_uint32)]


class _CREDENTIAL_ATTRIBUTEW(ctypes.Structure):
    _fields_ = [("Keyword", ctypes.c_wchar_p), ("Flags", ctypes.c_uint32),
                ("ValueSize", ctypes.c_uint32),
                ("Value", ctypes.POINTER(ctypes.c_ubyte))]


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_uint32), ("Type", ctypes.c_uint32),
        ("TargetName", ctypes.c_wchar_p), ("Comment", ctypes.c_wchar_p),
        ("LastWritten", _FILETIME), ("CredentialBlobSize", ctypes.c_uint32),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", ctypes.c_uint32), ("AttributeCount", ctypes.c_uint32),
        ("Attributes", ctypes.POINTER(_CREDENTIAL_ATTRIBUTEW)),
        ("TargetAlias", ctypes.c_wchar_p), ("UserName", ctypes.c_wchar_p),
    ]


_PCREDENTIALW = ctypes.POINTER(_CREDENTIALW)


def _load_advapi32():
    # WinDLL is absent on non-Windows. Import itself performs no native setup.
    return ctypes.WinDLL("Advapi32.dll", use_last_error=True)


class _Advapi32Adapter:
    """Presence-only native seam; returned buffers have one finally owner.

    This source retirement is not OS isolation from hostile same-user code.
    """

    def __init__(self) -> None:
        try:
            self._dll = _load_advapi32()
            self._dll.CredReadW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32,
                                            ctypes.c_uint32, ctypes.POINTER(_PCREDENTIALW)]
            self._dll.CredReadW.restype = ctypes.c_int32
            self._dll.CredFree.argtypes = [ctypes.c_void_p]
            self._dll.CredFree.restype = None
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def read(self, target: str) -> bytes | None:
        # Inert compatibility shim for original P258 mock-patch semantics.
        # No setup, reader call, buffer acquisition or plaintext extraction.
        raise SecretStorageError(_FAILURE)

    def contains(self, target: str) -> bool:
        pointer = _PCREDENTIALW()
        try:
            try:
                if not self._dll.CredReadW(target, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
                    if ctypes.get_last_error() == _ERROR_NOT_FOUND and not pointer:
                        return False
                    raise SecretStorageError(_FAILURE)
                if not pointer:
                    raise SecretStorageError(_FAILURE)
                return True
            finally:
                # Partial output belongs here even on false/exception paths.
                if pointer:
                    self._dll.CredFree(pointer)
        except Exception:
            raise SecretStorageError(_FAILURE) from None


class WindowsCredentialBackend:
    """Exact typed operations in a fixed internal Nayeon v1 namespace.

    The private adapter argument exists for deterministic tests. Construction
    makes no native call; real setup is lazy and fails closed when unavailable.
    Default get/put/delete are refused, including after a presence refresh.
    The injected adapter seam is not an authorization or OS isolation boundary.
    LOCAL_MACHINE persistence is for this Windows user on this computer.
    """

    def __init__(self, *, _native=None) -> None:
        self._native = _native
        # Only construction-time injection supplies the test read contract.
        # Lazy presence setup must never grant plaintext read access.
        self._injected_read_adapter = _native

    def _adapter(self):
        if self._native is None:
            self._native = _Advapi32Adapter()
        return self._native

    def _injected_mutation_adapter(self):
        # Preserve the existing fake-adapter contract without giving the lazy
        # real native adapter mutation authority. No mode/approval switch.
        if self._native is None or isinstance(self._native, _Advapi32Adapter):
            return None
        return self._native

    @staticmethod
    def _target(identifier: SecretIdentifier) -> str:
        if type(identifier) is not SecretIdentifier:
            raise TypeError("Identifier must be an exact SecretIdentifier")
        return _TARGET_PREFIX + identifier.value

    def get(self, identifier: SecretIdentifier) -> SecretValue:
        target = self._target(identifier)
        adapter = self._injected_read_adapter
        if adapter is None:
            raise SecretStorageError(_FAILURE)
        try:
            blob = adapter.read(target)
            if blob is not None:
                if type(blob) is not bytes or not 1 <= len(blob) <= _MAX_BLOB_BYTES:
                    raise SecretStorageError(_FAILURE)
                return SecretValue(blob.decode("utf-8", errors="strict"))
        except Exception:
            raise SecretStorageError(_FAILURE) from None
        raise SecretNotFoundError(_MISSING)

    def put(self, identifier: SecretIdentifier, value: SecretValue) -> None:
        target = self._target(identifier)
        if type(value) is not SecretValue:
            raise TypeError("Value must be an exact SecretValue")
        adapter = self._injected_mutation_adapter()
        if adapter is None:
            raise SecretStorageError(_FAILURE)
        try:
            blob = value.reveal().encode("utf-8", errors="strict")
            if len(blob) > _MAX_BLOB_BYTES:
                raise SecretStorageError(_FAILURE)
            adapter.write(target, blob, _CRED_TYPE_GENERIC,
                          _CRED_PERSIST_LOCAL_MACHINE, _USERNAME)
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def delete(self, identifier: SecretIdentifier) -> bool:
        target = self._target(identifier)
        adapter = self._injected_mutation_adapter()
        if adapter is None:
            raise SecretStorageError(_FAILURE)
        try:
            return adapter.delete(target)
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def is_available(self, identifier: SecretIdentifier) -> bool:
        target = self._target(identifier)
        try:
            return self._adapter().contains(target)
        except Exception:
            raise SecretStorageError(_FAILURE) from None
