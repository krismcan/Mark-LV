"""Phase 9.1 candidate: bounded, data-only memory contracts. NOT runtime-wired.

This module has no disk, provider, network, policy, confirmation, credential,
or computer-action operations. A field labelled "confirmed" is historical
data, NOT evidence that the human UI consent gate occurred. Trust the future
lifecycle service, never a serialized record, for admission.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import re
import unicodedata


SCHEMA_VERSION = 1
MAX_MEMORY_TEXT_BYTES = 2048
MAX_MEMORY_TEXT_CHARS = 1024
MAX_RECORD_JSON_BYTES = 4096
MAX_TTL_SECONDS = 90 * 86400
MAX_SHORT_TERM_ENTRIES = 16
MAX_SHORT_TERM_BYTES = 8192
MAX_RETRIEVAL_ITEMS = 5
MAX_RETRIEVAL_BYTES = 4096
MAX_UNIX_TIME = 4102444800  # 2100-01-01 UTC
MAX_REVISION = 2147483647
_HEX32 = re.compile(r"[0-9a-f]{32}\Z", re.ASCII)
_SECRET_LIKE = re.compile(
    r"(?i)(?:\bsk-[a-z0-9_-]{8,}|\bgh[psu]_[a-z0-9]{8,}"
    r"|\b(?:api[\s_-]?key|password|access[\s_-]?token|secret)"
    r"\s*[:=]\s*\S+|\bbearer\s+\S+"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


class MemoryContractError(ValueError):
    """Sanitized contract failure, without echoing candidate text or bytes."""


class SourceKind(str, Enum):
    EXPLICIT_USER = "explicit_user"


class Sensitivity(str, Enum):
    ORDINARY = "ordinary"


class ShortTermSource(str, Enum):
    USER = "user"
    LOCAL_STATUS = "local_status"


def _deny() -> None:
    # Never expose a rejected input via an implicit enum/JSON exception chain.
    raise MemoryContractError("Invalid memory contract") from None


def _identifier(value: object) -> None:
    if type(value) is not str or _HEX32.fullmatch(value) is None or value == "0" * 32:
        _deny()


def _time(value: object) -> None:
    if type(value) is not int or not 0 <= value <= MAX_UNIX_TIME:
        _deny()


def _text(value: object) -> int:
    if type(value) is not str or not 1 <= len(value) <= MAX_MEMORY_TEXT_CHARS:
        _deny()
    if not value.strip() or unicodedata.normalize("NFC", value) != value:
        _deny()
    if any(unicodedata.category(ch) in {"Cc", "Cf", "Cs"}
           or ch in {"\u2028", "\u2029"} for ch in value):
        _deny()
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError:
        _deny()
    if len(encoded) > MAX_MEMORY_TEXT_BYTES or _SECRET_LIKE.search(value):
        _deny()
    return len(encoded)


def _ttl(captured: int, confirmed: int, expires: int) -> None:
    _time(captured)
    _time(confirmed)
    _time(expires)
    if confirmed < captured or not confirmed < expires:
        _deny()
    if expires - confirmed > MAX_TTL_SECONDS:
        _deny()


@dataclass(frozen=True, slots=True, repr=False)
class ShortTermEntryV1:
    """A current-session text item; never eligible for direct durable saving."""

    source: ShortTermSource
    text: str

    def __post_init__(self) -> None:
        if type(self.source) is not ShortTermSource:
            _deny()
        _text(self.text)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ShortTermContextV1:
    """Process-local snapshot only. The identity is an opaque runtime object."""

    session_identity: object
    epoch: int
    entries: tuple[ShortTermEntryV1, ...]

    def __post_init__(self) -> None:
        if type(self.session_identity) is not object:
            _deny()
        if type(self.epoch) is not int or not 0 <= self.epoch <= MAX_REVISION:
            _deny()
        if type(self.entries) is not tuple or len(self.entries) > MAX_SHORT_TERM_ENTRIES:
            _deny()
        total = 0
        for item in self.entries:
            if type(item) is not ShortTermEntryV1:
                _deny()
            total += len(item.text.encode("utf-8", "strict"))
        if total > MAX_SHORT_TERM_BYTES:
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class MemoryDraftV1:
    """Non-authoritative proposed record. Constructing this does not save it."""

    owner_namespace: str
    text: str
    source: SourceKind
    source_reference: str
    captured_at_utc: int
    proposed_expires_at_utc: int

    def __post_init__(self) -> None:
        _identifier(self.owner_namespace)
        _text(self.text)
        if type(self.source) is not SourceKind or self.source is not SourceKind.EXPLICIT_USER:
            _deny()
        if type(self.source_reference) is not str or self.source_reference != "human-save":
            _deny()
        _time(self.captured_at_utc)
        _time(self.proposed_expires_at_utc)
        if not self.captured_at_utc < self.proposed_expires_at_utc:
            _deny()
        if self.proposed_expires_at_utc - self.captured_at_utc > MAX_TTL_SECONDS:
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class DurableMemoryRecordV1:
    """Plain data. NOT a consent token, authorisation, or durable store."""

    schema_version: int
    record_id: str
    owner_namespace: str
    text: str
    source: SourceKind
    source_reference: str
    sensitivity: Sensitivity
    captured_at_utc: int
    confirmed_at_utc: int
    expires_at_utc: int
    corrected_at_utc: int | None
    revision: int

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != SCHEMA_VERSION:
            _deny()
        _identifier(self.record_id)
        _identifier(self.owner_namespace)
        _text(self.text)
        if type(self.source) is not SourceKind or self.source is not SourceKind.EXPLICIT_USER:
            _deny()
        if type(self.source_reference) is not str or self.source_reference != "human-save":
            _deny()
        if type(self.sensitivity) is not Sensitivity or self.sensitivity is not Sensitivity.ORDINARY:
            _deny()
        _ttl(self.captured_at_utc, self.confirmed_at_utc, self.expires_at_utc)
        if self.corrected_at_utc is not None:
            _time(self.corrected_at_utc)
            if not self.confirmed_at_utc <= self.corrected_at_utc < self.expires_at_utc:
                _deny()
        if type(self.revision) is not int or not 1 <= self.revision <= MAX_REVISION:
            _deny()
        if (self.corrected_at_utc is None) != (self.revision == 1):
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class MemoryRetrievalItemV1:
    """Untrusted context only; the consumer must enforce owner + time again."""

    record: DurableMemoryRecordV1
    retrieved_at_utc: int

    def __post_init__(self) -> None:
        if type(self.record) is not DurableMemoryRecordV1:
            _deny()
        _time(self.retrieved_at_utc)
        # A corrected revision cannot be retrieved before that revision existed.
        effective_at = (self.record.corrected_at_utc
                        if self.record.corrected_at_utc is not None
                        else self.record.confirmed_at_utc)
        if not effective_at <= self.retrieved_at_utc < self.record.expires_at_utc:
            _deny()

    @property
    def trust_label(self) -> str:
        return "untrusted_memory_context"


@dataclass(frozen=True, slots=True, repr=False)
class MemoryRetrievalBatchV1:
    """Bounded same-owner retrieval DATA; never proves caller identity."""

    owner_namespace: str
    as_of_utc: int
    items: tuple[MemoryRetrievalItemV1, ...]

    def __post_init__(self) -> None:
        _identifier(self.owner_namespace)
        _time(self.as_of_utc)
        if type(self.items) is not tuple or len(self.items) > MAX_RETRIEVAL_ITEMS:
            _deny()
        seen: set[str] = set()
        total_bytes = 0
        for item in self.items:
            if type(item) is not MemoryRetrievalItemV1:
                _deny()
            if (item.record.owner_namespace != self.owner_namespace
                    or item.retrieved_at_utc != self.as_of_utc
                    or item.record.record_id in seen):
                _deny()
            seen.add(item.record.record_id)
            total_bytes += len(item.record.text.encode("utf-8", "strict"))
            if total_bytes > MAX_RETRIEVAL_BYTES:
                _deny()

    @property
    def trust_label(self) -> str:
        return "untrusted_memory_context"


_RECORD_KEYS = frozenset({
    "schema_version", "record_id", "owner_namespace", "text", "source",
    "source_reference", "sensitivity", "captured_at_utc", "confirmed_at_utc",
    "expires_at_utc", "corrected_at_utc", "revision",
})


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _deny()
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    _deny()


def parse_memory_record_json_v1(blob: bytes) -> DurableMemoryRecordV1:
    """Strict, bounded pure JSON decoder. No filesystem reads, owner admission or I/O."""
    if type(blob) is not bytes or not 1 <= len(blob) <= MAX_RECORD_JSON_BYTES:
        _deny()
    try:
        data = json.loads(
            blob.decode("utf-8", "strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if type(data) is not dict or set(data) != _RECORD_KEYS:
            _deny()
        # Enums cannot be passed in via JSON. Refuse unusual types/coercion.
        if type(data["source"]) is not str or type(data["sensitivity"]) is not str:
            _deny()
        return DurableMemoryRecordV1(
            schema_version=data["schema_version"],
            record_id=data["record_id"],
            owner_namespace=data["owner_namespace"],
            text=data["text"],
            source=SourceKind(data["source"]),
            source_reference=data["source_reference"],
            sensitivity=Sensitivity(data["sensitivity"]),
            captured_at_utc=data["captured_at_utc"],
            confirmed_at_utc=data["confirmed_at_utc"],
            expires_at_utc=data["expires_at_utc"],
            corrected_at_utc=data["corrected_at_utc"],
            revision=data["revision"],
        )
    except (UnicodeError, ValueError, TypeError, OverflowError, RecursionError):
        # Leave the handler before raising so parser exceptions are not
        # retained as the sanitized exception's implicit context.
        pass
    _deny()


def memory_record_to_json_v1(record: DurableMemoryRecordV1) -> bytes:
    """Canonical serialization is still ONLY data; not a persistence operation."""
    if type(record) is not DurableMemoryRecordV1:
        _deny()
    data = {
        "schema_version": record.schema_version,
        "record_id": record.record_id,
        "owner_namespace": record.owner_namespace,
        "text": record.text,
        "source": record.source.value,
        "source_reference": record.source_reference,
        "sensitivity": record.sensitivity.value,
        "captured_at_utc": record.captured_at_utc,
        "confirmed_at_utc": record.confirmed_at_utc,
        "expires_at_utc": record.expires_at_utc,
        "corrected_at_utc": record.corrected_at_utc,
        "revision": record.revision,
    }
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"),
                         allow_nan=False).encode("utf-8", "strict")
    if len(encoded) > MAX_RECORD_JSON_BYTES:
        _deny()
    return encoded
