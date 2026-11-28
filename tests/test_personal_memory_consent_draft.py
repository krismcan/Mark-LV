"""Synthetic tests for inert Memory operation previews."""
from dataclasses import FrozenInstanceError, fields, replace
import traceback
import unittest

from nayeon.memory.consent_draft import (
    MemoryClearConsentDraftV1,
    MemoryCorrectConsentDraftV1,
    MemoryRemoveConsentDraftV1,
    MemorySaveConsentDraftV1,
    build_memory_consent_draft_v1,
)
from nayeon.memory.contracts import (
    MAX_MEMORY_TEXT_BYTES,
    MAX_MEMORY_TEXT_CHARS,
    MAX_REVISION,
    MAX_TTL_SECONDS,
    MemoryContractError,
    MemoryDraftV1,
    SourceKind,
)


OWNER = "a" * 32
FOREIGN_OWNER = "b" * 32
CANDIDATE_ID = "c" * 32
RECORD_ID = "d" * 32
TEXT = "synthetic orbit preference"
CAPTURED = 80


def make_candidate(**changes):
    values = {
        "owner_namespace": OWNER,
        "text": TEXT,
        "source": SourceKind.EXPLICIT_USER,
        "source_reference": "human-save",
        "captured_at_utc": CAPTURED,
        "proposed_expires_at_utc": CAPTURED + 60,
    }
    return MemoryDraftV1(**(values | changes))


