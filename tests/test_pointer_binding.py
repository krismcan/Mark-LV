"""Deterministic Phase 6.8 exact location-bound pointer approval tests; no live input."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
import pickle
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor
from nayeon.agent.pointer_binding import (
    _PointerAction,
    _PointerActionKind,
    _PointerInvocation,
    _PointerOperation,
)
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.services.keyboard_text import _TextBinding
from nayeon.services.pointer_hit_validation import (
    _PointerHitResult,
    _PointerHitValidationService,
    _ProposedPoint,
)
from nayeon.services.target_validation import (
    MAX_AGE_NS,
    _TargetBinding,
    _TargetVerificationService,
)
from nayeon.services.window_focus import _FocusBinding
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationStatus
from tests.test_foreground_observation import CONTEXT as C, IDENTITY as I


POINT = (31415, 27182)
CHILD = I.hwnd + 111


class PointerBindingTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.capability = Capability(
            "test_pointer_binding", "Test only", ExecutionMode.LOCAL, "fake",
            requires_confirmation=True,
        )
        self.implementation = Mock(spec=["execute"])
        self.registry.register(self.capability, self.implementation)

        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant(self.capability.name)
        self.policy = PolicyService(self.permissions)
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(
            self.registry, self.policy, self.confirmation, self.audit, self.undo
        )

        self.native = Mock(spec=["context", "foreground", "identity"])
        self.native.context.return_value = C
        self.native.foreground.return_value = I.hwnd
        self.native.identity.return_value = I
        self.service = _TargetVerificationService(
            native=self.native, platform="win32",
            clock=Mock(side_effect=[10, 20]),
        )

        self.hit_native = Mock(spec=["context", "window_at", "root", "identity"])
        self.hit_native.context.return_value = C
        self.hit_native.window_at.return_value = CHILD
        self.hit_native.root.return_value = I.hwnd
        self.hit_native.identity.return_value = I
        self.hit_service = _PointerHitValidationService(
            native=self.hit_native, platform="win32",
            clock=Mock(side_effect=[30, 40]),
        )

        self.action = _PointerAction()
        self.point = _ProposedPoint(*POINT)

    def invocation(self):
        return self.executor._pointer_invocation(
            self.capability,
            service=self.service,
            hit_service=self.hit_service,
        )

    def assert_cleared(self, invocation):
        for name in (
            "_operation", "_target", "_action", "_point", "_snapshot",
            "_confirmation", "_service", "_hit_service",
        ):
            self.assertIsNone(getattr(invocation, name))
        self.assertTrue(invocation._closed)
        self.assertEqual(self.confirmation._pending, {})
        self.assertEqual(self.confirmation._bindings, {})
        self.implementation.execute.assert_not_called()
        self.assertEqual(self.undo.count(), 0)

    def prepare(self, invocation):
        return invocation.prepare(self.action, self.point)

    def approve(self, invocation, operation):
        return invocation.approve(
            operation,
            target=operation.target,
            action=operation.action,
            point=operation.point,
        )

    def test_exact_target_action_point_binding_accepted_once(self):
        with self.invocation() as invocation,                 patch.object(self.service, "verify_target") as verify_target:
            operation, confirmation = self.prepare(invocation)
            self.assertEqual(operation.target, _TargetBinding(I, C, 10, 20))
            self.assertIs(operation.action, self.action)
            self.assertIs(operation.point, self.point)
            self.assertEqual(operation.action.parameters, ())
            self.assertEqual((operation.point.x, operation.point.y), POINT)
            self.assertIs(self.confirmation._bindings[confirmation.token], operation)
            self.assertEqual(self.hit_native.window_at.call_count, 2)
            self.assertTrue(self.approve(invocation, operation))
            self.assertFalse(self.approve(invocation, operation))
            verify_target.assert_not_called()
            self.assertEqual(self.hit_native.window_at.call_count, 2)
        self.assert_cleared(invocation)

    def test_old_location_free_prepare_and_operation_are_rejected(self):
        with self.invocation() as invocation:
            with self.assertRaises(TypeError):
                invocation.prepare(self.action)
        with self.assertRaises(TypeError):
            _PointerOperation(_TargetBinding(I, C, 10, 20), self.action)
        self.assertEqual(self.native.mock_calls, [])
        self.assertEqual(self.hit_native.mock_calls, [])

    def test_reconstruction_or_substitution_rejected(self):
        substitutions = (
            "target_copy", "target_changed", "action_copy",
            "point_copy", "point_changed", "operation_copy",
        )
        for substitution in substitutions:
            with self.subTest(substitution=substitution):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    target = operation.target
                    action = operation.action
                    point = operation.point
                    candidate = operation
                    if substitution == "target_copy":
                        target = replace(target)
                    elif substitution == "target_changed":
                        target = replace(target, acquired_to_ns=21)
                    elif substitution == "action_copy":
                        action = _PointerAction()
                    elif substitution == "point_copy":
                        point = _ProposedPoint(point.x, point.y)
                    elif substitution == "point_changed":
                        point = _ProposedPoint(point.x + 1, point.y)
                    else:
                        candidate = _PointerOperation(target, action, point)
                    self.assertFalse(invocation.approve(
                        candidate, target=target, action=action, point=point
                    ))
                    self.assert_cleared(invocation)

    def test_post_prepare_tampering_rejected(self):
        tamperings = (
            "parameters", "kind", "timestamp", "bool_timestamp", "identity",
            "target", "action", "point_x", "point_y", "point",
        )
        for tampering in tamperings:
            with self.subTest(tampering=tampering):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    if tampering == "parameters":
                        object.__setattr__(self.action, "parameters", (True,))
                    elif tampering == "kind":
                        object.__setattr__(self.action, "kind", "single_left_click")
                    elif tampering in ("timestamp", "bool_timestamp"):
                        object.__setattr__(
                            operation.target, "acquired_to_ns",
                            True if tampering == "bool_timestamp" else 21,
                        )
                    elif tampering == "identity":
                        object.__setattr__(
                            operation.target, "identity",
                            replace(I, executable="changed.exe"),
                        )
                    elif tampering == "target":
                        object.__setattr__(operation, "target", replace(operation.target))
                    elif tampering == "action":
                        object.__setattr__(operation, "action", _PointerAction())
                    elif tampering == "point_x":
                        object.__setattr__(operation.point, "x", operation.point.x + 1)
                    elif tampering == "point_y":
                        object.__setattr__(operation.point, "y", True)
                    else:
                        object.__setattr__(
                            operation, "point",
                            _ProposedPoint(operation.point.x, operation.point.y),
                        )
                    self.assertFalse(invocation.approve(
                        operation,
                        target=operation.target,
                        action=operation.action,
                        point=operation.point,
                    ))
                    self.assert_cleared(invocation)

    def test_action_and_point_exact_types(self):
        for kind in (True, 1, "single_left_click", None, Mock()):
            with self.assertRaises(TypeError):
                _PointerAction(kind)
        for parameters in (True, 1, [], {}, None, ""):
            with self.assertRaises(TypeError):
                _PointerAction(parameters=parameters)
        for parameters in ((True,), (1,), ((10, 20),), ("left",)):
            with self.assertRaises(ValueError):
                _PointerAction(parameters=parameters)
        self.assertEqual(
            list(_PointerActionKind), [_PointerActionKind.SINGLE_LEFT_CLICK]
        )

        for value in (True, 1.0, "1", None):
            with self.assertRaises(TypeError):
                _ProposedPoint(value, 1)
            with self.assertRaises(TypeError):
                _ProposedPoint(1, value)
        for value in (-(2 ** 31) - 1, 2 ** 31):
            with self.assertRaises(ValueError):
                _ProposedPoint(value, 0)

    def test_legacy_or_malformed_values_cannot_construct_operation(self):
        target = _TargetBinding(I, C, 10, 20)
        for bad_target in (
            None, {}, _FocusBinding(I, C),
            _TextBinding(_FocusBinding(I, C), "test"),
        ):
            with self.assertRaises(TypeError):
                _PointerOperation(bad_target, self.action, self.point)
        for bad_point in (None, POINT, [*POINT], {}):
            with self.assertRaises(TypeError):
                _PointerOperation(target, self.action, bad_point)
        self.assertEqual(self.native.mock_calls, [])
        self.assertEqual(self.hit_native.mock_calls, [])

    def test_frozen_slotted_redacted_no_copy_pickle_json_import(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            for value in (self.action, self.point, operation, invocation):
                self.assertFalse(hasattr(value, "__dict__"))
                self.assertEqual(repr(value), type(value).__name__ + "(<private>)")
                self.assertEqual(str(value), repr(value))
                for exporter in (copy, deepcopy, pickle.dumps, json.dumps):
                    with self.assertRaises(TypeError):
                        exporter(value)
            with self.assertRaises(FrozenInstanceError):
                self.action.parameters = (1,)
            with self.assertRaises(FrozenInstanceError):
                self.point.x = 1
            with self.assertRaises(FrozenInstanceError):
                operation.point = _ProposedPoint(1, 2)
            self.assertFalse(hasattr(operation, "from_dict"))

    def test_invalid_action_or_point_fails_before_policy_or_desktop_reads(self):
        cases = (
            ({"kind": "single_left_click"}, self.point),
            (self.action, POINT),
            (self.action, [*POINT]),
        )
        for action, point in cases:
            with self.subTest(action=type(action).__name__, point=type(point).__name__):
                self.setUp()
                with self.invocation() as invocation:
                    with self.assertRaisesRegex(
                        ValueError, "^Pointer binding preparation failed.$"
                    ):
                        invocation.prepare(action, point)
                    self.assert_cleared(invocation)
                self.assertEqual(self.native.mock_calls, [])
                self.assertEqual(self.hit_native.mock_calls, [])
                self.assertEqual(self.audit.all(), ())

    def test_permission_or_policy_denial_precedes_all_native_reads(self):
        for denial in ("permission", "policy"):
            with self.subTest(denial=denial):
                self.setUp()
                if denial == "permission":
                    self.permissions.revoke(self.capability.name)
                else:
                    self.policy._blocked_capabilities.add(self.capability.name)
                with self.invocation() as invocation:
                    with self.assertRaises(ValueError):
                        self.prepare(invocation)
                    self.assert_cleared(invocation)
                self.assertEqual(self.native.mock_calls, [])
                self.assertEqual(self.hit_native.mock_calls, [])
                self.assertEqual(
                    [e.event_type for e in self.audit.all()],
                    [AuditEventType.POLICY_DECISION],
                )

    def test_policy_target_hit_confirmation_approval_recheck_order(self):
        calls = Mock()
        with patch.object(
            self.policy, "evaluate", wraps=self.policy.evaluate
        ) as policy, patch.object(
            self.service, "acquire_target", wraps=self.service.acquire_target
        ) as acquire, patch.object(
            self.confirmation, "create", wraps=self.confirmation.create
        ) as create, patch.object(
            self.confirmation, "approve", wraps=self.confirmation.approve
        ) as approve:
            calls.attach_mock(policy, "policy")
            calls.attach_mock(acquire, "acquire")
            calls.attach_mock(self.hit_native.window_at, "hit")
            calls.attach_mock(create, "create")
            calls.attach_mock(approve, "approve")
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                self.assertTrue(self.approve(invocation, operation))
        self.assertEqual(
            [c[0] for c in calls.mock_calls],
            ["policy", "acquire", "hit", "hit", "create", "approve", "policy"],
        )

    def test_only_exact_verified_hit_can_enter_confirmation_binding(self):
        # Real NOT_VERIFIED result.
        other = replace(
            I, hwnd=I.hwnd + 1, root=I.root + 1,
            pid=I.pid + 1, tid=I.tid + 1,
            creation_time=I.creation_time + 1,
        )
        self.hit_native.window_at.return_value = other.hwnd + 100
        self.hit_native.root.return_value = other.hwnd
        self.hit_native.identity.return_value = other
        with self.invocation() as invocation:
            with self.assertRaises(ValueError):
                self.prepare(invocation)
            self.assert_cleared(invocation)

        # Real INDETERMINATE result.
        self.setUp()
        self.hit_native.window_at.return_value = 0
        with self.invocation() as invocation:
            with self.assertRaises(ValueError):
                self.prepare(invocation)
            self.assert_cleared(invocation)

        # A fake object claiming VERIFIED is not trusted.
        self.setUp()
        with patch.object(
            _PointerHitValidationService,
            "validate_hit",
            return_value=Mock(status=VerificationStatus.VERIFIED),
        ):
            with self.invocation() as invocation:
                with self.assertRaises(ValueError):
                    self.prepare(invocation)
                self.assert_cleared(invocation)

    def test_stale_location_evidence_fails_without_reacquiring_target(self):
        self.hit_service._clock = Mock(return_value=20 + MAX_AGE_NS + 1)
        with patch.object(
            self.service, "acquire_target", wraps=self.service.acquire_target
        ) as acquire, patch.object(
            self.service, "verify_target"
        ) as verify:
            with self.invocation() as invocation:
                with self.assertRaises(ValueError):
                    self.prepare(invocation)
                self.assert_cleared(invocation)
        acquire.assert_called_once()
        verify.assert_not_called()
        self.assertEqual(self.confirmation._pending, {})

    def test_approval_does_not_promote_or_refresh_preparation_validation(self):
        with patch.object(self.service, "verify_target") as verify:
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                self.assertEqual(self.hit_native.window_at.call_count, 2)
                self.assertTrue(self.approve(invocation, operation))
        self.assertEqual(self.hit_native.window_at.call_count, 2)
        verify.assert_not_called()
        self.assertFalse(hasattr(operation, "hit_result"))
        self.assertFalse(hasattr(operation, "verification"))

    def test_permission_revocation_and_confirmation_expiry_fail_closed(self):
        for denial in ("permission", "expiry"):
            with self.subTest(denial=denial):
                self.setUp()
                with self.invocation() as invocation:
                    operation, confirmation = self.prepare(invocation)
                    if denial == "permission":
                        self.permissions.revoke(self.capability.name)
                    else:
                        self.confirmation._pending[confirmation.token] = replace(
                            confirmation,
                            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                        )
                    self.assertFalse(self.approve(invocation, operation))
                    self.assert_cleared(invocation)

    def test_legacy_confirmation_route_cannot_approve_location_bound_operation(self):
        with self.invocation() as invocation:
            operation, confirmation = self.prepare(invocation)
            result = self.executor.approve_and_execute(
                confirmation.token,
                capability=self.capability,
                request=confirmation.request,
            )
            self.assertFalse(result.succeeded)
            self.assertFalse(self.approve(invocation, operation))
            self.assert_cleared(invocation)

    def test_close_and_cross_invocation_reuse_rejected(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
        self.assert_cleared(invocation)
        self.assertFalse(self.approve(invocation, operation))

        self.setUp()
        with self.invocation() as next_invocation:
            self.prepare(next_invocation)
            self.assertFalse(next_invocation.approve(
                operation,
                target=operation.target,
                action=operation.action,
                point=operation.point,
            ))
            self.assert_cleared(next_invocation)

    def test_second_prepare_fails_closed(self):
        with self.invocation() as invocation:
            self.prepare(invocation)
            with self.assertRaises(ValueError):
                self.prepare(invocation)
            self.assert_cleared(invocation)

    def test_target_acquisition_and_hit_failures_are_sanitized(self):
        for stage in ("target", "hit"):
            with self.subTest(stage=stage):
                self.setUp()
                if stage == "target":
                    self.native.identity.side_effect = RuntimeError(
                        "PRIVATE_NATIVE_SECRET"
                    )
                else:
                    self.hit_native.identity.side_effect = RuntimeError(
                        "PRIVATE_HIT_SECRET"
                    )
                with self.invocation() as invocation:
                    with self.assertRaisesRegex(
                        ValueError, "^Pointer binding preparation failed.$"
                    ):
                        self.prepare(invocation)
                    self.assert_cleared(invocation)
                public = repr(self.audit.all())
                self.assertNotIn("PRIVATE_NATIVE_SECRET", public)
                self.assertNotIn("PRIVATE_HIT_SECRET", public)

    def test_approval_exception_and_lexical_exception_cleanup(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(
                self.policy, "evaluate", side_effect=RuntimeError("PRIVATE")
            ):
                self.assertFalse(self.approve(invocation, operation))
            self.assert_cleared(invocation)

        self.setUp()
        with self.assertRaisesRegex(RuntimeError, "caller"):
            with self.invocation() as invocation:
                self.prepare(invocation)
                raise RuntimeError("caller")
        self.assert_cleared(invocation)

    def test_registration_change_rejected(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.registry.unregister(self.capability.name)
            self.assertFalse(self.approve(invocation, operation))
            self.assert_cleared(invocation)

    def test_reversible_or_unprotected_metadata_has_zero_native_reads(self):
        for changes in ({"reversible": True}, {"requires_confirmation": False}):
            with self.subTest(changes=changes):
                self.setUp()
                self.capability = replace(self.capability, **changes)
                self.registry.unregister(self.capability.name)
                self.registry.register(self.capability, self.implementation)
                with self.invocation() as invocation:
                    with self.assertRaises(ValueError):
                        self.prepare(invocation)
                self.assertEqual(self.native.mock_calls, [])
                self.assertEqual(self.hit_native.mock_calls, [])

    def test_public_evidence_does_not_leak_target_or_point_and_no_execution(self):
        original_fields = set(vars(self.executor))
        with self.invocation() as invocation:
            operation, confirmation = self.prepare(invocation)
            self.assertTrue(self.approve(invocation, operation))
        self.assertEqual(set(vars(self.executor)), original_fields)
        self.assertEqual(self.executor._structured_pending, {})
        for event in self.audit.all():
            self.assertEqual(event.details, {})
            self.assertNotIn(
                event.event_type,
                (
                    AuditEventType.EXECUTION_STARTED,
                    AuditEventType.EXECUTION_SUCCEEDED,
                    AuditEventType.UNDO_REGISTERED,
                ),
            )
        public = repr(self.audit.all()) + repr(confirmation)
        for private in (
            I.executable, I.window_class, str(POINT[0]), str(POINT[1]),
            "acquired_from_ns", "_TargetBinding", "_ProposedPoint",
        ):
            self.assertNotIn(private, public)
        self.assert_cleared(invocation)

    def test_executor_rejects_untrusted_service_types(self):
        with self.assertRaises(TypeError):
            with self.executor._pointer_invocation(
                self.capability,
                service=self.service,
                hit_service=Mock(),
            ):
                pass
        with self.assertRaises(TypeError):
            with self.executor._pointer_invocation(
                self.capability,
                service=Mock(),
                hit_service=self.hit_service,
            ):
                pass

    def test_no_public_exports_native_mutation_or_execution_methods(self):
        from nayeon.agent import pointer_binding

        self.assertEqual(pointer_binding.__all__, ())
        for cls in (_PointerAction, _PointerOperation, _PointerInvocation):
            for name in (
                "execute", "click", "move", "focus", "verify_target",
                "validate_hit", "to_dict", "from_dict",
            ):
                self.assertFalse(hasattr(cls, name))
        self.assertEqual(
            [name for name in dir(ActionExecutor) if "pointer" in name],
            ["_pointer_invocation"],
        )


if __name__ == "__main__":
    unittest.main()
