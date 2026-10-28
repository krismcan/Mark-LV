"""Adversarial effect/trust tripwires for the bounded Phase 8 journey owner."""
import ast
from pathlib import Path
import threading
import unittest
from unittest import mock

from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinatedOutcome,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.secrets.contracts import SecretValue
from nayeon.desktop_alpha.first_run_connection_owner import (
    JourneyContext, JourneyRefused, TrustedFirstRunConnectionOwner,
)
from tests.test_first_run_credential_management_window import Harness

ROOT = Path(__file__).resolve().parents[1]


class FakeRoot:
    def __init__(self):
        self.alive = True

    def winfo_exists(self):
        return 1 if self.alive else 0


class EffectIsolationTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.configure()
        self.h.reconcile()
        self.addCleanup(self.h.close)
        self.root = FakeRoot()
        self.ctx = JourneyContext(self.root, object(), object(), object(), 3)
        self.owner = TrustedFirstRunConnectionOwner(
            coordinator=self.h.coordinator, context=self.ctx, is_current=lambda: True)
        self.addCleanup(lambda: self.owner.close(self.ctx))

    def test_source_has_no_transport_native_tk_storage_or_subprocess_import(self):
        source = (ROOT / "nayeon/desktop_alpha/first_run_connection_owner.py").read_text("utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
        denied = ("openai", "socket", "urllib", "requests", "http", "ssl",
                  "subprocess", "winreg", "ctypes", "tkinter", "os", "pathlib",
                  "nayeon.secrets.windows_credential",
                  "nayeon.brain.providers",
                  "nayeon.brain.credential_onboarding_composition")
        self.assertFalse(any(i.startswith(bad) for i in imports for bad in denied))
        forbidden_calls = {"exec", "eval", "open", "getattr", "setattr", "__import__"}
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                             and n.func.id in forbidden_calls for n in ast.walk(tree)))

    def test_default_desktop_will_not_implicitly_import_connection_owner(self):
        paths = [
            ROOT / "nayeon/desktop_alpha/__main__.py",
            ROOT / "nayeon/desktop_alpha/window.py",
            ROOT / "nayeon/desktop_alpha/application.py",
            ROOT / "nayeon/desktop_alpha/workspace_window.py",
        ]
        for path in paths:
            self.assertNotIn("first_run_connection_owner", path.read_text("utf-8"))
        # B permits the exact lazy window bridge, with no default coordinator
        # or test harness. Keep A's no-implicit-owner-import check above.
        source = (ROOT / "nayeon/desktop_alpha/application.py").read_text("utf-8")
        tree = ast.parse(source)
        app = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "OfflineWorkspaceApplication")
        constructor = next(n for n in app.body if isinstance(n, ast.FunctionDef)
                           and n.name == "__init__")
        defaults = dict(zip((a.arg for a in constructor.args.kwonlyargs),
                            constructor.args.kw_defaults))
        for name in ("connection_coordinator", "connection_test_harness"):
            self.assertIsInstance(defaults[name], ast.Constant)
            self.assertIsNone(defaults[name].value)
        # No production composition/native secret imports in either UI module.
        for name in ("application.py", "first_run_connection_window.py"):
            module = ast.parse((ROOT / "nayeon/desktop_alpha" / name).read_text("utf-8"))
            imports = [n.module for n in ast.walk(module)
                       if isinstance(n, ast.ImportFrom) and n.module]
            imports += [a.name for n in ast.walk(module)
                        if isinstance(n, ast.Import) for a in n.names]
            self.assertFalse(any(i.startswith((
                "nayeon.secrets", "nayeon.brain.credential_onboarding_composition",
                "nayeon.brain.providers", "openai", "httpx", "requests"))
                for i in imports))

    def test_wrong_coordinator_constructor_refuses_without_calling_attacker(self):
        class Attacker:
            def __getattribute__(self, field):
                raise AssertionError("Attacker cannot be inspected")
        with self.assertRaises(JourneyRefused):
            TrustedFirstRunConnectionOwner(
                coordinator=Attacker(), context=self.ctx, is_current=lambda: True)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)

    def test_cancel_reentrantly_during_request_prevents_publication(self):
        self.assertTrue(self.owner.start(self.ctx))
        original = CooperativeOnboardingCoordinator.request_ui
        calls = []
        def reentrant(receiver, *args, **kwargs):
            calls.append("entered")
            self.owner.close(self.ctx)
            return original(receiver, *args, **kwargs)
        with mock.patch.object(CooperativeOnboardingCoordinator, "request_ui",
                               autospec=True, side_effect=reentrant):
            receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertEqual(calls, ["entered"])
        self.assertIsNone(review)
        self.assertIsNot(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertTrue(self.owner.closed)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)

    def test_cancel_reentrantly_during_confirmation_never_claims_success(self):
        self.assertTrue(self.owner.start(self.ctx))
        receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        original = CooperativeOnboardingCoordinator.approve_ui
        def reentrant(receiver, **kwargs):
            self.owner.close(self.ctx)
            return original(receiver, **kwargs)
        with mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                               autospec=True, side_effect=reentrant):
            result = self.owner.confirm(
                self.ctx, review, candidate=SecretValue("fixture-good"),
                explicitly_approved=True)
        self.assertIsNot(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assertTrue(result.requires_reobservation)
        self.assertFalse(result.confirms_transaction)
        self.assertTrue(self.owner.closed)

    def test_foreign_thread_cancel_never_touches_coordinator(self):
        self.assertTrue(self.owner.start(self.ctx))
        self.owner.request(self.ctx, Op.CONNECT)
        observed = []
        def worker():
            try:
                self.owner.close(self.ctx)
            except JourneyRefused as ex:
                observed.append(str(ex))
        t = threading.Thread(target=worker)
        t.start()
        t.join(5)
        self.assertEqual(observed, ["WRONG_THREAD"])
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)

    def test_delete_requires_specific_acknowledgement_not_connect_approval(self):
        # Synthetic preexisting credential; none ever written to host WinCred.
        self.h.backend.value = SecretValue("fixture-existing")
        self.owner.start(self.ctx)
        receipt, review = self.owner.request(self.ctx, Op.REMOVE)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIs(self.owner.confirm(
            self.ctx, review, explicitly_approved=True).outcome,
            CoordinatedOutcome.REFUSED)
        self.assertEqual(self.h.backend.deletes, 0)
        self.owner.cancel(self.ctx, review)

    def test_wrong_owner_ticket_and_wrong_object_cannot_approve(self):
        self.owner.start(self.ctx)
        _, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertIs(self.owner.confirm(
            self.ctx, object(), candidate=SecretValue("fixture-good"),
            explicitly_approved=True).outcome, CoordinatedOutcome.REFUSED)
        altered = JourneyContext(self.ctx.root, self.ctx.application, self.ctx.pane,
                                 self.ctx.journey, self.ctx.generation)
        self.assertIs(self.owner.confirm(
            altered, review, candidate=SecretValue("fixture-good"),
            explicitly_approved=True).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)

    def test_close_reentrant_after_claim_releases_real_recovery_tenure(self):
        counter = [0]
        def reenter():
            counter[0] += 1
            if counter[0] == 2:
                self.owner.close(self.ctx)
            return True
        self.owner._live = reenter
        self.assertFalse(self.owner.start(self.ctx))
        self.assertTrue(self.owner.closed)
        self.assertFalse(self.owner.uncertain)
        self.assertIsNone(self.h.controller._ui_window_owner)
        self.assertIsNone(self.h.controller._ctx)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)

    def test_failed_close_after_reentrant_claim_remains_uncertain(self):
        counter = [0]
        def reenter():
            counter[0] += 1
            if counter[0] == 2:
                self.owner.close(self.ctx)
            return True
        self.owner._live = reenter
        with mock.patch.object(type(self.h.controller), "close_ui_window_owner",
                               return_value=False):
            self.assertFalse(self.owner.start(self.ctx))
        self.assertTrue(self.owner.closed)
        self.assertTrue(self.owner.uncertain)
        self.assertEqual(self.h.backend.puts, 0)

    def test_ticket_revoked_during_last_liveness_must_not_publish_pending(self):
        self.assertTrue(self.owner.start(self.ctx))
        calls = []
        def reenter():
            issued = self.h.coordinator._ui_ticket
            if issued is not None and not calls:
                calls.append("revoked")
                self.h.coordinator.reject_ui(
                    ticket=issued, owner_token=self.owner._owner_token,
                    root=self.root, operation=Op.CONNECT)
            return True
        self.owner._live = reenter
        receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertEqual(calls, ["revoked"])
        self.assertIsNone(review)
        self.assertIsNot(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)

    def test_ticket_final_clock_reentrant_close_cannot_publish_pending(self):
        import time
        from nayeon.brain import onboarding_coordination as coordination
        self.assertTrue(self.owner.start(self.ctx))
        original_clock = time.monotonic
        interrupted = []
        def clock():
            if self.h.coordinator._ui_ticket is not None and not interrupted:
                interrupted.append(True)
                self.owner.close(self.ctx)
            return original_clock()
        with mock.patch.object(coordination.time, "monotonic", side_effect=clock):
            receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertEqual(interrupted, [True])
        self.assertIsNone(review)
        self.assertIsNot(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertTrue(self.owner.closed)
        self.assertIsNone(self.h.controller._ui_window_owner)
        self.assertIsNone(self.h.controller._ctx)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 0)


if __name__ == "__main__":
    unittest.main()
