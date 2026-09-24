"""Exact application/process metadata and one read-only Windows snapshot."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
import re
import ntpath


class ApplicationState(str, Enum):
    """Snapshot state only; absence does not establish a failed launch outcome."""

    OBSERVED_OPEN = "observed_open"
    OBSERVED_CLOSED = "observed_closed"
    UNKNOWN = "unknown"


class ApplicationIdentity(str, Enum):
    MATCHED = "matched"
    MISMATCHED = "mismatched"
    UNKNOWN = "unknown"


def normalize_executable_path(path: str) -> str:
    """Compare explicit local Windows paths lexically, without filesystem reads.

    Reject ambiguous forms rather than resolving devices, UNC, dot components,
    environment references, streams, or trailing-dot/space aliases.
    """
    if not isinstance(path, str):
        raise ValueError("An explicit executable path is required.")
    path = path.replace("/", "\\")
    if not re.match(r"^[A-Za-z]:\\", path):
        raise ValueError("An absolute local Windows executable path is required.")
    parts = [part for part in path[3:].split("\\") if part]
    if (not parts or path.endswith("\\")
            or any(part in (".", "..") or part.endswith((".", " "))
                   or any(ord(char) < 32 or char in '<>:"|?*%' for char in part)
                   for part in parts)):
        raise ValueError("Executable path is ambiguous or malformed.")
    if not parts[-1].lower().endswith(".exe"):
        raise ValueError("An executable file path is required.")
    return ntpath.normcase(ntpath.normpath(path))


@dataclass(frozen=True)
class ApplicationDefinition:
    """Trusted host metadata, never inferred from a request or process listing.

    This is an observation allowlist, not a replacement launch resolver. Exact
    aliases preserve the existing launch target and Windows case-insensitivity.
    """

    application_id: str
    targets: tuple[str, ...]
    expected_process_names: tuple[str, ...] = ()
    accepted_executable_paths: tuple[str, ...] = ()

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
        if isinstance(self.accepted_executable_paths, str):
            raise ValueError("Executable paths must be an explicit collection.")
        paths = tuple(normalize_executable_path(path) for path in self.accepted_executable_paths)
        if any(ntpath.basename(path).casefold() not in self.expected_process_names for path in paths):
            raise ValueError("Executable paths must name an expected process.")
        object.__setattr__(self, "accepted_executable_paths", paths)


# Only an explicit Windows application already launchable by ApplicationService.
# Paths and arbitrary application names do not inherit this entry by basename.
# No installation path is assumed; trusted host code must supply it to verify.
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
    identity: ApplicationIdentity = ApplicationIdentity.UNKNOWN


@dataclass(frozen=True)
class ProcessIdentity:
    """Service-internal candidate only; never returned as verification evidence."""

    name: str
    executable_path: str | None = None


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
    api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenProcess.restype = wintypes.HANDLE
    api.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    ]
    api.QueryFullProcessImageNameW.restype = wintypes.BOOL
    return api


def windows_process_names() -> frozenset[str] | None:
    """Compatibility helper for name-only snapshots; insufficient for identity."""
    records = _windows_snapshot()
    return None if records is None else frozenset(record.name for record in records)


def windows_process_identities(expected_names: tuple[str, ...]) -> tuple[ProcessIdentity, ...] | None:
    """Read paths for exact candidates only, using one completed snapshot."""
    return _windows_snapshot(expected_names)


def _process_path(api, process_id: int) -> str | None:
    handle = api.OpenProcess(0x1000, False, process_id)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not api.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return None
        if not 0 < size.value < len(buffer) or len(buffer.value) != size.value:
            return None
        return buffer.value
    finally:
        api.CloseHandle(handle)


def _windows_snapshot(expected_names: tuple[str, ...] | None = None) -> tuple[ProcessIdentity, ...] | None:
    """Return candidates from one completed snapshot, or None on incomplete read.

    Query-only handles inspect candidate image paths. No process is mutated.
    Enumeration traverses one snapshot; it is not polling.
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
        records = []
        while True:
            name = entry.szExeFile
            if not name or len(name) >= 259:
                return None
            name = name.casefold()
            if expected_names is None:
                records.append(ProcessIdentity(name))
            elif name in expected_names:
                records.append(ProcessIdentity(name, _process_path(api, entry.th32ProcessID)))
            if not api.Process32NextW(snapshot, ctypes.byref(entry)):
                if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                    return None
                return tuple(records)
    finally:
        api.CloseHandle(snapshot)
