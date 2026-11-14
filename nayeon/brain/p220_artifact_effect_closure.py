"""P220: review-only audit of an actual ZIP member inventory for legacy BYOK effects.

Never an installer, code-signature verifier, OS trust boundary or admission grant.
Treat input as an untrusted archive. Do not extract, load or execute its members.
The lack of a named legacy member is NOT proof that any binary, PyInstaller
payload, dynamically imported code, native plugin or installed tree is safe.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib
import stat
import unicodedata
import zipfile

_MAX_ARCHIVE_BYTES = 24 * 1024 * 1024
_MAX_MEMBERS = 256
_MAX_MEMBER_BYTES = 2 * 1024 * 1024
_MAX_UNCOMPRESSED = 8 * 1024 * 1024
_MAX_MEMBER_NAME = 260

# Canonical shipped module suffixes, not filenames supplied by caller claims.
# Alternate real effects can exist outside this list: result remains NO-GO.
_LEGACY_SUFFIXES = frozenset((
    ("nayeon", "secrets", "windows_credential"),
    ("nayeon", "brain", "local_byok_user_scope"),
    ("nayeon", "desktop_alpha", "local_byok_window"),
    ("nayeon", "desktop_alpha", "local_byok_launch_bridge"),
))
_PYTHON_SUFFIXES = frozenset((".py", ".pyc", ".pyo", ".pyd"))
_OPAQUE = frozenset((
    ".exe", ".dll", ".msi", ".msp", ".cab", ".pyd", ".pyz",
    ".zip", ".whl", ".egg", ".7z", ".tar", ".gz", ".xz", ".so",
    ".bin", ".dat", ".ps1", ".bat", ".cmd", ".vbs", ".js",
))


class P220InventoryDisposition(str, Enum):
    INVALID = "INVALID_ARCHIVE_HOLD"
    LEGACY_EFFECT_PRESENT = "LEGACY_CREDENTIAL_ROUTE_PRESENT_HOLD"
    OPAQUE_CODE_UNPROVEN = "OPAQUE_RUNTIME_OR_NESTED_CODE_UNPROVEN_HOLD"
    SOURCE_ONLY_UNPROVEN = "NO_NAMED_LEGACY_SOURCE_IN_BOUNDED_ZIP_STILL_HOLD"


@dataclass(frozen=True, slots=True)
class P220InventoryReceipt:
    disposition: P220InventoryDisposition
    member_count: int
    legacy_members: tuple[str, ...]
    opaque_members: tuple[str, ...]
    archive_sha256: str | None
    reason: str
    real_key_allowed: bool = False
    native_effect_allowed: bool = False
    production_release_allowed: bool = False
    independent_signer_approved: bool = False
    signed_installed_image_verified: bool = False
    os_code_integrity_admitted: bool = False
    service_store_isolated: bool = False

    def __post_init__(self) -> None:
        if any((
            self.real_key_allowed, self.native_effect_allowed,
            self.production_release_allowed, self.independent_signer_approved,
            self.signed_installed_image_verified, self.os_code_integrity_admitted,
            self.service_store_isolated,
        )):
            raise ValueError("P220 review cannot mint release or Windows security authority")


def _invalid(reason: str) -> P220InventoryReceipt:
    return P220InventoryReceipt(
        P220InventoryDisposition.INVALID, 0, (), (), None, reason)


def _name_parts(name: str) -> tuple[str, ...] | None:
    if type(name) is not str or not name or len(name) > _MAX_MEMBER_NAME:
        return None
    if (unicodedata.normalize("NFKC", name) != name
        or "\\" in name or ":" in name or "%" in name
        or name.startswith("/") or "\x00" in name):
        return None
    parts = name.split("/")
    if (not parts or len(parts) > 32
        or any(not p or p in (".", "..") or p[-1] in (" ", ".")
               or any(ord(ch) < 32 or ord(ch) == 127 for ch in p)
               for p in parts)):
        return None
    return tuple(x.casefold() for x in parts)


def _known_legacy(parts: tuple[str, ...]) -> bool:
    if not parts:
        return False
    filename = parts[-1]
    stem, dot, extension = filename.rpartition(".")
    suffix = "." + extension if dot else ""
    if suffix not in _PYTHON_SUFFIXES:
        return False
    stem = stem.split(".")[0]  # Python cached bytecode name/module stem
    candidate = parts[:-1] + (stem,)
    for legacy in _LEGACY_SUFFIXES:
        if len(candidate) >= len(legacy) and candidate[-len(legacy):] == legacy:
            return True
    return False


def inspect_bounded_zip(archive: Path) -> P220InventoryReceipt:
    """Scan all bytes of a bounded actual ZIP; never extract or execute.

    Results are *review* diagnostics. No value is positive signer, service,
    native-effect, key migration, Windows policy or release authority.
    """
    if not isinstance(archive, Path) or not archive.is_absolute():
        return _invalid("ZIP path must be exact absolute Path")
    try:
        metadata = archive.lstat()
        if (not stat.S_ISREG(metadata.st_mode)
            or archive.is_symlink()
            or getattr(metadata, "st_file_attributes", 0) & 0x400
            or not 0 < metadata.st_size <= _MAX_ARCHIVE_BYTES):
            return _invalid("not an ordinary bounded archive")
        archive_hash = hashlib.sha256()
        with archive.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                archive_hash.update(chunk)
        legacy: list[str] = []
        opaque: list[str] = []
        seen: set[tuple[str, ...]] = set()
        total = 0
        with zipfile.ZipFile(archive, "r", allowZip64=False) as zf:
            records = zf.infolist()
            if not records or len(records) > _MAX_MEMBERS:
                return _invalid("empty or oversized ZIP member list")
            for member in records:
                if member.is_dir() or member.flag_bits & 0x1:
                    return _invalid("directory or encrypted ZIP member")
                # On Windows, ZipInfo.filename may normalise raw '\\' to '/'.
                # orig_filename preserves the untrusted central-directory
                # spelling, which must be rejected before normalisation.
                parts = _name_parts(member.orig_filename)
                if parts is None or parts in seen:
                    return _invalid("unsafe or casefold-colliding ZIP member")
                seen.add(parts)
                mode = (member.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    return _invalid("ZIP symbolic link is not an ordinary member")
                if (not 0 <= member.file_size <= _MAX_MEMBER_BYTES
                    or not 0 <= member.compress_size <= _MAX_ARCHIVE_BYTES):
                    return _invalid("ZIP member outside size limits")
                total += member.file_size
                if total > _MAX_UNCOMPRESSED:
                    return _invalid("ZIP decompressed size exceeds review bound")
                # Enforces ZIP CRC; cannot smuggle an unchecked member.
                with zf.open(member, "r") as stream:
                    read_bytes = 0
                    for chunk in iter(lambda: stream.read(64 * 1024), b""):
                        read_bytes += len(chunk)
                        if read_bytes > _MAX_MEMBER_BYTES:
                            return _invalid("actual ZIP decompressed bytes exceeded limit")
                    if read_bytes != member.file_size:
                        return _invalid("ZIP member did not match declared length")
                if _known_legacy(parts):
                    legacy.append(member.filename)
                else:
                    suffix = Path(parts[-1]).suffix
                    if suffix in _OPAQUE or "__pycache__" in parts:
                        opaque.append(member.filename)
        if legacy:
            disposition = P220InventoryDisposition.LEGACY_EFFECT_PRESENT
            reason = "actual archive includes a named historical direct credential effect/consumer/launcher"
        elif opaque:
            disposition = P220InventoryDisposition.OPAQUE_CODE_UNPROVEN
            reason = "opaque executable/nested/archive content cannot be proved excluded"
        else:
            disposition = P220InventoryDisposition.SOURCE_ONLY_UNPROVEN
            reason = "bounded ZIP inventory alone cannot prove signed installed runtime isolation"
        return P220InventoryReceipt(
            disposition, len(seen), tuple(sorted(legacy)),
            tuple(sorted(opaque)), archive_hash.hexdigest(), reason)
    except (OSError, ValueError, UnicodeError, RuntimeError, EOFError, zipfile.BadZipFile,
            zipfile.LargeZipFile, NotImplementedError):
        return _invalid("unreadable or invalid bounded ZIP")


def approve_high_assurance_release(_receipt: P220InventoryReceipt, **_claims: object) -> bool:
    """No manifest string, forged signature/approval or clean inventory grants GO."""
    return False
