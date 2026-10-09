"""Phase 7.3 file semantics, failure isolation, privacy and production boundaries."""

import ast
import json
from pathlib import Path, PurePath
import subprocess
import tempfile
import traceback
import unittest
from unittest.mock import patch

from nayeon.config import persistence as m
from nayeon.config.document import (
    PresentationConfigurationDocumentV1,
    parse_presentation_configuration_document,
    presentation_configuration_document_to_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
# Exact permitted Phase 8.5 + Phase 8.6 non-secret connection modules.
PHASE_8_5_DELTA = {
    "nayeon/brain/connection_document.py", "nayeon/brain/connection_persistence.py",
    "nayeon/brain/connection_service.py", "nayeon/brain/connection_bootstrap.py",
         "nayeon/brain/connection_composition.py", "nayeon/brain/connection_readiness.py",
         "nayeon/brain/connection_startup.py",
         "nayeon/brain/credential_onboarding.py",
         "nayeon/brain/credential_onboarding_composition.py",
         "nayeon/brain/connection_reconciliation.py",
         "nayeon/brain/connection_recovery_advice.py",
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
         "nayeon/brain/onboarding_metadata_document.py",
         "nayeon/brain/onboarding_metadata_review.py",
}
MODULE = "nayeon/config/persistence.py"
SERVICE_MODULE = "nayeon/config/service.py"
BOOTSTRAP_MODULE = "nayeon/config/bootstrap.py"
VIEW_MODULE = "nayeon/config/view.py"
STARTING_HEAD = "35c0246362fbecc3df8532b63d42087b32b22646"
PRODUCT_COMMIT = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
LIMIT = 65536
PRIVATE_VALUE = "PrivatePersonalValueMarker"
PRIVATE_KEY = "PrivateUnknownKeyMarker"


def mapping():
    return presentation_configuration_document_to_mapping(PresentationConfigurationDocumentV1())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class PresentationPersistenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "presentation.json"
        self.store = m.PresentationConfigurationFileStore(self.path)

    def assert_private_error(self, operation):
        with self.assertRaises(m.PresentationConfigurationPersistenceError) as caught:
            operation()
        error = caught.exception
        for text in (str(error), repr(error), "".join(traceback.format_exception(error))):
            self.assertNotIn(PRIVATE_VALUE, text)
            self.assertNotIn(PRIVATE_KEY, text)
        self.assertTrue(error.__suppress_context__)

    def test_explicit_exact_native_path_without_coercion_or_io(self):
        class HostilePath:
            def __fspath__(self):
                raise AssertionError("Must not coerce")

            def __repr__(self):
                raise AssertionError("Must not disclose")

        subclass = type("PathSubclass", (type(self.path),), {})
        for value in (None, str(self.path), b"file", PurePath("file"), HostilePath(), subclass(self.path)):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(TypeError):
                    m.PresentationConfigurationFileStore(value)
        with self.assertRaises(TypeError):
            m.PresentationConfigurationFileStore()
        with patch.object(type(self.path), "open", side_effect=AssertionError("No construction I/O")):
            m.PresentationConfigurationFileStore(Path("explicit-relative.json"))
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_missing_file_is_none_without_creating_parent_or_file(self):
        self.assertIsNone(self.store.load())
        self.assertEqual(list(self.directory.iterdir()), [])
        absent = self.directory / "absent" / "file.json"
        self.assertIsNone(m.PresentationConfigurationFileStore(absent).load())
        self.assertFalse(absent.parent.exists())

    def test_default_document_round_trip(self):
        document = PresentationConfigurationDocumentV1()
        self.assertIsNone(self.store.save(document))
        self.assertEqual(self.store.load(), document)
        self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_unicode_round_trip_and_literal_utf8_without_normalization(self):
        data = mapping()
        data["assistant"] = {"display_name": "\ub098\uc5f0", "wake_name": "Hey \ub098\uc5f0"}
        data["user"]["display_name"] = "E\u0301lodie \U0001f338"
        data["preferences"] = {"personality_ref": "Calm:\u00e9", "voice_ref": "Provider:\u97f3/Case-v1"}
        document = parse_presentation_configuration_document(data)
        self.store.save(document)
        raw = self.path.read_bytes()
        self.assertIn("\ub098\uc5f0".encode("utf-8"), raw)
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(json.loads(raw.decode("utf-8")), data)
        self.assertEqual(self.store.load(), document)

    def test_save_exact_document_rejection_precedes_io(self):
        class HostileValue:
            def __repr__(self):
                raise AssertionError("Must not disclose")

        subclass = type("DocumentSubclass", (PresentationConfigurationDocumentV1,), {})
        for value in (None, mapping(), object(), HostileValue(), subclass()):
            with self.subTest(value_type=type(value).__name__):
                with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=AssertionError("No I/O")):
                    with self.assertRaises(TypeError):
                        self.store.save(value)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_canonical_mapping_encoder_used_and_deterministic_bytes(self):
        document = PresentationConfigurationDocumentV1()
        with patch.object(m, "presentation_configuration_document_to_mapping",
                          wraps=presentation_configuration_document_to_mapping) as encoder:
            self.store.save(document)
            encoder.assert_called_once_with(document)
        first = self.path.read_bytes()
        self.store.save(document)
        self.assertEqual(self.path.read_bytes(), first)
        encoded = json.loads(first.decode("utf-8"))
        self.assertEqual(encoded, mapping())
        self.assertEqual(tuple(encoded), tuple(mapping()))
        for section in ("assistant", "user", "preferences"):
            self.assertEqual(tuple(encoded[section]), tuple(mapping()[section]))

    def test_malformed_json_and_invalid_utf8_fail_closed(self):
        for content in (b"", b"{", b"null trailing", b"// comment", b'{"x":1,}',
                        b"\xff", b"\xc3\x28", b"\xef\xbb\xbf{}",
                        ('{"' + PRIVATE_KEY + '":"' + PRIVATE_VALUE).encode("utf-8")):
            with self.subTest(content_length=len(content)):
                self.path.write_bytes(content)
                self.assert_private_error(self.store.load)

    def test_duplicate_keys_at_root_and_every_nested_section(self):
        raw = json.dumps(mapping(), separators=(",", ":"))
        samples = [raw.replace('"schema_version":1', '"schema_version":1,"schema_version":1')]
        for section in ("assistant", "user", "preferences"):
            key = next(iter(mapping()[section]))
            value = json.dumps(mapping()[section][key])
            token = '"' + key + '":' + value
            # Section substitution avoids the shared display_name spelling.
            section_raw = json.dumps(mapping()[section], separators=(",", ":"))
            samples.append(raw.replace(section_raw, section_raw.replace(token, token + "," + token), 1))
        samples.append('{"' + PRIVATE_KEY + '":1,"' + PRIVATE_KEY + '":"' + PRIVATE_VALUE + '"}')
        # Escaped and literal spellings denote the same JSON key.
        samples.append('{"schema_version":1,"schema_\\u0076ersion":1}')
        for content in samples:
            with self.subTest(length=len(content)):
                self.path.write_text(content, encoding="utf-8")
                self.assert_private_error(self.store.load)

    def test_nonstandard_constants_rejected_before_schema_parser(self):
        for constant in ("NaN", "Infinity", "-Infinity", "undefined", "+Infinity"):
            for raw in (constant, json.dumps(mapping()).replace('"voice_ref": null', '"voice_ref": ' + constant)):
                with self.subTest(constant=constant):
                    self.path.write_text(raw, encoding="utf-8")
                    with patch.object(m, "parse_presentation_configuration_document",
                                      side_effect=AssertionError("Must reject at JSON boundary")):
                        self.assert_private_error(self.store.load)

    def test_excessive_json_nesting_fails_with_bounded_private_error(self):
        self.path.write_bytes(b"[" * 2000 + b"0" + b"]" * 2000)
        self.assert_private_error(self.store.load)

    def test_schema_parser_rejects_all_roots_sections_keys_types_and_versions(self):
        samples = [None, [], True, 1, 1.5, PRIVATE_VALUE]
        for section in (None, "assistant", "user", "preferences"):
            source = mapping() if section is None else mapping()[section]
            for key in source:
                for mode in ("missing", "extra", "replaced"):
                    data = mapping()
                    target = data if section is None else data[section]
                    if mode != "extra":
                        del target[key]
                    if mode != "missing":
                        target[PRIVATE_KEY] = PRIVATE_VALUE
                    samples.append(data)
            if section is not None:
                for value in (None, [], True, PRIVATE_VALUE):
                    data = mapping()
                    data[section] = value
                    samples.append(data)
                for key in source:
                    for value in (True, 1, 1.5, [], {}, " " + PRIVATE_VALUE):
                        data = mapping()
                        data[section][key] = value
                        samples.append(data)
        for version in (True, None, "1", 1.0, 0, -1, 2):
            data = mapping()
            data["schema_version"] = version
            samples.append(data)
        for data in samples:
            self.path.write_bytes(json.dumps(data).encode("utf-8"))
            with patch.object(m, "parse_presentation_configuration_document",
                              wraps=parse_presentation_configuration_document) as parser:
                self.assert_private_error(self.store.load)
                parser.assert_called_once_with(data)

    def test_file_size_boundary_and_oversize_rejected_without_parsing(self):
        self.assertEqual(m.MAX_PRESENTATION_CONFIGURATION_FILE_BYTES, LIMIT)
        raw = json.dumps(mapping()).encode("utf-8")
        for size in (len(raw), LIMIT - 1, LIMIT):
            self.path.write_bytes(raw + b" " * (size - len(raw)))
            self.assertEqual(self.store.load(), PresentationConfigurationDocumentV1())
        self.path.write_bytes(raw + b" " * (LIMIT + 1 - len(raw)))
        with patch.object(m.json, "loads", side_effect=AssertionError("No oversized parsing")):
            self.assert_private_error(self.store.load)

    def test_read_is_bounded_to_limit_plus_one_bytes(self):
        with patch.object(type(self.path), "open") as opened:
            stream = opened.return_value
            stream.read.return_value = b" " * (LIMIT + 1)
            self.assert_private_error(self.store.load)
            opened.assert_called_once_with("rb")
            stream.read.assert_called_once_with(LIMIT + 1)

    def test_load_does_not_write_replace_or_mutate_files(self):
        self.store.save(PresentationConfigurationDocumentV1())
        for raw in (self.path.read_bytes(), b"invalid " + PRIVATE_VALUE.encode()):
            self.path.write_bytes(raw)
            before = self.path.stat()
            with patch.object(m.os, "replace", side_effect=AssertionError("No load writes")), \
                 patch.object(m.tempfile, "NamedTemporaryFile", side_effect=AssertionError("No load writes")):
                if raw.startswith(b"{"):
                    self.store.load()
                else:
                    self.assert_private_error(self.store.load)
            self.assertEqual(self.path.read_bytes(), raw)
            self.assertEqual(self.path.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_file_access_errors_are_not_missing_or_disclosing(self):
        self.path.mkdir()
        self.assert_private_error(self.store.load)
        with patch.object(type(self.path), "open", side_effect=PermissionError(PRIVATE_VALUE + PRIVATE_KEY)):
            self.assert_private_error(self.store.load)
        with patch.object(type(self.path), "open") as opened:
            opened.return_value.__enter__.return_value.read.side_effect = OSError(PRIVATE_VALUE)
            self.assert_private_error(self.store.load)

    def test_atomic_same_directory_replace_after_flush_fsync_and_close(self):
        old = PresentationConfigurationDocumentV1()
        data = mapping()
        data["user"]["display_name"] = "New Name"
        new = parse_presentation_configuration_document(data)
        self.store.save(old)
        original_bytes = self.path.read_bytes()
        real_replace, real_fsync = m.os.replace, m.os.fsync
        real_factory = m.tempfile.NamedTemporaryFile
        events = []

        class RecordingStream:
            def __init__(self, **kwargs):
                self.stream = real_factory(**kwargs)
                self.name = self.stream.name

            def __enter__(self):
                return self

            def write(self, content):
                result = self.stream.write(content)
                events.append("write")
                return result

            def flush(self):
                self.stream.flush()
                events.append("flush")

            def fileno(self):
                return self.stream.fileno()

            def __exit__(self, *args):
                self.stream.close()
                events.append("close")

        def sync(fd):
            self.assertEqual(events, ["write", "flush"])
            # A real fsync operates on the still-open temporary descriptor.
            real_fsync(fd)
            events.append("sync")

        def replace(source, destination):
            self.assertEqual(events, ["write", "flush", "sync", "close"])
            self.assertEqual(Path(source).parent, self.path.parent)
            self.assertNotEqual(Path(source), self.path)
            self.assertEqual(destination, self.path)
            self.assertEqual(self.path.read_bytes(), original_bytes)
            self.assertEqual(json.loads(Path(source).read_bytes()), data)
            real_replace(source, destination)
            events.append("replace")

        with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=RecordingStream), \
             patch.object(m.os, "fsync", side_effect=sync), patch.object(m.os, "replace", side_effect=replace):
            self.store.save(new)
        self.assertEqual(events, ["write", "flush", "sync", "close", "replace"])
        self.assertEqual(self.store.load(), new)
        self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_failed_sync_or_replace_preserves_valid_destination_and_cleans_temp(self):
        document = PresentationConfigurationDocumentV1()
        self.store.save(document)
        previous = self.path.read_bytes()
        for target in ("fsync", "replace"):
            with self.subTest(target=target):
                with patch.object(m.os, target, side_effect=OSError(PRIVATE_VALUE + PRIVATE_KEY)):
                    self.assert_private_error(lambda: self.store.save(document))
                self.assertEqual(self.path.read_bytes(), previous)
                self.assertEqual(self.store.load(), document)
                self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_failed_write_flush_or_close_preserves_destination_and_cleans_temp(self):
        document = PresentationConfigurationDocumentV1()
        self.store.save(document)
        previous = self.path.read_bytes()
        real_factory = m.tempfile.NamedTemporaryFile
        for stage in ("write", "flush", "close"):
            class FailingStream:
                def __init__(self, **kwargs):
                    self.stream = real_factory(**kwargs)
                    self.name = self.stream.name

                def __enter__(self):
                    return self

                def write(self, content):
                    if stage == "write":
                        self.stream.write(content[:3])
                        raise OSError(PRIVATE_VALUE)
                    return self.stream.write(content)

                def flush(self):
                    if stage == "flush":
                        raise OSError(PRIVATE_VALUE)
                    return self.stream.flush()

                def fileno(self):
                    return self.stream.fileno()

                def __exit__(self, *args):
                    self.stream.close()
                    if stage == "close":
                        raise OSError(PRIVATE_VALUE)

            with self.subTest(stage=stage):
                with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=FailingStream):
                    self.assert_private_error(lambda: self.store.save(document))
                self.assertEqual(self.path.read_bytes(), previous)
                self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_failed_creation_does_not_create_directories_or_replace_destination(self):
        document = PresentationConfigurationDocumentV1()
        self.store.save(document)
        previous = self.path.read_bytes()
        with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=OSError(PRIVATE_VALUE)):
            self.assert_private_error(lambda: self.store.save(document))
        self.assertEqual(self.path.read_bytes(), previous)
        absent = self.directory / "absent" / "file.json"
        self.assert_private_error(lambda: m.PresentationConfigurationFileStore(absent).save(document))
        self.assertFalse(absent.parent.exists())

    def test_cleanup_failure_keeps_original_sanitized_error(self):
        document = PresentationConfigurationDocumentV1()
        self.store.save(document)
        previous = self.path.read_bytes()
        with patch.object(m.os, "replace", side_effect=OSError(PRIVATE_VALUE)), \
             patch.object(type(self.path), "unlink", side_effect=OSError(PRIVATE_KEY)):
            self.assert_private_error(lambda: self.store.save(document))
        self.assertEqual(self.path.read_bytes(), previous)
        # The temporary directory fixture cleans the deliberately stranded file.

    def test_unencodable_document_fails_before_io_and_preserves_destination(self):
        self.store.save(PresentationConfigurationDocumentV1())
        previous = self.path.read_bytes()
        data = mapping()
        data["user"]["display_name"] = PRIVATE_VALUE + "\ud800"
        document = parse_presentation_configuration_document(data)
        with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=AssertionError("No I/O")):
            self.assert_private_error(lambda: self.store.save(document))
        self.assertEqual(self.path.read_bytes(), previous)


