"""Bounded UTF-8 reads from validated Windows handles; no discovery or writes."""

from __future__ import annotations

from contextlib import ExitStack
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
import platform
import re


MAX_FILE_BYTES = 64 * 1024
_MAX_PATH = 260
_GENERIC_READ = 0x80000000
_READ_ATTRIBUTES = 0x80
_SHARE_READ = 1
_OPEN_EXISTING = 3
_OPEN_FLAGS = 0x00200000 | 0x02000000 | 0x00100000  # reparse, directory, no recall
_DIRECTORY = 0x10
_UNSAFE_ATTRIBUTES = 0x400 | 0x1000 | 0x40000 | 0x400000  # reparse/offline/recall


class FileReadFailure(str, Enum):
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    INVALID_TARGET = "invalid_target"
    UNSAFE_PATH = "unsafe_path"
    TOO_LARGE = "too_large"
    UNSUPPORTED_CONTENT = "unsupported_content"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    BUSY = "busy"
    READ_ERROR = "read_error"
    STRUCTURED_REQUIRED = "structured_required"


class FileReadError(RuntimeError):
    """Typed domain failure with no OS exception text, path, or file content."""

    def __init__(self, failure: FileReadFailure) -> None:
        self.failure = failure
        super().__init__(f"File read failed: {failure.value}.")


@dataclass(frozen=True, repr=False)
class FileReadResult:
    path: str
    text: str
    byte_count: int
    state: str = "read"


def normalize_file_path(path: str) -> str:
    """Lexical only. Preserve component case; no IO, expansion or alias lookup."""
    if not isinstance(path, str):
        raise TypeError("An explicit file path string is required.")
    path = path.replace("/", "\\")
    if not re.match(r"^[A-Za-z]:\\", path) or len(path.encode("utf-16-le", errors="surrogatepass")) // 2 >= _MAX_PATH:
        raise ValueError("An explicit bounded local Windows file path is required.")
    parts = path[3:].split("\\")
    for part in parts:
        if (not part or part in (".", "..") or part.endswith((".", " "))
                or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF or c in '<>:"|?*[]%$' for c in part)
                or re.fullmatch(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])",
                                part.split(".")[0].rstrip(" "), re.IGNORECASE)):
            raise ValueError("File path is ambiguous or malformed.")
    return path[0].upper() + path[1:]


class FilesystemService:
    """Read only an explicit ordinary local file, after same-handle validation."""

    def read_file(self, path: str) -> FileReadResult:
        try:
            path = normalize_file_path(path)
        except (TypeError, ValueError):
            raise FileReadError(FileReadFailure.INVALID_TARGET) from None
        if platform.system() != "Windows":
            raise FileReadError(FileReadFailure.UNSUPPORTED_PLATFORM)
        try:
            data = _read_windows(path)
        except FileReadError:
            raise
        except OSError:
            raise FileReadError(FileReadFailure.READ_ERROR) from None
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise FileReadError(FileReadFailure.UNSUPPORTED_CONTENT) from None
        # Deterministic text policy, not a claim to detect every binary format.
        if any((ord(c) < 32 and c not in "\t\r\n") or 0x7F <= ord(c) <= 0x9F for c in text):
            raise FileReadError(FileReadFailure.UNSUPPORTED_CONTENT)
        return FileReadResult(path, text, len(data))


class _FileInformation(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD), ("creation", wintypes.FILETIME),
        ("access", wintypes.FILETIME), ("write", wintypes.FILETIME),
        ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
        ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD),
    ]


def _kernel32():
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateFileW": ([wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                         wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE], wintypes.HANDLE),
        "GetDriveTypeW": ([wintypes.LPCWSTR], wintypes.UINT),
        "GetFileType": ([wintypes.HANDLE], wintypes.DWORD),
        "GetFileInformationByHandle": ([wintypes.HANDLE, ctypes.POINTER(_FileInformation)], wintypes.BOOL),
        "GetFinalPathNameByHandleW": ([wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD,
                                       wintypes.DWORD], wintypes.DWORD),
        "ReadFile": ([wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                      ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = arguments, result
    return api


def _os_failure() -> FileReadError:
    return FileReadError({
        2: FileReadFailure.NOT_FOUND, 3: FileReadFailure.NOT_FOUND,
        5: FileReadFailure.ACCESS_DENIED, 32: FileReadFailure.BUSY,
    }.get(ctypes.get_last_error(), FileReadFailure.READ_ERROR))


def _inspect_handle(api, handle, expected: str, *, directory: bool) -> _FileInformation:
    if api.GetFileType(handle) != 1:  # FILE_TYPE_DISK
        raise FileReadError(FileReadFailure.INVALID_TARGET)
    info = _FileInformation()
    if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise _os_failure()
    if info.attributes & _UNSAFE_ATTRIBUTES:
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    if bool(info.attributes & _DIRECTORY) != directory:
        raise FileReadError(FileReadFailure.INVALID_TARGET)
    buffer = ctypes.create_unicode_buffer(_MAX_PATH + 4)
    length = api.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    # FILE_NAME_NORMALIZED | VOLUME_NAME_DOS (both zero). No retry or rewrite.
    if not 4 < length < len(buffer):
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    final = buffer.value
    if not final.startswith("\\\\?\\"):
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    final = final[4:]
    # Exact component spelling deliberately fails closed on case/short-name aliases.
    if final[:1].upper() + final[1:] != expected:
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    return info


def _read_windows(path: str) -> bytes:
    api = _kernel32()
    root = path[:3]
    if api.GetDriveTypeW(root) not in (2, 3, 6):  # removable, fixed, RAM; never network
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    parts = path[3:].split("\\")
    ancestors = [root] + [root + "\\".join(parts[:i]) for i in range(1, len(parts))]
    with ExitStack() as handles:
        # Inspect explicit ancestors without following their final reparse point.
        # Retain handles with no write/delete sharing until the read completes.
        # These checks never substitute for validation of the final read handle.
        for expected in ancestors + [path]:
            directory = expected != path
            handle = api.CreateFileW(expected, _READ_ATTRIBUTES if directory else _GENERIC_READ,
                                     _SHARE_READ, None, _OPEN_EXISTING, _OPEN_FLAGS, None)
            if handle in (None, 0, ctypes.c_void_p(-1).value):
                raise _os_failure()
            handles.callback(api.CloseHandle, handle)
            info = _inspect_handle(api, handle, expected, directory=directory)
        size = (info.size_high << 32) | info.size_low
        if size > MAX_FILE_BYTES:
            raise FileReadError(FileReadFailure.TOO_LARGE)
        # At most 64 KiB + one overflow byte, even if the file changes size.
        buffer = ctypes.create_string_buffer(MAX_FILE_BYTES + 1)
        total = 0
        while total < len(buffer):
            count = wintypes.DWORD()
            remaining = len(buffer) - total
            if not api.ReadFile(handle, ctypes.byref(buffer, total), remaining, ctypes.byref(count), None):
                raise _os_failure()
            if count.value > remaining:
                raise FileReadError(FileReadFailure.READ_ERROR)
            if count.value == 0:
                break
            total += count.value
        if total > MAX_FILE_BYTES:
            raise FileReadError(FileReadFailure.TOO_LARGE)
        return buffer.raw[:total]
