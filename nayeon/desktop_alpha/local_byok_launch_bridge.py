"""P133: explicit offline BYOK child-process launcher, NOT a credential actor.

Never launches or inspects Credential Manager on import, construction or
normal Nayeon navigation. Only the trusted Connection-page button callback
calls launch(). The child is the P132 manually reviewed local-user window.
No provider/network, model/tool invocation, secret arguments or secret env.
"""

from __future__ import annotations

from enum import Enum
import os
from pathlib import Path
import subprocess
import sys
import threading


_CHILD_MODULE = "nayeon.desktop_alpha.local_byok_window"
_ALLOWED_WINDOWS_ENV = frozenset({
    "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE",
    "APPDATA", "LOCALAPPDATA", "HOMEDRIVE", "HOMEPATH", "COMSPEC",
})


class LocalByokLaunchResult(str, Enum):
    LAUNCHED_OFFLINE = "launched_offline"
    ALREADY_RUNNING = "already_running"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"


def _child_windows_environment() -> dict[str, str]:
    """Pass only OS execution/profile basics, never ambient provider secrets."""
    return {
        key: value for key, value in os.environ.items()
        if key.upper() in _ALLOWED_WINDOWS_ENV and type(value) is str
    }


class LocalByokLaunchBridge:
    """One explicit child process per root owner; no auto-restart or key IO.

    The child remains independently owned by the logged-in person, even if
    the parent navigates away or exits. We do not terminate a process while
    it may be writing to Credential Manager. This is a reduced user-scope
    threat model, not a signed/broker-authenticated human consent scheme.
    """

    __slots__ = ("_child", "_gate")

    def __init__(self) -> None:
        self._child = None
        self._gate = threading.Lock()

    def launch(self) -> LocalByokLaunchResult:
        if not self._gate.acquire(blocking=False):
            return LocalByokLaunchResult.BUSY
        try:
            # Source mode still launches the fixed Python module exactly as
            # P133. Frozen mode has a different, independently signed native
            # companion admission gate; P140 has NO approved release pins.
            if (sys.platform != "win32" or not sys.executable or
                    not Path(sys.executable).is_absolute()):
                return LocalByokLaunchResult.UNAVAILABLE
            frozen = getattr(sys, "frozen", False) is True

            if self._child is not None:
                try:
                    if self._child.poll() is None:
                        return LocalByokLaunchResult.ALREADY_RUNNING
                except Exception:
                    # Cannot prove previous child retired; never open another.
                    return LocalByokLaunchResult.UNAVAILABLE
                self._child = None

            if frozen:
                # No fallback to Python -m, PATH lookup, unsigned helper or
                # unpinned adjacent executable. The gate currently ALWAYS
                # refuses (no signer/pins/Code Integrity policy owner GO).
                from nayeon.desktop_alpha.frozen_signed_byok_companion import (
                    approved_frozen_local_byok_companion,
                )
                approved = approved_frozen_local_byok_companion()
                if approved is None:
                    return LocalByokLaunchResult.UNAVAILABLE
                command = [str(approved)]
                working_dir = approved.parent
            else:
                source_root = Path(__file__).resolve().parents[2]
                if not (source_root / "nayeon" / "desktop_alpha"
                        / "local_byok_window.py").is_file():
                    return LocalByokLaunchResult.UNAVAILABLE
                command = [sys.executable, "-B", "-m", _CHILD_MODULE]
                working_dir = source_root

            try:
                child = subprocess.Popen(
                    command,
                    cwd=str(working_dir),
                    env=_child_windows_environment(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    shell=False,
                )
            except Exception:
                return LocalByokLaunchResult.UNAVAILABLE
            if type(getattr(child, "pid", None)) is not int or child.pid <= 0:
                # Do not claim a successful launch if child identity is
                # uncertain; never silently retry a possible process spawn.
                self._child = child
                return LocalByokLaunchResult.UNAVAILABLE
            self._child = child
            return LocalByokLaunchResult.LAUNCHED_OFFLINE
        finally:
            self._gate.release()

    def __repr__(self) -> str:
        return "LocalByokLaunchBridge(<redacted>)"
