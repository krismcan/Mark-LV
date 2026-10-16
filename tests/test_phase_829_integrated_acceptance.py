"""Phase 8.29 fake-only integrated first-run acceptance and adversarial tests.

These are simulated Tk journeys, not live human consent or release approval.
No live services. Reuse the sealed A02 fake classes/factory and attempt-counting
tripwires unchanged. Each poison raises before delegation; zero recorded attempts
covers only those entrypoints. Temporary fake metadata/journal I/O is permitted.
"""
import gc
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from unittest import mock
import weakref

from nayeon.brain.connection_reconciliation import observe_connection
from nayeon.brain.connection_document import (
    ProviderConnectionDocumentV1, parse_provider_connection_document,
)
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.onboarding_recovery_document import RecoveryState
from nayeon.brain.first_run_refresh import FirstRunRefreshStatus
from nayeon.brain.onboarding_metadata_commit import (
    TrustedMetadataCommitHost, MetadataOperation, MetadataCommitOutcome,
    MetadataCommitReceipt,
)
from nayeon.brain.onboarding_recovery import (
    RecoveryAdmissionError, TrustedOnboardingRecoveryController,
)
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.lifecycle import CredentialValidationStatus
from tests.a02_fake_isolation_support import (
    FakeBackend, FakeMutex, FakeObserver, FakeTempRoot, FakeValidator,
)
from tests.test_pre_829_a02_fake_isolation import ProhibitedIO
from tests import phase_829_integrated_support as support