class PresentationPersistenceBoundaryTests(unittest.TestCase):
    def test_production_dependency_boundary(self):
        tree = ast.parse((ROOT / MODULE).read_text(encoding="utf-8"))
        dependencies = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                dependencies.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                dependencies.add(node.module)
                if node.module == "nayeon.config.document":
                    self.assertEqual({alias.name for alias in node.names}, {
                        "PresentationConfigurationDocumentV1", "parse_presentation_configuration_document",
                        "presentation_configuration_document_to_mapping"})
        self.assertEqual(dependencies, {"__future__", "json", "os", "pathlib", "tempfile", "nayeon.config.document"})
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.ClassDef)],
                         ["PresentationConfigurationPersistenceError", "PresentationConfigurationFileStore"])

    def test_only_approved_service_consumer_without_runtime_wiring(self):
        targets = {"persistence", "nayeon.config.persistence", "PresentationConfigurationFileStore",
                   "PresentationConfigurationPersistenceError", "MAX_PRESENTATION_CONFIGURATION_FILE_BYTES"}
        for path in (ROOT / "nayeon").rglob("*.py"):
            # Bootstrap may construct the store; only service owns load/save.
            # Its exact composition source is frozen by the Phase 7.5 suite.
            if path in (ROOT / MODULE, ROOT / SERVICE_MODULE, ROOT / BOOTSTRAP_MODULE):
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, targets, str(path))
                if isinstance(node, ast.alias):
                    self.assertNotIn(node.name, targets, str(path))
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, targets, str(path))
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, targets, str(path))

    def test_starting_checkpoint_and_exact_production_scope(self):
        # The protected starting checkpoint remains an ancestor across seals.
        self.assertEqual(git("merge-base", STARTING_HEAD, "HEAD").decode().strip(), STARTING_HEAD)
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), PRODUCT_COMMIT)
        changed = set(git("diff", "--name-only", STARTING_HEAD, "--", "nayeon").decode().splitlines())
        untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon").decode().splitlines())
        self.assertEqual(changed | untracked, PHASE_8_5_DELTA)
        self.assertEqual(changed - PHASE_8_5_DELTA, set())
        self.assertEqual(untracked - PHASE_8_5_DELTA, set())
        tracked = git("ls-tree", "-r", "--name-only", STARTING_HEAD, "--", "nayeon").decode().splitlines()
        actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / "nayeon").rglob("*.py")}
        self.assertEqual(actual, {path for path in tracked if path.endswith(".py")} | PHASE_8_5_DELTA)
        for path in tracked:
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                 git("show", STARTING_HEAD + ":" + path).replace(b"\r\n", b"\n"))

    def test_protected_instruction_context_and_script_unchanged(self):
        # Codex handoff is intentionally mutable after a sealed product milestone.
        for path in ("AGENTS.md", "scripts/update_codex_context.py"):
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                             git("show", STARTING_HEAD + ":" + path).replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
