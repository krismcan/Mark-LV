"""One fixed, nonsecret denial exchange. A matching peer is never attested.

Only explicit Windows observation imports the standard-library pipe transport.
The request deadline bounds event waits; cancellation is drained before releasing
OS-owned buffers. A pathological kernel cleanup may outlive that deadline, so
the UI independently times out and latches a still-running worker disabled.
"""

from __future__ import annotations

from enum import Enum
import sys
import time


_PIPE = r"\\.\pipe\NayeonV1ByokCustody.Status.v1"
_QUERY = b"C1S1"
_REPLY = b"C1|NOT_AUTHORIZED|HOLD|NO_CREDENTIALS"
_SECONDS = 0.75


class NativeStatus(Enum):
    UNAVAILABLE = "UNAVAILABLE"
    UNTRUSTED_HOLD = "UNTRUSTED_HOLD"


class NativeServiceObserver:
    """No construction effects, endpoint/payload arguments, or authority result."""

    def observe(self) -> NativeStatus:
        if sys.platform != "win32":
            return NativeStatus.UNAVAILABLE
        handle = None
        active = None
        result = NativeStatus.UNAVAILABLE
        deadline = time.monotonic() + _SECONDS
        try:
            import _winapi

            def remaining():
                seconds = deadline - time.monotonic()
                if seconds <= 0:
                    raise TimeoutError
                # Round down so the event wait cannot extend the request budget.
                return int(seconds * 1000)

            def complete(operation, error):
                remaining()
                if error == _winapi.ERROR_IO_PENDING:
                    if _winapi.WaitForSingleObject(operation.event, remaining()) != 0:
                        raise TimeoutError
                elif error != 0:
                    raise OSError
                count, error = operation.GetOverlappedResult(False)
                remaining()  # A completion racing the deadline is unavailable.
                if error != 0:
                    raise OSError
                return count

            remaining()
            # Fixed local endpoint; no wait-for-server or reconnect retry.
            # SECURITY_SQOS_PRESENT with SECURITY_ANONYMOUS (zero) prevents
            # an impostor server from impersonating the interactive client.
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
                raise OSError  # Unsolicited data is not a response.
            remaining()
            active, error = _winapi.WriteFile(handle, _QUERY, overlapped=True)
            if complete(active, error) != len(_QUERY):
                raise OSError
            active = None
            # One message, with an extra byte to reject oversized/truncated data.
            active, error = _winapi.ReadFile(handle, len(_REPLY) + 1, overlapped=True)
            count = complete(active, error)
            reply = active.getbuffer()
            active = None
            if count != len(_REPLY) or reply != _REPLY:
                raise OSError
            # Refuse already queued extra frames. Future bytes cannot attest a
            # peer either: even a perfect exchange yields only UNTRUSTED_HOLD.
            if _winapi.PeekNamedPipe(handle, 0) != (0, 0):
                raise OSError
            remaining()
            result = NativeStatus.UNTRUSTED_HOLD
        except Exception:
            result = NativeStatus.UNAVAILABLE
        finally:
            if active is not None:
                try:
                    # cancel() handles a completion racing cancellation. Keep
                    # the overlapped object/buffer and pipe alive until drained.
                    active.cancel()
                except Exception:
                    result = NativeStatus.UNAVAILABLE
                try:
                    active.GetOverlappedResult(True)
                except Exception:
                    result = NativeStatus.UNAVAILABLE
            if handle is not None:
                try:
                    _winapi.CloseHandle(handle)
                except Exception:
                    result = NativeStatus.UNAVAILABLE
        return result
