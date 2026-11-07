"""P91 fake-only revocation/dispatch/crash specification probes.

No service, WinCred, installation, IPC, real consent, key or provider operation.
"""
import concurrent.futures
import inspect
import unittest

from tests.p91_disabled_admission_model import (
    DisabledAdmissionModel, FakeBinding, FakeOperation, FakeStage, ModelDenied,
)

A = "a" * 32
B = "b" * 32
C = "c" * 32


def binding(session=A, candidate=B, op=FakeOperation.SAVE_PENDING):
    return FakeBinding(op, session, candidate)


def approved():
    model = DisabledAdmissionModel()
    model.prepare(binding())
    model.synthetic_consent_fixture(binding())
    return model


class DisabledAdmissionOrderingTests(unittest.TestCase):
    def denied(self, method, *args):
        with self.assertRaises(ModelDenied):
            method(*args)

    def test_no_effect_without_preparation_or_consent(self):
        m = DisabledAdmissionModel()
        self.denied(m.begin_fake_dispatch, binding())
        self.denied(m.record_fake_durable_intent)
        self.assertEqual(m.snapshot().attempts, 0)

    def test_prepared_cannot_dispatch_without_intent(self):
        m = approved()
        self.denied(m.begin_fake_dispatch, binding())
        self.assertEqual(m.snapshot().attempts, 0)

    def test_no_consent_cannot_ack_intent(self):
        m = DisabledAdmissionModel()
        m.prepare(binding())
        self.denied(m.record_fake_durable_intent)

    def test_wrong_exact_candidate_denied_at_consent(self):
        m = DisabledAdmissionModel()
        m.prepare(binding())
        self.denied(m.synthetic_consent_fixture, binding(candidate=C))

    def test_wrong_exact_session_denied_at_consent(self):
        m = DisabledAdmissionModel()
        m.prepare(binding())
        self.denied(m.synthetic_consent_fixture, binding(session=C))

    def test_wrong_operation_denied_at_consent(self):
        m = DisabledAdmissionModel()
        m.prepare(binding())
        self.denied(m.synthetic_consent_fixture,
                    binding(op=FakeOperation.DELETE_PENDING))

    def test_second_synthetic_consent_denied(self):
        m = approved()
        self.denied(m.synthetic_consent_fixture, binding())

    def test_revoke_before_consent_prevents_any_attempt(self):
        m = DisabledAdmissionModel()
        m.prepare(binding())
        m.revoke_fixture_consent()
        self.denied(m.synthetic_consent_fixture, binding())
        self.denied(m.begin_fake_dispatch, binding())
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.assertEqual(m.snapshot().attempts, 0)

    def test_revoke_before_durable_intent_prevents_attempt(self):
        m = approved()
        m.revoke_fixture_consent()
        self.denied(m.record_fake_durable_intent)
        self.assertEqual(m.snapshot().attempts, 0)

    def test_revoke_after_durable_intent_before_dispatch_prevents_attempt(self):
        m = approved()
        m.record_fake_durable_intent()
        m.revoke_fixture_consent()
        self.denied(m.begin_fake_dispatch, binding())
        self.assertEqual(m.snapshot().attempts, 0)

    def test_fake_dispatch_before_revoke_keeps_possible_attempt(self):
        m = approved()
        m.record_fake_durable_intent()
        self.assertEqual(m.begin_fake_dispatch(binding()),
                         "FAKE_ATTEMPT_RECORDED__NO_EFFECT")
        m.revoke_fixture_consent()
        self.assertEqual(m.snapshot().attempts, 1)
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.denied(m.begin_fake_dispatch, binding())

    def test_fault_before_dispatch_denies_effect(self):
        m = approved()
        m.record_fake_durable_intent()
        m.fault_fixture()
        self.denied(m.begin_fake_dispatch, binding())
        self.assertEqual(m.snapshot().attempts, 0)

    def test_fault_after_dispatch_preserves_uncertainty(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        m.fault_fixture()
        self.denied(m.fake_native_result, True)
        self.assertEqual(m.snapshot().attempts, 1)
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)

    def test_exactly_one_fake_dispatch_attempt(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        self.denied(m.begin_fake_dispatch, binding())
        self.assertEqual(m.snapshot().attempts, 1)

    def test_wrong_dispatch_candidate_denied_with_approved_intent(self):
        m = approved()
        m.record_fake_durable_intent()
        self.denied(m.begin_fake_dispatch, binding(candidate=C))
        self.assertEqual(m.snapshot().attempts, 0)

    def test_caller_mutated_binding_does_not_change_model_owned_copy(self):
        m = DisabledAdmissionModel()
        user = binding()
        m.prepare(user)
        object.__setattr__(user, "candidate_fixture_id", C)
        self.denied(m.synthetic_consent_fixture, user)
        m.synthetic_consent_fixture(binding())
        m.record_fake_durable_intent()
        self.assertEqual(m.begin_fake_dispatch(binding()),
                         "FAKE_ATTEMPT_RECORDED__NO_EFFECT")

    def test_second_session_cannot_replace_in_flight(self):
        m = approved()
        self.denied(m.prepare, binding(session=C))
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        self.denied(m.prepare, binding(session=C))

    def test_crash_after_preparation_fails_closed(self):
        m = approved()
        m.restart_fixture()
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.denied(m.begin_fake_dispatch, binding())

    def test_crash_after_intent_fails_closed(self):
        m = approved()
        m.record_fake_durable_intent()
        m.restart_fixture()
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.assertEqual(m.snapshot().attempts, 0)

    def test_crash_after_dispatch_retains_possible_attempt_no_retry(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        m.restart_fixture()
        self.assertEqual(m.snapshot().attempts, 1)
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.denied(m.begin_fake_dispatch, binding())

    def test_native_failure_leaves_recovery_only(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        m.fake_native_result(False)
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.denied(m.record_fake_terminal, True)

    def test_native_success_then_terminal_persist_failure_blocks(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        m.fake_native_result(True)
        m.record_fake_terminal(False)
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)
        self.assertEqual(m.snapshot().attempts, 1)

    def test_fake_native_success_terminal_never_means_provider_verified(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        m.fake_native_result(True)
        m.record_fake_terminal(True)
        s = m.snapshot()
        self.assertEqual(s.stage, FakeStage.CLOSED_UNVERIFIED)
        self.assertFalse(s.product_verified)
        self.assertFalse(s.production_eligible)
        self.denied(m.begin_fake_dispatch, binding())

    def test_restart_even_after_synthetic_terminal_requires_real_recovery(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        m.fake_native_result(True)
        m.record_fake_terminal(True)
        m.restart_fixture()
        self.assertEqual(m.snapshot().stage, FakeStage.BLOCKED)

    def test_invalid_native_boolean_refused_without_replay(self):
        m = approved()
        m.record_fake_durable_intent()
        m.begin_fake_dispatch(binding())
        self.denied(m.fake_native_result, 1)
        self.assertEqual(m.snapshot().attempts, 1)
        self.denied(m.begin_fake_dispatch, binding())

    def test_cross_thread_cannot_dispatch(self):
        m = approved()
        m.record_fake_durable_intent()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            f = pool.submit(m.begin_fake_dispatch, binding())
            with self.assertRaises(ModelDenied):
                f.result(timeout=5)
        self.assertEqual(m.snapshot().attempts, 0)

    def test_reentrant_call_explicitly_denied(self):
        m = approved()
        m.record_fake_durable_intent()
        m._entered = True
        try:
            self.denied(m.begin_fake_dispatch, binding())
        finally:
            m._entered = False
        self.assertEqual(m.snapshot().attempts, 0)

    def test_wrong_binding_types_denied(self):
        self.denied(FakeBinding, "SAVE_PENDING", A, B)
        self.denied(FakeBinding, FakeOperation.SAVE_PENDING, "key_here", B)

    def test_no_production_authority_even_on_empty_model(self):
        s = DisabledAdmissionModel().snapshot()
        self.assertFalse(s.production_eligible)
        self.assertFalse(s.product_verified)
        self.assertEqual(s.attempts, 0)

    def test_module_has_no_native_credential_or_service_imports(self):
        import tests.p91_disabled_admission_model as module
        source = inspect.getsource(module)
        for prohibited in (
            "ctypes", "win32cred", "CredWrite", "CredDelete", "CredRead",
            "subprocess", "socket", "http.client", "requests",
            "winreg", "os.system", "powershell.exe",
        ):
            self.assertNotIn(prohibited, source)
        self.assertNotIn("nayeon.", source)


if __name__ == "__main__":
    unittest.main()
