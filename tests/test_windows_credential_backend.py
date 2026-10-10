"""Phase 8.1 deterministic fake-native behavior, ABI and isolation guards.

No test instantiates the real DLL or accesses the host credential set.
"""

import ast
import ctypes
from pathlib import Path
import runpy
import subprocess
import traceback
import unittest
from unittest.mock import patch

from nayeon.secrets import windows_credential as m
from nayeon.secrets.contracts import SecretIdentifier, SecretValue, SecretNotFoundError, SecretStorageError


ROOT = Path(__file__).resolve().parents[1]
START = "35c0246362fbecc3df8532b63d42087b32b22646"
SEALED = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
PHASE_8_5_DELTA = {"nayeon/brain/connection_document.py", "nayeon/brain/connection_persistence.py",
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
         "nayeon/brain/onboarding_metadata_change_preview.py",
         "nayeon/brain/onboarding_operation_advice.py",
         "nayeon/brain/onboarding_review_session.py",
         "nayeon/brain/credential_operation_host.py",
         "nayeon/brain/first_run_summary.py",
         "nayeon/brain/first_run_refresh.py",
         "nayeon/desktop_alpha/first_run_status_window.py",
         "nayeon/desktop_alpha/first_run_review_window.py",
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py",
         "nayeon/desktop_alpha/notepad.py"}
TARGET = "nayeon-v1/secret/openai.api_key"
FAILURE = "Secret storage operation failed"


