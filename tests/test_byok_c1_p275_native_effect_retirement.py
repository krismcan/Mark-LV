"""P275 actual product boundary tests: patched DLL only, never real WinCred.

Original historical tests are preserved and run separately. Source contracts
are bounded review guards, not protection against hostile same-SID Python.
"""
from __future__ import annotations

import ast
import ctypes
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nayeon.brain import local_byok_user_scope as scope
from nayeon.secrets import windows_credential as storage
from nayeon.secrets.contracts import SecretIdentifier, SecretStorageError, SecretValue
from scripts.p275_product_effect_entrypoint_inventory import (
    BACKEND, ROOT, check_backend, inspect_product,
)
from tests.test_local_user_scope_byok import FakeMutex, FakeNative as ControllerFake
from tests.test_windows_credential_backend import FakeNative as BackendFake


IDENTIFIER = SecretIdentifier("openai.api_key")
TARGET = "nayeon-v1/secret/openai.api_key"
FIXTURE = "p275-synthetic-not-a-key"
FAILURE = "Secret storage operation failed"


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class CounterDLL:
    """All four symbols exist; resolution as well as invocation is observed.

    The allocated fake CREDENTIAL has no plaintext/blob. No host DLL is used.
    """
    def __init__(self):
        self.resolved = []
        self.events = []
        self.read_result = 1
        self.read_error = False
        self.partial_output = False
        self.free_error = False
        self.credential = storage._CREDENTIALW()
        self.pointer = ctypes.pointer(self.credential)
        self._functions = {
            "CredReadW": FakeFunction(self.read),
            "CredFree": FakeFunction(self.free),
            "CredWriteW": FakeFunction(self.mutate),
            "CredDeleteW": FakeFunction(self.mutate),
        }

    def __getattr__(self, name):
        self.resolved.append(name)
        if name not in self._functions:
            raise AttributeError(name)
        return self._functions[name]

    def read(self, target, kind, flags, output):
        self.events.append(("read", target, kind, flags))
        if self.partial_output or self.read_result and not self.read_error:
            ctypes.cast(output, ctypes.POINTER(storage._PCREDENTIALW))[0] = self.pointer
        if self.read_error:
            raise OSError("synthetic reader detail")
        return self.read_result

    def free(self, pointer):
        self.events.append(("free", ctypes.cast(pointer, ctypes.c_void_p).value))
        if self.free_error:
            raise OSError("synthetic free detail")

    def mutate(self, *args):
        self.events.append(("MUTATION",))
        raise AssertionError("P275 must not invoke native mutation")


