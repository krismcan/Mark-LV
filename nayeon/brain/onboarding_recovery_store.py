"""Fail-closed local journal persistence; evidence only, never admission authority.

A trusted owner controller MUST hold the Windows-session mutex across calls.
A verified journal cannot authorize fresh ownership, and successful fsync plus
readback does not guarantee physical/directory durability or prevent attacks
by privileged/uncooperative external filesystem writers.
"""
from pathlib import Path
import os
import stat

from nayeon.brain.onboarding_recovery_document import (
    MAX_JOURNAL_BYTES, MAX_RECORDS, GENESIS_HASH,
    RecoveryEvidenceError, RecoveryRecord, RecoveryState, decode_journal, encode_frame,
    record_hash, MAX_RECORD_BYTES,
)


class RecoveryStoreUnavailable(RuntimeError):
    """Missing, malformed or untrustworthy storage denies admission."""


def _identity(info) -> tuple:
    return info.st_dev, info.st_ino


def _safe_regular(info) -> bool:
    return (stat.S_ISREG(info.st_mode) and
            not (getattr(info, "st_file_attributes", 0) & 0x400))


class OnboardingRecoveryJournalStore:
    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        if type(path) is not type(Path()):
            raise TypeError("Exact native journal path required")
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def _check_parent(self) -> None:
        try:
            parent = self._path.parent
            info = parent.lstat()
            if (not stat.S_ISDIR(info.st_mode) or parent.is_symlink() or
                    getattr(info, "st_file_attributes", 0) & 0x400):
                raise RecoveryStoreUnavailable("Untrusted journal parent")
        except (OSError, ValueError) as exc:
            raise RecoveryStoreUnavailable("Journal parent unavailable") from exc

    def _open_checked(self, *, create: bool, write: bool) -> int:
        """Open one descriptor and verify its identity BEFORE any mutation.

        A replaced symlink is rejected when the fd points at its target but the
        path's lstat describes the link. On Windows, unexpected reparse
        attributes are rejected. Parent-ancestor races and a malicious local
        filesystem writer remain outside the cooperative threat model.
        """
        self._check_parent()
        flags = os.O_WRONLY if write else os.O_RDONLY
        if write:
            flags |= os.O_CREAT | os.O_EXCL if create else os.O_APPEND
        flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
        try:
            before = None
            try:
                before = self._path.lstat()
            except FileNotFoundError:
                if not create:
                    raise
            if before is not None and not _safe_regular(before):
                raise RecoveryStoreUnavailable("Untrusted journal entry")
            if create and before is not None:
                raise RecoveryStoreUnavailable("Existing journal cannot be initialized")
            fd = os.open(self._path, flags, 0o600)
            try:
                observed = self._path.lstat()
                opened = os.fstat(fd)
                if (not _safe_regular(opened) or not _safe_regular(observed) or
                        _identity(opened) != _identity(observed) or
                        (before is not None and _identity(before) != _identity(opened))):
                    raise RecoveryStoreUnavailable("Journal entry replaced during opening")
                return fd
            except BaseException:
                os.close(fd)
                raise
        except (OSError, ValueError, RecursionError) as exc:
            raise RecoveryStoreUnavailable("Journal handle unavailable or replaced") from exc

    def _read(self) -> tuple[RecoveryRecord, ...] | None:
        self._check_parent()
        try:
            self._path.lstat()
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            raise RecoveryStoreUnavailable("Journal metadata unavailable") from exc
        try:
            fd = self._open_checked(create=False, write=False)
            with os.fdopen(fd, "rb", closefd=True) as source:
                opened = os.fstat(source.fileno())
                data = source.read(MAX_JOURNAL_BYTES + 1)
                current = self._path.lstat()
                if (_identity(current) != _identity(opened) or
                        not _safe_regular(current)):
                    raise RecoveryStoreUnavailable("Journal entry changed during read")
            return decode_journal(data)
        except (OSError, RecoveryEvidenceError, ValueError, RecursionError) as exc:
            raise RecoveryStoreUnavailable("Journal unreadable or invalid") from exc

    def read(self) -> tuple[RecoveryRecord, ...] | None:
        """Absent evidence is never readiness. Corrupt evidence is unavailable."""
        return self._read()

    def append(self, record: RecoveryRecord, *, create: bool = False) -> tuple[RecoveryRecord, ...]:
        """Exactly one checked append, fsync, close and full reread.

        The caller MUST serialize through the retained trusted mutex tenure.
        On any exception, the write may have occurred: NEVER retry automatically.
        """
        if type(create) is not bool or type(record) is not RecoveryRecord:
            raise TypeError("Exact record and creation flag required")
        before = self._read()
        if create and before is not None:
            raise RecoveryStoreUnavailable("Journal already initialized")
        if not create and before is None:
            raise RecoveryStoreUnavailable("Journal requires explicit initialization")
        old = () if before is None else before
        if len(old) >= MAX_RECORDS or record.sequence != len(old) + 1:
            raise RecoveryStoreUnavailable("Invalid sequence or exhausted journal")
        # Never start an effect without reserving the FINISH journal slot.
        if record.state is RecoveryState.IN_FLIGHT and (
                len(old) + 2 > MAX_RECORDS or
                sum(len(encode_frame(item)) for item in old)
                + len(encode_frame(record)) + MAX_RECORD_BYTES + 80
                > MAX_JOURNAL_BYTES):
            raise RecoveryStoreUnavailable("No completion headroom; archive by human review")
        predecessor = GENESIS_HASH if not old else record_hash(old[-1])
        if record.previous_hash != predecessor or (
                old and record.generation < old[-1].generation):
            raise RecoveryStoreUnavailable("Journal chain/generation conflict")
        try:
            frame = encode_frame(record)
            if sum(len(encode_frame(item)) for item in old) + len(frame) > MAX_JOURNAL_BYTES:
                raise RecoveryStoreUnavailable("Journal exhausted")
            fd = self._open_checked(create=create, write=True)
            with os.fdopen(fd, "wb", closefd=True) as dest:
                count = dest.write(frame)
                if type(count) is not int or count != len(frame):
                    raise RecoveryStoreUnavailable("Short journal write")
                dest.flush()
                os.fsync(dest.fileno())
            after = self._read()
            if after is None or after != old + (record,):
                raise RecoveryStoreUnavailable("Journal readback mismatch")
            return after
        except (OSError, ValueError, RecoveryEvidenceError, RecursionError) as exc:
            raise RecoveryStoreUnavailable("Journal append unverified") from exc

    def archive_required(self, history: tuple[RecoveryRecord, ...] | None) -> bool:
        """Reserve two reconciliation slots AND a future operation pair."""
        if history is None:
            return False
        size = sum(len(encode_frame(item)) for item in history)
        return (len(history) + 4 > MAX_RECORDS or
                size + 4 * (MAX_RECORD_BYTES + 80) > MAX_JOURNAL_BYTES)

    def archive_present(self) -> bool:
        """Previous archives warn the human even if current journal is absent."""
        self._check_parent()
        try:
            return any(self._path.parent.glob(self._path.name + ".archive-*"))
        except (OSError, ValueError) as exc:
            raise RecoveryStoreUnavailable("Cannot inspect journal archives") from exc

    def archive_exact(self, expected: RecoveryRecord) -> Path:
        """Human-authorised rotation only, inside retained mutex tenure.

        Rename original evidence to a checksum-named archive. A caller must
        append a new RECONCILING and READY to a fresh journal before granting
        authority. Failure AFTER rename is intentionally non-rollbackable:
        next owner sees archive and still requires fresh human reconciliation.
        This is API-level verified, not a claim of disk power-loss durability.
        """
        if type(expected) is not RecoveryRecord:
            raise TypeError("Exact previous evidence required")
        try:
            history = self._read()
            if not history or history[-1] != expected:
                raise RecoveryStoreUnavailable("Archived baseline changed")
            target = self._path.with_name(
                self._path.name + ".archive-" + record_hash(expected))
            if target.exists() or target.is_symlink():
                raise RecoveryStoreUnavailable("Archive already exists")
            self._check_parent()
            # This is inside a single trusted cooperative mutex tenure.
            os.rename(self._path, target)
            archived = OnboardingRecoveryJournalStore(target).read()
            if archived != history or self._read() is not None:
                raise RecoveryStoreUnavailable("Archive evidence failed verification")
            return target
        except (OSError, ValueError, RecoveryEvidenceError, RecursionError) as exc:
            raise RecoveryStoreUnavailable("Archive failed; current tenure invalid") from exc
