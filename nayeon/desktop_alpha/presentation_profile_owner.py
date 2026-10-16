"""Phase 8.30 STATIC_UNTESTED profile owners; NOT activated product wiring.

TemporaryPresentationProfileOwner remains an explicit test-only existing-child
interface. The separate production factory accepts no path; its known-folder
admission is lazy and missing fixed children are created only on reviewed Save.
Import/construction performs no native I/O. No UI, provider, credential or
entrypoint integration is supplied here.

HOLD before activation: authoritative Windows execution and independent review;
updated exact source/consumer guard migration; production admission and atomic
private-child creation verification; junction/ACL-race/crash and cross-process proof.
The old store uses pathnames and suppresses cleanup errors. We detect remaining
unexpected directory entries, but cannot prove every suppressed cleanup error.
This is a cooperating-process integrity experiment, NOT a malicious-same-user
boundary, universal CAS, directory-sync or power-loss durability guarantee. ABA
restoring identical bytes is undetectable. No such missing proof is waived here.

Win32 references (all checks below are real API calls, never stat substitutes):
https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-createfilew
https://learn.microsoft.com/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo
https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-lockfileex
"""

from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import threading
from typing import Callable

from nayeon.config.bootstrap import bootstrap_presentation_configuration
from nayeon.config.document import (
    PresentationConfigurationDocumentV1,
    parse_presentation_configuration_document,
    presentation_configuration_document_to_mapping,
)


PROFILE_LEAF = "presentation.v1.json"
LOCK_LEAF = "presentation.v1.lock"
_LIMIT = 65536
# Windows drive roots may legitimately be owned by TrustedInstaller.
# The private profile directory must still be owned by the current user.
_TRUSTED_SIDS = frozenset({
    "S-1-5-18", "S-1-5-32-544",
    "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464",
})


class ProfileStorageError(RuntimeError):
    """Sanitized refusal; never include paths, contents or native exceptions."""


class ProfileBusy(ProfileStorageError):
    """Immediate contention or reentrant use; no retry is performed."""


class ProfileConflict(ProfileStorageError):
    """A fresh explicit load and review is required."""


class ProfileUnverified(ProfileStorageError):
    """Storage may have changed; unverified. No retry or rollback is safe."""


@dataclass(frozen=True, slots=True, repr=False)
class ProfileSnapshot:
    present: bool
    byte_count: int
    sha256: str | None


@dataclass(frozen=True, slots=True, repr=False)
class ProfileEdit:
    document: PresentationConfigurationDocumentV1
    snapshot: ProfileSnapshot


@dataclass(frozen=True, slots=True, repr=False)
class ProfileSaveReview:
    """One-use exact draft receipt, issued by the trusted caller after review.

    This object does not itself prove human consent. Only a future separately
    reviewed trusted UI may call review_save from a genuine human Save flow.
    """

    edit: ProfileEdit
    document: PresentationConfigurationDocumentV1


class _FileInfo(ctypes.Structure):
    _fields_ = [
        ("attributes", w.DWORD), ("created", w.FILETIME),
        ("accessed", w.FILETIME), ("written", w.FILETIME),
        ("volume", w.DWORD), ("size_high", w.DWORD), ("size_low", w.DWORD),
        ("links", w.DWORD), ("index_high", w.DWORD), ("index_low", w.DWORD),
    ]


class _FileId(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_ulonglong), ("identifier", ctypes.c_ubyte * 16)]


class _TagInfo(ctypes.Structure):
    _fields_ = [("attributes", w.DWORD), ("tag", w.DWORD)]


class _Overlapped(ctypes.Structure):
    _fields_ = [
        ("internal", ctypes.c_size_t), ("internal_high", ctypes.c_size_t),
        ("offset", w.DWORD), ("offset_high", w.DWORD), ("event", w.HANDLE),
    ]


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", w.DWORD), ("descriptor", w.LPVOID), ("inherit", w.BOOL)]


class _Guid(ctypes.Structure):
    _fields_ = [("data1", w.DWORD), ("data2", w.WORD), ("data3", w.WORD),
                ("data4", ctypes.c_ubyte * 8)]


class _Acl(ctypes.Structure):
    _fields_ = [
        ("revision", w.BYTE), ("reserved", w.BYTE), ("size", w.WORD),
        ("count", w.WORD), ("reserved2", w.WORD),
    ]


class _Ace(ctypes.Structure):
    _fields_ = [("kind", w.BYTE), ("flags", w.BYTE), ("size", w.WORD), ("mask", w.DWORD)]