class PersonalMemoryConsentDraftTests(unittest.TestCase):
    def setUp(self):
        owner = {"owner_namespace": OWNER}
        record = owner | {"record_id": RECORD_ID, "expected_revision": 3}
        self.values = {
            "save": owner | {"candidate_id": CANDIDATE_ID, "candidate": make_candidate()},
            "correct": record | {"text": TEXT},
            "remove": record,
            "clear": owner,
        }

    def build(self, operation, **changes):
        return build_memory_consent_draft_v1(
            operation, self.values[operation] | changes, expected_owner_namespace=OWNER,
        )

    def test_save_uses_existing_candidate_and_requested_expiry(self):
        result = self.build("save")
        self.assertIs(type(result), MemorySaveConsentDraftV1)
        self.assertEqual(result.candidate_id, CANDIDATE_ID)
        self.assertIs(result.candidate, self.values["save"]["candidate"])
        self.assertEqual(result.candidate.proposed_expires_at_utc, CAPTURED + 60)

    def test_correct_and_remove_describe_the_exact_revision(self):
        correct = self.build("correct")
        remove = self.build("remove")
        self.assertIs(type(correct), MemoryCorrectConsentDraftV1)
        self.assertIs(type(remove), MemoryRemoveConsentDraftV1)
        self.assertEqual(correct.text, TEXT)
        self.assertFalse(hasattr(remove, "text"))
        for draft in (correct, remove):
            self.assertEqual((draft.record_id, draft.expected_revision), (RECORD_ID, 3))
        self.assertNotEqual(correct, remove)

    def test_clear_describes_only_the_owner_namespace(self):
        result = self.build("clear")
        self.assertIs(type(result), MemoryClearConsentDraftV1)
        self.assertEqual(result.owner_namespace, OWNER)
        self.assertEqual(tuple(field.name for field in fields(result)), ("owner_namespace",))

    def test_drafts_are_frozen_and_slotted(self):
        for operation in self.values:
            with self.subTest(operation=operation):
                draft = self.build(operation)
                self.assertFalse(hasattr(draft, "__dict__"))
                with self.assertRaises(FrozenInstanceError):
                    draft.owner_namespace = FOREIGN_OWNER
        with self.assertRaises(FrozenInstanceError):
            self.build("save").candidate.text = "changed synthetic text"

    def test_every_operation_rejects_foreign_and_invalid_owner_labels(self):
        for operation, values in self.values.items():
            for owner in (FOREIGN_OWNER, "0" * 32, "a" * 33, True, None):
                with self.subTest(operation=operation, supplied_type=type(owner)):
                    with self.assertRaises(MemoryContractError):
                        self.build(operation, owner_namespace=owner)
                    with self.assertRaises(MemoryContractError):
                        build_memory_consent_draft_v1(
                            operation, values, expected_owner_namespace=owner,
                        )

    def test_save_rejects_conflicting_candidate_owner_even_with_matching_labels(self):
        with self.assertRaises(MemoryContractError):
            self.build("save", candidate=make_candidate(owner_namespace=FOREIGN_OWNER))

    def test_candidate_and_record_identifiers_are_strict(self):
        class StringSubclass(str):
            pass

        for operation, name in (("save", "candidate_id"), ("correct", "record_id"),
                                ("remove", "record_id")):
            for identifier in ("", "0" * 32, "A" * 32, "f" * 1000, [],
                               StringSubclass(RECORD_ID)):
                with self.subTest(operation=operation, supplied_type=type(identifier)):
                    with self.assertRaises(MemoryContractError):
                        self.build(operation, **{name: identifier})

    def test_revision_bounds_match_the_described_operation(self):
        for operation in ("correct", "remove"):
            for revision in (0, -1, MAX_REVISION + 1, True, 3.0, "3"):
                with self.subTest(operation=operation, revision=revision):
                    with self.assertRaises(MemoryContractError):
                        self.build(operation, expected_revision=revision)
            self.assertEqual(self.build(operation, expected_revision=1).expected_revision, 1)
        with self.assertRaises(MemoryContractError):
            self.build("correct", expected_revision=MAX_REVISION)
        self.assertEqual(self.build("correct", expected_revision=MAX_REVISION - 1)
                         .expected_revision, MAX_REVISION - 1)
        self.assertEqual(self.build("remove", expected_revision=MAX_REVISION)
                         .expected_revision, MAX_REVISION)

    def test_save_revalidates_exact_candidate_type_fields_and_retention(self):
        class CandidateSubclass(MemoryDraftV1):
            __slots__ = ()

        limit = make_candidate(proposed_expires_at_utc=CAPTURED + MAX_TTL_SECONDS)
        self.assertIs(self.build("save", candidate=limit).candidate, limit)
        invalid_candidates = [object.__new__(MemoryDraftV1), object.__new__(CandidateSubclass),
                              {"text": TEXT}, None]
        for name, value in (
            ("proposed_expires_at_utc", CAPTURED + MAX_TTL_SECONDS + 1),
            ("proposed_expires_at_utc", CAPTURED),
            ("proposed_expires_at_utc", True),
            ("text", "x" * (MAX_MEMORY_TEXT_CHARS + 1)),
            ("source_reference", "synthetic-model"),
        ):
            candidate = make_candidate()
            object.__setattr__(candidate, name, value)
            invalid_candidates.append(candidate)
        for candidate in invalid_candidates:
            with self.subTest(candidate_type=type(candidate)):
                with self.assertRaises(MemoryContractError):
                    self.build("save", candidate=candidate)

    def test_correct_uses_existing_character_utf8_and_content_limits(self):
        at_char_limit = "x" * MAX_MEMORY_TEXT_CHARS
        at_byte_limit = "\U0001f642" * (MAX_MEMORY_TEXT_BYTES // 4)
        for text in (at_char_limit, at_byte_limit):
            self.assertEqual(self.build("correct", text=text).text, text)
        for text in (at_char_limit + "x", at_byte_limit + "x", b"synthetic text", " ",
                     "a\nsecond line", "e\u0301", "\ud800", "password=synthetic-value"):
            with self.subTest(text_type=type(text)):
                with self.assertRaises(MemoryContractError):
                    self.build("correct", text=text)

    def test_missing_extra_conflicting_and_inappropriate_fields_are_rejected(self):
        for operation, values in self.values.items():
            for missing in values:
                with self.subTest(operation=operation, missing=missing):
                    with self.assertRaises(MemoryContractError):
                        build_memory_consent_draft_v1(
                            operation, {key: val for key, val in values.items() if key != missing},
                            expected_owner_namespace=OWNER,
                        )
        for operation, inappropriate in (
            ("save", {"record_id": RECORD_ID, "expected_revision": 1}),
            ("save", {"proposed_expires_at_utc": CAPTURED + 61}),
            ("correct", {"candidate_id": CANDIDATE_ID}),
            ("correct", {"proposed_expires_at_utc": CAPTURED + 61}),
            ("remove", {"text": None}),
            ("remove", {"approved": True}),
            ("clear", {"record_id": RECORD_ID, "expected_revision": 3}),
            ("clear", {"authorization": None, "epoch": 1}),
        ):
            with self.subTest(operation=operation, fields=tuple(inappropriate)):
                with self.assertRaises(MemoryContractError):
                    self.build(operation, **inappropriate)

    def test_unknown_operations_and_nonexact_field_shapes_are_rejected(self):
        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        clear = self.values["clear"]
        for operation, values in (
            ("Clear", clear), ("approve", clear), (StringSubclass("clear"), clear),
            (None, clear), ("clear", list(clear.items())), ("clear", DictSubclass(clear)),
            ("clear", {StringSubclass("owner_namespace"): OWNER}),
            ("clear", {1: OWNER}), ("clear", {"owner": OWNER}),
            ("clear", {str(key): OWNER for key in range(1000)}),
        ):
            with self.assertRaises(MemoryContractError):
                build_memory_consent_draft_v1(operation, values, expected_owner_namespace=OWNER)

    def test_descriptions_have_only_data_fields_and_leave_inputs_untouched(self):
        for operation, values in self.values.items():
            with self.subTest(operation=operation):
                before = values.copy()
                draft = build_memory_consent_draft_v1(
                    operation, values, expected_owner_namespace=OWNER,
                )
                self.assertEqual(values, before)
                self.assertEqual({field.name for field in fields(draft)}, before.keys())
                for name in ("approve", "approved", "execute", "receipt", "authorization",
                             "verified", "persist", "token", "session_identity", "epoch"):
                    self.assertFalse(hasattr(draft, name))
                self.assertEqual(draft, replace(draft))
                values["owner_namespace"] = FOREIGN_OWNER
                self.assertEqual(draft.owner_namespace, OWNER)
                display = repr(draft)
                for value in (TEXT, OWNER, CANDIDATE_ID, RECORD_ID):
                    self.assertNotIn(value, display)

    def test_errors_omit_rejected_keys_values_and_exception_context(self):
        marker = "synthetic-private-marker"
        for operation, values in (
            (marker, self.values["clear"]),
            ("clear", {marker: OWNER}),
            ("clear", {"owner_namespace": marker}),
            ("correct", self.values["correct"] | {"text": marker + "\ud800"}),
            ("save", self.values["save"] | {"candidate": object.__new__(MemoryDraftV1)}),
        ):
            with self.assertRaises(MemoryContractError) as caught:
                build_memory_consent_draft_v1(operation, values, expected_owner_namespace=OWNER)
            error = caught.exception
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
            self.assertTrue(error.__suppress_context__)
            rendered = "".join(traceback.format_exception(error))
            for value in (marker, OWNER, CANDIDATE_ID, RECORD_ID, TEXT):
                self.assertNotIn(value, rendered)

    def test_direct_construction_and_replacement_validate_values(self):
        with self.assertRaises(MemoryContractError):
            MemoryClearConsentDraftV1(owner_namespace=None)
        with self.assertRaises(MemoryContractError):
            replace(self.build("save"), owner_namespace=FOREIGN_OWNER)
        with self.assertRaises(MemoryContractError):
            replace(self.build("correct"), text=object())
        with self.assertRaises(MemoryContractError):
            replace(self.build("remove"), expected_revision=True)
