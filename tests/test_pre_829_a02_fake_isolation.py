"""A-02 fake-only isolation acceptance; NO real SDK, network or WinCred IO."""
import builtins
from contextlib import ExitStack
import ctypes
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest
from unittest import mock

from nayeon.brain.credential_onboarding_composition import compose_openai_credential_onboarding
from nayeon.brain.onboarding_coordination import CoordinatedOutcome
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
from nayeon.brain.windows_onboarding_mutex import WindowsOnboardingMutex
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.lifecycle import CredentialValidationStatus
from tests.a02_fake_isolation_support import (
    FakeBackend, FakeValidator, FakeObserver, FakeMutex, FakeTempRoot,
    compose_fake_only_onboarding,
)


class ProhibitedIO:
    """Attempt-counting poison; no actual prohibited operation can complete."""
    def __init__(self):
        # Records only calls to patched forbidden entrypoints. There is no
        # fabricated "completed" metric: each poison raises before delegation.
        self.attempts = []
        self.stack = ExitStack()

    def deny(self, label):
        def refused(*args, **kwargs):
            self.attempts.append(label)
            raise AssertionError("A02_PROHIBITED_" + label)
        return refused

    def __enter__(self):
        self.stack.__enter__()
        try:
            self.stack.enter_context(mock.patch.object(
                socket, "socket", side_effect=self.deny("socket")))
            self.stack.enter_context(mock.patch.object(
                socket, "create_connection", side_effect=self.deny("network")))
            self.stack.enter_context(mock.patch.object(
                ctypes, "WinDLL", side_effect=self.deny("native"), create=True))
            self.stack.enter_context(mock.patch.object(
                WindowsOnboardingMutex, "hold", self.deny("native_mutex")))
            self.stack.enter_context(mock.patch(
                "nayeon.secrets.windows_credential._load_advapi32",
                side_effect=self.deny("wincred")))
            self.stack.enter_context(mock.patch(
                "nayeon.brain.providers.openai_client._load_openai_sdk",
                side_effect=self.deny("sdk")))
            original = builtins.__import__
            def protected_import(name, *args, **kwargs):
                if name.split(".", 1)[0] in {
                    "openai", "httpx", "win32cred", "keyring", "requests",
                }:
                    return self.deny("forbidden_import")()
                return original(name, *args, **kwargs)
            self.stack.enter_context(mock.patch.object(
                builtins, "__import__", protected_import))
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)


class FakeOnlyCompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = FakeTempRoot()
        self.addCleanup(self.tmp.cleanup)
        self.path = self.tmp.path / "provider.json"
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.observer = FakeObserver(self.backend)
        self.mutex = FakeMutex()

    def build(self, **overrides):
        kwargs = dict(backend=self.backend, validator=self.validator,
                      observer=self.observer, mutex=self.mutex,
                      temp_root=self.tmp, metadata_path=self.path)
        kwargs.update(overrides)
        composed = compose_fake_only_onboarding(**kwargs)
        self.addCleanup(lambda: composed.controller.close()
                        if composed.controller._ctx is not None else None)
        return composed

    def test_no_prohibited_import_or_native_effect_on_construction_and_review(self):
        with ProhibitedIO() as guard:
            fixture = self.build()
            self.assertIs(fixture.backend, self.backend)
            self.assertIs(fixture.observer.backend, fixture.backend)
            self.assertIs(fixture.coordinator._availability, self.observer)
            self.assertIs(fixture.coordinator._mutex, self.mutex)
            self.assertIs(fixture.controller._mutex, self.mutex)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.validator.calls, 0)
            review = fixture.controller.request_reconciliation()
            self.assertTrue(fixture.controller.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint,
                expected_review=review))
            self.assertIs(
                fixture.coordinator.request(OnboardingOperation.TEST_CANDIDATE).outcome,
                CoordinatedOutcome.PENDING)
            receipt = fixture.coordinator.approve(
                candidate=SecretValue("a02-synthetic-only"))
            self.assertIs(receipt.outcome, CoordinatedOutcome.COMPLETED)
            self.assertEqual(self.validator.calls, 1)
            self.assertNotIn("put", self.backend.calls)
            self.assertNotIn("delete", self.backend.calls)
            self.assertEqual(guard.attempts, [])

    def test_negative_dependency_types_and_missing_args_have_no_side_effect(self):
        class Poison:
            def __getattr__(self, name):
                raise AssertionError("unsafe reflection")

        class SubBackend(FakeBackend):
            pass

        bad = [
            {"backend": None}, {"backend": Poison()},
            {"backend": SubBackend()}, {"backend": object()},
            {"validator": object()}, {"validator": None},
            {"observer": Poison()}, {"observer": FakeObserver(FakeBackend())},
            {"mutex": WindowsOnboardingMutex()}, {"mutex": None},
            {"temp_root": object()}, {"metadata_path": object()},
        ]
        with ProhibitedIO() as guard:
            with self.assertRaises(TypeError):
                compose_fake_only_onboarding()
            for override in bad:
                with self.subTest(override=next(iter(override))):
                    with self.assertRaises((TypeError, ValueError)):
                        self.build(**override)
            self.assertEqual(guard.attempts, [])
            self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, 0)
        self.assertFalse(self.path.exists())

    def test_observer_backend_identity_cannot_be_replaced_after_construction(self):
        with ProhibitedIO() as guard:
            fixture = self.build()
            for field in ("backend", "_backend"):
                with self.subTest(field=field):
                    with self.assertRaises(AttributeError):
                        setattr(self.observer, field, FakeBackend())
            self.assertIs(fixture.observer.backend, fixture.backend)
            self.assertIs(fixture.coordinator._availability, fixture.observer)
            self.assertEqual(guard.attempts, [])

    def test_path_alias_escape_and_duplicate_composition_rejected(self):
        outside = self.path.parent.parent / "provider.json"
        variants = [outside, self.path.with_name("other.json"),
                    self.path.parent / ".." / self.path.parent.name / "provider.json"]
        with ProhibitedIO() as guard:
            for p in variants:
                with self.subTest(path=str(p)):
                    with self.assertRaises(ValueError):
                        self.build(metadata_path=p)
            built = self.build()
            with self.assertRaises(ValueError):
                self.build()
            self.assertIs(built.coordinator._availability, self.observer)
            self.assertEqual(guard.attempts, [])

    def test_validator_tri_state_and_synthetic_secrets_never_rendered(self):
        for result in CredentialValidationStatus:
            with self.subTest(status=result):
                validator = FakeValidator(result)
                backend = FakeBackend()
                secret = SecretValue("a02-DO-NOT-LOG-SYNTHETIC")
                with ProhibitedIO() as guard:
                    lifecycle = compose_fake_only_onboarding
                    # Each status gets a fresh exact TemporaryDirectory owner.
                    manager = FakeTempRoot()
                    with manager as temp:
                        path = temp.path / "provider.json"
                        observer = FakeObserver(backend)
                        mutex = FakeMutex()
                        fixture = lifecycle(
                            backend=backend, validator=validator, observer=observer,
                            mutex=mutex, temp_root=manager,
                            metadata_path=path,
                        )
                        self.assertIs(fixture.host._TrustedCredentialOperationHost__onboarding.test_candidate(secret), result)
                        output = repr(fixture) + repr(backend) + repr(validator) + repr(secret)
                        self.assertNotIn("a02-DO-NOT-LOG-SYNTHETIC", output)
                        self.assertEqual(guard.attempts, [])
                self.assertEqual(validator.calls, 1)

    def test_production_factory_negative_control_hits_blocked_sdk(self):
        # Intentionally exercise a *blocked* forbidden production route.
        # It must NOT send any request; the one attempted SDK access proves
        # the interceptor is armed. This is NOT normal harness execution.
        with ProhibitedIO() as guard:
            real = compose_openai_credential_onboarding(self.backend)
            outcome = real.test_candidate(SecretValue("a02-synthetic-sdk-control"))
            self.assertIs(outcome, CredentialValidationStatus.INDETERMINATE)
            self.assertEqual(guard.attempts, ["sdk"])
            self.assertEqual(self.backend.calls, [])

    def test_all_native_network_and_sdk_tripwires_are_real_negative_controls(self):
        # Positive evidence that a poisoned route CANNOT complete. Expected
        # attempts here are separate from the zero-attempt allowed-harness case.
        from nayeon.secrets import windows_credential
        from nayeon.brain.providers import openai_client
        with ProhibitedIO() as guard:
            blocked = [
                lambda: socket.socket(),
                lambda: socket.create_connection(("127.0.0.1", 9)),
                lambda: ctypes.WinDLL("Advapi32.dll"),
                lambda: windows_credential._load_advapi32(),
                lambda: openai_client._load_openai_sdk(),
                lambda: builtins.__import__("openai"),
                lambda: WindowsOnboardingMutex().hold(),
            ]
            for operation in blocked:
                with self.subTest(index=len(guard.attempts)):
                    with self.assertRaisesRegex(AssertionError, "A02_PROHIBITED_"):
                        operation()
        self.assertEqual(guard.attempts, [
            "socket", "network", "native", "wincred", "sdk",
            "forbidden_import", "native_mutex",
        ])

    def test_red_mutable_fake_class_lookup_and_descriptor_fail_closed(self):
        from tests import a02_fake_isolation_support as support
        impostor_class = type("ImpostorBackend", (), {
            "get": lambda self, identifier: None,
            "put": lambda self, identifier, value: None,
            "delete": lambda self, identifier: False,
            "is_available": lambda self, identifier: False,
        })
        with ProhibitedIO() as guard:
            # Rebinding a mutable module global must never make an untrusted
            # object into the exact fake backend allowed by this factory.
            with mock.patch.object(support, "FakeBackend", impostor_class):
                with self.assertRaises((TypeError, ValueError)):
                    self.build(backend=impostor_class())
            # A poisoned property must be detected before its getter executes.
            with mock.patch.object(FakeObserver, "backend",
                                   property(lambda _: (_ for _ in ()).throw(
                                       AssertionError("POISON_GETTER_EXECUTED")))):
                with self.assertRaises((TypeError, ValueError)):
                    self.build()
            self.assertEqual(guard.attempts, [])

    def test_red_direct_object_setattr_retarget_must_fail_closed(self):
        fixture = self.build()
        alien = FakeBackend()
        object.__setattr__(self.observer, "_backend", alien)
        with ProhibitedIO() as guard:
            with self.assertRaises((TypeError, ValueError, RuntimeError)):
                fixture.observer.is_available(
                    __import__("nayeon.secrets.contracts", fromlist=["SecretIdentifier"])
                    .SecretIdentifier("openai.api_key"))
            self.assertEqual(guard.attempts, [])
        self.assertNotIn("is_available", alien.calls)

    def test_red_mutated_temporary_owner_name_must_fail_closed(self):
        with TemporaryDirectory(prefix="nayeon-a02-alien-") as alien:
            old_name = self.tmp._manager.name
            try:
                self.tmp._manager.name = alien
                with ProhibitedIO() as guard:
                    with self.assertRaises((TypeError, ValueError)):
                        self.build(metadata_path=Path(alien) / "provider.json")
                    self.assertEqual(guard.attempts, [])
            finally:
                self.tmp._manager.name = old_name

    def test_red_preexisting_metadata_file_must_be_rejected(self):
        self.path.write_text('{"synthetic":true}', encoding="utf-8")
        with ProhibitedIO() as guard:
            with self.assertRaises((TypeError, ValueError)):
                self.build()
            self.assertEqual(guard.attempts, [])
        self.assertEqual(self.validator.calls, 0)
        self.assertEqual(self.backend.calls, [])

    def test_guarded_fresh_subprocess_import_and_factory_no_external_io(self):
        script = textwrap.dedent("""
            import builtins, ctypes, os, socket, sys
            from unittest import mock
            from pathlib import Path
            from tempfile import TemporaryDirectory
            sys.path.insert(0, os.getcwd())
            attempts=[]
            real_import=builtins.__import__
            def denied(label):
                def handler(*args, **kw):
                    attempts.append(label)
                    raise AssertionError("PROHIBITED_"+label)
                return handler
            def import_guard(name, *args, **kw):
                if name.split(".",1)[0] in {"openai","httpx","win32cred","keyring","requests"}:
                    return denied("sdk_import")()
                return real_import(name, *args, **kw)
            with mock.patch.object(socket,"socket",side_effect=denied("socket")), \\
                 mock.patch.object(socket,"create_connection",side_effect=denied("network")), \\
                 mock.patch.object(ctypes,"WinDLL",side_effect=denied("native"),create=True), \\
                 mock.patch.object(builtins,"__import__",import_guard):
                from tests.a02_fake_isolation_support import (
                    FakeBackend, FakeValidator, FakeObserver, FakeMutex,
                    FakeTempRoot, compose_fake_only_onboarding)
                temporary=FakeTempRoot()
                with temporary as temp:
                    backend=FakeBackend()
                    composed=compose_fake_only_onboarding(
                        backend=backend, validator=FakeValidator(),
                        observer=FakeObserver(backend),mutex=FakeMutex(),
                        temp_root=temporary,
                        metadata_path=temp.path/"provider.json")
                assert not attempts, attempts
            print("A02_IMPORT_GUARDED_OK")
        """)
        self.assertIn("A02_IMPORT_GUARDED_OK", script)
        result = subprocess.run(
            [sys.executable, "-I", "-c", script],
            cwd=str(Path(__file__).resolve().parents[1]),
            capture_output=True, text=True, timeout=18,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-1800:])
        self.assertEqual(result.stdout.strip(), "A02_IMPORT_GUARDED_OK")


if __name__ == "__main__":
    unittest.main()