class NativeRetirementTests(unittest.TestCase):
    def setUp(self):
        self.dll = CounterDLL()
        self.loader = self.enterContext(patch.object(storage, "_load_advapi32", return_value=self.dll))
        # A missed loader patch fails before touching a real DLL, including on Windows.
        self.os_loader = self.enterContext(patch.object(
            storage.ctypes, "WinDLL", side_effect=AssertionError("real DLL forbidden"), create=True))
        self.enterContext(patch.object(storage.ctypes, "get_last_error", return_value=1168, create=True))

    def tearDown(self):
        self.os_loader.assert_not_called()
        self.assertNotIn(("MUTATION",), self.dll.events)
        self.assertFalse(set(self.dll.resolved) - {"CredReadW", "CredFree"})

    def assert_denied(self, operation):
        with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
            operation()

    def test_actual_adapter_binds_only_read_and_free_without_resolving_mutators(self):
        storage._Advapi32Adapter()
        self.assertEqual(set(self.dll.resolved), {"CredReadW", "CredFree"})
        functions = self.dll._functions  # Inspection does not resolve DLL symbols.
        self.assertEqual(functions["CredReadW"].argtypes, [
            ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(storage._PCREDENTIALW)])
        self.assertIs(functions["CredReadW"].restype, ctypes.c_int32)
        self.assertEqual(functions["CredFree"].argtypes, [ctypes.c_void_p])
        self.assertIsNone(functions["CredFree"].restype)
        for name in ("CredWriteW", "CredDeleteW"):
            self.assertIsNone(functions[name].argtypes)
            self.assertIsNone(functions[name].restype)
        self.assertEqual(self.dll.events, [])

    def test_direct_read_shim_denies_even_without_init_or_acquisition(self):
        adapter = object.__new__(storage._Advapi32Adapter)
        self.assert_denied(lambda: adapter.read(TARGET))
        self.loader.assert_not_called()
        self.assertEqual(self.dll.resolved, [])
        self.assertEqual(self.dll.events, [])

    def test_native_method_surface_cannot_return_an_allocation(self):
        self.assertEqual({name for name, value in vars(storage._Advapi32Adapter).items()
                          if callable(value)}, {"__init__", "read", "contains"})
        adapter = storage._Advapi32Adapter()
        self.assertFalse(hasattr(adapter, "_acquire"))
        self.assertIs(adapter.contains(TARGET), True)

    def test_native_mutation_methods_are_physically_absent(self):
        adapter = storage._Advapi32Adapter()
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            for name, args in (("write", (TARGET, SecretValue(FIXTURE), 1, 2, "nayeon-v1")),
                               ("delete", (TARGET,))):
                with self.subTest(name=name), self.assertRaises(AttributeError):
                    getattr(adapter, name)(*args)
        reveal.assert_not_called()
        self.assertEqual(self.dll.events, [])

    def test_default_backend_denies_before_and_after_explicit_presence_without_reveal(self):
        backend = storage.WindowsCredentialBackend()
        for refreshed in (False, True):
            if refreshed:
                self.assertTrue(backend.is_available(IDENTIFIER))
            before = list(self.dll.events)
            with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
                self.assert_denied(lambda: backend.get(IDENTIFIER))
                self.assert_denied(lambda: backend.put(IDENTIFIER, SecretValue(FIXTURE)))
                self.assert_denied(lambda: backend.delete(IDENTIFIER))
            reveal.assert_not_called()
            self.assertEqual(self.dll.events, before)
            if not refreshed:
                self.loader.assert_not_called()
        self.assertEqual([event[0] for event in self.dll.events], ["read", "free"])

    def test_explicit_native_injection_does_not_restore_read_or_mutation(self):
        backend = storage.WindowsCredentialBackend(_native=storage._Advapi32Adapter())
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            self.assert_denied(lambda: backend.get(IDENTIFIER))
            self.assert_denied(lambda: backend.put(IDENTIFIER, SecretValue(FIXTURE)))
            self.assert_denied(lambda: backend.delete(IDENTIFIER))
        reveal.assert_not_called()
        self.assertEqual(self.dll.events, [])

    def test_default_actual_factory_and_controller_refuse_all_forged_reviews_after_refresh(self):
        mutex = FakeMutex()
        with patch.object(scope, "WindowsOnboardingMutex", return_value=mutex):
            controller = scope.compose_user_scope_local_byok()
        self.loader.assert_not_called()
        for refreshed in (False, True):
            if refreshed:
                self.assertIs(controller.inspect_presence(), scope.LocalByokPresence.PRESENT_UNVALIDATED)
            before = list(self.dll.events)
            for operation in scope.LocalByokOperation:
                self.assertIsNone(controller.begin(operation))
                review = scope.LocalByokReview(operation, refreshed, "p275-forged")
                controller._pending = review
                with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
                    result = controller.approve(
                        review, confirmed=True,
                        candidate=None if operation is scope.LocalByokOperation.REMOVE else SecretValue(FIXTURE),
                        deletion_acknowledged=operation is scope.LocalByokOperation.REMOVE)
                reveal.assert_not_called()
                self.assertIs(result, scope.LocalByokOutcome.REFUSED)
                self.assertIsNone(controller._pending)
                self.assertFalse(controller.mutation_available)
            self.assertEqual(self.dll.events, before)
        self.assertEqual(mutex.enters, 0)

    def test_presence_never_dereferences_or_copies_and_frees_the_exact_allocation_once(self):
        def poison(*args):
            raise AssertionError("blob/pointer inspection forbidden")
        with patch.object(storage._PCREDENTIALW, "contents", new=property(poison)), \
                patch.object(storage.ctypes, "string_at", side_effect=poison) as copy, \
                patch.object(storage, "SecretValue", side_effect=poison) as value:
            self.assertTrue(storage.WindowsCredentialBackend().is_available(IDENTIFIER))
        copy.assert_not_called()
        value.assert_not_called()
        self.assertEqual(self.dll.events, [
            ("read", TARGET, 1, 0),
            ("free", ctypes.cast(self.dll.pointer, ctypes.c_void_p).value)])

    def test_presence_absent_or_failed_read_has_no_allocation_to_free(self):
        self.dll.read_result = 0
        backend = storage.WindowsCredentialBackend()
        self.assertFalse(backend.is_available(IDENTIFIER))
        for error in (5, 1312):
            with patch.object(storage.ctypes, "get_last_error", return_value=error):
                self.assert_denied(lambda: backend.is_available(IDENTIFIER))
        self.dll.read_error = True
        self.assert_denied(lambda: backend.is_available(IDENTIFIER))
        self.assertEqual([event[0] for event in self.dll.events], ["read"] * 4)

    def test_successful_acquisition_with_free_error_attempts_free_once_and_fails_closed(self):
        self.dll.free_error = True
        self.assert_denied(lambda: storage.WindowsCredentialBackend().is_available(IDENTIFIER))
        self.assertEqual([event[0] for event in self.dll.events], ["read", "free"])

    def test_false_with_partial_output_frees_once_and_denies_even_not_found(self):
        self.dll.read_result = 0
        self.dll.partial_output = True
        adapter = storage._Advapi32Adapter()
        for error in (1168, 5, 1312):
            for free_error in (False, True):
                with self.subTest(error=error, free_error=free_error):
                    self.dll.events.clear()
                    self.dll.free_error = free_error
                    with patch.object(storage.ctypes, "get_last_error", return_value=error):
                        self.assert_denied(lambda: adapter.contains(TARGET))
                    self.assertEqual(self.dll.events, [
                        ("read", TARGET, 1, 0),
                        ("free", ctypes.cast(self.dll.pointer, ctypes.c_void_p).value)])

    def test_exception_after_partial_output_frees_once_and_denies(self):
        self.dll.read_error = True
        self.dll.partial_output = True
        adapter = storage._Advapi32Adapter()
        for free_error in (False, True):
            with self.subTest(free_error=free_error):
                self.dll.events.clear()
                self.dll.free_error = free_error
                self.assert_denied(lambda: adapter.contains(TARGET))
                self.assertEqual(self.dll.events, [
                    ("read", TARGET, 1, 0),
                    ("free", ctypes.cast(self.dll.pointer, ctypes.c_void_p).value)])

    def test_success_without_output_denies_without_free(self):
        self.dll.pointer = storage._PCREDENTIALW()
        adapter = storage._Advapi32Adapter()
        self.assert_denied(lambda: adapter.contains(TARGET))
        self.assertEqual(self.dll.events, [("read", TARGET, 1, 0)])

    def test_original_explicit_backend_fake_still_supports_get_put_delete(self):
        native = BackendFake()
        backend = storage.WindowsCredentialBackend(_native=native)
        backend.put(IDENTIFIER, SecretValue(FIXTURE))
        self.assertEqual(backend.get(IDENTIFIER).reveal(), FIXTURE)
        self.assertTrue(backend.delete(IDENTIFIER))
        self.assertFalse(backend.is_available(IDENTIFIER))
        self.loader.assert_not_called()

    def test_original_explicit_local_controller_fake_save_replace_remove(self):
        native = ControllerFake()
        backend = storage.WindowsCredentialBackend(_native=native)
        controller = scope.LocalByokController(backend, _mutex=FakeMutex())
        for operation in scope.LocalByokOperation:
            review = controller.begin(operation)
            self.assertIsNotNone(review)
            remove = operation is scope.LocalByokOperation.REMOVE
            self.assertIs(controller.approve(
                review, confirmed=True, candidate=None if remove else SecretValue(FIXTURE),
                deletion_acknowledged=remove),
                scope.LocalByokOutcome.SUBMITTED_REMOVAL if remove
                else scope.LocalByokOutcome.SUBMITTED_UNVALIDATED)
        self.assertEqual(native.blobs, {})
        self.loader.assert_not_called()


