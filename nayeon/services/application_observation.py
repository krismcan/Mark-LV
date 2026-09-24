"""Exact application/process metadata and one read-only Windows snapshot."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
import re


class ApplicationState(str, Enum):
    OBSERVED_OPEN = "observed_open"
    OBSERVED_CLOSED = "observed_closed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ApplicationDefinition:
    """Trusted host metadata, never inferred from a request or process listing.

    This is an observation allowlist, not a replacement launch resolver. Exact
    aliases preserve the existing launch target and Windows case-insensitivity.
    """

    application_id: str
    targets: tuple[str, ...]
    expected_process_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.application_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_.-]*", self.application_id,
        ):
            raise ValueError("A safe canonical application identifier is required.")
        if not self.targets or any(not isinstance(target, str) or not target.strip()
                                   for target in self.targets):
            raise ValueError("Explicit application targets are required.")
        if any(not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]*\.exe", name, re.IGNORECASE)
               for name in self.expected_process_names):
            raise ValueError("Exact process executable basenames are required.")
        object.__setattr__(self, "targets", tuple(target.strip().casefold() for target in self.targets))
        object.__setattr__(self, "expected_process_names",
                           tuple(name.casefold() for name in self.expected_process_names))


# Only an explicit Windows application already launchable by ApplicationService.
# Paths and arbitrary application names do not inherit this entry by basename.
DEFAULT_APPLICATIONS = (
    ApplicationDefinition("notepad", ("notepad", "notepad.exe"), ("notepad.exe",)),
)


@dataclass(frozen=True)
class ApplicationObservation:
    """Minimal result: request binding plus canonical identity/state; no inventory."""

    target: str
    state: ApplicationState
    application_id: str | None = None
    expected_process_names: tuple[str, ...] = ()


class _ProcessEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
    ]


def _kernel32():
    """Load read-only Tool Help functions only when Windows observation is used."""
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    api.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ("Process32FirstW", "Process32NextW"):
        function = getattr(api, name)
        function.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry)]
        function.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    return api


def windows_process_names() -> frozenset[str] | None:
    """Return a complete single snapshot, or None on any incomplete/invalid read.

    Enumeration traverses one snapshot; it is not polling. No processes are
    opened, launched, terminated, or modified. Inventory stays inside services.
    """
    api = _kernel32()
    snapshot = api.CreateToolhelp32Snapshot(0x00000002, 0)  # TH32CS_SNAPPROCESS
    if snapshot is None or snapshot == ctypes.c_void_p(-1).value:
        return None
    try:
        entry = _ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        # An empty/invalid initial snapshot is not reliable negative evidence.
        if not api.Process32FirstW(snapshot, ctypes.byref(entry)):
            return None
        names = set()
        while True:
            name = entry.szExeFile
            if not name or len(name) >= 259:
                return None
            names.add(name.casefold())
            if not api.Process32NextW(snapshot, ctypes.byref(entry)):
                if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                    return None
                return frozenset(names)
    finally:
        api.CloseHandle(snapshot)
