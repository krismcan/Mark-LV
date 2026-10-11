"""Windows-local cooperative single-writer admission for trusted onboarding.

One known Win32 named mutex, scoped to the current logon session. Every
cooperating Nayeon process must use it; it does NOT protect against external
credential writers, other Windows sessions, malicious same-user processes, or
a filesystem/credential-store transaction. Nothing is acquired at import.
"""
from contextlib import contextmanager
import ctypes
from enum import Enum
import sys
import threading

# The same known mutex name is shared by cooperating Nayeon v1 processes
# within one Windows session. User-controlled/model-controlled names are forbidden.
_MUTEX_NAME = r"Local\NayeonV1_ProviderOnboarding_OpenAI_v1"
_WAIT_OBJECT_0 = 0
_WAIT_ABANDONED = 0x80
_WAIT_TIMEOUT = 0x102
_PROCESS_LOCK = threading.Lock()


class MutexAdmission(str, Enum):
    HELD = "held"
    BUSY = "busy"
    ABANDONED = "abandoned"
    UNAVAILABLE = "unavailable"


class WindowsOnboardingMutex:
    """Fail closed, nonblocking; no persistent credential or configuration."""

    __slots__ = ()

    @contextmanager
    def hold(self):
        if not _PROCESS_LOCK.acquire(blocking=False):
            yield MutexAdmission.BUSY
            return
        handle = None
        owned = False
        kernel = None
        try:
            if sys.platform != "win32":
                yield MutexAdmission.UNAVAILABLE
                return
            try:
                kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
                kernel.CreateMutexW.restype = ctypes.c_void_p
                kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
                kernel.WaitForSingleObject.restype = ctypes.c_uint32
                kernel.ReleaseMutex.argtypes = [ctypes.c_void_p]
                kernel.ReleaseMutex.restype = ctypes.c_int
                kernel.CloseHandle.argtypes = [ctypes.c_void_p]
                kernel.CloseHandle.restype = ctypes.c_int
                handle = kernel.CreateMutexW(None, False, _MUTEX_NAME)
                if not handle:
                    yield MutexAdmission.UNAVAILABLE
                    return
                result = kernel.WaitForSingleObject(handle, 0)
            except Exception:
                yield MutexAdmission.UNAVAILABLE
                return
            if result in (_WAIT_OBJECT_0, _WAIT_ABANDONED):
                owned = True
            if result == _WAIT_ABANDONED:
                yield MutexAdmission.ABANDONED
            elif result == _WAIT_OBJECT_0:
                yield MutexAdmission.HELD
            elif result == _WAIT_TIMEOUT:
                yield MutexAdmission.BUSY
            else:
                yield MutexAdmission.UNAVAILABLE
        finally:
            # A zero BOOL or native exception is an *unproven* release.
            # Hold the process gate indefinitely on uncertainty: allowing
            # another local contender could violate continuous tenure.
            released = True
            if handle is not None and kernel is not None:
                if owned:
                    try:
                        if not kernel.ReleaseMutex(handle):
                            released = False
                    except Exception:
                        released = False
                try:
                    if not kernel.CloseHandle(handle):
                        released = False
                except Exception:
                    released = False
            if released:
                _PROCESS_LOCK.release()
            else:
                raise RuntimeError("Onboarding mutex native release unverified; restart process")
