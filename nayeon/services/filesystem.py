"""Bounded reads/listings and irreversible file/directory creation on Windows."""

from __future__ import annotations

from contextlib import ExitStack
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import platform
import re
import struct


MAX_FILE_BYTES = 64 * 1024
MAX_DIRECTORY_ENTRIES = 256
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


class DirectoryListFailure(str, Enum):
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    INVALID_TARGET = "invalid_target"
    UNSAFE_PATH = "unsafe_path"
    TOO_MANY_ENTRIES = "too_many_entries"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    BUSY = "busy"
    LIST_ERROR = "list_error"
    STRUCTURED_REQUIRED = "structured_required"


class DirectoryListError(RuntimeError):
    """Directory-domain failure without names, paths, or raw OS details."""

    def __init__(self, failure: DirectoryListFailure) -> None:
        self.failure = failure
        super().__init__(f"Directory listing failed: {failure.value}.")


@dataclass(frozen=True, repr=False)
class DirectoryEntry:
    name: str
    kind: str  # file or directory; never followed or opened


@dataclass(frozen=True, repr=False)
class DirectoryListResult:
    path: str
    entries: tuple[DirectoryEntry, ...]
    state: str = "listed"

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    @property
    def entry_count(self) -> int:
        return len(self.entries)


class FileCreateFailure(str, Enum):
    ALREADY_EXISTS = "already_exists"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    INVALID_TARGET = "invalid_target"
    UNSAFE_PATH = "unsafe_path"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    BUSY = "busy"
    CREATE_ERROR = "create_error"
    STRUCTURED_REQUIRED = "structured_required"


class FileCreateError(RuntimeError):
    """Pre-commit failure without path, identity or raw OS error details."""

    def __init__(self, failure: FileCreateFailure) -> None:
        self.failure = failure
        super().__init__(f"Empty file creation failed: {failure.value}.")


@dataclass(frozen=True, repr=False)
class FileCreateResult:
    """Committed creation receipt, not a claim about subsequent file state.

    Only copied metadata escapes; no handle, lease, rollback or undo resource.
    byte_count describes the empty creation, not later concurrent user writes.
    """

    path: str
    state: str = field(default="created", init=False)
    byte_count: int = field(default=0, init=False)
    _identity: tuple[int, bytes] | None = field(default=None, repr=False)


class FileCreateObservation(str, Enum):
    MATCHED = "matched"
    CHANGED = "changed"
    UNKNOWN = "unknown"


class DirectoryCreateFailure(str, Enum):
    ALREADY_EXISTS = "already_exists"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    INVALID_TARGET = "invalid_target"
    UNSAFE_PATH = "unsafe_path"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    BUSY = "busy"
    CREATE_ERROR = "create_error"
    STRUCTURED_REQUIRED = "structured_required"


class DirectoryCreateError(RuntimeError):
    """Pre-commit directory creation failure; no private OS details."""

    def __init__(self, failure: DirectoryCreateFailure) -> None:
        self.failure = failure
        super().__init__(f"Directory creation failed: {failure.value}.")


class DirectoryCreateObservation(str, Enum):
    PRESENT = "present"  # Safe current path, NOT proof of the exact created object.
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, repr=False)
class DirectoryCreateResult:
    """Committed creation with optional unbound snapshot, never an owning lease."""

    path: str
    state: str = field(default="created", init=False)
    _observation: DirectoryCreateObservation = field(default=DirectoryCreateObservation.UNKNOWN, repr=False)


class TextFileCreateFailure(str, Enum):
    ALREADY_EXISTS = "already_exists"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    INVALID_TARGET = "invalid_target"
    INVALID_TEXT = "invalid_text"
    UNSAFE_PATH = "unsafe_path"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    BUSY = "busy"
    CREATE_ERROR = "create_error"
    STRUCTURED_REQUIRED = "structured_required"


class TextFileCreateError(RuntimeError):
    """Pre-commit failure only; no path, text or OS details."""

    def __init__(self, failure: TextFileCreateFailure) -> None:
        self.failure = failure
        super().__init__(f"Text file creation failed: {failure.value}.")