class FakeNative:
    def __init__(self):
        self.blobs = {}
        self.calls = []

    def read(self, target):
        self.calls.append(("read", target))
        return self.blobs.get(target)

    def contains(self, target):
        self.calls.append(("contains", target))
        return target in self.blobs

    def write(self, target, blob, credential_type, persist, username):
        self.calls.append(("write", target, blob, credential_type, persist, username))
        self.blobs[target] = blob

    def delete(self, target):
        self.calls.append(("delete", target))
        return self.blobs.pop(target, None) is not None


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.native = FakeNative()
        self.backend = m.WindowsCredentialBackend(_native=self.native)
        self.identifier = SecretIdentifier("openai.api_key")

    def test_constructor_has_no_io_or_native_setup(self):
        self.assertEqual(self.native.calls, [])
        with patch.object(m, "_load_advapi32", side_effect=AssertionError("no setup")) as loader:
            m.WindowsCredentialBackend()
            loader.assert_not_called()

    def test_import_safe_without_windows_loader(self):
        # Even on Windows, this import-only test cannot reach Advapi32.
        with patch.object(ctypes, "WinDLL", side_effect=AssertionError("no native setup"), create=True) as loader:
            namespace = runpy.run_path(str(ROOT / "nayeon/secrets/windows_credential.py"))
            namespace["WindowsCredentialBackend"]()
            loader.assert_not_called()

    def test_exact_types_before_native_access(self):
        class IdentifierSubclass(SecretIdentifier):
            pass
        class ValueSubclass(SecretValue):
            pass
        for value in ("openai.api_key", None, {"value": "openai.api_key"},
                      IdentifierSubclass("openai.api_key")):
            for operation in (self.backend.get, self.backend.delete, self.backend.is_available):
                with self.assertRaises(TypeError):
                    operation(value)
            with self.assertRaises(TypeError):
                self.backend.put(value, SecretValue("synthetic"))
        for value in ("synthetic", None, b"synthetic", ValueSubclass("synthetic")):
            with self.assertRaises(TypeError):
                self.backend.put(self.identifier, value)
        self.assertEqual(self.native.calls, [])

    def test_exact_utf8_metadata_and_replacement(self):
        text = " \nsynthetic 한글🌸E\u0301\x00tail\t "
        self.assertIsNone(self.backend.put(self.identifier, SecretValue(text)))
        self.assertEqual(self.native.calls, [("write", TARGET, text.encode("utf-8"), 1, 2, "nayeon-v1")])
        self.assertEqual(self.backend.get(self.identifier).reveal(), text)
        self.backend.put(self.identifier, SecretValue("replacement"))
        self.assertEqual(self.backend.get(self.identifier).reveal(), "replacement")

    def test_provider_neutral_exact_namespace(self):
        for name in ("openai.api_key", "anthropic.api_key", "google.api_key", "custom-provider.key"):
            identifier = SecretIdentifier(name)
            self.backend.put(identifier, SecretValue("synthetic"))
            self.backend.get(identifier)
            self.backend.is_available(identifier)
            self.backend.delete(identifier)
            self.assertTrue(all(call[1] == "nayeon-v1/secret/" + name for call in self.native.calls[-4:]))

    def test_2560_byte_limit_before_write_or_setup(self):
        for text in ("a" * 2560, "é" * 1280):
            self.backend.put(self.identifier, SecretValue(text))
            self.assertEqual(len(self.native.blobs[TARGET]), 2560)
        calls = list(self.native.calls)
        for text in ("a" * 2561, "é" * 1280 + "a", "a\ud800"):
            with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                self.backend.put(self.identifier, SecretValue(text))
        self.assertEqual(self.native.calls, calls)
        with patch.object(m, "_load_advapi32") as loader:
            with self.assertRaises(SecretStorageError):
                m.WindowsCredentialBackend().put(self.identifier, SecretValue("a" * 2561))
            loader.assert_not_called()

    def test_missing_and_delete_semantics(self):
        with self.assertRaisesRegex(SecretNotFoundError, "^Secret is not available$"):
            self.backend.get(self.identifier)
        self.assertFalse(self.backend.delete(self.identifier))
        self.backend.put(self.identifier, SecretValue("synthetic"))
        self.assertTrue(self.backend.delete(self.identifier))
        self.assertFalse(self.backend.delete(self.identifier))

    def test_malformed_stored_values_fail_safely(self):
        for blob in (b"\xffsynthetic-marker", b"", b" \n\t", b"a" * 2561, "synthetic-marker"):
            self.native.blobs[TARGET] = blob
            with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                self.backend.get(self.identifier)

    def test_presence_never_reads_decodes_or_constructs_secret(self):
        self.native.blobs[TARGET] = b"\xff"  # Present even when unreadable.
        with patch.object(self.native, "read", side_effect=AssertionError("no read")), \
                patch.object(m, "SecretValue", side_effect=AssertionError("no value")):
            self.assertTrue(self.backend.is_available(self.identifier))
            self.assertFalse(self.backend.is_available(SecretIdentifier("absent")))
        self.assertEqual(self.native.calls, [("contains", TARGET), ("contains", "nayeon-v1/secret/absent")])

    def test_native_failures_have_fixed_redacted_tracebacks(self):
        value = SecretValue("synthetic-marker")
        for method, operation in (("read", lambda: self.backend.get(self.identifier)),
                                  ("write", lambda: self.backend.put(self.identifier, value)),
                                  ("delete", lambda: self.backend.delete(self.identifier)),
                                  ("contains", lambda: self.backend.is_available(self.identifier))):
            with patch.object(self.native, method, side_effect=OSError(TARGET + " synthetic-marker")):
                try:
                    operation()
                except SecretStorageError as error:
                    self.assertEqual(str(error), FAILURE)
                    self.assertEqual(repr(error), "SecretStorageError('" + FAILURE + "')")
                    rendered = "".join(traceback.format_exception(error))
                    self.assertNotIn(TARGET, rendered)
                    self.assertNotIn("synthetic-marker", rendered)
                else:
                    self.fail("Expected storage error")

    def test_unavailable_setup_fails_closed_for_each_operation(self):
        with patch.object(m, "_load_advapi32", side_effect=OSError("unstable details")):
            backend = m.WindowsCredentialBackend()
            for operation in (lambda: backend.get(self.identifier), lambda: backend.delete(self.identifier),
                              lambda: backend.is_available(self.identifier),
                              lambda: backend.put(self.identifier, SecretValue("synthetic"))):
                with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                    operation()

    def test_backend_public_surface_is_narrow(self):
        self.assertEqual({name for name in vars(m.WindowsCredentialBackend) if not name.startswith("_")},
                         {"get", "put", "delete", "is_available"})
        self.backend.put(self.identifier, SecretValue("synthetic-marker"))
        self.assertNotIn("synthetic-marker", repr(self.backend))
        self.assertNotIn("synthetic-marker", str(self.backend))


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *args):
        return self.callback(*args)


