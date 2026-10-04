"""Deterministic Phase 6.8 exact location-bound pointer approval tests; no live input."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
import pickle
import unittest
from tests.test_scoped_ui_element_observation import Harness as _UIAHarness
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor
from nayeon.agent.pointer_binding import (
    _PointerAction,
    _PointerActionKind,
    _PointerEligibilityResult,
    _PointerInvocation,
    _PointerOperation,
)
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.services.keyboard_text import _TextBinding
from nayeon.services.pointer_coordinates import _PointerCoordinateService
from nayeon.services.pointer_effect import _EffectStatus, _PointerEffectService
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
            clock=Mock(side_effect=[10, 20, 50, 60]),
        )

        self.hit_native = Mock(spec=["context", "window_at", "root", "identity"])
        self.hit_native.context.return_value = C
        self.hit_native.window_at.return_value = CHILD
        self.hit_native.root.return_value = I.hwnd
        self.hit_native.identity.return_value = I
        self.hit_service = _PointerHitValidationService(
            native=self.hit_native, platform="win32",
            clock=Mock(side_effect=[30, 40, 70, 80]),
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
            result = self.approve(invocation, operation)
            self.assertIs(type(result), _PointerEligibilityResult)
            self.assertIs(result.status, VerificationStatus.VERIFIED)
            self.assertIs(
                self.approve(invocation, operation).status,
                VerificationStatus.INDETERMINATE,
            )
            verify_target.assert_not_called()
            self.assertEqual(self.hit_native.window_at.call_count, 4)
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
                    self.assertIs(
                        invocation.approve(
                            candidate, target=target, action=action, point=point
                        ).status,
                        VerificationStatus.INDETERMINATE,
                    )
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
                    self.assertIs(
                        invocation.approve(
                            operation,
                            target=operation.target,
                            action=operation.action,
                            point=operation.point,
                        ).status,
                        VerificationStatus.INDETERMINATE,
                    )
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
                self.assertEqual(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
        self.assertEqual(
            [c[0] for c in calls.mock_calls],
            [
                "policy", "acquire", "hit", "hit", "create", "approve", "policy",
                "acquire", "hit", "hit",
            ],
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
                self.assertEqual(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
        self.assertEqual(self.hit_native.window_at.call_count, 4)
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
                    self.assertIsNot(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
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
            self.assertIsNot(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
            self.assert_cleared(invocation)

    def test_close_and_cross_invocation_reuse_rejected(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
        self.assert_cleared(invocation)
        self.assertIsNot(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)

        self.setUp()
        with self.invocation() as next_invocation:
            self.prepare(next_invocation)
            self.assertIs(
                next_invocation.approve(
                    operation,
                    target=operation.target,
                    action=operation.action,
                    point=operation.point,
                ).status,
                VerificationStatus.INDETERMINATE,
            )
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
                self.assertIsNot(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
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
            self.assertIsNot(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
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
            self.assertEqual(self.approve(invocation, operation).status, VerificationStatus.VERIFIED)
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


    def test_post_confirmation_fresh_target_mismatch_is_not_verified(self):
        other = replace(
            I, hwnd=I.hwnd + 10, root=I.root + 10,
            pid=I.pid + 10, tid=I.tid + 10,
            creation_time=I.creation_time + 10,
        )
        self.native.foreground.side_effect = [
            I.hwnd, I.hwnd, other.hwnd, other.hwnd,
        ]
        self.native.identity.side_effect = [I, I, other, other]
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.approve(invocation, operation)
        self.assertIs(result.status, VerificationStatus.NOT_VERIFIED)
        # Fresh target mismatch stops before a second point hit validation.
        self.assertEqual(self.hit_native.window_at.call_count, 2)
        self.assert_cleared(invocation)

    def test_post_confirmation_point_obstruction_is_not_verified(self):
        other = replace(
            I, hwnd=I.hwnd + 20, root=I.root + 20,
            pid=I.pid + 20, tid=I.tid + 20,
            creation_time=I.creation_time + 20,
        )
        self.hit_native.window_at.side_effect = [
            CHILD, CHILD, other.hwnd + 100, other.hwnd + 100,
        ]
        self.hit_native.root.side_effect = [
            I.hwnd, I.hwnd, other.hwnd, other.hwnd,
        ]
        self.hit_native.identity.side_effect = [I, I, other, other]
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.approve(invocation, operation)
        self.assertIs(result.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(self.hit_native.window_at.call_count, 4)
        self.assert_cleared(invocation)

    def test_post_confirmation_stale_fresh_hit_evidence_is_indeterminate(self):
        self.hit_service._clock = Mock(
            side_effect=[30, 40, 60 + MAX_AGE_NS + 1]
        )
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.approve(invocation, operation)
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)
        # The stale t0 check happens before post-confirmation native hit reads.
        self.assertEqual(self.hit_native.window_at.call_count, 2)
        self.assert_cleared(invocation)

    def test_post_confirmation_target_acquisition_failure_is_indeterminate(self):
        self.native.foreground.side_effect = [
            I.hwnd, I.hwnd, RuntimeError("PRIVATE_FRESH_SECRET"),
        ]
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.approve(invocation, operation)
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn("PRIVATE_FRESH_SECRET", repr(self.audit.all()))
        self.assertEqual(self.hit_native.window_at.call_count, 2)
        self.assert_cleared(invocation)

    def test_failed_confirmation_never_starts_fresh_eligibility_reads(self):
        with self.invocation() as invocation:
            operation, confirmation = self.prepare(invocation)
            self.confirmation._pending[confirmation.token] = replace(
                confirmation,
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
            target_reads = self.native.foreground.call_count
            hit_reads = self.hit_native.window_at.call_count
            result = self.approve(invocation, operation)
        self.assertIs(result.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(self.native.foreground.call_count, target_reads)
        self.assertEqual(self.hit_native.window_at.call_count, hit_reads)
        self.assert_cleared(invocation)

    def test_verified_eligibility_is_read_only_and_audited_separately(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            result = self.approve(invocation, operation)
        self.assertIs(result.status, VerificationStatus.VERIFIED)
        outcomes = [
            e for e in self.audit.all()
            if e.event_type is AuditEventType.VERIFICATION_OUTCOME
        ]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0].outcome, VerificationStatus.VERIFIED.value)
        self.assertEqual(outcomes[0].details, {})
        self.implementation.execute.assert_not_called()
        self.assertEqual(self.undo.count(), 0)
        for event in self.audit.all():
            self.assertNotIn(
                event.event_type,
                (AuditEventType.EXECUTION_STARTED, AuditEventType.EXECUTION_SUCCEEDED),
            )
        self.assert_cleared(invocation)

    def test_eligibility_result_is_private_typed_and_non_serializable(self):
        result = _PointerEligibilityResult(VerificationStatus.VERIFIED)
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertEqual(repr(result), "_PointerEligibilityResult(<private>)")
        for exporter in (copy, deepcopy, pickle.dumps, json.dumps):
            with self.assertRaises(TypeError):
                exporter(result)
        with self.assertRaises(TypeError):
            _PointerEligibilityResult("verified")

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

from nayeon.services.pointer_coordinates import (
    _CoordinateEvidence, _CoordinateNative, _CoordinateResult, _PointerCoordinateService,
)
from nayeon.services.pointer_effect import (
    _EffectStatus, _PointerEffectNative, _PointerEffectReceipt, _PointerEffectService,
)


class PointerEffectIntegrationTests(unittest.TestCase):
    """Phase 6.11: exact services and injected fakes only; no live input."""
    prepare = PointerBindingTests.prepare
    approve = PointerBindingTests.approve

    def setUp(self):
        PointerBindingTests.setUp(self)
        self.ui_element_service = _UIAHarness().service()
        self.native_guard = self.enterContext(patch.object(
            _PointerEffectNative, "__init__", side_effect=AssertionError("Live input forbidden")))
        self.coordinate_guard = self.enterContext(patch.object(
            _CoordinateNative, "__init__", side_effect=AssertionError("Live metrics forbidden")))
        self.metric_native = Mock(spec=["metric"])
        self.metric_native.metric.side_effect = lambda i: {76: 30000, 77: 26000, 78: 4000, 79: 4000}[i]
        self.coordinate_service = _PointerCoordinateService(platform="win32", native=self.metric_native)
        self.effect_native = Mock(spec=["_send_input"])
        self.effect_native._send_input.return_value = 3
        self.effect_service = _PointerEffectService(platform="win32", native=self.effect_native)

    def tearDown(self):
        self.native_guard.assert_not_called()
        self.coordinate_guard.assert_not_called()

    def invocation(self):
        return self.executor._pointer_invocation(
            self.capability, service=self.service, hit_service=self.hit_service,
            coordinate_service=self.coordinate_service, effect_service=self.effect_service, ui_element_service=self.ui_element_service)

    def execute_effect(self, invocation, operation, **overrides):
        args = dict(target=operation.target, action=operation.action, point=operation.point)
        args.update(overrides)
        return invocation._execute_effect(operation, **args)

    def assert_cleared(self, invocation):
        PointerBindingTests.assert_cleared(self, invocation)
        for name in ("_coordinate_service", "_effect_service", "_services", "_registered", "_implementation"):
            self.assertIsNone(getattr(invocation, name))

    def assert_not_attempted(self, invocation, receipt):
        self.assertEqual(receipt, _PointerEffectReceipt())
        self.metric_native.metric.assert_not_called()
        self.effect_native._send_input.assert_not_called()
        self.assert_cleared(invocation)

    def test_exact_confirmation_fresh_chain_original_point_and_one_effect(self):
        calls = Mock()
        with patch.object(self.confirmation, "approve", wraps=self.confirmation.approve) as approve, \
                patch.object(self.policy, "evaluate", wraps=self.policy.evaluate) as policy, \
                patch.object(_TargetVerificationService, "acquire_target", autospec=True, side_effect=_TargetVerificationService.acquire_target) as acquire, \
                patch.object(_PointerHitValidationService, "validate_hit", autospec=True, side_effect=_PointerHitValidationService.validate_hit) as hit, \
                patch.object(_PointerCoordinateService, "normalize", autospec=True,
                             side_effect=_PointerCoordinateService.normalize) as normalize, \
                patch.object(_PointerEffectService, "_insert", autospec=True,
                             side_effect=_PointerEffectService._insert) as insert:
            for mock, name in ((approve, "confirm"), (policy, "policy"), (acquire, "target"),
                               (hit, "hit"), (normalize, "normalize"), (insert, "insert")):
                calls.attach_mock(mock, name)
            with self.invocation() as invocation:
                operation, confirmation = self.prepare(invocation)
                self.assertIs(self.confirmation._bindings[confirmation.token], operation)
                self.metric_native.metric.assert_not_called()
                self.effect_native._send_input.assert_not_called()
                calls.mock_calls.clear()
                receipt = self.execute_effect(invocation, operation)
                self.assertEqual([c[0] for c in calls.mock_calls],
                                 ["confirm", "policy", "target", "hit", "normalize", "insert"])
                normalize.assert_called_once_with(self.coordinate_service, self.point)
                self.assertIs(normalize.call_args.args[1], operation.point)
                insert.assert_called_once()
                self.assertIs(insert.call_args.args[0], self.effect_service)
                self.assertIs(insert.call_args.args[1].point, self.point)
                self.assertEqual(self.execute_effect(invocation, operation), _PointerEffectReceipt())
                insert.assert_called_once()
        self.assertEqual(receipt, _PointerEffectReceipt(_EffectStatus.INSERTED, True, 3))
        self.effect_native._send_input.assert_called_once()
        self.assertEqual([c.args[0] for c in self.metric_native.metric.call_args_list], [76, 77, 78, 79])
        self.assert_cleared(invocation)

    def test_unprepared_and_substituted_exact_approval_block_effect(self):
        with self.invocation() as invocation:
            self.assert_not_attempted(invocation, invocation._execute_effect(
                None, target=None, action=None, point=None))
        for case in ("target", "action", "point", "operation"):
            with self.subTest(case=case):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    if case == "operation":
                        candidate = _PointerOperation(operation.target, operation.action, operation.point)
                        receipt = self.execute_effect(invocation, candidate)
                    else:
                        value = {"target": lambda: replace(operation.target), "action": _PointerAction,
                                 "point": lambda: _ProposedPoint(*POINT)}[case]()
                        receipt = self.execute_effect(invocation, operation, **{case: value})
                    self.assert_not_attempted(invocation, receipt)

    def test_policy_confirmation_registry_snapshot_service_tamper_blocked(self):
        for case in ("permission", "policy", "policy_result", "expiry", "binding", "confirmation_result",
                     "registry_metadata", "registry_implementation", "snapshot", "point",
                     "target_service", "hit_service", "coordinate_service", "effect_service"):
            with self.subTest(case=case):
                self.setUp()
                with self.invocation() as invocation:
                    operation, confirmation = self.prepare(invocation)
                    if case == "permission":
                        self.permissions.revoke(self.capability.name)
                    elif case == "policy":
                        self.policy._blocked_capabilities.add(self.capability.name)
                    elif case == "policy_result":
                        self.enterContext(patch.object(self.policy, "evaluate", return_value=Mock()))
                    elif case == "expiry":
                        self.confirmation._pending[confirmation.token] = replace(
                            confirmation, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
                    elif case == "binding":
                        self.confirmation._bindings[confirmation.token] = object()
                    elif case == "confirmation_result":
                        self.enterContext(patch.object(self.confirmation, "approve", return_value=Mock(approved=True)))
                    elif case.startswith("registry_"):
                        self.registry.unregister(self.capability.name)
                        self.registry.register(
                            replace(self.capability) if case == "registry_metadata" else self.capability,
                            Mock() if case == "registry_implementation" else self.implementation)
                    elif case == "snapshot":
                        invocation._snapshot = ()
                    elif case == "point":
                        object.__setattr__(operation.point, "x", operation.point.x + 1)
                    else:
                        value = {
                            "target_service": lambda: _TargetVerificationService(native=self.native, platform="win32"),
                            "hit_service": lambda: _PointerHitValidationService(native=self.hit_native, platform="win32"),
                            "coordinate_service": lambda: _PointerCoordinateService(native=self.metric_native, platform="win32"),
                            "effect_service": lambda: _PointerEffectService(native=self.effect_native, platform="win32"),
                        }[case]()
                        setattr(invocation, "_service" if case == "target_service" else "_" + case, value)
                    self.assert_not_attempted(invocation, self.execute_effect(invocation, operation))

    def test_non_verified_or_malformed_eligibility_blocks_mapping_and_effect(self):
        for result in (_PointerEligibilityResult(VerificationStatus.NOT_VERIFIED),
                       _PointerEligibilityResult(), Mock(status=VerificationStatus.VERIFIED)):
            with self.subTest(kind=type(result).__name__):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    with patch.object(_PointerInvocation, "_eligible_now", return_value=result) as eligible:
                        receipt = self.execute_effect(invocation, operation)
                        eligible.assert_called_once_with(operation)
                    self.assert_not_attempted(invocation, receipt)

    def test_non_verified_malformed_or_wrong_point_mapping_blocks_effect(self):
        for case in ("unknown", "duck", "wrong_point", "tampered", "wrong_status", "exception"):
            with self.subTest(case=case):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    if case == "unknown":
                        mapped = _CoordinateResult()
                    elif case == "duck":
                        mapped = Mock(status=VerificationStatus.VERIFIED)
                    else:
                        point = _ProposedPoint(*POINT) if case == "wrong_point" else self.point
                        evidence = _CoordinateEvidence(point, 30000, 26000, 4000, 4000,
                            ((point.x - 30000) * 65535) // 3999, ((point.y - 26000) * 65535) // 3999)
                        mapped = _CoordinateResult(VerificationStatus.VERIFIED, evidence)
                        if case == "tampered":
                            object.__setattr__(evidence, "normalized_x", True)
                        elif case == "wrong_status":
                            object.__setattr__(mapped, "status", VerificationStatus.NOT_VERIFIED)
                    with patch.object(_PointerCoordinateService, "normalize", return_value=mapped,
                                      side_effect=RuntimeError("PRIVATE_MAPPING") if case == "exception" else None) as normalize:
                        receipt = self.execute_effect(invocation, operation)
                        normalize.assert_called_once_with(self.point)
                    self.assert_not_attempted(invocation, receipt)

    def test_receipts_preserved_once_no_retry_no_undo_sanitized_audit(self):
        for count, status in ((3, _EffectStatus.INSERTED), (1, _EffectStatus.PARTIAL),
                              (2, _EffectStatus.PARTIAL), (0, _EffectStatus.INDETERMINATE),
                              (None, _EffectStatus.INDETERMINATE)):
            with self.subTest(count=count):
                self.setUp()
                self.effect_native._send_input.return_value = count
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    receipt = self.execute_effect(invocation, operation)
                    self.assertEqual(receipt, _PointerEffectReceipt(status, True, count))
                    self.assertEqual(self.execute_effect(invocation, operation), _PointerEffectReceipt())
                    self.assert_cleared(invocation)
                self.effect_native._send_input.assert_called_once()
                events = [e for e in self.audit.all() if e.event_type is AuditEventType.POINTER_EFFECT_OUTCOME]
                self.assertEqual([e.outcome for e in events], [status.value, "not_attempted"])
                for event in self.audit.all():
                    self.assertEqual(event.details, {})
                    text = event.message + repr(event.details)
                    for private in (str(POINT[0]), str(POINT[1]), repr(I), I.executable,
                                    "PRIVATE_MAPPING", "PRIVATE_NATIVE"):
                        self.assertNotIn(private, text)
                    self.assertNotIn(event.event_type, (AuditEventType.EXECUTION_SUCCEEDED, AuditEventType.UNDO_REGISTERED))

    def test_effect_exception_or_invalid_receipt_is_indeterminate_no_retry(self):
        for case in ("exception", "duck", "tampered"):
            with self.subTest(case=case):
                self.setUp()
                receipt = _PointerEffectReceipt(_EffectStatus.INSERTED, True, 3)
                if case == "tampered":
                    object.__setattr__(receipt, "inserted", True)
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    with patch.object(_PointerEffectService, "_insert",
                                      return_value=Mock() if case == "duck" else receipt,
                                      side_effect=RuntimeError("PRIVATE_NATIVE") if case == "exception" else None) as insert:
                        result = self.execute_effect(invocation, operation)
                        self.assertEqual(result, _PointerEffectReceipt(_EffectStatus.INDETERMINATE, True))
                        self.execute_effect(invocation, operation)
                        insert.assert_called_once()
                    self.assert_cleared(invocation)
                self.effect_native._send_input.assert_not_called()
                self.assertNotIn("PRIVATE_NATIVE", repr(self.audit.all()))

    def test_audit_failure_after_insertion_preserves_receipt(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            original_record = self.audit.record

            def record(event, **kwargs):
                if event in (AuditEventType.VERIFICATION_OUTCOME, AuditEventType.POINTER_EFFECT_OUTCOME):
                    raise OSError("PRIVATE_AUDIT_FAILURE")
                return original_record(event, **kwargs)

            with patch.object(self.audit, "record", side_effect=record):
                receipt = self.execute_effect(invocation, operation)
            self.assertEqual(receipt, _PointerEffectReceipt(_EffectStatus.INSERTED, True, 3))
            self.assert_cleared(invocation)
        self.effect_native._send_input.assert_called_once()

    def test_existing_approve_remains_read_only_in_effect_mode(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.assertEqual(self.approve(invocation, operation),
                             _PointerEligibilityResult(VerificationStatus.VERIFIED))
            self.assertEqual(self.execute_effect(invocation, operation), _PointerEffectReceipt())
            self.assert_cleared(invocation)
        self.metric_native.metric.assert_not_called()
        self.effect_native._send_input.assert_not_called()

    def test_fake_and_subclass_services_rejected_before_native_reads(self):
        class EffectSubclass(_PointerEffectService):
            pass

        class CoordinateSubclass(_PointerCoordinateService):
            pass

        for effect, coordinate in ((Mock(), self.coordinate_service),
                (object.__new__(EffectSubclass), self.coordinate_service),
                (self.effect_service, Mock()),
                (self.effect_service, CoordinateSubclass(native=self.metric_native, platform="win32"))):
            with self.subTest(effect=type(effect).__name__, coordinate=type(coordinate).__name__):
                with self.assertRaises(TypeError):
                    with self.executor._pointer_invocation(
                        self.capability, service=self.service, hit_service=self.hit_service,
                        effect_service=effect, coordinate_service=coordinate, ui_element_service=self.ui_element_service):
                        self.fail("Untrusted service accepted")
        self.native.foreground.assert_not_called()
        self.metric_native.metric.assert_not_called()
        self.effect_native._send_input.assert_not_called()



class PointerEffectBoundaryTests(unittest.TestCase):
    """Additional Phase 6.11 boundaries, injected fakes only."""
    prepare = PointerBindingTests.prepare

    def setUp(self):
        PointerBindingTests.setUp(self)
        self.ui_element_service = _UIAHarness().service()
        self.metrics = Mock(spec=['metric'])
        self.metrics.metric.side_effect = [0, 0, 65536, 65536]
        self.coordinates = _PointerCoordinateService(native=self.metrics, platform='win32')
        self.effect_native = Mock(spec=['_send_input'])
        self.effect_native._send_input.return_value = 3
        self.effect_service = _PointerEffectService(native=self.effect_native, platform='win32')
        for module, factory in (('pointer_effect', '_PointerEffectNative'),
                                ('pointer_coordinates', '_CoordinateNative')):
            guard = patch('nayeon.services.' + module + '.' + factory,
                          side_effect=AssertionError('NO LIVE NATIVE'))
            guarded = guard.start()
            self.addCleanup(guard.stop)
            self.addCleanup(guarded.assert_not_called)

    def invocation(self):
        return self.executor._pointer_invocation(
            self.capability, service=self.service, hit_service=self.hit_service,
            coordinate_service=self.coordinates, effect_service=self.effect_service, ui_element_service=self.ui_element_service)

    def effect(self, invocation, operation):
        return invocation._execute_effect(
            operation, target=operation.target, action=operation.action, point=operation.point)

    def assert_cleared(self, invocation):
        PointerBindingTests.assert_cleared(self, invocation)
        for name in ('_coordinate_service', '_effect_service', '_services',
                     '_registered', '_implementation'):
            self.assertIsNone(getattr(invocation, name))

    def assert_blocked(self, invocation, operation):
        result = self.effect(invocation, operation)
        self.assertIs(result.status, _EffectStatus.NOT_ATTEMPTED)
        self.assertFalse(result.attempted)
        self.effect_native._send_input.assert_not_called()
        self.assert_cleared(invocation)

    def test_replaced_services_including_same_exact_types_block_before_fresh_reads(self):
        for name in ('_service', '_hit_service', '_coordinate_service', '_effect_service'):
            for same_type in (False, True):
                with self.subTest(name=name, same_type=same_type):
                    self.setUp()
                    with self.invocation() as invocation:
                        operation, _ = self.prepare(invocation)
                        original = getattr(invocation, name)
                        replacement = type(original)(native=Mock(), platform='win32') if same_type else Mock()
                        setattr(invocation, name, replacement)
                        self.assert_blocked(invocation, operation)
                    self.metrics.metric.assert_not_called()
                    self.assertEqual(self.native.foreground.call_count, 2)

    def test_service_replacement_during_fresh_eligibility_blocks_mapping(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            original = self.service.acquire_target
            def acquire():
                fresh = original()
                invocation._coordinate_service = _PointerCoordinateService(native=Mock(), platform='win32')
                return fresh
            with patch.object(self.service, 'acquire_target', side_effect=acquire):
                self.assert_blocked(invocation, operation)
        self.metrics.metric.assert_not_called()

    def test_equal_registry_metadata_replacement_blocks_execution(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            self.registry.unregister(self.capability.name)
            self.registry.register(replace(self.capability), self.implementation)
            self.assert_blocked(invocation, operation)
        self.metrics.metric.assert_not_called()

    def test_malformed_policy_decisions_and_allow_block_before_fresh_reads(self):
        from nayeon.policy.service import PolicyAction, PolicyDecision
        for value in (None, Mock(action=PolicyAction.CONFIRM, reason='PRIVATE_POLICY'),
                      PolicyDecision('confirm', 'PRIVATE_POLICY'),
                      PolicyDecision(PolicyAction.ALLOW, 'PRIVATE_POLICY')):
            with self.subTest(value=type(value).__name__):
                self.setUp()
                with self.invocation() as invocation:
                    operation, _ = self.prepare(invocation)
                    with patch.object(self.policy, 'evaluate', return_value=value):
                        self.assert_blocked(invocation, operation)
                self.metrics.metric.assert_not_called()
                self.assertEqual(self.native.foreground.call_count, 2)
                self.assertNotIn('PRIVATE_POLICY', repr(self.audit.all()))

    def test_malformed_confirmation_results_and_exception_block_before_policy(self):
        from nayeon.policy.confirmation import ConfirmationResult
        for value in (None, Mock(approved=True, reason='PRIVATE_CONFIRM'),
                      ConfirmationResult(1, 'PRIVATE_CONFIRM'), OSError('PRIVATE_CONFIRM')):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                kwargs = {'side_effect': value} if isinstance(value, Exception) else {'return_value': value}
                with patch.object(self.confirmation, 'approve', **kwargs), \
                     patch.object(self.policy, 'evaluate', wraps=self.policy.evaluate) as policy:
                    self.assert_blocked(invocation, operation)
                    policy.assert_not_called()
            self.metrics.metric.assert_not_called()
            self.assertNotIn('PRIVATE_CONFIRM', repr(self.audit.all()))

    def test_confirmation_request_and_capability_mismatch_block(self):
        for field in ('request', 'capability'):
            self.setUp()
            with self.invocation() as invocation:
                operation, confirmation = self.prepare(invocation)
                self.confirmation._pending[confirmation.token] = replace(confirmation, **{field: 'changed'})
                self.assert_blocked(invocation, operation)
            self.metrics.metric.assert_not_called()
            self.assertEqual(self.native.foreground.call_count, 2)

    def test_effect_missing_and_verified_eligibility_cannot_be_promoted(self):
        with self.executor._pointer_invocation(
                self.capability, service=self.service, hit_service=self.hit_service) as invocation:
            operation, _ = self.prepare(invocation)
            self.assert_blocked(invocation, operation)
        self.setUp()
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            eligibility = invocation.approve(operation, target=operation.target,
                                             action=operation.action, point=operation.point)
            self.assertIs(eligibility.status, VerificationStatus.VERIFIED)
            self.assert_blocked(invocation, operation)
            result = invocation._execute_effect(eligibility, target=operation.target,
                                                action=operation.action, point=operation.point)
            self.assertFalse(result.attempted)
        self.metrics.metric.assert_not_called()
        self.assertFalse(hasattr(_PointerInvocation, '_effect_now'))

    def test_native_invalid_counts_and_seam_exception_are_indeterminate_without_retry(self):
        for returned in (True, False, -1, 4, 3.0, '3', None):
            self.setUp()
            self.effect_native._send_input.return_value = returned
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                result = self.effect(invocation, operation)
                self.assertIs(result.status, _EffectStatus.INDETERMINATE)
                self.assertTrue(result.attempted)
                self.assertIsNone(result.inserted)
                self.assert_cleared(invocation)
            self.effect_native._send_input.assert_called_once()
        self.setUp()
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(_PointerEffectService, '_insert', side_effect=OSError('PRIVATE_SEAM')) as insert:
                result = self.effect(invocation, operation)
                self.assertIs(result.status, _EffectStatus.INDETERMINATE)
                self.assertTrue(result.attempted)
                insert.assert_called_once()
            self.assert_cleared(invocation)
        self.assertNotIn('PRIVATE_SEAM', repr(self.audit.all()))

    def test_service_subclasses_rejected_without_native_construction(self):
        class Coordinates(_PointerCoordinateService):
            pass
        class Effect(_PointerEffectService):
            pass
        for coordinates, effect in ((Coordinates(native=Mock()), self.effect_service),
                                    (self.coordinates, object.__new__(Effect))):
            with self.assertRaises(TypeError):
                with self.executor._pointer_invocation(
                        self.capability, service=self.service, hit_service=self.hit_service,
                        coordinate_service=coordinates, effect_service=effect, ui_element_service=self.ui_element_service):
                    self.fail('Service subclass accepted')
        self.metrics.metric.assert_not_called()
        self.effect_native._send_input.assert_not_called()

    def test_malformed_fresh_service_results_block_execution(self):
        for kind in ('target', 'hit'):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                if kind == 'target':
                    with patch.object(self.service, 'acquire_target', return_value=Mock(identity=I, context=C)):
                        self.assert_blocked(invocation, operation)
                else:
                    with patch.object(_PointerHitValidationService, 'validate_hit',
                                      return_value=Mock(status=VerificationStatus.VERIFIED)):
                        self.assert_blocked(invocation, operation)
            self.metrics.metric.assert_not_called()

    def test_abandoned_and_cross_invocation_operations_have_no_effect(self):
        with self.assertRaisesRegex(RuntimeError, 'caller'):
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                raise RuntimeError('caller')
        self.assert_cleared(invocation)
        self.setUp()
        with self.invocation() as next_invocation:
            self.prepare(next_invocation)
            self.assert_blocked(next_invocation, operation)
        self.metrics.metric.assert_not_called()

    def test_cleanup_exception_after_insertion_preserves_receipt_and_clears(self):
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(self.confirmation, 'reject', side_effect=OSError('PRIVATE_CLEANUP')):
                result = self.effect(invocation, operation)
            self.assertIs(result.status, _EffectStatus.INSERTED)
            self.assertEqual(result.inserted, 3)
            self.assert_cleared(invocation)
        self.effect_native._send_input.assert_called_once()
        self.assertNotIn('PRIVATE_CLEANUP', repr(self.audit.all()))
        failures = [e for e in self.audit.all()
                    if e.message == 'Private pointer binding cleanup failed.']
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].outcome, 'indeterminate')

    def test_effect_eligibility_and_coordinate_subclasses_are_rejected(self):
        from nayeon.services.pointer_coordinates import _CoordinateResult
        class Eligibility(_PointerEligibilityResult):
            pass
        class Coordinates(_CoordinateResult):
            pass
        # Use uninitialized subclasses only to exercise exact-type rejection;
        # no native or trusted result construction takes place here.
        for kind, result in (('eligibility', Eligibility(VerificationStatus.VERIFIED)),
                             ('coordinate', object.__new__(Coordinates))):
            self.setUp()
            with self.invocation() as invocation:
                operation, _ = self.prepare(invocation)
                cls, method = ((_PointerInvocation, '_eligible_now') if kind == 'eligibility'
                               else (_PointerCoordinateService, 'normalize'))
                with patch.object(cls, method, return_value=result):
                    self.assert_blocked(invocation, operation)
            self.metrics.metric.assert_not_called()

    def test_audit_does_not_run_between_geometry_and_effect(self):
        calls = Mock()
        calls.attach_mock(self.metrics.metric, 'metric')
        calls.attach_mock(self.effect_native._send_input, 'effect')
        with self.invocation() as invocation:
            operation, _ = self.prepare(invocation)
            with patch.object(self.audit, 'record', wraps=self.audit.record) as audit:
                calls.attach_mock(audit, 'audit')
                self.effect(invocation, operation)
        names = [c[0] for c in calls.mock_calls]
        first_metric = names.index('metric')
        self.assertEqual(names[first_metric:first_metric + 5], ['metric'] * 4 + ['effect'])
        self.assert_cleared(invocation)


if __name__ == "__main__":
    unittest.main()