class IntegratedCompositionFoundationTests(unittest.TestCase):
    def setUp(self):
        self.root = FakeTempRoot()
        self.addCleanup(self.root.cleanup)
        self.path = self.root.path / "provider.json"
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.observer = FakeObserver(self.backend)
        self.mutex = FakeMutex()

    def arguments(self, **overrides):
        values = dict(backend=self.backend, validator=self.validator,
                      observer=self.observer, mutex=self.mutex,
                      temp_root=self.root, metadata_path=self.path)
        values.update(overrides)
        return values

    def retain_controller(self, controller):
        # Never clear/replace the production pool or A02 reservations. A fresh
        # owned temp path per test isolates keys; weak pool entries expire normally.
        self.addCleanup(lambda: controller.close()
                        if controller._ctx is not None else None)
        return controller

    def build(self, **overrides):
        result = support.compose_integrated_fake_only(**self.arguments(**overrides))
        self.retain_controller(result.controller)
        return result

    def assert_no_effects(self):
        self.assertEqual(self.validator.calls, 0)
        self.assertIsNone(self.backend.value)
        self.assertNotIn("get", self.backend.calls)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)

    def test_credential_metadata_status_order_and_exact_shared_identities(self):
        events = []
        retained = []
        real_credential = support.compose_fake_only_onboarding
        real_metadata = support.TrustedMetadataCommitHost
        real_status = support.FirstRunReadOnlyController

        def credential(**kwargs):
            events.append("credential")
            result = real_credential(**kwargs)
            retained.append(result)
            self.assertIs(result.controller._availability, self.observer)
            return result

        def metadata(**kwargs):
            self.assertEqual(events, ["credential"])
            events.append("metadata")
            result = real_metadata(**kwargs)
            self.assertIs(result.recovery_controller, retained[0].controller)
            self.assertIs(kwargs["metadata_path"], self.path)
            self.assertIs(kwargs["mutex"], self.mutex)
            return result

        def status(**kwargs):
            self.assertEqual(events, ["credential", "metadata"])
            events.append("status")
            self.assertEqual(self.observer.calls, 0)
            return real_status(**kwargs)

        with ProhibitedIO() as guard, \
                mock.patch.object(support, "compose_fake_only_onboarding", side_effect=credential), \
                mock.patch.object(support, "TrustedMetadataCommitHost", side_effect=metadata), \
                mock.patch.object(support, "FirstRunReadOnlyController", side_effect=status):
            fixture = self.build()
            fixture.check_unstarted()
            self.assertEqual(events, ["credential", "metadata", "status"])
            self.assertIs(fixture.temp_root, self.root)
            self.assertIs(fixture.metadata_path, self.path)
            self.assertIs(fixture.controller, retained[0].controller)
            self.assertIs(TrustedOnboardingRecoveryController.for_path(
                self.path, availability=self.observer, mutex=self.mutex), fixture.controller)
            self.assertEqual(guard.attempts, [])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(list(self.root.path.iterdir()), [])
        self.assert_no_effects()

    def test_status_closure_is_captured_and_called_only_by_explicit_refresh(self):
        with ProhibitedIO() as guard, mock.patch.object(
                support, "observe_connection", wraps=observe_connection) as observe:
            fixture = self.build()
            observe.assert_not_called()
            self.assertIs(fixture.status._observe, fixture.observe)
            bindings = dict(zip(fixture.observe.__code__.co_freevars,
                                (cell.cell_contents for cell in fixture.observe.__closure__)))
            self.assertEqual(set(bindings), {"metadata_path", "observer"})
            self.assertIs(bindings["metadata_path"], self.path)
            self.assertIs(bindings["observer"], self.observer)
            self.assertEqual(self.observer.calls, 0)
            for count in (1, 2):
                self.assertIs(fixture.refresh().status, FirstRunRefreshStatus.OBSERVED)
                self.assertEqual(observe.call_count, count)
                observe.assert_called_with(self.path, self.observer)
                self.assertEqual(self.observer.calls, count)
                self.assertEqual(self.backend.calls, ["is_available"] * count)
                fixture.check_unstarted()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(list(self.root.path.iterdir()), [])
        self.assert_no_effects()

    def test_root_and_controller_are_strongly_owned_and_bindings_read_only(self):
        # No test cleanup callback retains the controller in this case.
        values = self.arguments()
        fixture = support.compose_integrated_fake_only(**values)
        controller_ref = weakref.ref(fixture.controller)
        # setUp's cleanup callback also retains the root: check exact held
        # identity, not a misleading claim of sole GC/lifetime ownership.
        self.assertIs(fixture.temp_root, self.root)
        self.assertTrue(fixture.temp_root.path.is_dir())
        del values
        self.assertIs(controller_ref(), fixture.controller)
        for field in ("temp_root", "controller", "observer", "backend", "metadata_path"):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(fixture, field, object())
        fixture.check_unstarted()
        del fixture
        gc.collect()
        self.assertIsNone(controller_ref())

    def test_missing_wrong_subclassed_and_duck_dependencies_rejected_before_reflection(self):
        class Poison:
            def __getattr__(self, name):
                raise AssertionError("B1_UNEXPECTED_REFLECTION")

        class SubBackend(FakeBackend):
            pass

        with ProhibitedIO() as guard, mock.patch.object(
                support, "compose_fake_only_onboarding") as factory:
            with self.assertRaises(TypeError):
                support.compose_integrated_fake_only()
            for field in self.arguments():
                for value in (None, Poison()):
                    with self.subTest(field=field, kind=type(value).__name__):
                        with self.assertRaises(TypeError):
                            self.build(**{field: value})
            with self.assertRaises(TypeError):
                self.build(backend=SubBackend())
            with self.assertRaises(TypeError):
                self.build(unexpected_factory=object())
            factory.assert_not_called()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.mutex.entries, 0)
        self.assert_no_effects()

    def test_mixed_observer_backend_rejected_without_fallback(self):
        alien = FakeBackend()
        with ProhibitedIO() as guard, mock.patch.object(
                support, "compose_fake_only_onboarding") as factory:
            with self.assertRaisesRegex(ValueError, "observer/backend"):
                self.build(observer=FakeObserver(alien))
            factory.assert_not_called()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(alien.calls, [])
        self.assert_no_effects()

    def test_path_alias_escape_wrong_name_and_wrong_root_rejected(self):
        other_root = FakeTempRoot()
        self.addCleanup(other_root.cleanup)
        paths = (self.path.parent.parent / "provider.json",
                 self.path.with_name("other.json"),
                 self.path.parent / ".." / self.path.parent.name / "provider.json",
                 other_root.path / "provider.json")
        with ProhibitedIO() as guard:
            for path in paths:
                with self.subTest(variant=paths.index(path)), self.assertRaises(ValueError):
                    self.build(metadata_path=path)
            self.assertEqual(guard.attempts, [])
        self.assertEqual(list(self.root.path.iterdir()), [])
        self.assert_no_effects()

    def test_preexisting_metadata_rejected_by_unchanged_a02_factory(self):
        self.path.write_text('{"synthetic":true}', encoding="utf-8")
        before = self.path.read_bytes()
        with ProhibitedIO() as guard, mock.patch.object(
                support, "TrustedMetadataCommitHost") as metadata:
            with self.assertRaises(ValueError):
                self.build()
            metadata.assert_not_called()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(self.path.read_bytes(), before)
        self.assert_no_effects()

    def test_substituted_temp_owner_is_rejected_without_adoption(self):
        other_root = FakeTempRoot()
        self.addCleanup(other_root.cleanup)
        with ProhibitedIO() as guard, mock.patch.object(
                self.root._manager, "name", str(other_root.path)):
            with self.assertRaises(ValueError):
                self.build(metadata_path=other_root.path / "provider.json")
            self.assertEqual(guard.attempts, [])
        self.assertEqual(self.root.path, self.path.parent)
        self.assert_no_effects()

    def test_changed_fake_descriptors_rejected_before_poisoned_getter(self):
        poison = mock.Mock(side_effect=AssertionError("B1_POISON_GETTER"))
        with ProhibitedIO() as guard, mock.patch.object(
                FakeObserver, "backend", property(poison)):
            with self.assertRaises(TypeError):
                self.build()
            poison.assert_not_called()
            self.assertEqual(guard.attempts, [])
        with mock.patch.object(FakeValidator, "validate", side_effect=AssertionError("B1_POISON_VALIDATOR")):
            with self.assertRaises(TypeError):
                self.build()
        self.assert_no_effects()

    def test_metadata_first_unowned_assembly_rejected_before_a02(self):
        metadata = TrustedMetadataCommitHost(metadata_path=self.path, mutex=self.mutex)
        controller = self.retain_controller(metadata.recovery_controller)
        with ProhibitedIO() as guard, mock.patch.object(
                support, "compose_fake_only_onboarding") as factory:
            with self.assertRaisesRegex(ValueError, "unused path"):
                self.build()
            factory.assert_not_called()
            self.assertIsNone(controller._availability)
            self.assertIsNone(controller._ctx)
            self.assertFalse(controller._faulted)
            self.assertEqual(guard.attempts, [])
        self.assert_no_effects()

    def test_production_late_observer_after_fake_tenure_is_rejected(self):
        metadata = TrustedMetadataCommitHost(metadata_path=self.path, mutex=self.mutex)
        controller = self.retain_controller(metadata.recovery_controller)
        with ProhibitedIO() as guard:
            # Explicit negative stimulus, never an automatic factory action.
            controller.request_reconciliation()
            self.assertIsNotNone(controller._ctx)
            with self.assertRaisesRegex(RecoveryAdmissionError, "after tenure begins"):
                TrustedOnboardingRecoveryController.for_path(
                    self.path, availability=self.observer, mutex=self.mutex)
            self.assertFalse(controller.ready)
            self.assertTrue(controller._faulted)
            self.assertIsNone(controller._availability)
            self.assertEqual(self.observer.calls, 0)
            self.assertEqual(self.mutex.entries, 1)
            self.assertEqual(guard.attempts, [])
        self.assert_no_effects()

    def test_duplicate_composition_rejected_without_changing_original(self):
        fixture = self.build()
        with ProhibitedIO() as guard, mock.patch.object(
                support, "compose_fake_only_onboarding") as factory:
            with self.assertRaisesRegex(ValueError, "unused path"):
                self.build()
            factory.assert_not_called()
            fixture.check_unstarted()
            self.assertEqual(guard.attempts, [])
        self.assert_no_effects()

    def test_existing_controller_with_different_fake_mutex_is_not_adopted(self):
        other_mutex = FakeMutex()
        controller = self.retain_controller(TrustedOnboardingRecoveryController.for_path(
            self.path, availability=self.observer, mutex=other_mutex))
        with ProhibitedIO() as guard:
            with self.assertRaisesRegex(ValueError, "unused path"):
                self.build()
            self.assertIs(controller._mutex, other_mutex)
            self.assertEqual(other_mutex.entries, 0)
            self.assertEqual(self.mutex.entries, 0)
            self.assertEqual(guard.attempts, [])
        self.assert_no_effects()

    def test_replaced_assembly_bindings_refuse_refresh_before_observation(self):
        fixture = self.build()
        alien = FakeBackend()
        replacements = (
            (fixture.credential.coordinator, "_availability", FakeObserver(alien)),
            (fixture.controller, "_availability", FakeObserver(alien)),
            (fixture.metadata_host, "_mutex", FakeMutex()),
            (fixture.metadata_host, "_path", self.path.with_name("other.json")),
            (fixture.status, "_observe", mock.Mock(side_effect=AssertionError("B1_RETARGETED"))),
        )
        with ProhibitedIO() as guard, mock.patch.object(support, "observe_connection") as observe:
            for target, name, replacement in replacements:
                with self.subTest(field=name), mock.patch.object(target, name, replacement):
                    with self.assertRaises(ValueError):
                        fixture.refresh()
                fixture.check_unstarted()
            observe.assert_not_called()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(alien.calls, [])
        self.assert_no_effects()

    def test_backend_retarget_and_descriptor_change_fail_before_refresh(self):
        fixture = self.build()
        alien = FakeBackend()
        with ProhibitedIO() as guard, mock.patch.object(support, "observe_connection") as observe:
            # Same adversarial retarget as sealed A02; restore without weakening
            # its __setattr__/per-observation checks or changing the old fixture.
            try:
                object.__setattr__(self.observer, "_backend", alien)
                with self.assertRaises(ValueError):
                    fixture.refresh()
            finally:
                object.__setattr__(self.observer, "_backend", self.backend)
            poison = mock.Mock(side_effect=AssertionError("B1_POISON_GETTER"))
            with mock.patch.object(FakeObserver, "backend", property(poison)):
                with self.assertRaises(TypeError):
                    fixture.refresh()
                poison.assert_not_called()
            observe.assert_not_called()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(alien.calls, [])
        fixture.check_unstarted()
        self.assert_no_effects()

    def test_status_closure_path_divergence_refuses_before_observation(self):
        fixture = self.build()
        cells = dict(zip(fixture.observe.__code__.co_freevars, fixture.observe.__closure__))
        with ProhibitedIO() as guard, mock.patch.object(support, "observe_connection") as observe:
            try:
                cells["metadata_path"].cell_contents = self.path.with_name("other.json")
                with self.assertRaisesRegex(ValueError, "observation bindings"):
                    fixture.refresh()
            finally:
                cells["metadata_path"].cell_contents = self.path
            observe.assert_not_called()
            self.assertEqual(guard.attempts, [])
        fixture.check_unstarted()
        self.assert_no_effects()

    def test_unexpected_factory_result_or_constructor_error_has_no_fallback(self):
        with ProhibitedIO() as guard, mock.patch.object(
                support, "compose_fake_only_onboarding", return_value=object()) as factory, \
                mock.patch.object(support, "TrustedMetadataCommitHost") as metadata:
            with self.assertRaises(TypeError):
                self.build()
            factory.assert_called_once_with(**self.arguments())
            metadata.assert_not_called()
            self.assertEqual(guard.attempts, [])
        with ProhibitedIO() as guard, mock.patch.object(
                support, "TrustedMetadataCommitHost", side_effect=RuntimeError("B1_STOP")) as metadata, \
                mock.patch.object(support, "FirstRunReadOnlyController") as status:
            with self.assertRaisesRegex(RuntimeError, "B1_STOP"):
                self.build()
            metadata.assert_called_once_with(metadata_path=self.path, mutex=self.mutex)
            status.assert_not_called()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.mutex.entries, 0)
        self.assert_no_effects()

    def test_poisoned_sdk_negative_control_is_distinct_from_allowed_composition(self):
        from nayeon.brain.credential_onboarding_composition import compose_openai_credential_onboarding

        with ProhibitedIO() as guard:
            fixture = self.build()
            fixture.refresh()
            self.assertEqual(guard.attempts, [])
        # Only this deliberate negative control references the forbidden real
        # factory. Poison raises at SDK loader BEFORE any client/network work.
        backend = FakeBackend()
        with ProhibitedIO() as guard:
            poisoned = compose_openai_credential_onboarding(backend)
            result = poisoned.test_candidate(SecretValue("b1-synthetic-sdk-control"))
            self.assertIs(result, CredentialValidationStatus.INDETERMINATE)
            self.assertEqual(guard.attempts, ["sdk"])
            self.assertEqual(backend.calls, [])
        self.assert_no_effects()