class ProductSourceContractTests(unittest.TestCase):
    def test_actual_source_inventory_has_no_native_effects_and_reports_custody(self):
        receipt = inspect_product()
        self.assertEqual(receipt["SOURCE_NATIVE_EFFECTS"], "NONE")
        self.assertEqual(receipt["SOURCE_NATIVE_PLAINTEXT_RETURN"], "NONE")
        self.assertEqual(receipt["PRODUCTION"], "HOLD")
        self.assertEqual(receipt["REAL_KEYS"], "NO-GO")
        self.assertEqual(sorted(call["call"] for call in receipt["native_presence_calls"]),
                         ["self._dll.CredFree", "self._dll.CredReadW"])
        self.assertEqual(len(receipt["source_sha256"][BACKEND]), 64)

    def test_native_effect_plaintext_and_dynamic_alias_reintroduction_is_rejected(self):
        source = (ROOT / BACKEND).read_text(encoding="utf-8")
        check_backend(source)
        mutations = (
            source.replace("self._dll.CredReadW.restype", "self._dll.CredWriteW.restype"),
            source.replace("self._dll.CredFree.restype", "self._dll.CredDeleteW.restype"),
            source.replace("return True", "return ctypes.string_at(pointer.contents.CredentialBlob)"),
            source.replace("return True", "return pointer[0].CredentialBlobSize > 0"),
            source.replace("return True", "return bytes(pointer)"),
            source.replace("return True", "return pointer"),
            source.replace("return True", "return ctypes.c_void_p()"),
            source.replace("    def read(", "    def _acquire(self) -> _PCREDENTIALW:\n        return _PCREDENTIALW()\n\n    def read("),
            source.replace("    def read(", "    def escape(self) -> ctypes.c_void_p:\n        return ctypes.c_void_p()\n\n    def read("),
            source.replace("return True", 'return getattr(self._dll, "Cred" + "WriteW")(pointer, 0)'),
            source.replace("return True", 'return self._dll["Cred" + "DeleteW"](target, 1, 0)'),
            source.replace("return True", "return self._dll.CredReadW"),
            source.replace("import ctypes", "import ctypes as native"),
            source.replace("import ctypes", "from ctypes import WinDLL as Native"),
            source + "\nnative = ctypes\n",
            source + "\nload = ctypes.WinDLL\n",
            source + '\nalternative = ctypes.WinDLL("Advapi32.dll")\n',
            source + "\nload = _load_advapi32\n",
            source + "\ndef escape(self):\n    return self._dll\n",
            source + "\ndef escape() -> ctypes.c_void_p:\n    return ctypes.c_void_p()\n",
            source + "\n_Advapi32Adapter.escape = lambda self: _PCREDENTIALW()\n",
            source.replace("self._dll.CredFree(pointer)", "pass"),
            source.replace("self._dll.CredFree(pointer)", "self._dll.CredFree(pointer)\n                    self._dll.CredFree(pointer)"),
            source.replace("raise SecretStorageError(_FAILURE)\n\n    def contains", "return _PCREDENTIALW()\n\n    def contains"),
            source + "\n_Advapi32Adapter.write = lambda self, *args: self._dll.CredWriteW(*args)\n",
        )
        for mutant in mutations:
            with self.subTest(index=mutations.index(mutant)):
                self.assertNotEqual(mutant, source)
                ast.parse(mutant)  # Rejection must be a source contract, not invalid syntax.
                with self.assertRaises(AssertionError):
                    check_backend(mutant)

    def test_inventory_rejects_unreviewed_ctypes_import_and_alias_in_new_product_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for dependency in (BACKEND, "nayeon/desktop_alpha/local_byok_launch_bridge.py",
                               "nayeon/desktop_alpha/local_byok_window.py",
                               "nayeon/brain/local_byok_user_scope.py", "nayeon/secrets/lifecycle.py"):
                path = root / dependency
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / dependency).read_bytes())
            extra = root / "nayeon/unreviewed.py"
            for source in ("import ctypes", "import ctypes as c", "from ctypes import WinDLL as load"):
                extra.write_text(source, encoding="utf-8")
                with self.subTest(source=source), self.assertRaisesRegex(AssertionError, "unreviewed ctypes"):
                    inspect_product(root)


if __name__ == "__main__":
    unittest.main()
