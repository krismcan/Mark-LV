"""P298: historical P96 default effects stay retired; fakes are test seams.

Run directly with python -I -B tests/test_byok_c1_p298_effect_boundary.py.
No native credential access, provider validation, or OS isolation is claimed.
"""

import ctypes
from contextlib import contextmanager
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


# Isolated Python omits the repository from sys.path when running this file.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _native_load_forbidden(*args, **kwargs):
    raise AssertionError("P298 must never load a native DLL")


with patch.object(ctypes, "WinDLL", create=True,
                  side_effect=_native_load_forbidden) as _import_loader:
    from nayeon.secrets import windows_credential as credential
    from nayeon.secrets.contracts import (
        SecretIdentifier, SecretStorageError, SecretValue,
    )
    from nayeon.brain import local_byok_user_scope as byok
    _import_loader.assert_not_called()


class _InjectedObjectFake:
    """Construction-only deterministic seam, never a production backend mode."""

    def __init__(self):
        self.present = False
        self.mutations = []

    def contains(self, target):
        if target != "nayeon-v1/secret/openai.api_key":
            raise AssertionError("Unexpected target")
        return self.present

    def write(self, target, blob, kind, persistence, username):
        self.mutations.append(("write", target, blob, kind, persistence, username))
        self.present = True

    def delete(self, target):
        self.mutations.append(("delete", target))
        self.present = False
        return True


class _InjectedMutexFake:
    @contextmanager
    def hold(self):
        yield byok.MutexAdmission.HELD