class IntegratedImportInertnessTests(unittest.TestCase):
    def test_fresh_process_import_has_no_composition_observation_gui_or_service_attempts(self):
        script = textwrap.dedent('''
            import builtins, ctypes, os, socket, sys, tempfile
            from contextlib import ExitStack
            from unittest import mock
            sys.path.insert(0, os.getcwd())
            attempts = []
            original_import = builtins.__import__
            def deny(label):
                def blocked(*args, **kwargs):
                    attempts.append(label)
                    raise AssertionError("B1_IMPORT_PROHIBITED_" + label)
                return blocked
            def guarded_import(name, *args, **kwargs):
                if (name.split(".", 1)[0] in {
                        "openai", "httpx", "requests", "win32cred", "keyring",
                        "tkinter", "_tkinter"} or
                        name.startswith("nayeon.brain.providers") or
                        name == "nayeon.secrets.windows_credential"):
                    return deny("service_import")()
                return original_import(name, *args, **kwargs)
            with ExitStack() as stack:
                for obj, name, label in (
                    (builtins, "__import__", None),
                    (socket, "socket", "socket"),
                    (socket, "create_connection", "network"),
                    (ctypes, "WinDLL", "native"),
                    (tempfile, "mkdtemp", "temp_root"),
                ):
                    stack.enter_context(mock.patch.object(
                        obj, name, guarded_import if label is None else deny(label),
                        create=True))
                # First import the unchanged dependency definitions under guards.
                from tests import a02_fake_isolation_support as a02
                from nayeon.brain import onboarding_recovery as recovery
                from nayeon.brain import onboarding_metadata_commit as metadata
                from nayeon.brain import first_run_refresh as status
                from nayeon.brain import connection_reconciliation as observation
                for cls in (a02.FakeBackend, a02.FakeValidator, a02.FakeObserver,
                            a02.FakeMutex, a02.FakeTempRoot,
                            metadata.TrustedMetadataCommitHost,
                            status.FirstRunReadOnlyController):
                    stack.enter_context(mock.patch.object(cls, "__init__", deny("constructor")))
                for obj, name in (
                    (a02, "compose_fake_only_onboarding"),
                    (a02.FakeMutex, "hold"),
                    (a02.FakeObserver, "is_available"),
                    (a02.FakeBackend, "is_available"),
                    (a02.FakeBackend, "get"),
                    (a02.FakeBackend, "put"),
                    (a02.FakeBackend, "delete"),
                    (a02.FakeValidator, "validate"),
                    (recovery.TrustedOnboardingRecoveryController, "for_path"),
                    (observation, "observe_connection"),
                ):
                    stack.enter_context(mock.patch.object(obj, name, deny("composition_or_observation")))
                from tests import phase_829_integrated_support
                from tests import phase_829_simulated_first_run
                assert not attempts, attempts
                assert not recovery._POOL
                assert not a02._RESERVED
                assert "tkinter" not in sys.modules
                assert "_tkinter" not in sys.modules
            print("B1_IMPORT_INERT_OK")
        ''')
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=str(Path(__file__).resolve().parents[1]),
            capture_output=True, text=True, timeout=25,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertEqual(result.stdout.strip(), "B1_IMPORT_INERT_OK")


