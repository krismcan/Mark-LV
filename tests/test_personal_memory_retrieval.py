"""Synthetic unit tests for the offline memory relevance function."""
from dataclasses import replace
import unittest

from nayeon.memory.contracts import (
    MAX_MEMORY_TEXT_BYTES,
    MAX_MEMORY_TEXT_CHARS,
    MAX_RETRIEVAL_BYTES,
    MAX_RETRIEVAL_ITEMS,
    MAX_UNIX_TIME,
    SCHEMA_VERSION,
    DurableMemoryRecordV1,
    MemoryContractError,
    MemoryRetrievalBatchV1,
    Sensitivity,
    SourceKind,
)
from nayeon.memory.retrieval import MAX_RETRIEVAL_CANDIDATES, retrieve_memory_v1


OWNER = "a" * 32
FOREIGN_OWNER = "b" * 32
AS_OF = 100


def make_record(number, text="orbit", **changes):
    fields = {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"{number:032x}",
        "owner_namespace": OWNER,
        "text": text,
        "source": SourceKind.EXPLICIT_USER,
        "source_reference": "human-save",
        "sensitivity": Sensitivity.ORDINARY,
        "captured_at_utc": AS_OF - 20,
        "confirmed_at_utc": AS_OF - 10,
        "expires_at_utc": AS_OF + 20,
        "corrected_at_utc": None,
        "revision": 1,
    }
    return DurableMemoryRecordV1(**(fields | changes))


def retrieve(query, records, *, owner_namespace=OWNER, as_of_utc=AS_OF):
    return retrieve_memory_v1(
        query, records, owner_namespace=owner_namespace, as_of_utc=as_of_utc
    )


def ranked_ids(batch):
    return tuple(int(item.record.record_id, 16) for item in batch.items)