class FakeDLL:
    """ctypes-compatible in-memory pointers, with explicit acquisition/free log."""
    def __init__(self, blob=b"synthetic\x00tail", size=None, null_blob=False):
        self.buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        self.credential = m._CREDENTIALW()
        self.credential.CredentialBlobSize = len(blob) if size is None else size
        if not null_blob:
            self.credential.CredentialBlob = ctypes.cast(self.buffer, ctypes.POINTER(ctypes.c_ubyte))
        self.pointer = ctypes.pointer(self.credential)
        self.events = []
        self.read_result = 1
        self.write_result = 1
        self.delete_result = 1
        self.CredReadW = FakeFunction(self.read)
        self.CredWriteW = FakeFunction(self.write)
        self.CredDeleteW = FakeFunction(self.delete)
        self.CredFree = FakeFunction(self.free)

    def read(self, target, kind, flags, output):
        self.events.append(("read", target, kind, flags))
        if self.read_result:
            ctypes.cast(output, ctypes.POINTER(m._PCREDENTIALW))[0] = self.pointer
        return self.read_result

    def write(self, pointer, flags):
        value = ctypes.cast(pointer, m._PCREDENTIALW).contents
        self.events.append(("write", value.TargetName, value.Type, value.Persist, value.UserName,
                            value.Flags, value.AttributeCount, flags,
                            ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize)))
        return self.write_result

    def delete(self, target, kind, flags):
        self.events.append(("delete", target, kind, flags))
        return self.delete_result

    def free(self, pointer):
        self.events.append(("free", ctypes.cast(pointer, ctypes.c_void_p).value))


