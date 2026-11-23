"""Explicit, no-key synthetic Add frame; a replying peer is never attested.

The shared deadline bounds request event waits. Cancellation must be drained
before releasing OS-owned buffers, even if kernel cleanup outlives that budget.
The UI separately expires and permanently disables its single attempt.
"""

from __future__ import annotations

from enum import Enum
import os
import struct
import sys
import time


_PIPE = r"\\.\pipe\NayeonV1ByokCustody.SyntheticDenied.v1"
_REPLY = b"C1|DENIED|HOLD|NO_CREDENTIALS"
_SECONDS = 0.75


class SyntheticRequestStatus(Enum):
    UNAVAILABLE = "UNAVAILABLE"
    UNTRUSTED_HOLD = "UNTRUSTED_HOLD"


class NativeSyntheticRequester:
    """Construction has no effects; request accepts no caller-selected data."""

    def request(self) -> SyntheticRequestStatus:
        if sys.platform != "win32":
            return SyntheticRequestStatus.UNAVAILABLE
        handle = None
        active = None
        result = SyntheticRequestStatus.UNAVAILABLE
        try:
            deadline = time.monotonic() + _SECONDS
            import _winapi

            def remaining():
                seconds = deadline - time.monotonic()
                if seconds <= 0:
                    raise TimeoutError
                return int(seconds * 1000)  # Round down within the total budget.

            def complete(operation, error):
                remaining()
                if error == _winapi.ERROR_IO_PENDING:
                    if _winapi.WaitForSingleObject(operation.event, remaining()) != 0:
                        raise TimeoutError
                elif error != 0:
                    raise OSError
                count, error = operation.GetOverlappedResult(False)
                remaining()
                if error != 0:
                    raise OSError
                return count

            random_bytes = os.urandom(8)
            if len(random_bytes) != 8:
                raise OSError
            request_id = int.from_bytes(random_bytes, "little")
            if request_id == 0:
                raise OSError  # Refuse an unusable draw; no retry or fixed ID.
            frame = struct.pack('<4sQB', b'C1T1', request_id, 1)
            remaining()
            # One local open only. SECURITY_SQOS_PRESENT | SECURITY_ANONYMOUS
            # (zero) prevents impersonation; it does not authenticate a peer.
            handle = _winapi.CreateFile(
                _PIPE, 0xC0000000, 0, 0, 3,
                _winapi.FILE_FLAG_OVERLAPPED | 0x00100000, 0,
            )
            remaining()
            _winapi.SetNamedPipeHandleState(
                handle, _winapi.PIPE_READMODE_MESSAGE, None, None,
            )
            remaining()
            if _winapi.PeekNamedPipe(handle, 0) != (0, 0):
                raise OSError
            remaining()
            active, error = _winapi.WriteFile(handle, frame, overlapped=True)
            if complete(active, error) != 13:
                raise OSError
            active = None
            remaining()
            active, error = _winapi.ReadFile(handle, len(_REPLY) + 1, overlapped=True)
            count = complete(active, error)
            reply = active.getbuffer()
            active = None
            if count != len(_REPLY) or reply != _REPLY:
                raise OSError
            remaining()
            if _winapi.PeekNamedPipe(handle, 0) != (0, 0):
                raise OSError
            remaining()
            result = SyntheticRequestStatus.UNTRUSTED_HOLD
        except Exception:
            result = SyntheticRequestStatus.UNAVAILABLE
        finally:
            if active is not None:
                try:
                    active.cancel()
                except Exception:
                    result = SyntheticRequestStatus.UNAVAILABLE
                try:
                    # Retain the operation, its buffer and pipe until drained.
                    active.GetOverlappedResult(True)
                except Exception:
                    result = SyntheticRequestStatus.UNAVAILABLE
            if handle is not None:
                try:
                    _winapi.CloseHandle(handle)
                    remaining()
                except Exception:
                    result = SyntheticRequestStatus.UNAVAILABLE
        return result
