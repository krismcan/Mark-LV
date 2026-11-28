"""Inert Memory operation previews for a future trusted user interface.

These descriptions convey no consent, receipt, permission to write, or proof
of human confirmation. Owner, candidate, and record identifiers are caller data.
The contract performs no lookup or operation on Memory records.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

from .contracts import MAX_REVISION, MemoryDraftV1, _deny, _identifier, _text


@dataclass(frozen=True, slots=True, repr=False, kw_only=True)
class MemorySaveConsentDraftV1:
    """Preview a candidate with the bounded expiry in its existing draft."""

    owner_namespace: str
    candidate_id: str
    candidate: MemoryDraftV1

    def __post_init__(self) -> None:
        _identifier(self.owner_namespace)
        _identifier(self.candidate_id)
        if type(self.candidate) is not MemoryDraftV1:
            _deny()
        try:
            MemoryDraftV1.__post_init__(self.candidate)
        except AttributeError:
            # An exact instance can have unset slots if its constructor was bypassed.
            pass
        else:
            if self.candidate.owner_namespace == self.owner_namespace:
                return
        _deny()


def _record_selection(owner_namespace: str, record_id: str, expected_revision: int) -> None:
    _identifier(owner_namespace)
    _identifier(record_id)
    if type(expected_revision) is not int or not 1 <= expected_revision <= MAX_REVISION:
        _deny()


@dataclass(frozen=True, slots=True, repr=False, kw_only=True)
class MemoryCorrectConsentDraftV1:
    """Preview replacement text for one revision with its existing retention."""

    owner_namespace: str
    record_id: str
    expected_revision: int
    text: str

    def __post_init__(self) -> None:
        _record_selection(self.owner_namespace, self.record_id, self.expected_revision)
        if self.expected_revision == MAX_REVISION:
            _deny()
        _text(self.text)


@dataclass(frozen=True, slots=True, repr=False, kw_only=True)
class MemoryRemoveConsentDraftV1:
    """Preview removal of one revision."""

    owner_namespace: str
    record_id: str
    expected_revision: int

    def __post_init__(self) -> None:
        _record_selection(self.owner_namespace, self.record_id, self.expected_revision)


@dataclass(frozen=True, slots=True, repr=False, kw_only=True)
class MemoryClearConsentDraftV1:
    """Preview a clear scoped to one Memory owner namespace."""

    owner_namespace: str

    def __post_init__(self) -> None:
        _identifier(self.owner_namespace)


MemoryConsentDraftV1 = (
    MemorySaveConsentDraftV1 | MemoryCorrectConsentDraftV1
    | MemoryRemoveConsentDraftV1 | MemoryClearConsentDraftV1
)


def build_memory_consent_draft_v1(
    operation: str, values: dict[str, object], *, expected_owner_namespace: str,
) -> MemoryConsentDraftV1:
    """Build a typed preview from caller-supplied fields with sanitized errors.

    Matching the supplied owner labels is a data consistency check only.
    Record IDs and revisions describe expectations for a later trusted caller.
    """
    _identifier(expected_owner_namespace)
    if type(operation) is not str:
        _deny()
    draft_type: type[MemoryConsentDraftV1]
    match operation:
        case "save":
            draft_type = MemorySaveConsentDraftV1
        case "correct":
            draft_type = MemoryCorrectConsentDraftV1
        case "remove":
            draft_type = MemoryRemoveConsentDraftV1
        case "clear":
            draft_type = MemoryClearConsentDraftV1
        case _:
            _deny()

    names = {field.name for field in fields(draft_type)}
    if type(values) is not dict or len(values) != len(names):
        _deny()
    supplied = values.copy()
    if (len(supplied) != len(names) or any(type(key) is not str for key in supplied)
            or supplied.keys() != names):
        _deny()

    owner_namespace = supplied["owner_namespace"]
    _identifier(owner_namespace)
    if owner_namespace != expected_owner_namespace:
        _deny()
    return draft_type(**supplied)
