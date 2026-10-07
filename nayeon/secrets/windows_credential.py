"""Isolated Windows Generic Credential storage; no production consumers yet."""

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
    """Private native seam. Returned CredRead buffers have one finally owner."""

    def __init__(self) -> None:
        try:
            self._dll = _load_advapi32()
            self._dll.CredReadW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32,
                                            ctypes.c_uint32, ctypes.POINTER(_PCREDENTIALW)]
            self._dll.CredReadW.restype = ctypes.c_int32
            self._dll.CredWriteW.argtypes = [_PCREDENTIALW, ctypes.c_uint32]
            self._dll.CredWriteW.restype = ctypes.c_int32
            self._dll.CredDeleteW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
            self._dll.CredDeleteW.restype = ctypes.c_int32
            self._dll.CredFree.argtypes = [ctypes.c_void_p]
            self._dll.CredFree.restype = None
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def _acquire(self, target: str):
        pointer = _PCREDENTIALW()
        if not self._dll.CredReadW(target, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == _ERROR_NOT_FOUND:
                return None
            raise SecretStorageError(_FAILURE)
        return pointer

    def read(self, target: str) -> bytes | None:
        pointer = self._acquire(target)
        if pointer is None:
            return None
        try:
            credential = pointer.contents
            size = credential.CredentialBlobSize
            if not 1 <= size <= _MAX_BLOB_BYTES or not credential.CredentialBlob:
                raise SecretStorageError(_FAILURE)
            return ctypes.string_at(credential.CredentialBlob, size)
        finally:
            self._dll.CredFree(pointer)

    def contains(self, target: str) -> bool:
        pointer = self._acquire(target)
        if pointer is None:
            return False
        try:
            return True
        finally:
            self._dll.CredFree(pointer)

    def write(self, target: str, blob: bytes, credential_type: int,
              persist: int, username: str) -> None:
        buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = _CREDENTIALW()
        credential.Type = credential_type
        credential.TargetName = target
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = persist
        credential.UserName = username
        try:
            if not self._dll.CredWriteW(ctypes.byref(credential), 0):
                raise SecretStorageError(_FAILURE)
        finally:
            # Best-effort cleanup of this ctypes copy, not all Python plaintext.
            ctypes.memset(buffer, 0, len(blob))

    def delete(self, target: str) -> bool:
        if self._dll.CredDeleteW(target, _CRED_TYPE_GENERIC, 0):
            return True
        if ctypes.get_last_error() == _ERROR_NOT_FOUND:
            return False
        raise SecretStorageError(_FAILURE)


class WindowsCredentialBackend:
    """Exact typed operations in a fixed internal Nayeon v1 namespace.

    The private adapter argument exists for deterministic tests. Construction
    makes no native call; real setup is lazy and fails closed when unavailable.
    LOCAL_MACHINE persistence is for this Windows user on this computer.
    """

    def __init__(self, *, _native=None) -> None:
        self._native = _native

    def _adapter(self):
        if self._native is None:
            self._native = _Advapi32Adapter()
        return self._native

    @staticmethod
    def _target(identifier: SecretIdentifier) -> str:
        if type(identifier) is not SecretIdentifier:
            raise TypeError("Identifier must be an exact SecretIdentifier")
        return _TARGET_PREFIX + identifier.value

    def get(self, identifier: SecretIdentifier) -> SecretValue:
        target = self._target(identifier)
        try:
            blob = self._adapter().read(target)
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
        try:
            blob = value.reveal().encode("utf-8", errors="strict")
            if len(blob) > _MAX_BLOB_BYTES:
                raise SecretStorageError(_FAILURE)
            self._adapter().write(target, blob, _CRED_TYPE_GENERIC,
                                  _CRED_PERSIST_LOCAL_MACHINE, _USERNAME)
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def delete(self, identifier: SecretIdentifier) -> bool:
        target = self._target(identifier)
        try:
            return self._adapter().delete(target)
        except Exception:
            raise SecretStorageError(_FAILURE) from None

    def is_available(self, identifier: SecretIdentifier) -> bool:
        target = self._target(identifier)
        try:
            return self._adapter().contains(target)
        except Exception:
            raise SecretStorageError(_FAILURE) from None