@unittest.skipUnless(sys.platform == "win32", "Real Tk navigation requires Windows")
class IntegratedRealTkNavigationTests(unittest.TestCase):
    """Actual Tk event-loop navigation, fake-only; not release acceptance."""

    def setUp(self):
        from tests.phase_829_simulated_first_run import launch
        self.temp = FakeTempRoot()
        self.addCleanup(self.temp.cleanup)
        self.io_guard = ProhibitedIO()
        self.io_guard.__enter__()
        self.addCleanup(self.io_guard.__exit__, None, None, None)
        self.addCleanup(self._assert_final_guarded_cleanup)
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.observer = FakeObserver(self.backend)
        self.mutex = FakeMutex()
        self.fixture = support.compose_integrated_fake_only(
            backend=self.backend, validator=self.validator, observer=self.observer,
            mutex=self.mutex, temp_root=self.temp,
            metadata_path=self.temp.path / "provider.json")
        self._expect_cleared_metadata_document = False
        self._expected_fake_validation_calls = 0
        self._expected_credential_puts = 0
        self._expected_credential_deletes = 0
        self._expected_preserved_key = None
        self._expect_existing_metadata_after_put = False
        self.sim = launch(self.fixture)
        self.root = self.sim.root
        self.addCleanup(self._close)
        self.root.update_idletasks()
        self.root.update()

    def _assert_final_guarded_cleanup(self):
        # unittest invokes this even if the preceding Tk-close cleanup fails.
        self.assertEqual(self.io_guard.attempts, [])
        if not hasattr(self, "fixture"):
            return
        if self._expect_cleared_metadata_document:
            cleared = self.fixture.metadata_host._store.load()
            self.assertIsNotNone(cleared)
            self.assertIsNone(cleared.connection)
            self.assertTrue(self.fixture.metadata_path.is_file())
            self.assertIsNone(self.backend.value)
            self.assertEqual(self.validator.calls, 0)
            self.assertNotIn("put", self.backend.calls)
            self.assertNotIn("delete", self.backend.calls)
        elif self._expected_preserved_key is not None:
            self.assertIs(self.backend.value, self._expected_preserved_key)
            self.assertEqual(self.validator.calls, self._expected_fake_validation_calls)
            self.assertNotIn("put", self.backend.calls)
            self.assertNotIn("delete", self.backend.calls)
            self.assertTrue(self.fixture.metadata_path.is_file())
        elif self._expected_credential_deletes:
            self.assertEqual(self.backend.calls.count("delete"), self._expected_credential_deletes)
            self.assertIsNone(self.backend.value)
            self.assertNotIn("put", self.backend.calls)
            self.assertEqual(self.validator.calls, 0)
            self.assertTrue(self.fixture.metadata_path.is_file())
        elif self._expected_credential_puts:
            self.assertEqual(self.backend.calls.count("put"), self._expected_credential_puts)
            self.assertIs(type(self.backend.value), SecretValue)
            self.assertNotIn("delete", self.backend.calls)
            self.assertEqual(self.validator.calls, self._expected_fake_validation_calls)
            self.assertEqual(self.fixture.metadata_path.is_file(),
                             self._expect_existing_metadata_after_put)
        elif self._expected_fake_validation_calls:
            self.assertEqual(self.validator.calls, self._expected_fake_validation_calls)
            self.assertIsNone(self.backend.value)
            self.assertNotIn("put", self.backend.calls)
            self.assertNotIn("delete", self.backend.calls)
            self.assertFalse(self.fixture.metadata_path.exists())
        else:
            self._no_effects()
        self.assertTrue(self.sim._finished)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertIsNone(self.fixture.controller._ui_window_owner)

    def _close(self):
        import tkinter as tk
        try:
            alive = self.root.winfo_exists()
        except tk.TclError:
            alive = False
        if alive:
            self.sim.finish()

    def _fire(self, button):
        # Actual Tk binding route, not Button.invoke or Python callback.
        button.event_generate("<Enter>", x=5, y=5)
        self.root.update()
        button.event_generate("<ButtonPress-1>", x=5, y=5)
        self.root.update()
        button.event_generate("<ButtonRelease-1>", x=5, y=5)
        self.root.update()

    def _no_effects(self):
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(self.validator.calls, 0)
        self.assertIsNone(self.backend.value)
        self.assertNotIn("get", self.backend.calls)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)
        self.assertFalse(self.fixture.metadata_path.exists())
        self.assertFalse(self.fixture.controller.ready)

    def test_mapped_metadata_then_credential_widget_dispatch_and_release(self):
        self.assertIsNone(self.sim.owned_manager)
        self.assertEqual(self.observer.calls, 0)
        self.assertTrue(self.sim.metadata_button.winfo_ismapped())
        self._fire(self.sim.metadata_button)
        self.assertIsNotNone(self.sim.owned_manager)
        self.assertTrue(self.sim.owned_child.winfo_exists())
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(
            owner=self.sim.owned_manager._owner_token))
        self._no_effects()
        self.assertEqual(self.observer.calls, 0)
        self.sim.close_current()
        self.root.update()
        self.assertFalse(self.sim.owned_child.winfo_exists())
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self._fire(self.sim.credential_button)
        self.assertTrue(self.sim.owned_child.winfo_exists())
        self.assertTrue(self.fixture.controller.is_ui_window_owner(
            self.sim.owned_manager._owner_token))
        self.assertEqual(self.observer.calls, 0)
        self._no_effects()

    def test_refresh_requires_widget_event_and_is_read_only(self):
        self.assertEqual(self.observer.calls, 0)
        self._fire(self.sim.refresh_button)
        self.assertEqual(self.observer.calls, 1)
        self.assertEqual(self.backend.calls, ["is_available"])
        self.assertIsNone(self.sim.owned_manager)
        self._no_effects()

    def test_unmapped_navigation_does_not_claim_owner(self):
        self.root.withdraw()
        self.root.update()
        self.assertFalse(self.sim.metadata_button.winfo_ismapped())
        import contextlib
        import io
        error_output = io.StringIO()
        with contextlib.redirect_stderr(error_output):
            self._fire(self.sim.metadata_button)
        self.assertEqual(error_output.getvalue(), "", "Unexpected Tk callback exception")
        self.assertIsNone(self.sim.owned_manager)
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.assertEqual(self.observer.calls, 0)
        self._no_effects()

    def test_nested_navigation_during_metadata_construction(self):
        from nayeon.desktop_alpha import first_run_metadata_management_window as module
        original = module.FirstRunMetadataManagementWindow

        reached = []

        def on_create(*, root, host):
            reached.append("constructor")
            self.sim._dispatch_navigation("credential")
            return original(root=root, host=host)

        import contextlib
        import io
        import tkinter as tk
        with mock.patch.object(module, "FirstRunMetadataManagementWindow",
                               side_effect=on_create):
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self._fire(self.sim.metadata_button)
        self.assertEqual(reached, ["constructor"])
        self.assertEqual(errors.getvalue(), "")
        self.assertEqual(self.sim.failure_type, "RuntimeError")
        self.assertFalse(self.sim._transition)
        self.assertIsNone(self.sim.owned_manager)
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.assertEqual([w for w in self.root.winfo_children()
                          if isinstance(w, tk.Toplevel)], [])
        self._no_effects()

    def test_competing_manager_keeps_original_owner(self):
        import contextlib
        import io
        self._fire(self.sim.metadata_button)
        original = self.sim.owned_manager
        token = original._owner_token
        with contextlib.redirect_stderr(io.StringIO()) as log:
            self._fire(self.sim.credential_button)
        self.assertEqual(log.getvalue(), "")
        self.assertIs(self.sim.owned_manager, original)
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=token))
        self.assertEqual(self.observer.calls, 0)
        self._no_effects()

    def test_after_claim_binding_fault_destroys_attempted_child_only(self):
        import contextlib
        import io
        import tkinter as tk
        original = type(self.fixture).check_bindings
        calls = []

        def on_check(instance):
            calls.append(len(calls))
            if len(calls) == 2:
                raise RuntimeError("synthetic post-claim binding fault")
            return original(instance)

        with mock.patch.object(type(self.fixture), "check_bindings", on_check):
            with contextlib.redirect_stderr(io.StringIO()) as log:
                self._fire(self.sim.metadata_button)
        self.assertEqual(log.getvalue(), "")
        self.assertGreaterEqual(len(calls), 2)
        self.assertIsNone(self.sim.owned_manager)
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.assertEqual(
            [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)], [])
        self.assertEqual(self.observer.calls, 0)
        self._no_effects()

    def test_nested_finish_during_manager_construction_preserves_root(self):
        from nayeon.desktop_alpha import first_run_metadata_management_window as module
        original = module.FirstRunMetadataManagementWindow

        reached = []

        def on_create(*, root, host):
            reached.append("constructor")
            self.sim.finish()
            return original(root=root, host=host)

        import contextlib
        import io
        import tkinter as tk
        with mock.patch.object(module, "FirstRunMetadataManagementWindow",
                               side_effect=on_create):
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self._fire(self.sim.metadata_button)
        self.assertEqual(reached, ["constructor"])
        self.assertEqual(errors.getvalue(), "")
        self.assertEqual(self.sim.failure_type, "RuntimeError")
        self.assertFalse(self.sim._transition)
        self.assertTrue(self.root.winfo_exists())
        self.assertIsNone(self.sim.owned_manager)
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.assertEqual([w for w in self.root.winfo_children()
                          if isinstance(w, tk.Toplevel)], [])
        self._no_effects()

    def test_busy_close_refuses_handover_and_retains_parent(self):
        self._fire(self.sim.metadata_button)
        manager = self.sim.owned_manager
        with mock.patch.object(manager, "close_from_window", return_value=None):
            with self.assertRaises(RuntimeError):
                self.sim.close_current()
        self.assertTrue(self.root.winfo_exists())
        self.assertTrue(self.sim.owned_child.winfo_exists())
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(
            owner=manager._owner_token))
        self._no_effects()

    def test_unadmitted_management_reviews_cannot_create_effects(self):
        # A2 negative control: mapped Tk events cannot substitute for recovery
        # admission or silently create a human approval ticket.
        self._fire(self.sim.metadata_button)
        meta = self.sim.owned_manager
        meta._model.insert(0, "gpt-4o-mini")
        self._fire(meta._save)
        self.assertFalse(self.fixture.metadata_host.has_pending)
        self.assertIsNone(meta._ticket)
        self.assertIsNone(meta._operation)
        self._no_effects()

        self.sim.close_current()
        self.root.update()
        self._fire(self.sim.credential_button)
        creds = self.sim.owned_manager
        self._fire(creds._choices[0])
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.assertFalse(self.fixture.credential.host.has_pending)
        self.assertIsNone(creds._ticket)
        self.assertIsNone(creds._operation)
        self._no_effects()

    def test_recovery_review_requires_acknowledgement_and_rejects_safely(self):
        # A2 negative: explicit mapped Tk recovery review is not authority.
        self._fire(self.sim.metadata_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self.assertIsNotNone(child)
        self.assertTrue(child._root.winfo_exists())
        self.assertFalse(self.fixture.controller.ready)
        self._fire(child._review_button)
        review = child._review
        self.assertIsNotNone(review)
        self.assertIs(self.fixture.controller._review, review)
        self._fire(child._approve)
        self.assertFalse(self.fixture.controller.ready)
        self.assertIsNotNone(child._review)
        # Reject this exact controller-owned review now, before parent teardown
        # could mask an orphaned recovery review.
        captured_review = child._review
        self.assertIs(self.fixture.controller._review, captured_review)
        self._fire(child._reject)
        self.assertIsNone(child._review)
        self.assertIsNone(self.fixture.controller._review)
        self.assertFalse(self.fixture.controller.ready)
        child.close_from_window()
        self.root.update()
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(
            owner=panel._owner_token))
        self.assertEqual(self.observer.calls, 2)
        self.assertEqual(self.backend.calls, ["is_available"] * 2)
        self._no_effects()

    def test_mapped_recovery_ack_event_admits_then_owner_close_revokes_fake_tenure(self):
        # Synthetic mapped Tk choices: not a claim of physical human consent.
        # Tk routes callback failures to this root hook instead of raising.
        callback_faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: callback_faults.append(kind.__name__))
        self.assertFalse(self.fixture.controller.ready)
        self._fire(self.sim.metadata_button)
        parent = self.sim.owned_manager
        self._fire(parent._recovery_button)
        child = parent._recovery_dialog
        self.assertIsNotNone(child)
        self._fire(child._review_button)
        reviewed = child._review
        self.assertIsNotNone(reviewed)
        self.assertIs(self.fixture.controller._review, reviewed)
        self.assertFalse(child._ack.get())
        self._fire(child._ack_button)
        self.assertIs(child._ack.get(), True)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self.assertIsNone(child._review)
        self.assertTrue(self.mutex.active)
        self.assertEqual(self.validator.calls, 0)
        self.assertIsNone(self.backend.value)
        self.assertFalse(self.fixture.metadata_path.exists())
        self.assertEqual(self.io_guard.attempts, [])
        self.sim.close_current()
        self.root.update()
        self.assertFalse(self.fixture.controller.ready)
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self._no_effects()
        self.sim.finish()
        self.assertTrue(self.sim._finished)
        self.assertEqual(callback_faults, [], "Unexpected Tk callback fault")


    def test_reconciled_metadata_review_rejection_has_no_effect(self):
        # Recovery consent alone is not consent to SAVE metadata. The pending
        # SAVE review must be independently rejected without writing metadata.
        callback_faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: callback_faults.append(kind.__name__))
        self._fire(self.sim.metadata_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self.assertIsNotNone(child)
        self._fire(child._review_button)
        self.assertIsNotNone(child._review)
        self._fire(child._ack_button)
        self.assertIs(child._ack.get(), True)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        # Explicit separate SAVE review; no approval or effect.
        panel._model.insert(0, "gpt-4o-mini")
        self._fire(panel._save)
        self.assertTrue(self.fixture.metadata_host.has_pending)
        self.assertIsNotNone(panel._ticket)
        self.assertIs(panel._operation, MetadataOperation.SAVE)
        original_ticket = panel._ticket
        owner = panel._owner_token
        host = self.fixture.metadata_host
        self.assertIs(host.pending_ui_operation(
            ticket=original_ticket, owner=owner), MetadataOperation.SAVE)
        self.assertFalse(self.fixture.metadata_path.exists())
        real_reject = TrustedMetadataCommitHost.reject_ui
        completed_rejections = []
        def recording_reject(instance, *, ticket, owner=None):
            if instance is not host:
                raise AssertionError("Foreign metadata host")
            receipt = real_reject(instance, ticket=ticket, owner=owner)
            completed_rejections.append((ticket, owner, receipt))
            return receipt
        # Class-level autospec is needed for this slotted host. Delegate to
        # the real method, recording only a fully returned rejection receipt.
        with mock.patch.object(TrustedMetadataCommitHost, "reject_ui",
                               autospec=True, side_effect=recording_reject):
            self._fire(panel._reject)
        self.assertEqual(len(completed_rejections), 1)
        self.assertEqual(completed_rejections[0][:2], (original_ticket, owner))
        receipt = completed_rejections[0][2]
        self.assertIs(type(receipt), MetadataCommitReceipt)
        self.assertIs(receipt.outcome, MetadataCommitOutcome.REFUSED)
        self.assertFalse(self.fixture.metadata_host.has_pending)
        self.assertIsNone(panel._ticket)
        self.assertIsNone(panel._operation)
        self.assertFalse(self.fixture.metadata_path.exists())
        self.assertIsNone(self.backend.value)
        self.assertEqual(self.validator.calls, 0)
        self.sim.close_current()
        self.root.update()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self._no_effects()
        self.sim.finish()
        self.assertEqual(callback_faults, [])


    def test_mapped_metadata_save_and_clear_need_distinct_approvals(self):
        # Full positive fake-only Tk path: reconciliation does not approve
        # either metadata operation, and CLEAR requires its own checkbox.
        callback_faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: callback_faults.append(kind.__name__))
        self._fire(self.sim.metadata_button)
        panel = self.sim.owned_manager
        host = self.fixture.metadata_host
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self.assertIs(child._ack.get(), True)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self.assertFalse(self.fixture.metadata_path.exists())
        panel._model.insert(0, "gpt-4o-mini")
        self._fire(panel._save)
        self.assertIs(panel._operation, MetadataOperation.SAVE)
        save_ticket = panel._ticket
        owner = panel._owner_token
        self.assertIs(host.pending_ui_operation(
            ticket=save_ticket, owner=owner), MetadataOperation.SAVE)
        self.assertFalse(self.fixture.metadata_path.exists())
        original_approve = TrustedMetadataCommitHost.approve_ui
        original_save = ProviderConnectionFileStore.save
        receipts = []
        prewrite_journals = []
        def recording_approve(instance, **kwargs):
            self.assertIs(instance, host)
            receipt = original_approve(instance, **kwargs)
            receipts.append((kwargs.copy(), receipt))
            return receipt
        def recording_save(instance, document):
            # Observe the actual re-read journal before real metadata I/O.
            self.assertIs(instance, host._store)
            controller = self.fixture.controller
            chain = controller._store.read()
            self.assertTrue(chain)
            last = chain[-1]
            self.assertEqual(last, controller._last)
            self.assertIs(last.state, RecoveryState.IN_FLIGHT)
            self.assertIsNotNone(controller._active)
            self.assertEqual(last.operation_id, controller._active.operation_id)
            expected_kind = ("save_metadata", "clear_metadata")[len(prewrite_journals)]
            self.assertEqual(last.operation_kind, expected_kind)
            # Public epoch/generation are intentionally None during
            # IN_FLIGHT; compare against the exact active permit instead.
            self.assertEqual(last.epoch, controller._active.epoch)
            self.assertEqual(last.generation, controller._active.generation)
            original_save(instance, document)
            prewrite_journals.append((last.operation_kind, document))
        with mock.patch.object(TrustedMetadataCommitHost, "approve_ui",
                               autospec=True, side_effect=recording_approve), mock.patch.object(
                                   ProviderConnectionFileStore, "save",
                                   autospec=True, side_effect=recording_save):
            self._fire(panel._approve)
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0][0]["ticket"], save_ticket)
            self.assertIs(receipts[0][0]["operation"], MetadataOperation.SAVE)
            self.assertIs(receipts[0][1].outcome, MetadataCommitOutcome.VERIFIED)
            self.assertEqual(len(prewrite_journals), 1)
            self.assertIsNone(panel._ticket)
            self.assertIsNone(panel._operation)
            self.assertIn("Metadata write verified by immediate file re-read",
                          panel._status.cget("text"))
            self.assertTrue(self.fixture.metadata_path.is_file())
            saved = host._store.load()
            expected_saved = parse_provider_connection_document({
                "schema_version": 1,
                "connection": {"provider": "openai", "model": "gpt-4o-mini",
                               "credential": "openai.api_key"},
            })
            self.assertIs(type(saved), ProviderConnectionDocumentV1)
            self.assertEqual(saved, expected_saved)
            self.assertEqual(prewrite_journals[0],
                             ("save_metadata", expected_saved))
            self._fire(panel._clear)
            self.assertIs(panel._operation, MetadataOperation.CLEAR)
            clear_ticket = panel._ticket
            self.assertNotEqual(clear_ticket, save_ticket)
            self.assertIs(host.pending_ui_operation(
                ticket=clear_ticket, owner=owner), MetadataOperation.CLEAR)
            self.assertIs(panel._clear_acknowledged.get(), False)
            self._fire(panel._approve)
            self.assertEqual(len(receipts), 1, "CLEAR approved without ACK")
            self.assertTrue(host.has_pending)
            self.assertIsNotNone(host._store.load().connection)
            self._fire(panel._clear_ack)
            self.assertIs(panel._clear_acknowledged.get(), True)
            self._fire(panel._approve)
        self.assertEqual(len(receipts), 2)
        self.assertEqual(len(prewrite_journals), 2)
        self.assertEqual(receipts[1][0]["ticket"], clear_ticket)
        self.assertIs(receipts[1][0]["operation"], MetadataOperation.CLEAR)
        self.assertIs(receipts[1][1].outcome, MetadataCommitOutcome.VERIFIED)
        self.assertIsNone(panel._ticket)
        self.assertIsNone(panel._operation)
        self.assertIn("Metadata write verified by immediate file re-read",
                      panel._status.cget("text"))
        cleared = host._store.load()
        expected_cleared = ProviderConnectionDocumentV1(connection=None)
        self.assertIs(type(cleared), ProviderConnectionDocumentV1)
        self.assertEqual(cleared, expected_cleared)
        self.assertEqual(prewrite_journals[1],
                         ("clear_metadata", expected_cleared))
        self._expect_cleared_metadata_document = True
        self.assertTrue(self.fixture.metadata_path.is_file())
        self.assertFalse(host.has_pending)
        self.assertIsNone(self.backend.value)
        self.assertEqual(self.validator.calls, 0)
        self.assertEqual(self.io_guard.attempts, [])
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(callback_faults, [])


    def test_mapped_credential_connect_invalid_candidate_never_writes(self):
        # Integrated real Tk event flow with fake INVALID validation. Recovery
        # acknowledgement does not itself authorize a CONNECT operation.
        callback_faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: callback_faults.append(kind.__name__))
        self.validator.result = CredentialValidationStatus.INVALID
        self._expected_fake_validation_calls = 1
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self.assertIsNotNone(panel)
        self.assertIsNone(panel._ticket)
        self.assertEqual(self.validator.calls, 0)
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self.assertIsNotNone(child)
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self.assertIs(child._ack.get(), True)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        self.assertIs(panel._operation, OnboardingOperation.CONNECT)
        original_ticket = panel._ticket
        self.assertIsNotNone(original_ticket)
        self.assertTrue(self.fixture.credential.coordinator.is_current_ui_ticket(
            ticket=original_ticket, owner_token=panel._owner_token,
            root=panel._root, operation=OnboardingOperation.CONNECT))
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self.assertEqual(panel._entry.cget("show"), "*")
        panel._entry.insert(0, "synthetic-invalid-key")
        self._fire(panel._approve)
        self.assertEqual(self.validator.calls, 1)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)
        self.assertIsNone(self.backend.value)
        self.assertIsNone(panel._ticket)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(callback_faults, [])


    def test_mapped_credential_connect_valid_fake_effect_is_not_durability_proof(self):
        # A real Tk event binds a single candidate and explicit approval to
        # an exact fake coordinator review. SUBMITTED != verified durability.
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
        self._expected_fake_validation_calls = 1
        self._expected_credential_puts = 1
        callback_faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: callback_faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        ticket = panel._ticket
        owner = panel._owner_token
        self.assertIs(panel._operation, OnboardingOperation.CONNECT)
        self.assertIsNotNone(ticket)
        self.assertTrue(self.fixture.credential.coordinator.is_current_ui_ticket(
            ticket=ticket, owner_token=owner, root=panel._root,
            operation=OnboardingOperation.CONNECT))
        panel._entry.insert(0, "fixture-synthetic-valid")
        original_approve = CooperativeOnboardingCoordinator.approve_ui
        completed = []
        def record_approve(instance, **kwargs):
            self.assertIs(instance, self.fixture.credential.coordinator)
            result = original_approve(instance, **kwargs)
            completed.append((kwargs, result))
            return result
        import contextlib
        import io
        captured_stdout, captured_stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                               autospec=True, side_effect=record_approve), (
                                   contextlib.redirect_stdout(captured_stdout)), (
                                   contextlib.redirect_stderr(captured_stderr)):
            self._fire(panel._approve)
        self.assertEqual(len(completed), 1)
        self.assertIs(completed[0][0]["operation"], OnboardingOperation.CONNECT)
        self.assertIs(completed[0][0]["ticket"], ticket)
        self.assertEqual(completed[0][0]["owner_token"], owner)
        from nayeon.brain.onboarding_coordination import (
            CoordinationReceipt, CoordinatedOutcome)
        from nayeon.brain.credential_operation_host import CredentialHostOutcome
        receipt = completed[0][1]
        self.assertIs(type(receipt), CoordinationReceipt)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(receipt.host_outcome, CredentialHostOutcome.SUBMITTED)
        self.assertEqual(self.backend.calls.count("put"), 1)
        self.assertEqual(self.validator.calls, 1)
        self.assertIs(type(self.backend.value), SecretValue)
        self.assertIsNone(panel._ticket)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.assertNotIn("successfully stored", panel._status.cget("text").lower())
        journal = self.fixture.controller.journal_path
        self.assertTrue(journal.is_file())
        evidence = {
            "route": "mapped Tk review plus explicit approve",
            "receipt": receipt.outcome.value,
            "host_outcome": receipt.host_outcome.value,
            "fake_validation_calls": self.validator.calls,
            "fake_puts": self.backend.calls.count("put"),
            "prohibited_attempts": len(self.io_guard.attempts),
        }
        self.assertEqual(evidence["prohibited_attempts"], 0)
        self.assertEqual(evidence["fake_puts"], 1)
        secret_marker = "fixture-synthetic-valid"
        disclosures = "\\n".join((
            captured_stdout.getvalue(), captured_stderr.getvalue(),
            panel._status.cget("text"), repr(receipt),
            repr(self.backend.value), repr(self.fixture.controller._last),
            repr(evidence),
        ))
        self.assertNotIn(secret_marker, disclosures)
        self.assertNotIn(secret_marker.encode("utf-8"), journal.read_bytes())
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(callback_faults, [])


    def test_mapped_credential_remove_requires_independent_delete_ack(self):
        # Preexisting fake key/config is fixture data, not live credentials.
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        from nayeon.brain.connection_document import parse_provider_connection_document
        expected_doc = parse_provider_connection_document({
            "schema_version": 1, "connection": {
                "provider": "openai", "model": "gpt-4o-mini",
                "credential": "openai.api_key"}})
        self.fixture.metadata_host._store.save(expected_doc)
        self.backend.value = SecretValue("synthetic-preexisting")
        self._expected_credential_deletes = 1
        callback_faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: callback_faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[2])
        self.assertIs(panel._operation, OnboardingOperation.REMOVE)
        ticket = panel._ticket
        self.assertIsNotNone(ticket)
        self.assertTrue(self.fixture.credential.coordinator.is_current_ui_ticket(
            ticket=ticket, owner_token=panel._owner_token,
            root=panel._root, operation=OnboardingOperation.REMOVE))
        self.assertIs(panel._acknowledged.get(), False)
        self._fire(panel._approve)
        self.assertIs(panel._ticket, ticket)
        self.assertTrue(self.fixture.credential.coordinator.has_pending)
        self.assertIsNotNone(self.backend.value)
        self.assertNotIn("delete", self.backend.calls)
        self.assertEqual(self.validator.calls, 0)
        self._fire(panel._delete_ack)
        self.assertIs(panel._acknowledged.get(), True)
        from nayeon.brain.onboarding_coordination import (
            CooperativeOnboardingCoordinator, CoordinationReceipt,
            CoordinatedOutcome)
        from nayeon.brain.credential_operation_host import CredentialHostOutcome
        original_approve = CooperativeOnboardingCoordinator.approve_ui
        receipts = []
        def record_approve(instance, **kwargs):
            self.assertIs(instance, self.fixture.credential.coordinator)
            result = original_approve(instance, **kwargs)
            receipts.append((kwargs, result))
            return result
        with mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                               autospec=True, side_effect=record_approve):
            self._fire(panel._approve)
        self.assertEqual(len(receipts), 1)
        self.assertIs(receipts[0][0]["operation"], OnboardingOperation.REMOVE)
        self.assertIs(receipts[0][0]["ticket"], ticket)
        self.assertIs(receipts[0][0]["acknowledged"], True)
        self.assertIs(type(receipts[0][1]), CoordinationReceipt)
        self.assertIs(receipts[0][1].outcome, CoordinatedOutcome.COMPLETED)
        self.assertIs(receipts[0][1].host_outcome, CredentialHostOutcome.SUBMITTED)
        self.assertEqual(self.backend.calls.count("delete"), 1)
        self.assertIsNone(self.backend.value)
        self.assertIsNone(panel._ticket)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.assertEqual(self.fixture.metadata_host._store.load(), expected_doc)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(callback_faults, [])


    def test_mapped_replace_invalid_preserves_exact_previous_fake_key(self):
        # Invalid replacement is refused: existing fake key and metadata stay.
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        prior = SecretValue("synthetic-prior")
        doc = parse_provider_connection_document({
            "schema_version": 1, "connection": {
                "provider": "openai", "model": "gpt-4o-mini",
                "credential": "openai.api_key"}})
        self.fixture.metadata_host._store.save(doc)
        self.backend.value = prior
        self.validator.result = CredentialValidationStatus.INVALID
        self._expected_fake_validation_calls = 1
        self._expected_preserved_key = prior
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[1])
        self.assertIs(panel._operation, OnboardingOperation.REPLACE)
        ticket = panel._ticket
        self.assertIsNotNone(ticket)
        self.assertTrue(self.fixture.credential.coordinator.is_current_ui_ticket(
            ticket=ticket, owner_token=panel._owner_token,
            root=panel._root, operation=OnboardingOperation.REPLACE))
        panel._entry.insert(0, "synthetic-invalid-replacement")
        self._fire(panel._approve)
        self.assertEqual(self.validator.calls, 1)
        self.assertIs(self.backend.value, prior)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)
        self.assertEqual(self.fixture.metadata_host._store.load(), doc)
        self.assertIsNone(panel._ticket)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_mapped_connect_indeterminate_validation_makes_no_fake_write(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        self.validator.result = CredentialValidationStatus.INDETERMINATE
        self._expected_fake_validation_calls = 1
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIs(panel._operation, OnboardingOperation.CONNECT)
        ticket = panel._ticket
        self.assertIsNotNone(ticket)
        self.assertTrue(self.fixture.credential.coordinator.is_current_ui_ticket(
            ticket=ticket, owner_token=panel._owner_token,
            root=panel._root, operation=OnboardingOperation.CONNECT))
        panel._entry.insert(0, "synthetic-indeterminate")
        self._fire(panel._approve)
        self.assertEqual(self.validator.calls, 1)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)
        self.assertIsNone(self.backend.value)
        self.assertIsNone(panel._ticket)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_mapped_replace_valid_fake_effect_preserves_metadata(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        prior = SecretValue("synthetic-existing")
        doc = parse_provider_connection_document({
            "schema_version": 1, "connection": {
                "provider": "openai", "model": "gpt-4o-mini",
                "credential": "openai.api_key"}})
        self.fixture.metadata_host._store.save(doc)
        self.backend.value = prior
        self._expected_fake_validation_calls = 1
        self._expected_credential_puts = 1
        self._expect_existing_metadata_after_put = True
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self.assertIs(child._review, self.fixture.controller._review)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[1])
        self.assertIs(panel._operation, OnboardingOperation.REPLACE)
        ticket = panel._ticket
        self.assertIsNotNone(ticket)
        self.assertTrue(self.fixture.credential.coordinator.is_current_ui_ticket(
            ticket=ticket, owner_token=panel._owner_token,
            root=panel._root, operation=OnboardingOperation.REPLACE))
        panel._entry.insert(0, "synthetic-valid-replacement")
        from nayeon.brain.onboarding_coordination import (
            CooperativeOnboardingCoordinator, CoordinationReceipt,
            CoordinatedOutcome)
        from nayeon.brain.credential_operation_host import CredentialHostOutcome
        original_approve = CooperativeOnboardingCoordinator.approve_ui
        receipts = []
        def record_approve(instance, **kwargs):
            self.assertIs(instance, self.fixture.credential.coordinator)
            result = original_approve(instance, **kwargs)
            receipts.append((kwargs, result))
            return result
        with mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                               autospec=True, side_effect=record_approve):
            self._fire(panel._approve)
        self.assertEqual(len(receipts), 1)
        self.assertIs(receipts[0][0]["operation"], OnboardingOperation.REPLACE)
        self.assertIs(receipts[0][0]["ticket"], ticket)
        self.assertIs(type(receipts[0][1]), CoordinationReceipt)
        self.assertIs(receipts[0][1].outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(receipts[0][1].host_outcome, CredentialHostOutcome.SUBMITTED)
        self.assertEqual(self.validator.calls, 1)
        self.assertEqual(self.backend.calls.count("put"), 1)
        self.assertIs(type(self.backend.value), SecretValue)
        self.assertIsNot(self.backend.value, prior)
        self.assertEqual(self.fixture.metadata_host._store.load(), doc)
        self.assertIsNone(panel._ticket)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_competing_real_credential_manager_does_not_steal_metadata_owner(self):
        # Construct an actual second management window under the same fake
        # root; admission must refuse a foreign owner even if GUI is visible.
        import tkinter as tk
        from nayeon.desktop_alpha.first_run_credential_management_window import (
            FirstRunCredentialManagementWindow)
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.metadata_button)
        first = self.sim.owned_manager
        owner = first._owner_token
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=owner))
        foreign_root = tk.Toplevel(self.root)
        foreign = FirstRunCredentialManagementWindow(
            foreign_root, coordinator=self.fixture.credential.coordinator)
        self.root.update()
        self.assertFalse(self.fixture.controller.is_ui_window_owner(
            foreign._owner_token))
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=owner))
        self._fire(foreign._choices[0])
        self.assertIsNone(foreign._ticket)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=owner))
        foreign_root.destroy()
        self.root.update()
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=owner))
        self.sim.finish()
        self._no_effects()
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(faults, [])

    def test_wrong_owner_and_root_cannot_consume_mapped_connect_review(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        from nayeon.brain.onboarding_coordination import CoordinatedOutcome
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        ticket = panel._ticket
        self.assertIsNotNone(ticket)
        coord = self.fixture.credential.coordinator
        for owner, root in (("synthetic-wrong-owner", panel._root),
                            (panel._owner_token, self.root)):
            denied = coord.approve_ui(
                ticket=ticket, owner_token=owner, root=root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic-never-written"),
                acknowledged=False)
            self.assertIs(denied.outcome, CoordinatedOutcome.REFUSED)
            self.assertTrue(coord.is_current_ui_ticket(
                ticket=ticket, owner_token=panel._owner_token,
                root=panel._root, operation=OnboardingOperation.CONNECT))
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self._fire(panel._reject)
        self.assertIsNone(panel._ticket)
        self.assertFalse(coord.has_pending)
        self.sim.finish()
        self._no_effects()
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(faults, [])


    def test_destroy_recovery_child_cancels_exact_review_not_manager_owner(self):
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.metadata_button)
        panel = self.sim.owned_manager
        owner = panel._owner_token
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self.assertIsNotNone(child)
        self._fire(child._review_button)
        captured = child._review
        self.assertIsNotNone(captured)
        self.assertIs(self.fixture.controller._review, captured)
        child._root.destroy()
        self.root.update()
        self.assertIsNone(self.fixture.controller._review)
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=owner))
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.fixture.metadata_host.has_pending)
        self.sim.finish()
        self._no_effects()
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(faults, [])


    def test_destroy_credential_window_during_real_approval_callback(self):
        # Destruction while the actual mapped Tk approval callback is active
        # must defer exact-owner release and prevent a stale credential effect.
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        from nayeon.brain.onboarding_coordination import (
            CooperativeOnboardingCoordinator, CoordinatedOutcome)
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIs(panel._operation, OnboardingOperation.CONNECT)
        self.assertIsNotNone(panel._ticket)
        panel._entry.insert(0, "synthetic-must-not-store")
        real_approve = CooperativeOnboardingCoordinator.approve_ui
        outcomes = []
        def destroy_then_delegate(instance, **kwargs):
            self.assertIs(instance, self.fixture.credential.coordinator)
            panel._root.destroy()
            result = real_approve(instance, **kwargs)
            outcomes.append(result.outcome)
            return result
        with mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                               autospec=True, side_effect=destroy_then_delegate):
            self._fire(panel._approve)
        # Negative control: a destroyed owning Tk root cannot authorize a
        # new fake credential effect, irrespective of receipt category.
        self.assertNotIn("put", self.backend.calls,
                         "Fake credential write occurred after root destruction")
        self.assertEqual(outcomes, [CoordinatedOutcome.REFUSED])
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.fixture.controller._ui_window_owner)
        self.sim.finish()
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_digest_reentrancy_destroyed_tk_root_cannot_write_fake_key(self):
        # Adversarial trusted digest callback destroys the real owner while
        # coordinator admission is in progress; no backend write may follow.
        from nayeon.brain import onboarding_coordination as module
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIsNotNone(panel._ticket)
        panel._entry.insert(0, "synthetic-digest-destroy")
        real_digest = module.canonical_evidence_digest
        hits = []
        def destroy_on_digest(*args, **kwargs):
            hits.append(1)
            panel._root.destroy()
            return real_digest(*args, **kwargs)
        with mock.patch.object(module, "canonical_evidence_digest",
                               side_effect=destroy_on_digest):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertNotIn("put", self.backend.calls)
        self.assertEqual(self.validator.calls, 0)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_wrong_recovery_fingerprint_cannot_admit_current_tk_review(self):
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.metadata_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        review = child._review
        self.assertIs(review, self.fixture.controller._review)
        denied = self.fixture.controller.approve_reconciliation(
            human_approved=True, fingerprint="synthetic-wrong-fingerprint",
            expected_review=review)
        self.assertIs(denied, False)
        self.assertFalse(self.fixture.controller.ready)
        self.assertIs(self.fixture.controller._review, review)
        self._fire(child._reject)
        self.assertIsNone(self.fixture.controller._review)
        self.sim.finish()
        self._no_effects()
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(faults, [])

    def test_registered_tk_wm_delete_protocol_closes_exact_manager(self):
        # Tcl executes the registered WM_DELETE_WINDOW handler through Tk;
        # this is not a claim of a physical operating-system close event.
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.metadata_button)
        child = self.sim.owned_child
        manager = self.sim.owned_manager
        owner = manager._owner_token
        self.assertTrue(self.fixture.metadata_host.has_ui_owner(owner=owner))
        tcl_handler = self.root.tk.call(
            "wm", "protocol", str(child), "WM_DELETE_WINDOW")
        self.assertIs(type(tcl_handler), str)
        self.assertTrue(tcl_handler)
        self.root.tk.eval(tcl_handler)
        self.root.update()
        self.assertFalse(child.winfo_exists())
        self.assertIsNone(manager._owner_token)
        self.assertFalse(self.fixture.metadata_host.has_ui_owner(owner=owner))
        self.assertIsNone(self.fixture.controller._ui_window_owner)
        self.sim.finish()
        self._no_effects()
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(faults, [])


    def test_late_host_observation_destroyed_root_never_writes_fake_credential(self):
        from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIsNotNone(panel._ticket)
        panel._entry.insert(0, "synthetic-host-reentry")
        original = TrustedCredentialOperationHost._fresh
        hits = []
        def destroy_during_observation(host):
            hits.append(1)
            panel._root.destroy()
            return original(host)
        with mock.patch.object(TrustedCredentialOperationHost, "_fresh",
                               autospec=True, side_effect=destroy_during_observation):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertNotIn("put", self.backend.calls)
        self.assertEqual(self.validator.calls, 0)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])

    def test_late_validator_destroyed_root_never_writes_fake_credential(self):
        from tests.a02_fake_isolation_support import FakeValidator
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIsNotNone(panel._ticket)
        panel._entry.insert(0, "synthetic-validator-reentry")
        self._expected_fake_validation_calls = 1
        original = FakeValidator.validate
        hits = []
        def destroy_during_validation(instance, value):
            self.assertIs(instance, self.validator)
            result = original(instance, value)
            hits.append(1)
            panel._root.destroy()
            return result
        with mock.patch.object(FakeValidator, "validate", autospec=True,
                               side_effect=destroy_during_validation):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertEqual(self.validator.calls, 1)
        self.assertNotIn("put", self.backend.calls)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_final_availability_reentrancy_destroyed_root_never_writes(self):
        from tests.a02_fake_isolation_support import FakeBackend
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIsNotNone(panel._ticket)
        panel._entry.insert(0, "synthetic-final-availability")
        self._expected_fake_validation_calls = 1
        original = FakeBackend.is_available
        hits = []
        def destroy_after_validation(backend, identifier):
            self.assertIs(backend, self.backend)
            if self.validator.calls == 1 and not hits:
                hits.append(1)
                panel._root.destroy()
            return original(backend, identifier)
        with mock.patch.object(FakeBackend, "is_available", autospec=True,
                               side_effect=destroy_after_validation):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertEqual(self.validator.calls, 1)
        self.assertNotIn("put", self.backend.calls)
        self.assertIsNone(self.backend.value)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])

    def test_late_review_clock_destroyed_root_never_reaches_validation(self):
        from nayeon.brain.onboarding_review_session import OnboardingReviewSession
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        self._fire(self.sim.credential_button)
        panel = self.sim.owned_manager
        self._fire(panel._recovery_button)
        child = panel._recovery_dialog
        self._fire(child._review_button)
        self._fire(child._ack_button)
        self._fire(child._approve)
        self.assertTrue(self.fixture.controller.ready)
        self._fire(panel._choices[0])
        self.assertIsNotNone(panel._ticket)
        panel._entry.insert(0, "synthetic-review-clock")
        original = OnboardingReviewSession._now
        hits = []
        def destroy_during_clock(session):
            hits.append(1)
            panel._root.destroy()
            return original(session)
        with mock.patch.object(OnboardingReviewSession, "_now", autospec=True,
                               side_effect=destroy_during_clock):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self.assertFalse(self.fixture.credential.coordinator.has_pending)
        self.sim.finish()
        self.assertFalse(self.fixture.controller.ready)
        self.assertFalse(self.mutex.active)
        self.assertEqual(self.mutex.entries, self.mutex.exits)
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


    def test_legacy_candidate_window_host_reentrancy_must_stop_validation(self):
        import tkinter as tk
        from nayeon.desktop_alpha.first_run_credential_validation_window import (
            FirstRunCredentialValidationWindow)
        from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        child = tk.Toplevel(self.root)
        panel = FirstRunCredentialValidationWindow(
            child, host=self.fixture.credential.host)
        self.root.update()
        self._fire(panel._request)
        self.assertIsNotNone(panel._validation_ticket)
        panel._entry.insert(0, "synthetic-candidate-late-observe")
        original = TrustedCredentialOperationHost._fresh
        hits = []
        def destroy_and_observe(host):
            hits.append(1)
            child.destroy()
            return original(host)
        with mock.patch.object(TrustedCredentialOperationHost, "_fresh",
                               autospec=True, side_effect=destroy_and_observe):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertEqual(self.validator.calls, 0)
        self.assertFalse(self.fixture.credential.host.has_pending)
        self.assertNotIn("put", self.backend.calls)
        self.sim.finish()
        self._no_effects()
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])

    def test_legacy_candidate_window_clock_reentrancy_must_stop_validation(self):
        import tkinter as tk
        from nayeon.desktop_alpha.first_run_credential_validation_window import (
            FirstRunCredentialValidationWindow)
        from nayeon.brain.onboarding_review_session import OnboardingReviewSession
        faults = []
        self.root.report_callback_exception = (
            lambda kind, value, tb: faults.append(kind.__name__))
        child = tk.Toplevel(self.root)
        panel = FirstRunCredentialValidationWindow(
            child, host=self.fixture.credential.host)
        self.root.update()
        self._fire(panel._request)
        self.assertIsNotNone(panel._validation_ticket)
        panel._entry.insert(0, "synthetic-candidate-late-clock")
        original = OnboardingReviewSession._now
        hits = []
        def destroy_on_clock(session):
            hits.append(1)
            child.destroy()
            return original(session)
        with mock.patch.object(OnboardingReviewSession, "_now",
                               autospec=True, side_effect=destroy_on_clock):
            self._fire(panel._approve)
        self.assertEqual(hits, [1])
        self.assertEqual(self.validator.calls, 0)
        self.assertFalse(self.fixture.credential.host.has_pending)
        self.assertNotIn("put", self.backend.calls)
        self.sim.finish()
        self._no_effects()
        self.assertEqual(self.io_guard.attempts, [])
        self.assertEqual(faults, [])