class _SidAndAttributes(ctypes.Structure):
    _fields_ = [("sid", w.LPVOID), ("attributes", w.DWORD)]


class _Win32:
    """Lazy, fail-closed NTFS-only native adapter. No injected success backend."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise ProfileStorageError("Windows profile storage unavailable")
        try:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            security = ctypes.WinDLL("advapi32", use_last_error=True)
            pointer = ctypes.c_void_p
            pp = ctypes.POINTER(pointer)

            def bind(library, name, result, *arguments):
                function = getattr(library, name)
                function.restype = result
                function.argtypes = list(arguments)
                return function

            self.create = bind(kernel, "CreateFileW", w.HANDLE, w.LPCWSTR, w.DWORD,
                               w.DWORD, pointer, w.DWORD, w.DWORD, w.HANDLE)
            self.create_directory = bind(kernel, "CreateDirectoryW", w.BOOL,
                                         w.LPCWSTR, ctypes.POINTER(_SecurityAttributes))
            self.close_handle = bind(kernel, "CloseHandle", w.BOOL, w.HANDLE)
            self.file_type = bind(kernel, "GetFileType", w.DWORD, w.HANDLE)
            self.file_info = bind(kernel, "GetFileInformationByHandle", w.BOOL,
                                  w.HANDLE, ctypes.POINTER(_FileInfo))
            self.file_info_ex = bind(kernel, "GetFileInformationByHandleEx", w.BOOL,
                                     w.HANDLE, ctypes.c_int, pointer, w.DWORD)
            self.final_name = bind(kernel, "GetFinalPathNameByHandleW", w.DWORD,
                                   w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD)
            self.drive_type = bind(kernel, "GetDriveTypeW", w.UINT, w.LPCWSTR)
            self.volume_info = bind(kernel, "GetVolumeInformationW", w.BOOL,
                                    w.LPCWSTR, w.LPWSTR, w.DWORD, ctypes.POINTER(w.DWORD),
                                    ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD),
                                    w.LPWSTR, w.DWORD)
            self.read_file = bind(kernel, "ReadFile", w.BOOL, w.HANDLE, pointer,
                                  w.DWORD, ctypes.POINTER(w.DWORD), pointer)
            self.lock_file = bind(kernel, "LockFileEx", w.BOOL, w.HANDLE, w.DWORD,
                                  w.DWORD, w.DWORD, w.DWORD, ctypes.POINTER(_Overlapped))
            self.unlock_file = bind(kernel, "UnlockFileEx", w.BOOL, w.HANDLE,
                                    w.DWORD, w.DWORD, w.DWORD, ctypes.POINTER(_Overlapped))
            self.local_free = bind(kernel, "LocalFree", pointer, pointer)
            current_process = bind(kernel, "GetCurrentProcess", w.HANDLE)
            current_thread = bind(kernel, "GetCurrentThread", w.HANDLE)
            process_token = bind(security, "OpenProcessToken", w.BOOL, w.HANDLE, w.DWORD, pp)
            thread_token = bind(security, "OpenThreadToken", w.BOOL, w.HANDLE,
                                w.DWORD, w.BOOL, pp)
            token_info = bind(security, "GetTokenInformation", w.BOOL, w.HANDLE,
                              ctypes.c_int, pointer, w.DWORD, ctypes.POINTER(w.DWORD))
            self.security_info = bind(security, "GetSecurityInfo", w.DWORD, w.HANDLE,
                                     ctypes.c_int, w.DWORD, pp, pp, pp, pp, pp)
            self.sd_control = bind(security, "GetSecurityDescriptorControl", w.BOOL,
                                  pointer, ctypes.POINTER(w.WORD), ctypes.POINTER(w.DWORD))
            self.valid_acl = bind(security, "IsValidAcl", w.BOOL, pointer)
            self.get_ace = bind(security, "GetAce", w.BOOL, pointer, w.DWORD, pp)
            self.valid_sid = bind(security, "IsValidSid", w.BOOL, pointer)
            self.sid_length = bind(security, "GetLengthSid", w.DWORD, pointer)
            self.sid_string = bind(security, "ConvertSidToStringSidW", w.BOOL, pointer, pp)
            self.sddl = bind(security, "ConvertStringSecurityDescriptorToSecurityDescriptorW",
                             w.BOOL, w.LPCWSTR, w.DWORD, pp, ctypes.POINTER(w.DWORD))

            # Never accidentally validate a process SID while executing under an
            # impersonating thread. Impersonation is unsupported, even same-SID.
            token = pointer()
            if thread_token(current_thread(), 8, True, ctypes.byref(token)):
                self.close(token)
                raise ProfileStorageError("Impersonated storage owner unsupported")
            if ctypes.get_last_error() != 1008:  # ERROR_NO_TOKEN only
                raise ProfileStorageError("Cannot establish storage owner")
            if not process_token(current_process(), 8, ctypes.byref(token)):
                raise ProfileStorageError("Cannot establish storage owner")
            try:
                needed = w.DWORD()
                token_info(token, 1, None, 0, ctypes.byref(needed))
                if ctypes.get_last_error() != 122 or not 0 < needed.value <= 65536:
                    raise ProfileStorageError("Cannot establish storage owner")
                buffer = ctypes.create_string_buffer(needed.value)
                if not token_info(token, 1, buffer, needed.value, ctypes.byref(needed)):
                    raise ProfileStorageError("Cannot establish storage owner")
                sid = ctypes.cast(buffer, ctypes.POINTER(_SidAndAttributes)).contents.sid
                self.user_sid = self.sid_text(sid)
            finally:
                self.close(token)
        except ProfileStorageError:
            raise
        except (AttributeError, OSError, ValueError, TypeError):
            raise ProfileStorageError("Required Windows profile primitives unavailable") from None

    def close(self, handle) -> None:
        if not self.close_handle(handle):
            raise ProfileUnverified("Profile handle release unverified")

    def sid_text(self, sid) -> str:
        output = ctypes.c_void_p()
        if not sid or not self.valid_sid(sid) or not self.sid_string(sid, ctypes.byref(output)):
            raise ProfileStorageError("Invalid storage security identity")
        try:
            return ctypes.wstring_at(output)
        finally:
            if self.local_free(output):
                raise ProfileUnverified("Security resource release unverified")

    @contextmanager
    def private_security(self):
        # Atomic private sidecar/fixed-child creation. Tests also use this real
        # descriptor to create disposable synthetic directories.
        sid = self.user_sid
        descriptor = ctypes.c_void_p()
        text = f"O:{sid}D:P(A;OICI;FA;;;{sid})(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)"
        if not self.sddl(text, 1, ctypes.byref(descriptor), None):
            raise ProfileStorageError("Private security descriptor unavailable")
        try:
            attributes = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
            yield attributes
        finally:
            if self.local_free(descriptor):
                raise ProfileUnverified("Security resource release unverified")

    def security(self, handle, *, private: bool, protected: bool = False,
                 admin_created_profile_leaf: bool = False,
                 current_user_policy: bool = False) -> None:
        owner, dacl, descriptor = (ctypes.c_void_p() for _ in range(3))
        status = self.security_info(handle, 1, 5, ctypes.byref(owner), None,
                                    ctypes.byref(dacl), None, ctypes.byref(descriptor))
        try:
            if status or not descriptor or not dacl or not self.valid_acl(dacl):
                raise ProfileStorageError("Storage security descriptor unavailable")
            trusted = _TRUSTED_SIDS | {self.user_sid}
            leaf_trustees = {self.user_sid, "S-1-5-18", "S-1-5-32-544"}
            owner_sid = self.sid_text(owner)
            if admin_created_profile_leaf:
                # Only the exact regular profile leaf, inspected and pinned by
                # _snapshot, may inherit the elevated token's default owner.
                # Never apply this exception to a private directory or lock.
                if (not private or protected or owner_sid not in
                        {self.user_sid, "S-1-5-32-544"}):
                    raise ProfileStorageError("Storage owner refused")
            elif owner_sid not in trusted or (private and owner_sid != self.user_sid):
                raise ProfileStorageError("Storage owner refused")
            control, revision = w.WORD(), w.DWORD()
            if not self.sd_control(descriptor, ctypes.byref(control), ctypes.byref(revision)):
                raise ProfileStorageError("Storage security control unavailable")
            if not control.value & 4 or (protected and not control.value & 0x1000):
                raise ProfileStorageError("Private storage DACL required")
            acl = ctypes.cast(dacl, ctypes.POINTER(_Acl)).contents
            if not acl.count or acl.count > 256:
                raise ProfileStorageError("Storage DACL refused")
            for index in range(acl.count):
                pointer = ctypes.c_void_p()
                if not self.get_ace(dacl, index, ctypes.byref(pointer)):
                    raise ProfileStorageError("Storage ACE unavailable")
                ace = ctypes.cast(pointer, ctypes.POINTER(_Ace)).contents
                # Unknown/object/callback/deny ACEs are conservatively unsupported.
                # No partial AccessCheck emulation and no generic-mask guessing.
                if ace.kind != 0 or ace.size < 16:
                    raise ProfileStorageError("Unsupported storage ACE")
                sid = pointer.value + 8
                if not self.valid_sid(sid) or self.sid_length(sid) > ace.size - 8:
                    raise ProfileStorageError("Invalid storage ACE identity")
                sid_text = self.sid_text(sid)
                if private:
                    # The leaf-only exception does NOT allow extra DACL trustees.
                    # Inherited ACEs and even read-only foreign ACEs are refused.
                    allowed = (leaf_trustees if admin_created_profile_leaf
                               or current_user_policy else trusted)
                    if sid_text not in allowed:
                        raise ProfileStorageError("Private storage DACL refused")
                elif not ace.flags & 8 and sid_text not in trusted:
                    # Ancestors may permit creating NEW children (e.g. drive
                    # root). They must not permit replacing/deleting the pinned
                    # existing chain, changing its DACL/owner or attributes.
                    mutation = 0xD0000 | 0x40 | 0x100 | 0x10 | 0x50000000 | 0x02000000
                    if ace.mask & mutation:
                        raise ProfileStorageError("Ancestor storage DACL refused")
        finally:
            if descriptor and self.local_free(descriptor):
                raise ProfileUnverified("Security resource release unverified")

    def open(self, path: Path, *, directory: bool = False, lock: bool = False,
             absent_ok: bool = False, existing_lock: bool = False):
        access = (0x80000000 if not directory else 0x80) | 0x20000
        if lock:
            access |= 0x40000000
        # Directory pins/sidecar never share DELETE. A profile read also denies
        # WRITE/DELETE, and its handle is closed before service.replace.
        share = 3 if directory or lock or existing_lock else 1
        flags = 0x00200000 | (0x02000000 if directory else 0)
        invalid_handle = ctypes.c_void_p(-1).value
        if lock:
            handle = None
            try:
                with self.private_security() as attributes:
                    handle = self.create(str(path), access, share,
                                         ctypes.byref(attributes), 4, flags, None)
                    # CreateFileW last-error is lost if LocalFree runs first.
                    error = ctypes.get_last_error()
            except BaseException:
                # A successful open must not leak if private_security's
                # descriptor cleanup raises on context-manager exit.
                if handle is not None and handle != invalid_handle:
                    self.close(handle)
                raise
        else:
            handle = self.create(str(path), access, share, None, 3, flags, None)
            error = ctypes.get_last_error()
        if handle == invalid_handle:
            if error == 2 and absent_ok:
                return None
            if lock and error in (32, 33):
                raise ProfileBusy("Presentation profile lock unavailable")
            raise ProfileStorageError("Cannot open trusted profile object")
        return handle

    def inspect(self, handle, path: Path, *, directory: bool = False):
        info, tag, identifier = _FileInfo(), _TagInfo(), _FileId()
        if (self.file_type(handle) != 1
                or not self.file_info(handle, ctypes.byref(info))
                or not self.file_info_ex(handle, 9, ctypes.byref(tag), ctypes.sizeof(tag))
                or not self.file_info_ex(handle, 18, ctypes.byref(identifier), ctypes.sizeof(identifier))):
            raise ProfileStorageError("Profile handle evidence unavailable")
        if (info.attributes & 0x440 or tag.attributes & 0x440 or tag.tag
                or bool(info.attributes & 0x10) != directory):
            raise ProfileStorageError("Reparse or nonregular profile object refused")
        if not directory and info.links != 1:
            raise ProfileStorageError("Hard-linked profile object refused")
        name = ctypes.create_unicode_buffer(1024)
        length = self.final_name(handle, name, len(name), 0)
        if not 0 < length < len(name) or name.value.casefold() != ("\\\\?\\" + str(path)).casefold():
            raise ProfileStorageError("Profile namespace identity refused")
        return (identifier.volume, bytes(identifier.identifier)), (info.size_high << 32) | info.size_low

    def require_volume(self, anchor: str) -> None:
        flags, serial, maximum = w.DWORD(), w.DWORD(), w.DWORD()
        filesystem = ctypes.create_unicode_buffer(32)
        if (self.drive_type(anchor) != 3
                or not self.volume_info(anchor, None, 0, ctypes.byref(serial), ctypes.byref(maximum),
                                        ctypes.byref(flags), filesystem, len(filesystem))
                or filesystem.value != "NTFS" or not flags.value & 8):
            raise ProfileStorageError("Private local NTFS volume required")

    def read(self, handle) -> bytes:
        result = bytearray()
        while len(result) <= _LIMIT:
            count = min(8192, _LIMIT + 1 - len(result))
            buffer, read = ctypes.create_string_buffer(count), w.DWORD()
            if not self.read_file(handle, buffer, count, ctypes.byref(read), None):
                raise ProfileStorageError("Cannot read profile snapshot")
            if not read.value:
                return bytes(result)
            result.extend(buffer.raw[:read.value])
        raise ProfileStorageError("Profile snapshot exceeds limit")


def _directory_path(directory: Path) -> Path:
    if type(directory) is not type(Path()):
        raise TypeError("An exact native temporary-directory Path is required")
    if (not directory.is_absolute() or not re.fullmatch(r"[A-Za-z]:\\", directory.anchor)
            or len(directory.parts) < 3 or len(str(directory)) > 240):
        raise ProfileStorageError("Unambiguous local child directory required")
    for part in directory.parts[1:]:
        if (part in (".", "..") or part[-1:] in (".", " ")
                or any(ord(c) < 32 or c in '<>:"/\\|?*' for c in part)
                or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?", part)):
            raise ProfileStorageError("Unsafe profile path refused")
    return directory


def _resolve_local_app_data() -> Path:
    """Private host-test seam; never called at import or owner construction.

    A disposable synthetic root may replace THIS resolver in an external test
    harness. The public production factory has no caller-selected path seam.
    SHGetKnownFolderPath is queried with flags zero and NULL token, never CREATE.
    """
    if os.name != "nt":
        raise ProfileStorageError("Windows profile storage unavailable")
    output = ctypes.c_void_p()
    try:
        shell = ctypes.WinDLL("shell32", use_last_error=True)
        ole = ctypes.WinDLL("ole32", use_last_error=True)
        resolve = shell.SHGetKnownFolderPath
        resolve.argtypes = [ctypes.POINTER(_Guid), w.DWORD, w.HANDLE,
                            ctypes.POINTER(ctypes.c_void_p)]
        resolve.restype = ctypes.c_long  # HRESULT is signed 32-bit on Windows.
        free = ole.CoTaskMemFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = None
        folder = _Guid(0xF1B32785, 0x6FBA, 0x4FCF,
                       (ctypes.c_ubyte * 8)(0x9D, 0x55, 0x7B, 0x8E,
                                           0x7F, 0x15, 0x70, 0x91))
        try:
            status = resolve(ctypes.byref(folder), 0, None, ctypes.byref(output))
            if status != 0 or not output.value:
                raise ProfileStorageError("Trusted known folder unavailable")
            return _directory_path(Path(ctypes.wstring_at(output)))
        finally:
            if output.value:
                free(output)
    except ProfileStorageError:
        raise
    except Exception:
        raise ProfileStorageError("Trusted known folder unavailable") from None


class _Pins:
    def __init__(self, native: _Win32, directory: Path) -> None:
        self.native, self.directory = native, directory
        self.handles = []
        self.storage_present = True

    def __enter__(self):
        try:
            self.native.require_volume(self.directory.anchor)
            for path in (*reversed(self.directory.parents), self.directory):
                self._pin(path, self.native.open(path, directory=True))
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def _directory_security(self, path: Path, handle) -> None:
        self.native.security(handle, private=path == self.directory,
                             protected=path == self.directory)

    def _pin(self, path: Path, handle) -> None:
        # Register before inspection so every failed proof still releases it.
        self.handles.append((path, handle, None))
        identity, _ = self.native.inspect(handle, path, directory=True)
        self.handles[-1] = (path, handle, identity)
        self._directory_security(path, handle)

    def check(self) -> None:
        for path, handle, identity in self.handles:
            current, _ = self.native.inspect(handle, path, directory=True)
            if current != identity:
                raise ProfileStorageError("Profile directory identity changed")
            self._directory_security(path, handle)

    def inventory(self) -> None:
        # Only the dedicated child's immediate fixed names; no recursive scan.
        with os.scandir(self.directory) as entries:
            for index, entry in enumerate(entries):
                if index >= 2 or entry.name not in (PROFILE_LEAF, LOCK_LEAF):
                    raise ProfileStorageError("Unexpected profile directory entry")

    def __exit__(self, *_):
        failed = False
        for _, handle, _ in reversed(self.handles):
            try:
                self.native.close(handle)
            except ProfileStorageError:
                failed = True
        self.handles.clear()
        if failed:
            raise ProfileUnverified("Profile directory release unverified")


class _ProductionPins(_Pins):
    """Existing known-folder chain plus two fixed, individually private children.

    CreateDirectoryW cannot return a creation handle. A successful call is
    immediately followed by no-delete-share open, handle inspection and pinning.
    This is the RFC's cooperating-process boundary, not exclusion of malicious
    same-user code during that native create/open interval. No cleanup/rollback
    removes a created component after any failure.
    """

    def __init__(self, native: _Win32, known_folder: Path, *,
                 before_create: Callable[[], None] | None) -> None:
        self.known_folder = known_folder
        self.application = known_folder / "Nayeon"
        super().__init__(native, _directory_path(self.application / "Presentation"))
        self.before_create = before_create
        self.storage_present = False
        self.missing = None

    def _directory_security(self, path: Path, handle) -> None:
        private = path in (self.known_folder, self.application, self.directory)
        self.native.security(handle, private=private,
                             protected=path in (self.application, self.directory),
                             current_user_policy=private)

    def __enter__(self):
        try:
            self.native.require_volume(self.known_folder.anchor)
            # No absent_ok at the known folder or its ancestry. Nothing here
            # creates, repairs or falls back from a missing/invalid root.
            for path in (*reversed(self.known_folder.parents), self.known_folder):
                self._pin(path, self.native.open(path, directory=True))
            for path in (self.application, self.directory):
                handle = self.native.open(path, directory=True, absent_ok=True)
                if handle is not None:
                    self._pin(path, handle)
                    continue
                self.missing = path
                if self.before_create is None:
                    break
                self.check()
                with self.native.private_security() as attributes:
                    self.check()
                    self.before_create()
                    # No OPEN_ALWAYS/mkdir/exist_ok: ANY failure, including an
                    # unexpected already-existing winner, is a hard refusal.
                    if not self.native.create_directory(str(path), ctypes.byref(attributes)):
                        raise ProfileStorageError("Private profile child creation refused")
                    self.missing = None
                    self._pin(path, self.native.open(path, directory=True))
                    self.check()
                    self.before_create()
            self.storage_present = self.missing is None
            self.check()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def check(self) -> None:
        super().check()
        if self.missing is not None:
            appeared = self.native.open(self.missing, directory=True, absent_ok=True)
            if appeared is not None:
                self.native.close(appeared)
                raise ProfileConflict("Profile directory changed; reload and review")

    def inventory(self) -> None:
        self.check()
        if not self.storage_present:
            return
        super().inventory()
        # A pre-existing sidecar is storage too: validate it even on read-only
        # load. OPEN_EXISTING, read-only and share WRITE permits this check while
        # our Save holds the separately opened exclusive byte-range lock.
        path = self.directory / LOCK_LEAF
        handle = self.native.open(path, existing_lock=True, absent_ok=True)
        if handle is not None:
            try:
                _, size = self.native.inspect(handle, path)
                self.native.security(handle, private=True, protected=True,
                                     current_user_policy=True)
                if size:
                    raise ProfileStorageError("Unexpected profile lock content")
            finally:
                self.native.close(handle)
        self.check()


class _ProfileLock:
    def __init__(self, pins: _Pins) -> None:
        self.pins, self.native = pins, pins.native
        self.handle = None
        self.locked = False
        self.overlapped = _Overlapped()

    def __enter__(self):
        try:
            path = self.pins.directory / LOCK_LEAF
            self.handle = self.native.open(path, lock=True)
            self.identity, size = self.native.inspect(self.handle, path)
            self.native.security(self.handle, private=True, protected=True)
            if size:
                raise ProfileStorageError("Unexpected profile lock content")
            if not self.native.lock_file(self.handle, 3, 0, 1, 0, ctypes.byref(self.overlapped)):
                if ctypes.get_last_error() in (32, 33):
                    raise ProfileBusy("Presentation profile lock unavailable")
                raise ProfileStorageError("Cannot lock presentation profile")
            self.locked = True
            self.check()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def check(self) -> None:
        identity, size = self.native.inspect(self.handle, self.pins.directory / LOCK_LEAF)
        if identity != self.identity or size:
            raise ProfileStorageError("Profile lock identity changed")
        self.native.security(self.handle, private=True, protected=True)
        self.pins.check()

    def __exit__(self, *_):
        failed = False
        if self.locked:
            failed = not self.native.unlock_file(self.handle, 0, 1, 0, ctypes.byref(self.overlapped))
            self.locked = False
        if self.handle is not None:
            try:
                self.native.close(self.handle)
            except ProfileStorageError:
                failed = True
            self.handle = None
        if failed:
            raise ProfileUnverified("Profile lock release unverified")


class _PresentationProfileTransaction:
    """Shared receipt/liveness/lock/replace engine; private admission hooks."""

    def __init__(self, *, owner_is_current: Callable[[], bool]) -> None:
        if not callable(owner_is_current):
            raise TypeError("Trusted owner liveness callback required")
        self._owner_is_current = owner_is_current
        self._thread = threading.get_ident()
        self._generation = 0
        self._busy = False
        self._edit = None
        self._review = None

    def _admit_storage(self, native: _Win32, generation: int, *, create: bool):
        raise NotImplementedError

    def _thread_check(self) -> None:
        if threading.get_ident() != self._thread:
            raise ProfileStorageError("Profile owner thread mismatch")

    def invalidate(self) -> None:
        self._thread_check()
        self._generation += 1
        self._edit = self._review = None

    @contextmanager
    def _operation(self):
        self._thread_check()
        if self._busy:
            self.invalidate()
            raise ProfileBusy("Reentrant profile operation refused")
        self._busy = True
        try:
            yield self._generation
        except BaseException:
            self.invalidate()
            raise
        finally:
            self._busy = False

    def _live(self, generation: int) -> None:
        try:
            current = self._owner_is_current()
        except Exception:
            raise ProfileStorageError("Profile owner unavailable") from None
        if current is not True or generation != self._generation:
            raise ProfileStorageError("Profile owner invalidated")

    def _snapshot(self, pins: _Pins):
        path, native = self._directory / PROFILE_LEAF, pins.native
        pins.check()
        pins.inventory()
        if not pins.storage_present:
            document = PresentationConfigurationDocumentV1()
            self._validate_document(document)
            pins.check()
            return ProfileEdit(document, ProfileSnapshot(False, 0, None)), None
        handle = native.open(path, absent_ok=True)
        try:
            if handle is None:
                token = ProfileSnapshot(False, 0, None)
            else:
                identity, size = native.inspect(handle, path)
                native.security(handle, private=True,
                                admin_created_profile_leaf=True)
                if size > _LIMIT:
                    raise ProfileStorageError("Profile snapshot exceeds limit")
                content = native.read(handle)
                if len(content) != size:
                    raise ProfileStorageError("Profile snapshot changed")
                token = ProfileSnapshot(True, len(content), hashlib.sha256(content).hexdigest())
            # Every call constructs a separate real store/service via the sealed
            # bootstrap. Its strict parser rejects corrupt/duplicate/oversize data.
            service = bootstrap_presentation_configuration(path)
            if handle is not None:
                if native.inspect(handle, path)[0] != identity:
                    raise ProfileStorageError("Profile leaf identity changed")
                native.security(handle, private=True,
                                admin_created_profile_leaf=True)
            else:
                appeared = native.open(path, absent_ok=True)
                if appeared is not None:
                    native.close(appeared)
                    raise ProfileConflict("Profile changed; reload and review")
            pins.check()
            pins.inventory()
            return ProfileEdit(service.current, token), service
        finally:
            if handle is not None:
                native.close(handle)

    def load_for_edit(self) -> ProfileEdit:
        try:
            with self._operation() as generation:
                self._live(generation)
                self._edit = self._review = None
                native = _Win32()
                self._live(generation)
                with self._admit_storage(native, generation, create=False) as pins:
                    edit, _ = self._snapshot(pins)
                    self._live(generation)
                self._live(generation)
                self._edit = edit
                return edit
        except ProfileStorageError:
            raise
        except Exception:
            raise ProfileStorageError("Cannot load trusted presentation profile") from None

    def review_save(self, edit: ProfileEdit,
                    document: PresentationConfigurationDocumentV1) -> ProfileSaveReview:
        """Bind a separately human-reviewed exact draft; no native/filesystem I/O."""
        with self._operation() as generation:
            self._live(generation)
            if type(edit) is not ProfileEdit or edit is not self._edit:
                raise ProfileConflict("Profile edit expired; reload and review")
            self._validate_document(document)
            self._live(generation)
            review = ProfileSaveReview(edit, document)
            self._review = review
            return review

    @staticmethod
    def _validate_document(document) -> None:
        if type(document) is not PresentationConfigurationDocumentV1:
            raise TypeError("Exact presentation document required")
        if parse_presentation_configuration_document(
                presentation_configuration_document_to_mapping(document)) != document:
            raise ProfileStorageError("Invalid presentation draft")
        # Encode-check before even opening the sidecar or creating a child.
        # Both synthetic and production owners share this non-mutating guard.
        try:
            content = json.dumps(
                presentation_configuration_document_to_mapping(document),
                ensure_ascii=False, allow_nan=False, separators=(",", ":"),
            ).encode("utf-8")
            if len(content) > _LIMIT:
                raise ValueError
        except (UnicodeError, ValueError, TypeError):
            raise ProfileStorageError("Invalid presentation draft") from None

    def save(self, review: ProfileSaveReview) -> PresentationConfigurationDocumentV1:
        """Consume once; compare under lock; replace once; independently reread.

        Any Save failure expires the edit, including contention. Any exception
        after entering replace is uncertain even when an original remains intact.
        Success is returned only AFTER lock and all directory handles release.
        """
        write_started = False
        try:
            with self._operation() as generation:
                self._live(generation)
                if (type(review) is not ProfileSaveReview or review is not self._review
                        or review.edit is not self._edit):
                    raise ProfileConflict("Save review expired; reload and review")
                self._review = None
                self._validate_document(review.document)
                native = _Win32()
                self._live(generation)
                with self._admit_storage(native, generation, create=True) as pins:
                    pins.inventory()
                    # Admission may create production children only for this
                    # consumed reviewed Save. Sidecar creation follows the same
                    # liveness gate and never occurs during read-only admission.
                    self._live(generation)
                    with _ProfileLock(pins) as lock:
                        self._live(generation)
                        fresh, service = self._snapshot(pins)
                        self._live(generation)
                        if fresh.snapshot != review.edit.snapshot:
                            raise ProfileConflict("Profile changed; reload and review")
                        lock.check()
                        self._live(generation)
                        write_started = True
                        service.replace(review.document)
                        self._live(generation)
                        lock.check()
                        readback, _ = self._snapshot(pins)
                        self._live(generation)
                        if not readback.snapshot.present or readback.document != review.document:
                            raise ProfileUnverified("Storage may have changed; unverified")
                        lock.check()
                        pins.inventory()
                    pins.check()
                    self._live(generation)
                self._live(generation)
                return readback.document
        except Exception as error:
            if write_started:
                raise ProfileUnverified("Storage may have changed; unverified") from None
            # Only our fixed public refusals may cross this boundary. An
            # unexpected OSError (including a pathname) must never escape.
            if isinstance(error, ProfileStorageError):
                raise
            raise ProfileStorageError("Presentation profile save refused") from None
        finally:
            # Never leave a consumed/uncertain edit or review reusable. A caller
            # must explicitly load again even after a successful replacement.
            self.invalidate()


class TemporaryPresentationProfileOwner(_PresentationProfileTransaction):
    """Inactive test-only trusted owner, restricted to its creating thread.

    The caller owns the EXISTING temporary child and supplies exact current
    root/view/generation liveness. review_save is a trusted human-review adapter
    boundary, not something model text may call. Production NEVER enters through
    this class. An arbitrary path cannot be proven temporary by Python; this
    explicit test interface relies on the trusted caller, never UI input.
    """

    def __init__(self, directory: Path, *, owner_is_current: Callable[[], bool]) -> None:
        self._directory = _directory_path(directory)
        super().__init__(owner_is_current=owner_is_current)

    def _admit_storage(self, native: _Win32, generation: int, *, create: bool):
        # Both load and Save require an already-existing synthetic directory.
        return _Pins(native, self._directory)


class ProductionPresentationProfileOwner(_PresentationProfileTransaction):
    """Inactive production boundary: no caller-selected path or temporary owner.

    Construction is inert. First load lazily admits the Windows known folder;
    every subsequent operation resolves it again and rejects a changed root.
    The trusted future UI must supply exact root/view/generation liveness and
    call review_save only from its separately reviewed human Save flow. Calling
    this factory/class is not itself consent and no UI activation is provided.
    """

    def __init__(self, *, owner_is_current: Callable[[], bool]) -> None:
        super().__init__(owner_is_current=owner_is_current)
        self._known_folder = None
        self._directory = None

    def _admit_storage(self, native: _Win32, generation: int, *, create: bool):
        known_folder = _directory_path(_resolve_local_app_data())
        self._live(generation)
        if self._known_folder is not None and known_folder != self._known_folder:
            raise ProfileConflict("Trusted known folder changed; reopen settings")
        pins = _ProductionPins(native, known_folder,
                               before_create=(lambda: self._live(generation))
                               if create else None)
        self._known_folder = known_folder
        self._directory = pins.directory
        return pins


def create_production_presentation_profile_owner(
    *, owner_is_current: Callable[[], bool],
) -> ProductionPresentationProfileOwner:
    """Trusted composition only; inert and deliberately accepts no path.

    External host tests may monkeypatch _resolve_local_app_data BEFORE load to
    admit disposable synthetic storage. Never route real paths through the
    TemporaryPresentationProfileOwner test-only API. No default app wiring.
    """
    return ProductionPresentationProfileOwner(owner_is_current=owner_is_current)
