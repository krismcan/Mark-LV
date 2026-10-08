"""Phase 8.5 bounded files, atomic replacement ordering and safe failures."""

import ast
import io
import json
from pathlib import Path, PurePath
import tempfile
import traceback
import unittest
from unittest.mock import Mock, patch

from nayeon.brain import connection_persistence as m
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1 as Document
from nayeon.brain.connection_document import provider_connection_document_to_mapping
from nayeon.secrets.contracts import SecretIdentifier


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = "synthetic-private-path-data-marker"
LIMIT = 16384


def configured():
    return Document(connection=ProviderConnectionConfiguration(
        "vendor", "Model Caf\u00e9 / \ub098\uc5f0", SecretIdentifier("unmapped.key")
    ))


class ProviderConnectionPersistenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / (PRIVATE + ".json")
        self.store = m.ProviderConnectionFileStore(self.path)

    def assert_safe_error(self, operation, message):
        with self.assertRaises(m.ProviderConnectionPersistenceError) as caught:
            operation()
        error = caught.exception
        self.assertEqual(str(error), message)
        self.assertIsNone(error.__cause__)
        self.assertTrue(error.__suppress_context__)
        for rendered in (str(error), repr(error), "".join(traceback.format_exception(error))):
            for sensitive in (PRIVATE, str(self.path), "unmapped.key", "Model Caf"):
                self.assertNotIn(sensitive, rendered)
        return error

    def invalid(self):
        return self.assert_safe_error(self.store.load, "Invalid or unreadable provider connection configuration")

    def save_error(self, document=None):
        return self.assert_safe_error(lambda: self.store.save(document or configured()),
                                      "Cannot save provider connection configuration")

    def test_constructor_requires_exact_native_path_and_does_no_io(self):
        class HostilePath:
            def __fspath__(self):
                raise AssertionError("No coercion")

        subclass = type("PathSubclass", (type(self.path),), {})
        for bad in (None, str(self.path), b"file", PurePath("file"), HostilePath(), subclass(self.path)):
            with self.assertRaises(TypeError):
                m.ProviderConnectionFileStore(bad)
        with self.assertRaises(TypeError):
            m.ProviderConnectionFileStore()
        with patch.object(type(self.path), "open", side_effect=AssertionError("No I/O")):
            m.ProviderConnectionFileStore(Path("explicit-relative.json"))
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_missing_file_returns_none_without_creating_file_or_parent(self):
        self.assertIsNone(self.store.load())
        absent = self.directory / "absent" / "connection.json"
        self.assertIsNone(m.ProviderConnectionFileStore(absent).load())
        self.assertFalse(absent.parent.exists())
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_null_and_configured_round_trip_compact_canonical_literal_utf8(self):
        for doc in (Document(), configured()):
            self.assertIsNone(self.store.save(doc))
            self.assertEqual(self.store.load(), doc)
            expected = json.dumps(provider_connection_document_to_mapping(doc), ensure_ascii=False,
                                  allow_nan=False, separators=(",", ":")).encode("utf-8")
            self.assertEqual(self.path.read_bytes(), expected)
            self.assertEqual(set(self.directory.iterdir()), {self.path})
        self.assertIn("Caf\u00e9 / \ub098\uc5f0".encode("utf-8"), self.path.read_bytes())
        self.assertNotIn(b"\\u", self.path.read_bytes())

    def test_invalid_utf8_malformed_json_schema_and_legacy_shapes(self):
        for content in (b"\xff", b"\xef\xbb\xbf{}", b"{", b"", b"null", b"[]", b"{}",
                        b'{"schema_version":true,"connection":null}',
                        b'{"schema_version":2,"connection":null}',
                        b'{"schema_version":1,"connection":null,"extra":"' + PRIVATE.encode() + b'"}',
                        b'{"schema_version":1,"connection":{"provider":"Vendor","model":"m","credential":"key"}}',
                        b'{"schema_version":1,"connection":{"provider":"vendor","model":" m","credential":"key"}}',
                        b'{"schema_version":1,"connection":{"provider":"vendor","model":"m","credential":42}}',
                        b'{"schema_version":1,"connection":{"provider":"vendor","model":"m","credential":"Key"}}',
                        b'{"assistant_name":"legacy"}'):
            with self.subTest(size=len(content)):
                self.path.write_bytes(content)
                self.invalid()
                self.assertEqual(self.path.read_bytes(), content)

    def test_duplicate_keys_rejected_at_top_and_every_nested_key(self):
        for content in (
            b'{"schema_version":1,"schema_version":1,"connection":null}',
            b'{"schema_version":1,"connection":null,"connection":null}',
            b'{"schema_version":1,"connection":{"provider":"v","provider":"v","model":"m","credential":"key"}}',
            b'{"schema_version":1,"connection":{"provider":"v","model":"m","model":"m","credential":"key"}}',
            b'{"schema_version":1,"connection":{"provider":"v","model":"m","credential":"key","credential":"key"}}',
        ):
            self.path.write_bytes(content)
            self.invalid()

    def test_nonstandard_constants_and_recursive_json_rejected(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            for template in ('{"schema_version":%s,"connection":null}',
                             '{"schema_version":1,"connection":{"provider":"v","model":"m","credential":%s}}'):
                self.path.write_bytes((template % constant).encode())
                self.invalid()
        self.path.write_bytes(b"[" * 2000 + b"0" + b"]" * 2000)
        self.invalid()

    def test_exact_size_accepted_and_one_byte_over_rejected_before_decode(self):
        self.assertIs(type(m.MAX_PROVIDER_CONNECTION_FILE_BYTES), int)
        self.assertEqual(m.MAX_PROVIDER_CONNECTION_FILE_BYTES, LIMIT)
        raw = b'{"schema_version":1,"connection":null}'
        bounded = raw + b" " * (LIMIT - len(raw))
        self.path.write_bytes(bounded)
        self.assertEqual(self.store.load(), Document())
        self.path.write_bytes(bounded + b" ")
        with patch.object(m.json, "loads", side_effect=AssertionError("No oversized parsing")):
            self.invalid()

    def test_binary_open_reads_only_limit_plus_one_and_closes(self):
        stream = io.BytesIO(b'{"schema_version":1,"connection":null}')
        with patch.object(type(self.path), "open", return_value=stream) as opened, \
             patch.object(stream, "read", wraps=stream.read) as read:
            self.assertEqual(self.store.load(), Document())
            opened.assert_called_once_with("rb")
            read.assert_called_once_with(LIMIT + 1)
        self.assertTrue(stream.closed)

    def test_open_read_and_close_errors_are_safe_and_suppressed(self):
        for error in (PermissionError(PRIVATE), OSError(PRIVATE), IsADirectoryError(PRIVATE)):
            with patch.object(type(self.path), "open", side_effect=error):
                self.assert_safe_error(self.store.load, "Cannot read provider connection configuration")
        for stage in ("read", "__exit__"):
            stream = Mock()
            stream.__enter__ = Mock(return_value=stream)
            stream.__exit__ = Mock(return_value=False)
            stream.read.return_value = b'{"schema_version":1,"connection":null}'
            getattr(stream, stage).side_effect = OSError(PRIVATE)
            with patch.object(type(self.path), "open", return_value=stream):
                self.invalid()

    def test_decode_parse_type_value_and_recursion_failures_are_safe(self):
        self.path.write_bytes(b'{"schema_version":1,"connection":null}')
        for error in (TypeError(PRIVATE), ValueError(PRIVATE), RecursionError(PRIVATE), UnicodeError(PRIVATE)):
            with patch.object(m, "parse_provider_connection_document", side_effect=error):
                self.invalid()

    def test_save_exact_document_gate_precedes_mapping_and_temp_io(self):
        subclass = type("DocumentSubclass", (Document,), {})
        with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=AssertionError("No I/O")) as temporary, \
             patch.object(m, "provider_connection_document_to_mapping", side_effect=AssertionError("No coercion")):
            for bad in (None, {}, object(), Mock(spec=Document), subclass()):
                with self.assertRaises(TypeError):
                    self.store.save(bad)
            temporary.assert_not_called()

    def test_size_bound_enforced_before_temp_creation(self):
        with patch.object(m, "provider_connection_document_to_mapping", return_value={"huge": "x" * LIMIT}), \
             patch.object(m.tempfile, "NamedTemporaryFile", side_effect=AssertionError("No I/O")) as temporary:
            self.save_error()
            temporary.assert_not_called()

    def test_mapping_json_and_utf8_errors_precede_io_and_are_safe(self):
        for bad in ({"value": float("nan")}, {"value": object()}, {"value": "\ud800"}):
            with patch.object(m, "provider_connection_document_to_mapping", return_value=bad), \
                 patch.object(m.tempfile, "NamedTemporaryFile") as temporary:
                self.save_error()
                temporary.assert_not_called()
        for error in (TypeError(PRIVATE), ValueError(PRIVATE), UnicodeError(PRIVATE)):
            with patch.object(m, "provider_connection_document_to_mapping", side_effect=error):
                self.save_error()

    def test_same_directory_write_flush_fsync_close_before_one_replace(self):
        events = []
        temporary_path = self.directory / "test-temporary.json"
        stream = Mock(name="temporary")
        stream.name = str(temporary_path)
        stream.__enter__ = Mock(return_value=stream)
        stream.__exit__ = Mock(side_effect=lambda *args: events.append("close"))
        stream.write.side_effect = lambda data: events.append("write")
        stream.flush.side_effect = lambda: events.append("flush")
        stream.fileno.return_value = 7
        with patch.object(m.tempfile, "NamedTemporaryFile", return_value=stream) as temporary, \
             patch.object(m.os, "fsync", side_effect=lambda fd: events.append("fsync")) as fsync, \
             patch.object(m.os, "replace", side_effect=lambda *args: events.append("replace")) as replace, \
             patch.object(type(self.path), "unlink") as unlink:
            doc = configured()
            self.store.save(doc)
            temporary.assert_called_once_with(mode="wb", dir=self.path.parent, delete=False)
            fsync.assert_called_once_with(7)
            replace.assert_called_once_with(temporary_path, self.path)
            unlink.assert_called_once_with(missing_ok=True)
            stream.write.assert_called_once_with(json.dumps(provider_connection_document_to_mapping(doc),
                ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8"))
        self.assertEqual(events, ["write", "flush", "fsync", "close", "replace"])

    def test_temp_creation_and_fsync_replace_failure_preserve_destination_cleanup(self):
        self.store.save(Document())
        before = self.path.read_bytes()
        for target in ("tempfile.NamedTemporaryFile", "os.fsync", "os.replace"):
            with patch("nayeon.brain.connection_persistence." + target, side_effect=OSError(PRIVATE)):
                self.save_error()
            self.assertEqual(self.path.read_bytes(), before)
            self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_write_flush_and_close_failure_cleanup_without_replace(self):
        for stage in ("write", "flush", "__exit__"):
            temporary_path = self.directory / "temp.json"
            stream = Mock()
            stream.name = str(temporary_path)
            stream.__enter__ = Mock(return_value=stream)
            stream.__exit__ = Mock(return_value=False)
            stream.fileno.return_value = 7
            getattr(stream, stage).side_effect = OSError(PRIVATE)
            with patch.object(m.tempfile, "NamedTemporaryFile", return_value=stream), \
                 patch.object(m.os, "fsync"), patch.object(m.os, "replace") as replace, \
                 patch.object(type(self.path), "unlink") as unlink:
                self.save_error()
                replace.assert_not_called()
                unlink.assert_called_once_with(missing_ok=True)

    def test_cleanup_failure_neither_masks_failure_nor_undoes_success(self):
        with patch.object(m.os, "replace", side_effect=OSError(PRIVATE)), \
             patch.object(type(self.path), "unlink", side_effect=OSError("cleanup-" + PRIVATE)):
            self.save_error()
        # Remove only this test's abandoned temporary file after the patch ends.
        for path in self.directory.iterdir():
            path.unlink()
        doc = configured()
        with patch.object(type(self.path), "unlink", side_effect=OSError(PRIVATE)):
            self.assertIsNone(self.store.save(doc))
        self.assertEqual(self.store.load(), doc)
        self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_missing_parent_save_does_not_create_directories(self):
        absent = self.directory / "absent" / "file.json"
        store = m.ProviderConnectionFileStore(absent)
        self.assert_safe_error(lambda: store.save(Document()), "Cannot save provider connection configuration")
        self.assertFalse(absent.parent.exists())

    def test_process_control_exceptions_propagate(self):
        for error in (KeyboardInterrupt(), SystemExit()):
            with patch.object(type(self.path), "open", side_effect=error):
                with self.assertRaises(type(error)):
                    self.store.load()
            with patch.object(m.tempfile, "NamedTemporaryFile", side_effect=error):
                with self.assertRaises(type(error)):
                    self.store.save(Document())

    def test_source_exact_imports_and_no_extra_filesystem_authority(self):
        tree = ast.parse((ROOT / "nayeon/brain/connection_persistence.py").read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(n.level == 0 for n in imports if isinstance(n, ast.ImportFrom)))
        self.assertEqual([(n.module if isinstance(n, ast.ImportFrom) else None,
                           [(a.name, a.asname) for a in n.names]) for n in imports], [
            ("__future__", [("annotations", None)]), (None, [("json", None)]), (None, [("os", None)]),
            ("pathlib", [("Path", None)]), (None, [("tempfile", None)]),
            ("nayeon.brain.connection_document", [("ProviderConnectionDocumentV1", None),
                ("parse_provider_connection_document", None), ("provider_connection_document_to_mapping", None)]),
        ])
        self.assertEqual({ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}, {
            "type", "Path", "TypeError", "ValueError", "ProviderConnectionPersistenceError", "len",
            "self._path.open", "stream.read", "json.loads", "content.decode", "parse_provider_connection_document",
            "provider_connection_document_to_mapping", "json.dumps", "json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode",
            "tempfile.NamedTemporaryFile", "stream.write", "stream.flush", "os.fsync", "stream.fileno",
            "os.replace", "temporary_path.unlink",
        })
        docstring = ast.get_docstring(next(n for n in tree.body if isinstance(n, ast.ClassDef)
                                        and n.name == "ProviderConnectionFileStore"))
        for phrase in ("same-directory atomic replace", "fsync and close", "No locking", "last-writer-wins",
                       "directory fsync durability", "caller owns path and filesystem permissions"):
            self.assertIn(phrase, docstring)


if __name__ == "__main__":
    unittest.main()