class TextWriteOutcome(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class TextFlushOutcome(str, Enum):
    COMPLETE = "complete"
    UNKNOWN = "unknown"
    NOT_ATTEMPTED = "not_attempted"


@dataclass(frozen=True, repr=False)
class TextFileCreateResult:
    """Committed creation; write counts are acknowledgements, not verification.

    No content or owning handle is retained. Identity is private copied metadata.
    """

    path: str
    expected_byte_count: int
    write_outcome: TextWriteOutcome = TextWriteOutcome.UNKNOWN
    flush_outcome: TextFlushOutcome = TextFlushOutcome.NOT_ATTEMPTED
    written_byte_count: int | None = None
    state: str = field(default="created", init=False)
    _identity: tuple[int, bytes] | None = field(default=None, repr=False)


class FileCopyFailure(str, Enum):
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    ACCESS_DENIED = "access_denied"
    INVALID_TARGET = "invalid_target"
    UNSAFE_PATH = "unsafe_path"
    TOO_LARGE = "too_large"
    CROSS_VOLUME = "cross_volume"
    BUSY = "busy"
    COPY_ERROR = "copy_error"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    STRUCTURED_REQUIRED = "structured_required"


class FileCopyError(RuntimeError):
    """Pre-commit copy failure with fixed, non-sensitive domain information."""

    def __init__(self, failure: FileCopyFailure) -> None:
        self.failure = failure
        super().__init__(f"File copy failed: {failure.value}.")


class CopyOutcome(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class CopyFlushOutcome(str, Enum):
    COMPLETE = "complete"
    UNKNOWN = "unknown"
    NOT_ATTEMPTED = "not_attempted"


@dataclass(frozen=True, repr=False)
class FileCopyResult:
    """Committed destination receipt. Private evidence, never content or handles."""

    source_path: str
    destination_path: str
    expected_byte_count: int
    copy_outcome: CopyOutcome = CopyOutcome.UNKNOWN
    flush_outcome: CopyFlushOutcome = CopyFlushOutcome.NOT_ATTEMPTED
    written_byte_count: int | None = None
    state: str = field(default="created", init=False)
    source_read_complete: bool = field(default=True, init=False)
    _source_identity: tuple[int, bytes] | None = field(default=None, repr=False)
    _destination_identity: tuple[int, bytes] | None = field(default=None, repr=False)
    _digest: bytes | None = field(default=None, repr=False)


class FileDeleteError(RuntimeError):
    """Fixed, redacted pre-disposition failure."""

    def __init__(self) -> None:
        super().__init__("File deletion could not be safely prepared or executed.")


class DeleteDisposition(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    NOT_ACKNOWLEDGED = "not_acknowledged"
    UNKNOWN = "unknown"


class DeleteClose(str, Enum):
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class DeleteObservation(str, Enum):
    CONFIRMED_ABSENT = "confirmed_absent"
    PRESENT_SAME_IDENTITY = "present_same_identity"
    PRESENT_DIFFERENT_IDENTITY = "present_different_identity"
    UNKNOWN = "unknown"


@dataclass(frozen=True, repr=False)
class _DeletionBinding:
    """Internally observed values only; no content, access time or owning handle."""

    path: str
    namespace: tuple[tuple[int, bytes], ...]
    identity: tuple[int, bytes]
    size: int
    links: int
    attributes: int
    creation_time: int
    write_time: int


@dataclass(frozen=True, repr=False)
class FileDeleteResult:
    disposition: DeleteDisposition
    source_close: DeleteClose
    observation: DeleteObservation
    _binding: _DeletionBinding = field(repr=False)
    _cleanup_complete: bool = field(default=True, repr=False)


def encode_creation_text(text: str) -> bytes:
    """Strict UTF-8, 1..64 KiB; reject C0/C1/DEL except TAB, LF and CR.

    No stripping, newline conversion, normalization or BOM insertion.
    The character bound avoids allocating an unbounded encoded buffer.
    """
    if not isinstance(text, str):
        raise TypeError("An explicit text string is required.")
    if not 1 <= len(text) <= MAX_FILE_BYTES:
        raise ValueError("Text must encode to 1 through 65536 bytes.")
    try:
        data = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise ValueError("Text must be valid UTF-8.") from None
    if len(data) > MAX_FILE_BYTES or any(
        (ord(c) < 32 and c not in "\t\r\n") or 0x7F <= ord(c) <= 0x9F for c in text
    ):
        raise ValueError("Text is oversized or contains unsupported control characters.")
    return data


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


def normalize_directory_path(path: str) -> str:
    """Reuse file component rules, additionally permitting an explicit drive root."""
    if isinstance(path, str) and re.fullmatch(r"[A-Za-z]:[\\/]", path):
        return path[0].upper() + ":\\"
    return normalize_file_path(path)


class FilesystemService:
    """Own local filesystem IO; creation is explicit and never rolled back."""

    def prepare_deletion(self, path: str) -> _DeletionBinding:
        """Approved DeleteFile-only metadata preparation, before confirmation.

        No mutation or content read; all handles close before evidence escapes.
        """
        try:
            path = normalize_file_path(path)
            if platform.system() != "Windows":
                raise FileDeleteError()
            return _prepare_delete_windows(path)
        except Exception:
            raise FileDeleteError() from None

    def delete_file(self, binding: _DeletionBinding) -> FileDeleteResult:
        try:
            if not _valid_deletion_binding(binding) or platform.system() != "Windows":
                raise FileDeleteError()
            return _delete_windows(binding)
        except Exception:
            raise FileDeleteError() from None

    def observe_deleted_file(self, result: FileDeleteResult) -> DeleteObservation:
        """Fresh read-only observation; never re-prepare or freshen the binding."""
        if (type(result) is not FileDeleteResult or not _valid_deletion_binding(result._binding)
                or result._cleanup_complete is not True or platform.system() != "Windows"):
            return DeleteObservation.UNKNOWN
        try:
            api = _kernel32()
            def close(handle):
                if not api.CloseHandle(handle):
                    raise FileDeleteError()
            with ExitStack() as handles:
                namespace = _delete_namespace(api, result._binding.path, handles, close)
                if namespace != result._binding.namespace:
                    return DeleteObservation.UNKNOWN
                return _delete_observe_path(api, result._binding)
        except Exception:
            return DeleteObservation.UNKNOWN

    def copy_file(self, source_path: str, destination_path: str) -> FileCopyResult:
        try:
            source_path = normalize_file_path(source_path)
            destination_path = normalize_file_path(destination_path)
            if source_path.casefold() == destination_path.casefold():
                raise ValueError("Self-copy is not supported.")
        except (TypeError, ValueError):
            raise FileCopyError(FileCopyFailure.INVALID_TARGET) from None
        if platform.system() != "Windows":
            raise FileCopyError(FileCopyFailure.UNSUPPORTED_PLATFORM)
        try:
            return _copy_file_windows(source_path, destination_path)
        except FileCopyError:
            raise
        except FileReadError as exc:
            failure = FileCopyFailure.__members__.get(exc.failure.name, FileCopyFailure.COPY_ERROR)
            raise FileCopyError(failure) from None
        except Exception:
            raise FileCopyError(FileCopyFailure.COPY_ERROR) from None

    def observe_copied_file(self, result: FileCopyResult) -> FileCreateObservation:
        # Incomplete receipts are inconclusive; never upgrade them from pathname presence.
        if not isinstance(result, FileCopyResult) or platform.system() != "Windows":
            return FileCreateObservation.UNKNOWN
        try:
            normalize_file_path(result.source_path)
            path = normalize_file_path(result.destination_path)
            if (result.state != "created" or result.source_read_complete is not True
                    or type(result.expected_byte_count) is not int
                    or not 0 <= result.expected_byte_count <= MAX_FILE_BYTES
                    or result.copy_outcome is not CopyOutcome.COMPLETE
                    or result.flush_outcome is not CopyFlushOutcome.COMPLETE
                    or type(result.written_byte_count) is not int
                    or result.written_byte_count != result.expected_byte_count
                    or not _valid_create_identity(result._source_identity)
                    or not _valid_create_identity(result._destination_identity)
                    or type(result._digest) is not bytes or len(result._digest) != 32):
                return FileCreateObservation.UNKNOWN
            if (result._source_identity == result._destination_identity
                    or result._source_identity[0] != result._destination_identity[0]
                    or result.source_path.casefold() == path.casefold()):
                return FileCreateObservation.CHANGED
            return _observe_copy_windows(path, result)
        except Exception:
            return FileCreateObservation.UNKNOWN

    def create_text_file(self, path: str, text: str) -> TextFileCreateResult:
        try:
            path = normalize_file_path(path)
        except (TypeError, ValueError):
            raise TextFileCreateError(TextFileCreateFailure.INVALID_TARGET) from None
        try:
            data = encode_creation_text(text)
        except (TypeError, ValueError):
            raise TextFileCreateError(TextFileCreateFailure.INVALID_TEXT) from None
        if platform.system() != "Windows":
            raise TextFileCreateError(TextFileCreateFailure.UNSUPPORTED_PLATFORM)
        try:
            return _create_text_windows(path, data)
        except FileReadError as exc:
            failure = TextFileCreateFailure.__members__.get(exc.failure.name, TextFileCreateFailure.CREATE_ERROR)
            raise TextFileCreateError(failure) from None
        except OSError:
            raise TextFileCreateError(TextFileCreateFailure.CREATE_ERROR) from None

    def observe_created_text_file(self, result: TextFileCreateResult, text: str) -> FileCreateObservation:
        if not isinstance(result, TextFileCreateResult) or platform.system() != "Windows":
            return FileCreateObservation.UNKNOWN
        try:
            path = normalize_file_path(result.path)
            expected = encode_creation_text(text)
            if (result.state != "created" or type(result.expected_byte_count) is not int
                    or result.expected_byte_count != len(expected)
                    or not isinstance(result.write_outcome, TextWriteOutcome)
                    or not isinstance(result.flush_outcome, TextFlushOutcome)):
                return FileCreateObservation.UNKNOWN
            observation = _observe_created_text_windows(path, result._identity, expected)
            if observation is FileCreateObservation.CHANGED:
                return observation
            if (result.write_outcome is TextWriteOutcome.COMPLETE
                    and result.flush_outcome is TextFlushOutcome.COMPLETE
                    and type(result.written_byte_count) is int
                    and result.written_byte_count == len(expected)):
                return observation
        except Exception:
            pass
        return FileCreateObservation.UNKNOWN

    def create_directory(self, path: str) -> DirectoryCreateResult:
        try:
            # A final component is required; unlike listing, drive root is invalid.
            path = normalize_file_path(path)
        except (TypeError, ValueError):
            raise DirectoryCreateError(DirectoryCreateFailure.INVALID_TARGET) from None
        if platform.system() != "Windows":
            raise DirectoryCreateError(DirectoryCreateFailure.UNSUPPORTED_PLATFORM)
        try:
            return _create_directory_windows(path)
        except FileReadError as exc:
            failure = DirectoryCreateFailure.__members__.get(exc.failure.name, DirectoryCreateFailure.CREATE_ERROR)
            raise DirectoryCreateError(failure) from None
        except OSError:
            raise DirectoryCreateError(DirectoryCreateFailure.CREATE_ERROR) from None

    def observe_created_directory(self, result: DirectoryCreateResult) -> DirectoryCreateObservation:
        if not isinstance(result, DirectoryCreateResult) or platform.system() != "Windows":
            return DirectoryCreateObservation.UNKNOWN
        try:
            path = normalize_file_path(result.path)
            api = _kernel32()
            with ExitStack() as handles:
                try:
                    _create_ancestors(api, path, handles, lambda h: api.CloseHandle(h))
                except FileReadError as exc:
                    return (DirectoryCreateObservation.CONTRADICTED if exc.failure is FileReadFailure.NOT_FOUND
                            else DirectoryCreateObservation.UNKNOWN)
                return _directory_create_snapshot(api, path)
        except Exception:
            return DirectoryCreateObservation.UNKNOWN

    def create_empty_file(self, path: str) -> FileCreateResult:
        try:
            path = normalize_file_path(path)
        except (TypeError, ValueError):
            raise FileCreateError(FileCreateFailure.INVALID_TARGET) from None
        if platform.system() != "Windows":
            raise FileCreateError(FileCreateFailure.UNSUPPORTED_PLATFORM)
        try:
            return _create_empty_windows(path)
        except FileReadError as exc:
            # Ancestor checks retain their existing read-only contract.
            failure = FileCreateFailure.__members__.get(exc.failure.name, FileCreateFailure.CREATE_ERROR)
            raise FileCreateError(failure) from None
        except OSError:
            raise FileCreateError(FileCreateFailure.CREATE_ERROR) from None

    def observe_created_file(self, result: FileCreateResult) -> FileCreateObservation:
        if (not isinstance(result, FileCreateResult) or not _valid_create_identity(result._identity)
                or platform.system() != "Windows"):
            return FileCreateObservation.UNKNOWN
        try:
            path = normalize_file_path(result.path)
            return _observe_created_windows(path, result._identity)
        except Exception:
            # No fallback identity, retry, mutation, or raw exception disclosure.
            return FileCreateObservation.UNKNOWN

    def list_directory(self, path: str) -> DirectoryListResult:
        try:
            path = normalize_directory_path(path)
        except (TypeError, ValueError):
            raise DirectoryListError(DirectoryListFailure.INVALID_TARGET) from None
        if platform.system() != "Windows":
            raise DirectoryListError(DirectoryListFailure.UNSUPPORTED_PLATFORM)
        try:
            entries = _list_windows(path)
        except FileReadError as exc:
            # Reuse unchanged handle checks and OS error classification. Read-only
            # helpers retain their existing contract; translate at this boundary.
            try:
                failure = DirectoryListFailure(exc.failure.value)
            except ValueError:
                failure = DirectoryListFailure.LIST_ERROR
            raise DirectoryListError(failure) from None
        except OSError:
            raise DirectoryListError(DirectoryListFailure.LIST_ERROR) from None
        return DirectoryListResult(path, entries)

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
        "GetFileInformationByHandleEx": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                         wintypes.DWORD], wintypes.BOOL),
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


def _list_windows(path: str) -> tuple[DirectoryEntry, ...]:
    api = _kernel32()
    root = path[:3]
    if api.GetDriveTypeW(root) not in (2, 3, 6):
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    parts = path[3:].split("\\")
    ancestors = [] if path == root else (
        [root] + [root + "\\".join(parts[:i]) for i in range(1, len(parts))])
    with ExitStack() as handles:
        for expected in ancestors + [path]:
            # FILE_LIST_DIRECTORY (1) only for the target. No write/delete sharing;
            # retain every inspected ancestor and the exact target until done.
            access = _READ_ATTRIBUTES | (1 if expected == path else 0)
            handle = api.CreateFileW(expected, access, _SHARE_READ, None,
                                     _OPEN_EXISTING, _OPEN_FLAGS, None)
            if handle in (None, 0, ctypes.c_void_p(-1).value):
                raise _os_failure()
            handles.callback(api.CloseHandle, handle)
            _inspect_handle(api, handle, expected, directory=True)
        return _enumerate_directory(api, handle)


def _enumerate_directory(api, handle) -> tuple[DirectoryEntry, ...]:
    # FILE_FULL_DIR_INFO: fixed 68-byte prefix, variable UTF-16 name; each
    # non-final record begins at an 8-byte boundary. No child handle queries.
    # https://learn.microsoft.com/windows/win32/api/winbase/ns-winbase-file_full_dir_info
    buffer = (ctypes.c_longlong * 512)()  # aligned, fixed 4096-byte batch
    entries = []
    seen = set()
    information_class = 15  # FileFullDirectoryRestartInfo, then continuation 14
    while True:
        ctypes.memset(buffer, 0, ctypes.sizeof(buffer))
        if not api.GetFileInformationByHandleEx(handle, information_class, buffer, ctypes.sizeof(buffer)):
            if ctypes.get_last_error() == 18:  # ERROR_NO_MORE_FILES is the only normal end
                return tuple(entries)
            raise _os_failure()
        information_class = 14  # FileFullDirectoryInfo
        data = bytes(buffer)
        offset = 0
        while True:
            if offset + 68 > len(data):
                raise DirectoryListError(DirectoryListFailure.LIST_ERROR)
            next_offset = struct.unpack_from("<I", data, offset)[0]
            attributes, name_length = struct.unpack_from("<II", data, offset + 56)
            end = offset + 68 + name_length
            if (not name_length or name_length % 2 or name_length > 510 or end > len(data)
                    or (next_offset and (next_offset % 8 or next_offset < 68 + name_length
                                         or offset + next_offset + 68 > len(data)))):
                raise DirectoryListError(DirectoryListFailure.LIST_ERROR)
            try:
                name = data[offset + 68:end].decode("utf-16-le", errors="strict")
            except UnicodeDecodeError:
                raise DirectoryListError(DirectoryListFailure.LIST_ERROR) from None
            if (name in seen or any(ord(c) < 32 or c in '\\/:<>"|?*' for c in name)):
                raise DirectoryListError(DirectoryListFailure.LIST_ERROR)
            seen.add(name)
            if name not in (".", ".."):
                if len(entries) == MAX_DIRECTORY_ENTRIES:
                    raise DirectoryListError(DirectoryListFailure.TOO_MANY_ENTRIES)
                # The two-kind v1 contract does not represent links. Fail closed
                # rather than mislabel or follow a child reparse point.
                if attributes & 0x400:
                    raise DirectoryListError(DirectoryListFailure.UNSAFE_PATH)
                entries.append(DirectoryEntry(name, "directory" if attributes & _DIRECTORY else "file"))
            if not next_offset:
                break
            offset += next_offset


class _FileIdInfo(ctypes.Structure):
    # FILE_ID_INFO, FileIdInfo (18). Never substitute the older 64-bit index.
    # https://learn.microsoft.com/windows/win32/api/winbase/ns-winbase-file_id_info
    _fields_ = [("volume", ctypes.c_ulonglong), ("identifier", ctypes.c_ubyte * 16)]


def _valid_create_identity(identity) -> bool:
    return (type(identity) is tuple and len(identity) == 2
            and type(identity[0]) is int and 0 < identity[0] < 2**64
            and type(identity[1]) is bytes and len(identity[1]) == 16 and any(identity[1]))


def _create_snapshot(api, handle, expected: str):
    """Read-only snapshot: affirmative contradictions differ from missing evidence."""
    if api.GetFileType(handle) != 1:
        return FileCreateObservation.UNKNOWN, None
    info = _FileInformation()
    if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
        return FileCreateObservation.UNKNOWN, None
    if info.attributes & (_DIRECTORY | _UNSAFE_ATTRIBUTES):
        return FileCreateObservation.CHANGED, None
    buffer = ctypes.create_unicode_buffer(_MAX_PATH + 4)
    length = api.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    if not 4 < length < len(buffer) or length != len(buffer.value.encode("utf-16-le")) // 2:
        return FileCreateObservation.UNKNOWN, None
    if not buffer.value.startswith("\\\\?\\"):
        return FileCreateObservation.UNKNOWN, None
    final = buffer.value[4:]
    if final[:1].upper() + final[1:] != expected or info.size_high or info.size_low:
        return FileCreateObservation.CHANGED, None
    identity = _FileIdInfo()
    if not api.GetFileInformationByHandleEx(handle, 18, ctypes.byref(identity), ctypes.sizeof(identity)):
        return FileCreateObservation.UNKNOWN, None
    value = (identity.volume, bytes(identity.identifier))
    if not _valid_create_identity(value):
        return FileCreateObservation.UNKNOWN, None
    return FileCreateObservation.MATCHED, value


def _create_ancestors(api, path: str, handles: ExitStack, close):
    root = path[:3]
    if api.GetDriveTypeW(root) not in (2, 3, 6):
        raise FileReadError(FileReadFailure.UNSAFE_PATH)
    parts = path[3:].split("\\")
    ancestors = [root] + [root + "\\".join(parts[:i]) for i in range(1, len(parts))]
    for expected in ancestors:
        # Include FILE_LIST_DIRECTORY (read-data sharing category), not only
        # attributes. Keep no-write/no-delete sharing until creation completes.
        handle = api.CreateFileW(expected, _READ_ATTRIBUTES | 1, _SHARE_READ,
                                 None, _OPEN_EXISTING, _OPEN_FLAGS, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            raise _os_failure()
        handles.callback(close, handle)
        _inspect_handle(api, handle, expected, directory=True)
    return handle  # Retained immediate parent, for native volume evidence.


def _create_empty_windows(path: str) -> FileCreateResult:
    api = _kernel32()
    identity = None
    close_ok = True

    def close(handle):
        nonlocal close_ok
        try:
            if not api.CloseHandle(handle):
                close_ok = False
        except Exception:
            close_ok = False
        # A close diagnostic must not misreport committed creation as FAILED.
        # Attempt every close once; do not retry a possibly already closed handle.

    with ExitStack() as handles:
        _create_ancestors(api, path, handles, close)
        # CREATE_NEW (1) is the mutation commit point. No write/delete access,
        # overwrite fallback, pathname precheck or rollback. Read-data access
        # makes no-write/no-delete sharing effective during the short snapshot.
        handle = api.CreateFileW(path, _READ_ATTRIBUTES | 1, _SHARE_READ, None, 1,
                                 0x80 | 0x00200000 | 0x00100000, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            failure = {80: FileCreateFailure.ALREADY_EXISTS, 183: FileCreateFailure.ALREADY_EXISTS,
                       2: FileCreateFailure.NOT_FOUND, 3: FileCreateFailure.NOT_FOUND,
                       5: FileCreateFailure.ACCESS_DENIED, 32: FileCreateFailure.BUSY}.get(
                           ctypes.get_last_error(), FileCreateFailure.CREATE_ERROR)
            raise FileCreateError(failure)
        handles.callback(close, handle)
        try:
            observation, evidence = _create_snapshot(api, handle, path)
            if observation is FileCreateObservation.MATCHED:
                identity = evidence
        except Exception:
            # The file exists now. Optional evidence failure NEVER deletes it
            # or changes execution into a pre-commit failure.
            pass
    return FileCreateResult(path, _identity=identity if close_ok else None)


def _observe_created_windows(path: str, original_identity) -> FileCreateObservation:
    api = _kernel32()
    with ExitStack() as handles:
        try:
            _create_ancestors(api, path, handles, lambda h: api.CloseHandle(h))
        except FileReadError as exc:
            return (FileCreateObservation.CHANGED if exc.failure is FileReadFailure.NOT_FOUND
                    else FileCreateObservation.UNKNOWN)
        handle = api.CreateFileW(path, _READ_ATTRIBUTES | 1, _SHARE_READ, None,
                                 _OPEN_EXISTING, _OPEN_FLAGS, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            return (FileCreateObservation.CHANGED if ctypes.get_last_error() in (2, 3)
                    else FileCreateObservation.UNKNOWN)
        handles.callback(api.CloseHandle, handle)
        observation, identity = _create_snapshot(api, handle, path)
        if observation is FileCreateObservation.MATCHED and identity != original_identity:
            return FileCreateObservation.CHANGED
        return observation


def _directory_create_snapshot(api, path: str) -> DirectoryCreateObservation:
    """Bounded read-only pathname reopen; cannot establish creation continuity."""
    handle = api.CreateFileW(path, _READ_ATTRIBUTES | 1, _SHARE_READ, None,
                             _OPEN_EXISTING, _OPEN_FLAGS, None)
    if handle in (None, 0, ctypes.c_void_p(-1).value):
        return (DirectoryCreateObservation.CONTRADICTED if ctypes.get_last_error() in (2, 3)
                else DirectoryCreateObservation.UNKNOWN)
    with ExitStack() as handles:
        handles.callback(api.CloseHandle, handle)
        if api.GetFileType(handle) != 1:
            return DirectoryCreateObservation.UNKNOWN
        info = _FileInformation()
        if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
            return DirectoryCreateObservation.UNKNOWN
        if not info.attributes & _DIRECTORY or info.attributes & _UNSAFE_ATTRIBUTES:
            return DirectoryCreateObservation.CONTRADICTED
        buffer = ctypes.create_unicode_buffer(_MAX_PATH + 4)
        length = api.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if (not 4 < length < len(buffer) or not buffer.value.startswith("\\\\?\\")
                or length != len(buffer.value.encode("utf-16-le")) // 2):
            return DirectoryCreateObservation.UNKNOWN
        final = buffer.value[4:]
        if final[:1].upper() + final[1:] != path:
            return DirectoryCreateObservation.CONTRADICTED
        # Even FileIdInfo here would identify only this later open, not the
        # handle-less creation. Do not manufacture a trusted identity baseline.
        return DirectoryCreateObservation.PRESENT


def _create_directory_windows(path: str) -> DirectoryCreateResult:
    api = _kernel32()
    # Configure only this new path; existing file/list API loading stays intact.
    create = api.CreateDirectoryW
    create.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p]
    create.restype = wintypes.BOOL
    observation = DirectoryCreateObservation.UNKNOWN
    close_ok = True

    def close(handle):
        nonlocal close_ok
        try:
            if not api.CloseHandle(handle):
                close_ok = False
        except Exception:
            close_ok = False
        # Diagnostics cannot convert committed mutation into a pre-commit error.

    with ExitStack() as handles:
        _create_ancestors(api, path, handles, close)
        # Exactly one final component. NULL security attributes inherit the
        # parent ACL; no recursion, precheck, replace, rollback or delete path.
        # https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-createdirectoryw
        if not create(path, None):
            failure = {80: DirectoryCreateFailure.ALREADY_EXISTS, 183: DirectoryCreateFailure.ALREADY_EXISTS,
                       2: DirectoryCreateFailure.NOT_FOUND, 3: DirectoryCreateFailure.NOT_FOUND,
                       5: DirectoryCreateFailure.ACCESS_DENIED, 32: DirectoryCreateFailure.BUSY}.get(
                           ctypes.get_last_error(), DirectoryCreateFailure.CREATE_ERROR)
            raise DirectoryCreateError(failure)
        # Mutation has committed. This path-open snapshot is optional evidence
        # only and cannot turn success into failure or trigger deletion.
        try:
            observation = _directory_create_snapshot(api, path)
        except Exception:
            pass
    return DirectoryCreateResult(path, _observation=observation if close_ok else DirectoryCreateObservation.UNKNOWN)


def _text_file_snapshot(api, handle, path: str):
    """Observe type/path/size and 128-bit identity on this exact handle."""
    if api.GetFileType(handle) != 1:
        return FileCreateObservation.UNKNOWN, None, None
    info = _FileInformation()
    if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
        return FileCreateObservation.UNKNOWN, None, None
    if info.attributes & (_DIRECTORY | _UNSAFE_ATTRIBUTES):
        return FileCreateObservation.CHANGED, None, None
    buffer = ctypes.create_unicode_buffer(_MAX_PATH + 4)
    length = api.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    if (not 4 < length < len(buffer) or not buffer.value.startswith("\\\\?\\")
            or length != len(buffer.value.encode("utf-16-le")) // 2):
        return FileCreateObservation.UNKNOWN, None, None
    final = buffer.value[4:]
    if final[:1].upper() + final[1:] != path:
        return FileCreateObservation.CHANGED, None, None
    identity = _FileIdInfo()
    if not api.GetFileInformationByHandleEx(handle, 18, ctypes.byref(identity), ctypes.sizeof(identity)):
        return FileCreateObservation.UNKNOWN, None, None
    value = (identity.volume, bytes(identity.identifier))
    if not _valid_create_identity(value):
        return FileCreateObservation.UNKNOWN, None, None
    return FileCreateObservation.MATCHED, value, (info.size_high << 32) | info.size_low


def _create_text_windows(path: str, data: bytes) -> TextFileCreateResult:
    api = _kernel32()
    # Load/configure the new APIs and allocate the bounded buffer BEFORE mutation.
    api.WriteFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                             ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    api.WriteFile.restype = wintypes.BOOL
    api.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    api.FlushFileBuffers.restype = wintypes.BOOL
    buffer = ctypes.create_string_buffer(data)
    count = wintypes.DWORD()
    write = TextWriteOutcome.UNKNOWN
    flush = TextFlushOutcome.NOT_ATTEMPTED
    written = None
    identity = None
    close_ok = True

    def close(handle):
        nonlocal close_ok
        try:
            if not api.CloseHandle(handle):
                close_ok = False
        except Exception:
            close_ok = False

    with ExitStack() as handles:
        _create_ancestors(api, path, handles, close)
        # GENERIC_WRITE supports FlushFileBuffers; read/attribute access permits
        # same-handle inspection. No write/delete sharing, OVERLAPPED or delete flag.
        handle = api.CreateFileW(path, 0x40000000 | _READ_ATTRIBUTES | 1, _SHARE_READ,
                                 None, 1, 0x80 | 0x00200000 | 0x00100000, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            failure = {80: TextFileCreateFailure.ALREADY_EXISTS, 183: TextFileCreateFailure.ALREADY_EXISTS,
                       2: TextFileCreateFailure.NOT_FOUND, 3: TextFileCreateFailure.NOT_FOUND,
                       5: TextFileCreateFailure.ACCESS_DENIED, 32: TextFileCreateFailure.BUSY}.get(
                           ctypes.get_last_error(), TextFileCreateFailure.CREATE_ERROR)
            raise TextFileCreateError(failure)
        # CREATE_NEW committed. Every ordinary failure below returns a receipt;
        # nothing deletes, truncates, retries or reopens a path for mutation.
        handles.callback(close, handle)
        try:
            state, initial_identity, size = _text_file_snapshot(api, handle, path)
            if state is FileCreateObservation.MATCHED and size == 0:
                identity = initial_identity
                # One synchronous attempt. FALSE does not establish zero bytes.
                if api.WriteFile(handle, buffer, len(data), ctypes.byref(count), None):
                    if count.value <= len(data):
                        written = count.value
                        write = (TextWriteOutcome.COMPLETE if written == len(data)
                                 else TextWriteOutcome.PARTIAL)
                if write is TextWriteOutcome.COMPLETE:
                    flush = TextFlushOutcome.UNKNOWN
                    if api.FlushFileBuffers(handle):
                        flush = TextFlushOutcome.COMPLETE
                state, final_identity, _ = _text_file_snapshot(api, handle, path)
                if state is not FileCreateObservation.MATCHED or final_identity != identity:
                    identity = None
        except Exception:
            # Keep any completed write/flush acknowledgements; drop uncertain
            # identity evidence. A later observer cannot upgrade this weak receipt.
            identity = None
    return TextFileCreateResult(path, len(data), write, flush, written,
                                _identity=identity if close_ok else None)


class _FileDispositionInfo(ctypes.Structure):
    # FILE_DISPOSITION_INFO contains BOOLEAN, not the four-byte Win32 BOOL.
    _fields_ = [("delete_file", ctypes.c_ubyte)]


def _valid_deletion_binding(binding) -> bool:
    if type(binding) is not _DeletionBinding:
        return False
    try:
        return (normalize_file_path(binding.path) == binding.path
                and type(binding.namespace) is tuple
                and len(binding.namespace) == len(binding.path[3:].split("\\"))
                and all(_valid_create_identity(value) for value in binding.namespace)
                and _valid_create_identity(binding.identity)
                and type(binding.size) is int and 0 <= binding.size <= MAX_FILE_BYTES
                and type(binding.links) is int and binding.links == 1
                and type(binding.attributes) is int and 0 <= binding.attributes < 2**32
                and not binding.attributes & (_DIRECTORY | _UNSAFE_ATTRIBUTES | 1 | 4)
                and all(type(value) is int and 0 <= value < 2**64
                        for value in (binding.creation_time, binding.write_time)))
    except (TypeError, ValueError):
        return False


def _delete_identity(api, handle):
    info = _FileIdInfo()
    if not api.GetFileInformationByHandleEx(handle, 18, ctypes.byref(info), ctypes.sizeof(info)):
        raise FileDeleteError()
    identity = (info.volume, bytes(info.identifier))
    if not _valid_create_identity(identity):
        raise FileDeleteError()
    return identity


def _delete_namespace(api, path, handles, close):
    ancestors = []
    class Registration:
        def callback(self, callback, handle):
            handles.callback(callback, handle)
            ancestors.append(handle)
    # Identical production access/share/path checks; collect identities only.
    _create_ancestors(api, path, Registration(), close)
    return tuple(_delete_identity(api, handle) for handle in ancestors)


def _delete_snapshot(api, handle, path, namespace):
    state, identity, size = _text_file_snapshot(api, handle, path)
    if state is not FileCreateObservation.MATCHED:
        raise FileDeleteError()
    info = _inspect_handle(api, handle, path, directory=False)
    if size != (info.size_high << 32) | info.size_low:
        raise FileDeleteError()
    # Existing native helpers expose creation and last-write, not ChangeTime.
    binding = _DeletionBinding(path, namespace, identity, size, info.links, info.attributes,
                               (info.creation.dwHighDateTime << 32) | info.creation.dwLowDateTime,
                               (info.write.dwHighDateTime << 32) | info.write.dwLowDateTime)
    if not _valid_deletion_binding(binding):
        raise FileDeleteError()
    return binding


def _prepare_delete_windows(path):
    api = _kernel32()
    def close(handle):
        if not api.CloseHandle(handle):
            raise FileDeleteError()
    with ExitStack() as handles:
        namespace = _delete_namespace(api, path, handles, close)
        handle = api.CreateFileW(path, _READ_ATTRIBUTES, 0, None, _OPEN_EXISTING, _OPEN_FLAGS, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            raise FileDeleteError()
        handles.callback(close, handle)
        return _delete_snapshot(api, handle, path, namespace)


def _delete_observe_path(api, binding):
    # Caller retains and has matched every ancestor against the saved namespace.
    handle = api.CreateFileW(binding.path, _READ_ATTRIBUTES, 0, None,
                             _OPEN_EXISTING, _OPEN_FLAGS, None)
    if handle in (None, 0, ctypes.c_void_p(-1).value):
        return (DeleteObservation.CONFIRMED_ABSENT if ctypes.get_last_error() == 2
                else DeleteObservation.UNKNOWN)
    observation = DeleteObservation.UNKNOWN
    try:
        state, identity, _ = _text_file_snapshot(api, handle, binding.path)
        if state is FileCreateObservation.MATCHED:
            observation = (DeleteObservation.PRESENT_SAME_IDENTITY if identity == binding.identity
                           else DeleteObservation.PRESENT_DIFFERENT_IDENTITY)
    finally:
        if not api.CloseHandle(handle):
            observation = DeleteObservation.UNKNOWN
    return observation


def _delete_windows(binding):
    api = _kernel32()
    set_info = api.SetFileInformationByHandle
    set_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    set_info.restype = wintypes.BOOL
    disposition_info = _FileDispositionInfo(1)
    if ctypes.sizeof(disposition_info) != 1:
        raise FileDeleteError()
    disposition = DeleteDisposition.UNKNOWN
    source_close = DeleteClose.UNKNOWN
    observation = DeleteObservation.UNKNOWN
    cleanup_complete = True
    def close(handle):
        nonlocal cleanup_complete
        try:
            ok = bool(api.CloseHandle(handle))
        except Exception:
            ok = False
        if not ok:
            cleanup_complete = False
        return ok
    with ExitStack() as ancestors:
        namespace = _delete_namespace(api, binding.path, ancestors, close)
        if namespace != binding.namespace:
            raise FileDeleteError()
        target = api.CreateFileW(binding.path, 0x10000 | _READ_ATTRIBUTES, 0, None,
                                 _OPEN_EXISTING, _OPEN_FLAGS, None)
        if target in (None, 0, ctypes.c_void_p(-1).value):
            raise FileDeleteError()
        try:
            if _delete_snapshot(api, target, binding.path, namespace) != binding:
                raise FileDeleteError()
            # One invocation. TRUE is committed destructive state; FALSE is
            # known non-acknowledgement. Exceptions cannot establish completion.
            try:
                acknowledged = set_info(target, 4, ctypes.byref(disposition_info), 1)
                disposition = (DeleteDisposition.ACKNOWLEDGED if acknowledged
                               else DeleteDisposition.NOT_ACKNOWLEDGED)
            except Exception:
                disposition = DeleteDisposition.UNKNOWN
        finally:
            # Sole owner: no outer target callback can close this handle again.
            source_close = DeleteClose.COMPLETE if close(target) else DeleteClose.UNKNOWN
        # All ancestors remain retained through this bounded observation.
        try:
            observation = _delete_observe_path(api, binding)
        except Exception:
            observation = DeleteObservation.UNKNOWN
    return FileDeleteResult(disposition, source_close, observation, binding, cleanup_complete)


def _copy_read(api, handle, size: int) -> bytes:
    """Fresh synchronous handle starts at zero; bounded bytes AND native calls.

    Return at EOF or at the N+1 ceiling. Caller distinguishes trustworthy
    length disagreement from native/malformed evidence failures.
    """
    buffer = ctypes.create_string_buffer(size + 1)
    total = 0
    for _ in range(size + 2):
        count = wintypes.DWORD()
        remaining = len(buffer) - total
        if not api.ReadFile(handle, ctypes.byref(buffer, total), remaining, ctypes.byref(count), None):
            raise FileCopyError(FileCopyFailure.COPY_ERROR)
        if count.value > remaining:
            raise FileCopyError(FileCopyFailure.COPY_ERROR)
        total += count.value
        if count.value == 0 or total == len(buffer):
            return buffer.raw[:total]
    raise FileCopyError(FileCopyFailure.COPY_ERROR)


def _copy_file_windows(source: str, destination: str) -> FileCopyResult:
    api = _kernel32()
    api.WriteFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                             ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    api.WriteFile.restype = wintypes.BOOL
    api.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    api.FlushFileBuffers.restype = wintypes.BOOL
    copy = CopyOutcome.UNKNOWN
    flush = CopyFlushOutcome.NOT_ATTEMPTED
    written = None
    destination_identity = None
    close_ok = True

    def close(handle):
        nonlocal close_ok
        try:
            if not api.CloseHandle(handle):
                close_ok = False
        except Exception:
            close_ok = False

    with ExitStack() as handles:
        _create_ancestors(api, source, handles, close)
        source_handle = api.CreateFileW(source, _GENERIC_READ, _SHARE_READ, None,
                                        _OPEN_EXISTING, _OPEN_FLAGS, None)
        if source_handle in (None, 0, ctypes.c_void_p(-1).value):
            raise _os_failure()
        handles.callback(close, source_handle)
        state, source_identity, size = _text_file_snapshot(api, source_handle, source)
        if state is not FileCreateObservation.MATCHED:
            raise FileCopyError(FileCopyFailure.INVALID_TARGET)
        if size > MAX_FILE_BYTES:
            raise FileCopyError(FileCopyFailure.TOO_LARGE)
        parent = _create_ancestors(api, destination, handles, close)
        parent_id = _FileIdInfo()
        if not api.GetFileInformationByHandleEx(parent, 18, ctypes.byref(parent_id), ctypes.sizeof(parent_id)):
            raise FileCopyError(FileCopyFailure.COPY_ERROR)
        parent_identity = (parent_id.volume, bytes(parent_id.identifier))
        if not _valid_create_identity(parent_identity):
            raise FileCopyError(FileCopyFailure.COPY_ERROR)
        if parent_identity[0] != source_identity[0]:
            raise FileCopyError(FileCopyFailure.CROSS_VOLUME)

        data = _copy_read(api, source_handle, size)
        after, identity_after, size_after = _text_file_snapshot(api, source_handle, source)
        if (len(data) != size or after is not FileCreateObservation.MATCHED
                or identity_after != source_identity or size_after != size):
            raise FileCopyError(FileCopyFailure.COPY_ERROR)
        digest = hashlib.sha256(data).digest()
        buffer = ctypes.create_string_buffer(data)
        count = wintypes.DWORD()
        handle = api.CreateFileW(destination, 0x40000000 | _READ_ATTRIBUTES | 1, _SHARE_READ,
                                 None, 1, 0x80 | 0x00200000 | 0x00100000, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            failure = {80: FileCopyFailure.ALREADY_EXISTS, 183: FileCopyFailure.ALREADY_EXISTS,
                       2: FileCopyFailure.NOT_FOUND, 3: FileCopyFailure.NOT_FOUND,
                       5: FileCopyFailure.ACCESS_DENIED, 32: FileCopyFailure.BUSY}.get(
                           ctypes.get_last_error(), FileCopyFailure.COPY_ERROR)
            raise FileCopyError(failure)
        # CREATE_NEW committed. No ordinary later diagnostic may erase it.
        handles.callback(close, handle)
        try:
            state, identity, initial_size = _text_file_snapshot(api, handle, destination)
            if (state is FileCreateObservation.MATCHED and initial_size == 0
                    and identity != source_identity and identity[0] == source_identity[0]):
                destination_identity = identity
                if size == 0:
                    copy, written = CopyOutcome.COMPLETE, 0
                elif api.WriteFile(handle, buffer, size, ctypes.byref(count), None):
                    if count.value <= size:
                        written = count.value
                        copy = CopyOutcome.COMPLETE if written == size else CopyOutcome.PARTIAL
                if copy is CopyOutcome.COMPLETE:
                    flush = CopyFlushOutcome.UNKNOWN
                    if api.FlushFileBuffers(handle):
                        flush = CopyFlushOutcome.COMPLETE
                state, final_identity, _ = _text_file_snapshot(api, handle, destination)
                if state is not FileCreateObservation.MATCHED or final_identity != destination_identity:
                    destination_identity = None
        except Exception:
            destination_identity = None
    return FileCopyResult(source, destination, size, copy, flush, written,
                          _source_identity=source_identity,
                          _destination_identity=destination_identity if close_ok else None,
                          _digest=digest)


def _observe_copy_windows(path: str, result: FileCopyResult) -> FileCreateObservation:
    """Destination-only observation, bound to execution-time content and identity."""
    api = _kernel32()

    def close(handle):
        if not api.CloseHandle(handle):
            raise OSError("Observation cleanup was inconclusive.")

    with ExitStack() as handles:
        try:
            _create_ancestors(api, path, handles, close)
        except FileReadError as exc:
            return (FileCreateObservation.CHANGED if exc.failure is FileReadFailure.NOT_FOUND
                    else FileCreateObservation.UNKNOWN)
        handle = api.CreateFileW(path, _GENERIC_READ, _SHARE_READ, None,
                                 _OPEN_EXISTING, _OPEN_FLAGS, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            return (FileCreateObservation.CHANGED if ctypes.get_last_error() in (2, 3)
                    else FileCreateObservation.UNKNOWN)
        handles.callback(close, handle)
        state, identity, size = _text_file_snapshot(api, handle, path)
        if state is not FileCreateObservation.MATCHED:
            return state
        if identity != result._destination_identity or size != result.expected_byte_count:
            return FileCreateObservation.CHANGED
        data = _copy_read(api, handle, size)
        after, identity_after, size_after = _text_file_snapshot(api, handle, path)
        if after is not FileCreateObservation.MATCHED:
            return after
        if (identity_after != identity or size_after != size or len(data) != size
                or hashlib.sha256(data).digest() != result._digest):
            return FileCreateObservation.CHANGED
        return FileCreateObservation.MATCHED


def _observe_created_text_windows(path: str, original_identity, expected: bytes) -> FileCreateObservation:
    api = _kernel32()

    def close(handle):
        if not api.CloseHandle(handle):
            # The service converts failed observation cleanup to UNKNOWN, while
            # ExitStack still attempts the remaining closes exactly once.
            raise OSError("Observation cleanup was inconclusive.")

    with ExitStack() as handles:
        try:
            _create_ancestors(api, path, handles, close)
        except FileReadError as exc:
            return (FileCreateObservation.CHANGED if exc.failure is FileReadFailure.NOT_FOUND
                    else FileCreateObservation.UNKNOWN)
        handle = api.CreateFileW(path, _GENERIC_READ, _SHARE_READ, None,
                                 _OPEN_EXISTING, _OPEN_FLAGS, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            return (FileCreateObservation.CHANGED if ctypes.get_last_error() in (2, 3)
                    else FileCreateObservation.UNKNOWN)
        handles.callback(close, handle)
        state, identity, size = _text_file_snapshot(api, handle, path)
        if state is not FileCreateObservation.MATCHED:
            return state
        if not _valid_create_identity(original_identity):
            return FileCreateObservation.UNKNOWN
        if identity != original_identity or size != len(expected):
            return FileCreateObservation.CHANGED
        # Bound both allocation and calls. Each non-EOF read must make progress;
        # at most expected length + 1 bytes are ever read, on this same handle.
        buffer = ctypes.create_string_buffer(len(expected) + 1)
        total = 0
        while total < len(buffer):
            count = wintypes.DWORD()
            remaining = len(buffer) - total
            if not api.ReadFile(handle, ctypes.byref(buffer, total), remaining, ctypes.byref(count), None):
                return FileCreateObservation.UNKNOWN
            if count.value > remaining:
                return FileCreateObservation.UNKNOWN
            if count.value == 0:
                break
            total += count.value
        return (FileCreateObservation.MATCHED if buffer.raw[:total] == expected
                else FileCreateObservation.CHANGED)