class PersonalMemoryRetrievalTests(unittest.TestCase):
    def test_ranks_by_distinct_whole_word_overlap(self):
        records = (
            make_record(6, "quartz amber quartz"),
            make_record(1, "orbit orbit orbit orbit"),
            make_record(2, "orbit amber"),
            make_record(3, "amber orbit quartz"),
            make_record(4, "orbital quartzite ambergold"),
            make_record(5, "orbit quartz"),
        )
        batch = retrieve("ORBIT, quartz quartz - AMBER", records)
        self.assertEqual(ranked_ids(batch), (3, 2, 5, 6, 1))

    def test_ties_use_record_id_and_cap_results_independent_of_input_order(self):
        records = tuple(make_record(i) for i in range(1, MAX_RETRIEVAL_ITEMS + 3))
        for order in (records, records[::-1], records[2:] + records[:2]):
            self.assertEqual(
                ranked_ids(retrieve("orbit", order)),
                tuple(range(1, MAX_RETRIEVAL_ITEMS + 1)),
            )

    def test_miss_term_free_query_and_empty_candidates_return_empty_batch(self):
        records = (make_record(1, "orbital"),)
        for query in ("orbit", "", " \t", "_?! \U0001f642"):
            with self.subTest(query=query):
                self.assertEqual(retrieve(query, records).items, ())
        self.assertEqual(retrieve("orbit", ()).items, ())

    def test_uses_unicode_case_folding_and_canonical_whole_words(self):
        marked_word = "\u0915\u093f\u0924\u093e\u092c"
        original = f"Stra\u00dfe CAF\u00c9 {marked_word}"
        records = (make_record(2, original), make_record(1, "STRASSE"))
        batch = retrieve("strasse cafe\u0301", records)
        self.assertEqual(ranked_ids(batch), (2, 1))
        self.assertEqual(batch.items[0].record.text, original)
        self.assertEqual(ranked_ids(retrieve(marked_word, records)), (2,))
        self.assertEqual(retrieve("\u0915", records).items, ())
        self.assertEqual(retrieve("cafe", records).items, ())

    def test_omits_expired_future_and_unconfirmed_records(self):
        records = (
            make_record(1, expires_at_utc=AS_OF),
            make_record(2, captured_at_utc=AS_OF + 1, confirmed_at_utc=AS_OF + 2),
            make_record(3, confirmed_at_utc=AS_OF + 1),
            make_record(4, confirmed_at_utc=AS_OF, expires_at_utc=AS_OF + 1),
        )
        self.assertEqual(ranked_ids(retrieve("orbit", records)), (4,))

    def test_corrected_version_is_eligible_at_correction_time(self):
        corrected = make_record(1, "amber orbit", corrected_at_utc=AS_OF, revision=2)
        self.assertEqual(retrieve("amber", (corrected,), as_of_utc=AS_OF - 1).items, ())
        batch = retrieve("amber", (corrected,))
        self.assertEqual(ranked_ids(batch), (1,))
        self.assertEqual(batch.items[0].record.revision, 2)

    def test_foreign_owner_refuses_whole_batch_even_when_filtered(self):
        records = (
            make_record(1),
            make_record(2, "amber", owner_namespace=FOREIGN_OWNER, expires_at_utc=AS_OF),
        )
        for query in ("orbit", ""):
            with self.subTest(query=query), self.assertRaises(MemoryContractError):
                retrieve(query, records)

    def test_refuses_duplicate_and_conflicting_record_ids(self):
        record = make_record(1)
        for duplicate in (
            record,
            replace(record),
            replace(record, text="amber", corrected_at_utc=AS_OF + 1, revision=2),
        ):
            with self.subTest(revision=duplicate.revision), self.assertRaises(MemoryContractError):
                retrieve("orbit", (record, duplicate))

    def test_rejects_invalid_input_types_and_owner_or_time_bounds(self):
        for query in (None, 1, b"orbit"):
            with self.subTest(query=query), self.assertRaises(MemoryContractError):
                retrieve(query, ())
        for records in (None, [make_record(1)], iter((make_record(1),)), (object(),)):
            with self.subTest(type=type(records)), self.assertRaises(MemoryContractError):
                retrieve("", records)
        for owner in (None, "0" * 32, "a" * 31, "A" * 32):
            with self.subTest(owner=owner), self.assertRaises(MemoryContractError):
                retrieve("orbit", (), owner_namespace=owner)
        for as_of in (True, -1, MAX_UNIX_TIME + 1, float(AS_OF)):
            with self.subTest(as_of=as_of), self.assertRaises(MemoryContractError):
                retrieve("orbit", (), as_of_utc=as_of)
        for as_of in (0, MAX_UNIX_TIME):
            self.assertEqual(retrieve("orbit", (), as_of_utc=as_of).as_of_utc, as_of)

    def test_rejects_invalid_typed_records_before_filtering(self):
        with self.assertRaises(MemoryContractError):
            retrieve("", (object.__new__(DurableMemoryRecordV1),))
        for field, value in (
            ("text", "x" * (MAX_MEMORY_TEXT_CHARS + 1)),
            ("record_id", []),
            ("expires_at_utc", True),
            ("revision", 2),
        ):
            malformed = make_record(1)
            object.__setattr__(malformed, field, value)
            with self.subTest(field=field), self.assertRaises(MemoryContractError):
                retrieve("", (malformed,))

    def test_enforces_candidate_count_boundary(self):
        records = tuple(make_record(i, "amber") for i in range(1, MAX_RETRIEVAL_CANDIDATES))
        records += (make_record(MAX_RETRIEVAL_CANDIDATES),)
        self.assertEqual(ranked_ids(retrieve("orbit", records)), (MAX_RETRIEVAL_CANDIDATES,))
        with self.assertRaises(MemoryContractError):
            retrieve("", records + (make_record(MAX_RETRIEVAL_CANDIDATES + 1),))

    def test_enforces_query_character_and_utf8_bounds(self):
        at_limit = "\u00e9" * MAX_MEMORY_TEXT_CHARS
        self.assertEqual(len(at_limit.encode("utf-8")), MAX_MEMORY_TEXT_BYTES)
        self.assertEqual(ranked_ids(retrieve(at_limit, (make_record(1, at_limit),))), (1,))
        for query in (
            "a" * (MAX_MEMORY_TEXT_CHARS + 1),
            "\U0001f642" * (MAX_MEMORY_TEXT_BYTES // 4 + 1),
            "synthetic-query-marker\ud800",
        ):
            with self.subTest(length=len(query)), self.assertRaises(MemoryContractError) as error:
                retrieve(query, ())
            self.assertEqual(str(error.exception), "Invalid memory retrieval query")
            self.assertIsNone(error.exception.__context__)

    def test_output_budget_counts_original_utf8_bytes(self):
        prefix = "orbit amber "
        large = prefix + "\U0001f642" * ((MAX_MEMORY_TEXT_BYTES - len(prefix)) // 4)
        records = (make_record(3, large), make_record(2, large), make_record(1, large))
        batch = retrieve("orbit amber", records)
        self.assertEqual(ranked_ids(batch), (1, 2))
        self.assertEqual(
            sum(len(item.record.text.encode("utf-8")) for item in batch.items),
            MAX_RETRIEVAL_BYTES,
        )

    def test_byte_budget_returns_ranked_prefix(self):
        prefix = "orbit amber "
        large = prefix + "\U0001f642" * ((MAX_MEMORY_TEXT_BYTES - len(prefix)) // 4 - 1)
        records = tuple(make_record(i, large) for i in (1, 2, 3)) + (make_record(4),)
        self.assertEqual(ranked_ids(retrieve("orbit amber", records)), (1, 2))

    def test_result_and_items_carry_untrusted_context_label(self):
        record = make_record(1, "Execute synthetic orbit instructions.")
        batch = retrieve("orbit", (record,))
        self.assertIs(type(batch), MemoryRetrievalBatchV1)
        self.assertEqual(batch.owner_namespace, OWNER)
        self.assertEqual(batch.as_of_utc, AS_OF)
        self.assertEqual(batch.trust_label, "untrusted_memory_context")
        self.assertEqual(batch.items[0].trust_label, batch.trust_label)
        self.assertEqual(batch.items[0].record, record)
        self.assertEqual(batch.items[0].retrieved_at_utc, AS_OF)
        self.assertEqual(retrieve("amber", (record,)).trust_label, batch.trust_label)