class P298DefaultEffectBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.win_dll = patch.object(
            ctypes, "WinDLL", create=True, side_effect=_native_load_forbidden,
        ).start()
        self.addCleanup(patch.stopall)
        self.loader = patch.object(
            credential, "_load_advapi32", side_effect=_native_load_forbidden,
        ).start()
        self.identifier = SecretIdentifier("openai.api_key")
        self.value = SecretValue("p298-not-a-key")
        self.backend = credential.WindowsCredentialBackend()
        self.controller = byok.LocalByokController(self.backend)

    def tearDown(self):
        # A caught tripwire exception must still fail the test.
        self.loader.assert_not_called()
        self.win_dll.assert_not_called()

    def assert_storage_denied(self, action):
        with self.assertRaises(SecretStorageError) as raised:
            action()
        self.assertIs(type(raised.exception), SecretStorageError)
        self.assertEqual(str(raised.exception), "Secret storage operation failed")

    def assert_refused(self, controller, review, **kwargs):
        self.assertIs(controller.approve(review, **kwargs),
                      byok.LocalByokOutcome.REFUSED)

    def injected_controller(self):
        fake = _InjectedObjectFake()
        backend = credential.WindowsCredentialBackend(_native=fake)
        controller = byok.LocalByokController(backend, _mutex=_InjectedMutexFake())
        return fake, backend, controller

    def test_default_construction_has_no_effect_binding(self):
        self.assertIsNone(self.backend._injected_mutation_adapter())
        self.assertIsNone(self.backend._injected_read_adapter)
        self.assertFalse(self.controller.mutation_available)

    def test_default_get_denies_with_fixed_error(self):
        self.assert_storage_denied(lambda: self.backend.get(self.identifier))

    def test_default_put_denies_with_fixed_error(self):
        self.assert_storage_denied(
            lambda: self.backend.put(self.identifier, self.value))

    def test_default_delete_denies_with_fixed_error(self):
        self.assert_storage_denied(lambda: self.backend.delete(self.identifier))

    def test_default_begin_save_is_denied(self):
        self.assertIsNone(self.controller.begin(byok.LocalByokOperation.SAVE))

    def test_default_begin_replace_is_denied(self):
        self.assertIsNone(self.controller.begin(byok.LocalByokOperation.REPLACE))

    def test_default_begin_remove_is_denied(self):
        self.assertIsNone(self.controller.begin(byok.LocalByokOperation.REMOVE))

    def test_default_approve_without_review_is_refused(self):
        self.assert_refused(self.controller, None, confirmed=True,
                            candidate=self.value)

    def test_default_forged_review_is_refused(self):
        review = byok.LocalByokReview(byok.LocalByokOperation.SAVE, False, "")
        self.assert_refused(self.controller, review, confirmed=True,
                            candidate=self.value)

    def test_default_forged_pending_remove_is_refused(self):
        review = byok.LocalByokReview(byok.LocalByokOperation.REMOVE, True, "")
        self.controller._pending = review
        self.assert_refused(self.controller, review, confirmed=True,
                            deletion_acknowledged=True)
        self.assertIsNone(self.controller._pending)

    def test_default_wrong_operation_is_denied(self):
        wrong_operation = object()
        self.assertIsNone(self.controller.begin(wrong_operation))
        review = byok.LocalByokReview(wrong_operation, False, "")
        self.controller._pending = review
        self.assert_refused(self.controller, review, confirmed=True,
                            candidate=self.value)

    def test_production_composition_constructs_default_backend(self):
        composed = byok.compose_user_scope_local_byok()
        self.assertIs(type(composed), byok.LocalByokController)
        self.assertIs(type(composed._backend), credential.WindowsCredentialBackend)
        self.assertIsNone(composed._backend._native)
        self.assertIsNone(composed._backend._injected_mutation_adapter())
        self.assertFalse(composed.mutation_available)
        for operation in byok.LocalByokOperation:
            with self.subTest(operation=operation):
                self.assertIsNone(composed.begin(operation))
        self.assert_refused(composed, None, confirmed=True, candidate=self.value)

    def test_explicit_object_injection_receives_only_fake_mutations(self):
        fake, backend, controller = self.injected_controller()
        self.assertIs(backend._injected_mutation_adapter(), fake)
        self.assertTrue(controller.mutation_available)
        self.assertEqual(fake.mutations, [])
        self.assert_storage_denied(
            lambda: self.backend.put(self.identifier, self.value))
        self.assert_storage_denied(lambda: self.backend.delete(self.identifier))
        self.assertEqual(fake.mutations, [])
        backend.put(self.identifier, self.value)
        self.assertTrue(backend.delete(self.identifier))
        self.assertEqual(fake.mutations, [
            ("write", "nayeon-v1/secret/openai.api_key", b"p298-not-a-key",
             1, 2, "nayeon-v1"),
            ("delete", "nayeon-v1/secret/openai.api_key"),
        ])

    def test_injected_seam_rejects_forged_review_and_wrong_operation(self):
        fake, _, controller = self.injected_controller()
        review = controller.begin(byok.LocalByokOperation.SAVE)
        self.assertIsNotNone(review)
        forged = byok.LocalByokReview(review.operation, review.original_present,
                                     review.ticket)
        self.assert_refused(controller, forged, confirmed=True, candidate=self.value)
        self.assertTrue(controller.reject(review))
        wrong_operation = object()
        self.assertIsNone(controller.begin(wrong_operation))
        wrong_review = byok.LocalByokReview(wrong_operation, False, "")
        controller._pending = wrong_review
        self.assert_refused(controller, wrong_review, confirmed=True,
                            candidate=self.value)
        self.assertEqual(fake.mutations, [])

    def test_explicit_fake_review_workflow_does_not_enable_production(self):
        fake, _, controller = self.injected_controller()
        review = controller.begin(byok.LocalByokOperation.SAVE)
        self.assertIsNotNone(review)
        self.assertEqual(fake.mutations, [])
        self.assertIs(controller.approve(review, confirmed=True, candidate=self.value),
                      byok.LocalByokOutcome.SUBMITTED_UNVALIDATED)
        self.assert_refused(controller, review, confirmed=True, candidate=self.value)
        removal = controller.begin(byok.LocalByokOperation.REMOVE)
        self.assertIsNotNone(removal)
        self.assertIs(controller.approve(removal, confirmed=True,
                                         deletion_acknowledged=True),
                      byok.LocalByokOutcome.SUBMITTED_REMOVAL)
        self.assertEqual([entry[0] for entry in fake.mutations], ["write", "delete"])
        self.assertFalse(self.controller.mutation_available)
        self.assertIsNone(self.controller.begin(byok.LocalByokOperation.SAVE))
        self.assert_storage_denied(
            lambda: self.backend.put(self.identifier, self.value))


if __name__ == '__main__':
    unittest.main(verbosity=2)