class StagedHistoricalMigrationIntegrityTests(unittest.TestCase):
    """Both migration pins protect index bytes before and after commits."""

    def test_staged_and_committed_divergence_rejected_for_both_pins(self):
        import hashlib
        import tempfile
        from tests import phase_8_29_lifecycle_scope_migration as migration

        for path in tuple(migration.PINNED_SHA256):
            with self.subTest(path=path):
                approved = (migration.ROOT / path).read_bytes()
                baseline = b"old protected source for isolated fixture\n"
                with tempfile.TemporaryDirectory(prefix="nayeon_829_staged_guard_") as folder:
                    root = Path(folder)
                    target = root / path
                    target.parent.mkdir(parents=True)
                    def git(*args):
                        return subprocess.run(
                            ["git", *args], cwd=root, capture_output=True,
                            text=True, check=True,
                        )
                    git("init", "-q")
                    target.write_bytes(baseline)
                    git("add", "--", path)
                    git("-c", "user.name=Fake Test", "-c",
                        "user.email=fake@example.invalid", "commit", "-qm", "base")
                    protected_head = git("rev-parse", "HEAD").stdout.strip()
                    target.write_bytes(approved)
                    # HEAD still equals the pinned pre-8.29 baseline before staging.
                    with mock.patch.object(migration, "ROOT", root), \
                         mock.patch.object(migration, "PROTECTED_HEAD", protected_head), \
                         mock.patch.dict(
                             migration.PINNED_BASELINE_SHA256,
                             {path: hashlib.sha256(baseline).hexdigest()},
                         ):
                        migration._assert_exact_migration(path)
                        # The index contains unapproved source, despite good disk bytes.
                        target.write_bytes(b"malicious staged source\n")
                        git("add", "--", path)
                        target.write_bytes(approved)
                        with self.assertRaisesRegex(
                            AssertionError, "Staged historical source differs"
                        ):
                            migration._assert_exact_migration(path)
                        git("add", "--", path)
                        migration._assert_exact_migration(path)
                        # Approved postcommit remains accepted.
                        git("-c", "user.name=Fake Test", "-c",
                            "user.email=fake@example.invalid", "commit",
                            "-qm", "approved")
                        migration._assert_exact_migration(path)
                        # Cached diff is empty following a malicious commit.
                        target.write_bytes(b"malicious committed source\n")
                        git("add", "--", path)
                        git("-c", "user.name=Fake Test", "-c",
                            "user.email=fake@example.invalid", "commit",
                            "-qm", "unauthorized")
                        target.write_bytes(approved)
                        with self.assertRaisesRegex(
                            AssertionError, "Staged historical source differs"
                        ):
                            migration._assert_exact_migration(path)

    def test_actual_repository_prestaging_or_postcommit_index_is_pinned(self):
        from tests import phase_8_29_lifecycle_scope_migration as migration
        for path in migration.PINNED_SHA256:
            with self.subTest(path=path):
                migration._assert_exact_migration(path)


if __name__ == "__main__":
    unittest.main()
