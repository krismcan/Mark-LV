"""Bounded lexical ranking for caller-supplied synthetic memory records."""
from __future__ import annotations

import unicodedata

from .contracts import (
    MAX_MEMORY_TEXT_BYTES,
    MAX_MEMORY_TEXT_CHARS,
    MAX_RETRIEVAL_BYTES,
    MAX_RETRIEVAL_ITEMS,
    DurableMemoryRecordV1,
    MemoryContractError,
    MemoryRetrievalBatchV1,
    MemoryRetrievalItemV1,
)


MAX_RETRIEVAL_CANDIDATES = 256


def _terms(text: str) -> set[str]:
    folded = unicodedata.normalize("NFC", text).casefold()
    normalized = unicodedata.normalize("NFC", folded)
    terms: set[str] = set()
    word: list[str] = []
    for char in normalized:
        if char.isalnum() or (word and unicodedata.category(char).startswith("M")):
            word.append(char)
        elif word:
            terms.add("".join(word))
            word.clear()
    if word:
        terms.add("".join(word))
    return terms


def _query_terms(query: str) -> set[str]:
    if type(query) is not str or len(query) > MAX_MEMORY_TEXT_CHARS:
        raise MemoryContractError("Invalid memory retrieval query") from None
    try:
        within_budget = len(query.encode("utf-8")) <= MAX_MEMORY_TEXT_BYTES
    except UnicodeEncodeError:
        within_budget = False
    if not within_budget:
        raise MemoryContractError("Invalid memory retrieval query") from None
    return _terms(query)


def _validate_record(record: DurableMemoryRecordV1) -> None:
    if type(record) is DurableMemoryRecordV1:
        try:
            record.__post_init__()
            return
        except AttributeError:
            # An instance created without its constructor can have unset slots.
            pass
    raise MemoryContractError("Invalid memory retrieval record") from None


def retrieve_memory_v1(
    query: str,
    records: tuple[DurableMemoryRecordV1, ...],
    *,
    owner_namespace: str,
    as_of_utc: int,
) -> MemoryRetrievalBatchV1:
    """Rank unique, eligible records as untrusted memory context.

    The owner namespace and as-of time are caller-supplied data. A future
    admitted caller must independently enforce owner identity and trusted time.
    Any malformed, foreign-owner, or repeated record invalidates the call.

    The query uses the contract's memory text size limits. Rank by the number
    of distinct shared Unicode words after NFC normalization and case folding,
    breaking ties by ascending record ID. Return the highest-ranked prefix of
    positive matches that fits both retrieval limits, keeping original text.
    """
    empty_batch = MemoryRetrievalBatchV1(owner_namespace, as_of_utc, ())
    if type(records) is not tuple or len(records) > MAX_RETRIEVAL_CANDIDATES:
        raise MemoryContractError("Invalid memory retrieval candidates") from None
    query_terms = _query_terms(query)

    seen_ids: set[str] = set()
    ranked: list[tuple[int, DurableMemoryRecordV1]] = []
    for record in records:
        _validate_record(record)
        if record.owner_namespace != owner_namespace or record.record_id in seen_ids:
            raise MemoryContractError("Invalid memory retrieval candidates") from None
        seen_ids.add(record.record_id)

        effective_at = record.corrected_at_utc
        if effective_at is None:
            effective_at = record.confirmed_at_utc
        if not query_terms or not effective_at <= as_of_utc < record.expires_at_utc:
            continue
        score = len(query_terms.intersection(_terms(record.text)))
        if score:
            ranked.append((score, record))

    if not ranked:
        return empty_batch
    ranked.sort(key=lambda match: (-match[0], match[1].record_id))
    items: list[MemoryRetrievalItemV1] = []
    remaining_bytes = MAX_RETRIEVAL_BYTES
    for _, record in ranked[:MAX_RETRIEVAL_ITEMS]:
        text_bytes = len(record.text.encode("utf-8"))
        if text_bytes > remaining_bytes:
            break
        remaining_bytes -= text_bytes
        items.append(MemoryRetrievalItemV1(record, as_of_utc))
    return MemoryRetrievalBatchV1(owner_namespace, as_of_utc, tuple(items))