class NativeAdapterTests(unittest.TestCase):
    def adapter(self, dll):
        with patch.object(m, "_load_advapi32", return_value=dll):
            return m._Advapi32Adapter()

    def test_credential_layout_and_api_declarations(self):
        dll = FakeDLL()
        self.adapter(dll)
        pointer = m._PCREDENTIALW
        self.assertEqual(dll.CredReadW.argtypes,
                         [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(pointer)])
        self.assertEqual(dll.CredWriteW.argtypes, [pointer, ctypes.c_uint32])
        self.assertEqual(dll.CredDeleteW.argtypes, [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32])
        self.assertEqual(dll.CredFree.argtypes, [ctypes.c_void_p])
        for method in (dll.CredReadW, dll.CredWriteW, dll.CredDeleteW):
            self.assertIs(method.restype, ctypes.c_int32)
        self.assertIsNone(dll.CredFree.restype)
        self.assertEqual([name for name, _ in m._CREDENTIALW._fields_],
                         ["Flags", "Type", "TargetName", "Comment", "LastWritten", "CredentialBlobSize",
                          "CredentialBlob", "Persist", "AttributeCount", "Attributes", "TargetAlias", "UserName"])
        offsets = ([0, 4, 8, 16, 24, 32, 40, 48, 52, 56, 64, 72]
                   if ctypes.sizeof(ctypes.c_void_p) == 8 else
                   [0, 4, 8, 12, 16, 24, 28, 32, 36, 40, 44, 48])
        self.assertEqual([getattr(m._CREDENTIALW, name).offset for name, _ in m._CREDENTIALW._fields_], offsets)
        self.assertEqual(ctypes.sizeof(m._CREDENTIALW), 80 if ctypes.sizeof(ctypes.c_void_p) == 8 else 52)

    def test_native_read_copies_exact_size_before_single_free(self):
        dll = FakeDLL(blob=b"abc\x00tail-ignored", size=8)
        adapter = self.adapter(dll)
        original = ctypes.string_at
        def copy(pointer, size):
            self.assertEqual(len(dll.events), 1)
            self.assertEqual(size, 8)
            return original(pointer, size)
        with patch.object(m.ctypes, "string_at", side_effect=copy):
            self.assertEqual(adapter.read(TARGET), b"abc\x00tail")
        self.assertEqual(dll.events, [("read", TARGET, 1, 0),
                                     ("free", ctypes.cast(dll.pointer, ctypes.c_void_p).value)])

    def test_native_read_invalid_blob_and_copy_failure_still_free_once(self):
        for dll in (FakeDLL(size=0), FakeDLL(size=2561), FakeDLL(null_blob=True)):
            adapter = self.adapter(dll)
            with self.assertRaises(SecretStorageError):
                adapter.read(TARGET)
            self.assertEqual([event[0] for event in dll.events], ["read", "free"])
        dll = FakeDLL()
        with patch.object(m.ctypes, "string_at", side_effect=RuntimeError("synthetic")):
            with self.assertRaises(RuntimeError):
                self.adapter(dll).read(TARGET)
        self.assertEqual([event[0] for event in dll.events], ["read", "free"])

    def test_presence_frees_without_copy_or_blob_inspection(self):
        dll = FakeDLL(size=999999, null_blob=True)
        with patch.object(m.ctypes, "string_at", side_effect=AssertionError("no copy")):
            self.assertTrue(self.adapter(dll).contains(TARGET))
        self.assertEqual([event[0] for event in dll.events], ["read", "free"])
        # Freeze the absence of pointer dereferencing as well as blob copying.
        tree = ast.parse((ROOT / "nayeon/secrets/windows_credential.py").read_text(encoding="utf-8"))
        method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "contains")
        self.assertFalse(any(isinstance(node, ast.Attribute) and node.attr in
                             {"contents", "CredentialBlob", "CredentialBlobSize", "decode"}
                             for node in ast.walk(method)))

    def test_backend_native_read_decode_failure_releases_buffer(self):
        dll = FakeDLL(blob=b"\xffsynthetic")
        backend = m.WindowsCredentialBackend(_native=self.adapter(dll))
        with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
            backend.get(SecretIdentifier("openai.api_key"))
        self.assertEqual([event[0] for event in dll.events], ["read", "free"])

    def test_missing_and_native_error_mapping_no_free_on_failed_read(self):
        for error in (1168, 5, 1312):
            dll = FakeDLL()
            dll.read_result = dll.delete_result = 0
            adapter = self.adapter(dll)
            with patch.object(m.ctypes, "get_last_error", return_value=error, create=True):
                if error == 1168:
                    self.assertIsNone(adapter.read(TARGET))
                    self.assertFalse(adapter.contains(TARGET))
                    self.assertFalse(adapter.delete(TARGET))
                else:
                    for operation in (adapter.read, adapter.contains, adapter.delete):
                        with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                            operation(TARGET)
            self.assertNotIn("free", [event[0] for event in dll.events])

    def test_native_write_fields_and_cleanup_on_success_or_failure(self):
        for result in (1, 0):
            dll = FakeDLL()
            dll.write_result = result
            adapter = self.adapter(dll)
            original = ctypes.memset
            cleaned = []
            def zero(buffer, value, count):
                answer = original(buffer, value, count)
                cleaned.append(bytes(buffer))
                return answer
            with patch.object(m.ctypes, "memset", side_effect=zero):
                if result:
                    adapter.write(TARGET, b"a\x00b", 1, 2, "nayeon-v1")
                else:
                    with self.assertRaises(SecretStorageError):
                        adapter.write(TARGET, b"a\x00b", 1, 2, "nayeon-v1")
            self.assertEqual(dll.events, [("write", TARGET, 1, 2, "nayeon-v1", 0, 0, 0, b"a\x00b")])
            self.assertEqual(cleaned, [b"\x00\x00\x00"])

    def test_native_delete_success_uses_generic_and_zero_flags(self):
        dll = FakeDLL()
        self.assertTrue(self.adapter(dll).delete(TARGET))
        self.assertEqual(dll.events, [("delete", TARGET, 1, 0)])


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class ScopeGuards(unittest.TestCase):
    def assert_frozen(self, path, baseline):
        self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                         git("show", baseline + ":" + path).replace(b"\r\n", b"\n"), path)

    def test_exact_phase_8_3_delta_and_other_production_frozen(self):
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        # The protected starting checkpoint remains an ancestor across seals.
        self.assertEqual(git("merge-base", START, "HEAD").decode().strip(), START)
        self.assertEqual(git("cat-file", "-t", TAG).decode().strip(), "tag")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), SEALED)
        for baseline in (START, SEALED):
            changed = set(git("diff", "--name-only", baseline, "--", "nayeon").decode().splitlines())
            untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon").decode().splitlines())
            self.assertEqual(changed | untracked, PHASE_8_5_DELTA)
            tracked = git("ls-tree", "-r", "--name-only", baseline, "--", "nayeon").decode().splitlines()
            actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / "nayeon").rglob("*.py")}
            self.assertEqual(actual, {path for path in tracked if path.endswith(".py")} | PHASE_8_5_DELTA)
            for path in tracked:
                with self.subTest(baseline=baseline, path=path):
                    self.assert_frozen(path, baseline)

    def test_protected_files_dependencies_and_legacy_unchanged(self):
        # Codex handoff is intentionally mutable after a sealed product milestone.
        for path in ("AGENTS.md", "scripts/update_codex_context.py",
                     "setup.py", "main.py", "ui.py"):
            self.assert_frozen(path, START)
        for directory in ("actions", "core", "dashboard", "plugins", "memory"):
            for path in git("ls-tree", "-r", "--name-only", START, "--", directory).decode().splitlines():
                self.assert_frozen(path, START)

    def test_exact_import_boundaries_and_no_forbidden_native_calls(self):
        allowed = {
            "nayeon/secrets/contracts.py": {"__future__", "dataclasses", "typing"},
            "nayeon/secrets/windows_credential.py": {"__future__", "ctypes", "nayeon.secrets.contracts"},
        }
        for path, permitted in allowed.items():
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 0)
                    imports.add(node.module)
                elif isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, {"print", "open", "__import__", "eval", "exec"})
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, {"CredEnumerate", "CredEnumerateW", "CredEnumerateA", "FormatError"})
            self.assertEqual(imports, permitted)

    def test_only_approved_secret_consumers_and_legacy_store_unused(self):
        old_consumers = set()
        new_symbols = {"SecretIdentifier", "SecretValue", "SecretBackend", "WindowsCredentialBackend",
                       "SecretStorageError", "contracts", "windows_credential"}
        for path in (ROOT / "nayeon").rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "nayeon.secrets.store":
                    old_consumers.add(relative)
                if relative in {"nayeon/brain/connection_document.py",
                               "nayeon/brain/providers/openai_client.py", "nayeon/brain/providers/openai_validation.py",
                               "nayeon/secrets/lifecycle.py", "nayeon/brain/connection.py", "nayeon/secrets/contracts.py", "nayeon/secrets/windows_credential.py",
                                                   "nayeon/secrets/resolver.py", "nayeon/brain/providers/openai.py"}:
                    continue
                if relative in {"nayeon/brain/credential_onboarding.py",
                                "nayeon/brain/credential_onboarding_composition.py"}:
                    # Phase 8.8 credential onboarding only. Canonical contracts
                    # and bound lifecycle allowed; no native or legacy store.
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "nayeon.secrets.contracts":
                            expected = ({"SecretBackend", "SecretIdentifier"}
                                        if relative.endswith("composition.py")
                                        else {"SecretIdentifier", "SecretNotFoundError",
                                              "SecretStorageError", "SecretValue"})
                            self.assertEqual({a.name for a in node.names}, expected)
                        self.assertNotIn(node.module, {"nayeon.secrets.windows_credential",
                                                       "nayeon.secrets.store"})
                    elif isinstance(node, ast.Import):
                        self.assertFalse({a.name for a in node.names} &
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store"})
                    elif isinstance(node, (ast.Name, ast.Attribute)):
                        forbidden = {"WindowsCredentialBackend", "SecretStore"}
                        if relative == "nayeon/brain/credential_onboarding_composition.py":
                            forbidden |= {"SecretValue", "SecretStorageError",
                                          "SecretNotFoundError"}
                        self.assertNotIn(node.id if isinstance(node, ast.Name)
                                         else node.attr, forbidden)
                    continue
                if relative == "nayeon/brain/onboarding_metadata_document.py":
                    # Phase 8.12 pure typed metadata construction only.
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "nayeon.secrets.contracts":
                            self.assertEqual({a.name for a in node.names},
                                             {"SecretIdentifier"})
                        self.assertNotIn(node.module,
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store"})
                    elif isinstance(node, (ast.Name, ast.Attribute)):
                        self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr,
                                         {"SecretValue", "SecretBackend", "SecretStorageError",
                                          "WindowsCredentialBackend", "SecretStore",
                                          "get", "put", "delete", "reveal"})
                    continue
                if relative == "nayeon/brain/connection_reconciliation.py":
                    # Phase 8.9: only safe identifier availability checks.
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "nayeon.secrets.contracts":
                            self.assertEqual({a.name for a in node.names},
                                             {"SecretIdentifier"})
                        self.assertNotIn(node.module,
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store"})
                    elif isinstance(node, ast.Import):
                        self.assertFalse({a.name for a in node.names} &
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store"})
                    elif isinstance(node, (ast.Name, ast.Attribute)):
                        self.assertNotIn(node.id if isinstance(node, ast.Name)
                                         else node.attr,
                                         {"SecretValue", "SecretBackend",
                                          "SecretStorageError", "WindowsCredentialBackend",
                                          "SecretStore", "reveal", "get", "put", "delete"})
                    continue
                if relative in {"nayeon/brain/connection_composition.py",
                                "nayeon/brain/connection_readiness.py"}:
                    # Only these approved metadata consumers may import contracts;
                    # neither can import native or legacy credential storage.
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "nayeon.secrets.contracts":
                            approved = ({"SecretBackend", "SecretIdentifier"}
                                        if relative == "nayeon/brain/connection_composition.py"
                                        else {"SecretIdentifier"})
                            self.assertEqual({alias.name for alias in node.names}, approved)
                        self.assertNotIn(node.module, {"nayeon.secrets.windows_credential",
                                                       "nayeon.secrets.store"})
                    elif isinstance(node, ast.Import):
                        self.assertFalse({alias.name for alias in node.names} &
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store"})
                    elif isinstance(node, (ast.Name, ast.Attribute)):
                        self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr,
                                         {"SecretValue", "WindowsCredentialBackend",
                                          "SecretStore", "SecretStorageError"})
                    continue
                if relative == "nayeon/brain/credential_operation_host.py":
                    # Phase 8.18 trusted-host adapter: only transient SecretValue
                    # may cross into the existing bound credential lifecycle.
                    # Never authorize direct store access, native APIs or reveal.
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "nayeon.secrets.contracts":
                            self.assertEqual({alias.name for alias in node.names},
                                             {"SecretValue"})
                        self.assertNotIn(node.module,
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store",
                                          "nayeon.secrets.resolver"})
                    elif isinstance(node, ast.Import):
                        self.assertFalse({alias.name for alias in node.names} &
                                         {"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.store",
                                          "nayeon.secrets.resolver",
                                          "nayeon.secrets.contracts"})
                    elif isinstance(node, (ast.Name, ast.Attribute)):
                        self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr,
                                         {"SecretIdentifier", "SecretBackend",
                                          "SecretStorageError", "WindowsCredentialBackend",
                                          "SecretStore", "reveal", "get", "put", "delete"})
                    continue
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, {"nayeon.secrets.contracts", "nayeon.secrets.windows_credential"})
                    if node.module == "nayeon.secrets":
                        self.assertFalse({alias.name for alias in node.names} & new_symbols)
                elif isinstance(node, ast.Import):
                    self.assertFalse({alias.name for alias in node.names} &
                                     {"nayeon.secrets.contracts", "nayeon.secrets.windows_credential"})
                elif isinstance(node, (ast.Name, ast.Attribute)):
                    self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr, new_symbols)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn("nayeon.secrets.contracts", node.value)
                    self.assertNotIn("nayeon.secrets.windows_credential", node.value)
        self.assertEqual(old_consumers, set())


if __name__ == "__main__":
    unittest.main()
