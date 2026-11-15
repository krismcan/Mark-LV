"""P240 synthetic equality adversaries only; no product or original test imports."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import p240_g1_safe_transport as candidate


class WitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = candidate.load_original(Path(__file__).resolve().parents[1])

    def setUp(self):
        self.value = {"head": candidate.SOURCE,
                      "raw_tracked_sha256": {"synthetic": "a" * 64},
                      "historical_tags": {"synthetic": ("b" * 40, "c" * 40)},
                      "hook_free_methods": {"synthetic": ["synthetic.method"]}}
        self.raw = self.original.canonical(self.value)
        self.digest = candidate.sha(self.raw)
        self.verifier = mock.Mock(return_value=copy.deepcopy(self.value))
        self.api = types.SimpleNamespace(canonical=self.original.canonical,
                                         verify_source=self.verifier)

    def compare(self, raw=None, value=None, digest=None):
        return candidate.compare_witness(
            self.api, self.raw if raw is None else raw,
            self.digest if digest is None else digest,
            self.value if value is None else value)

    def test_identical_serialized_witnesses(self):
        report = self.compare()
        self.assertTrue(report["canonical_bytes_equal"])
        self.assertEqual(report["before_sha256"], report["after_sha256"])
        self.assertEqual(report["release"], "HOLD")
        self.assertFalse(report["g1_executed"])
        self.assertFalse(report["additional_transport_admitted"])

    def test_original_tuple_list_mismatch_reproduced_and_corrected(self):
        decoded = json.loads(self.raw)
        self.assertNotEqual(self.value, decoded)  # P239's actual bad comparison
        self.assertEqual(self.original.canonical(decoded), self.raw)
        self.assertTrue(self.compare(value=decoded)["canonical_bytes_equal"])

    def test_noncanonical_byte_change_rejected_even_with_new_hash(self):
        changed = self.raw + b"\n"
        with self.assertRaisesRegex(RuntimeError, "NONCANONICAL_WITNESS"):
            self.compare(raw=changed, digest=candidate.sha(changed))

    def test_byte_change_rejected_against_frozen_original_hash(self):
        with self.assertRaisesRegex(RuntimeError, "BEFORE_SHA256"):
            self.compare(raw=self.raw.replace(b"synthetic", b"altered", 1))

    def test_json_structural_tamper_rejected_even_with_matching_input_hash(self):
        changed = copy.deepcopy(self.value)
        changed["historical_tags"]["synthetic"] = ["d" * 40, "c" * 40]
        raw = self.original.canonical(changed)
        with self.assertRaisesRegex(RuntimeError, "SOURCE_WITNESS_BYTES_CHANGED"):
            self.compare(raw=raw, digest=candidate.sha(raw))

    def test_missing_witness_bytes(self):
        for raw in (b"", None, "text", bytearray(self.raw)):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(RuntimeError):
                candidate.revalidate_source(self.api, Path("unused"), raw, self.digest)
        self.verifier.assert_not_called()

    def test_missing_witness_file(self):
        with tempfile.TemporaryDirectory(prefix="p240-synthetic-") as directory:
            with self.assertRaises(FileNotFoundError):
                candidate.reconcile_file(self.api, Path("unused"),
                                         Path(directory) / "absent.json", self.digest)
        self.verifier.assert_not_called()

    def test_no_stale_positive_across_fresh_source_verifications(self):
        changed = copy.deepcopy(self.value)
        changed["raw_tracked_sha256"]["synthetic"] = "e" * 64
        self.verifier.side_effect = [self.value, changed, RuntimeError("synthetic refusal")]
        source = Path("unused")
        self.assertTrue(candidate.revalidate_source(
            self.api, source, self.raw, self.digest)["canonical_bytes_equal"])
        with self.assertRaisesRegex(RuntimeError, "SOURCE_WITNESS_BYTES_CHANGED"):
            candidate.revalidate_source(self.api, source, self.raw, self.digest)
        with self.assertRaisesRegex(RuntimeError, "synthetic refusal"):
            candidate.revalidate_source(self.api, source, self.raw, self.digest)
        self.assertEqual(self.verifier.call_args_list, [mock.call(source)] * 3)

    def test_no_stale_positive_after_before_file_changes(self):
        with tempfile.TemporaryDirectory(prefix="p240-synthetic-") as directory:
            path = Path(directory) / "source-before.json"
            path.write_bytes(self.raw)
            self.assertTrue(candidate.reconcile_file(
                self.api, Path("unused"), path, self.digest)["canonical_bytes_equal"])
            path.write_bytes(self.raw + b" ")
            with self.assertRaisesRegex(RuntimeError, "BEFORE_SHA256"):
                candidate.reconcile_file(self.api, Path("unused"), path, self.digest)
        self.assertEqual(self.verifier.call_count, 1)

    def test_before_file_mutation_during_parent_verification_rejected(self):
        with tempfile.TemporaryDirectory(prefix="p240-synthetic-") as directory:
            path = Path(directory) / "source-before.json"
            path.write_bytes(self.raw)
            def mutate(_source):
                path.write_bytes(self.raw + b" ")
                return self.value
            self.verifier.side_effect = mutate
            with self.assertRaisesRegex(RuntimeError, "BEFORE_FILE_CHANGED_DURING_REVALIDATION"):
                candidate.reconcile_file(self.api, Path("unused"), path, self.digest)

    def test_foreign_before_source_rejected(self):
        changed = dict(self.value, head="f" * 40)
        raw = self.original.canonical(changed)
        with self.assertRaisesRegex(RuntimeError, "WITNESS_SOURCE_IDENTITY"):
            self.compare(raw=raw, digest=candidate.sha(raw), value=changed)

    def test_fresh_foreign_source_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "SOURCE_WITNESS_BYTES_CHANGED"):
            self.compare(value=dict(self.value, head="f" * 40))

    def test_duplicate_json_key_rejected(self):
        raw = self.raw.replace(b'{\n', b'{\n  "head": "forged",\n', 1)
        with self.assertRaisesRegex(RuntimeError, "DUPLICATE_KEY"):
            self.compare(raw=raw, digest=candidate.sha(raw))

    def test_missing_or_extra_structural_field_rejected(self):
        for name in candidate.WITNESS_KEYS:
            changed = dict(self.value)
            del changed[name]
            raw = self.original.canonical(changed)
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "WITNESS_SOURCE_IDENTITY"):
                self.compare(raw=raw, digest=candidate.sha(raw))
        raw = self.original.canonical(dict(self.value, extra=True))
        with self.assertRaisesRegex(RuntimeError, "WITNESS_SOURCE_IDENTITY"):
            self.compare(raw=raw, digest=candidate.sha(raw))

    def test_noncanonical_json_and_malformed_json_rejected(self):
        for raw in (b"null", b"{", b"[]", self.raw.replace(b"\n", b"\r\n"), b"\xff"):
            with self.subTest(raw_sha=candidate.sha(raw)), self.assertRaises(
                    (RuntimeError, ValueError, UnicodeError)):
                self.compare(raw=raw, digest=candidate.sha(raw))

    def test_resource_cap_rejected_before_source_work(self):
        with self.assertRaisesRegex(RuntimeError, "MISSING_OR_OVERSIZED_WITNESS"):
            candidate.revalidate_source(self.api, Path("unused"),
                                        b"x" * (candidate.LIMIT + 1), self.digest)
        self.verifier.assert_not_called()

    def test_independent_sha_required(self):
        for digest in ("0" * 64, None, "", self.digest.upper(), "g" * 64):
            with self.subTest(digest=digest), self.assertRaisesRegex(RuntimeError, "BEFORE_SHA256"):
                candidate.compare_witness(self.api, self.raw, digest, self.value)

    def test_exclusive_producer_and_original_canonical_serializer(self):
        with tempfile.TemporaryDirectory(prefix="p240-synthetic-") as directory:
            path = Path(directory) / "source-before.json"
            self.assertEqual(candidate.capture_before(self.api, Path("unused"), path), self.digest)
            self.assertEqual(path.read_bytes(), self.raw)
            with self.assertRaises(FileExistsError):
                candidate.capture_before(self.api, Path("unused"), path)

    def test_original_verifier_failure_is_not_equality(self):
        self.verifier.side_effect = RuntimeError("synthetic refusal")
        with self.assertRaisesRegex(RuntimeError, "synthetic refusal"):
            candidate.revalidate_source(self.api, Path("unused"), self.raw, self.digest)


class GuardTests(unittest.TestCase):
    def test_exact_four_additions_and_one_parent(self):
        rows = ["A\t" + path for path in candidate.ADDITIONS]
        candidate.check_delta([candidate.PARENT], rows)
        cases = [([], rows), (["0" * 40], rows),
                 ([candidate.PARENT, "0" * 40], rows),
                 ([candidate.PARENT], rows[:-1]),
                 ([candidate.PARENT], rows + ["A\textra"]),
                 ([candidate.PARENT], [rows[0].replace("A\t", "M\t")] + rows[1:]),
                 ([candidate.PARENT], rows + rows[:1])]
        for parents, changed in cases:
            with self.subTest(parents=parents, rows=changed), self.assertRaises(RuntimeError):
                candidate.check_delta(parents, changed)

    def test_every_dependency_raw_byte_pin_and_tamper(self):
        root = Path(__file__).resolve().parents[1]
        for path in candidate.PINS:
            raw = (root / path).read_bytes()
            self.assertIs(candidate.authenticate(path, raw), raw)
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, "RAW_SOURCE_PIN"):
                candidate.authenticate(path, raw + b"tamper")

    def test_host_guard_cannot_be_used_as_local_bypass(self):
        with mock.patch.dict(candidate.os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch"}):
            with self.assertRaisesRegex(RuntimeError, "HOST_IDENTITY"):
                candidate.provenance(Path(__file__).resolve().parents[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (WitnessTests, GuardTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    code = 0 if result.wasSuccessful() and result.testsRun == 22 and not result.skipped else 1
    if args.report:
        report = {"schema": 240, "scope": "SYNTHETIC ONLY", "tests_run": result.testsRun,
                  "failures": len(result.failures), "errors": len(result.errors),
                  "skips": len(result.skipped), "native_exit": code, "release": "HOLD",
                  "g1_executed": False, "additional_transport_admitted": False}
        args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
