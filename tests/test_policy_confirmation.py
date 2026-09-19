"""Permission precedence and confirmations with a controlled clock."""

from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyAction, PolicyService
from nayeon.registry import Capability, ExecutionMode


class PermissionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.permissions = PermissionService(default_allowed=False)
        self.capability = Capability(
            "example", "Test", ExecutionMode.LOCAL, "fake", requires_confirmation=True
        )

    def test_permission_defaults_are_configurable(self):
        self.assertFalse(self.permissions.check("example").allowed)
        self.assertTrue(PermissionService().check("example").allowed)

    def test_grant_revoke_and_regrant_normalize_names(self):
        self.permissions.grant(" example ")
        self.assertTrue(self.permissions.check("example").allowed)
        self.permissions.revoke("example")
        self.assertFalse(self.permissions.check(" example ").allowed)
        self.permissions.grant("example")
        self.assertTrue(self.permissions.check("example").allowed)

    def test_permission_methods_reject_blank_names(self):
        for method in (self.permissions.check, self.permissions.grant, self.permissions.revoke):
            with self.subTest(method=method.__name__), self.assertRaises(ValueError):
                method("  ")

    def test_permission_denial_precedes_confirmation(self):
        decision = PolicyService(self.permissions).evaluate(self.capability)
        self.assertEqual(decision.action, PolicyAction.DENY)
        self.assertTrue(decision.denied)
        self.assertFalse(decision.allowed)
        self.assertFalse(decision.requires_confirmation)

    def test_explicit_grant_cannot_override_policy_block(self):
        self.permissions.grant("example")
        decision = PolicyService(self.permissions, {"example"}).evaluate(self.capability)
        self.assertTrue(decision.denied)

    def test_allowed_permission_preserves_confirmation_requirement(self):
        self.permissions.grant("example")
        decision = PolicyService(self.permissions).evaluate(self.capability)
        self.assertEqual(decision.action, PolicyAction.CONFIRM)
        self.assertTrue(decision.requires_confirmation)
        self.assertFalse(decision.allowed)
        self.assertFalse(decision.denied)

    def test_unprotected_permitted_capability_is_allowed(self):
        capability = Capability("example", "Test", ExecutionMode.LOCAL, "fake")
        self.permissions.grant("example")
        decision = PolicyService(self.permissions).evaluate(capability)
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)
        self.assertFalse(decision.denied)


class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.clock = self.enterContext(patch("nayeon.policy.confirmation.datetime"))
        self.clock.now.return_value = self.now
        self.enterContext(patch("nayeon.policy.confirmation.secrets.token_urlsafe",
                                side_effect=("test-token-1", "test-token-2")))
        self.service = ConfirmationService(ttl_seconds=120)

    def create(self):
        return self.service.create("example", "do example")

    def approve(self, token, capability="example", request="do example"):
        return self.service.approve(token, capability=capability, request=request)

    def test_create_normalizes_and_sets_lifetime(self):
        pending = self.service.create(" example ", " do example ")
        self.assertEqual(pending.capability, "example")
        self.assertEqual(pending.request, "do example")
        self.assertEqual(pending.created_at, self.now)
        self.assertEqual(pending.expires_at, self.now + timedelta(seconds=120))

    def test_invalid_lifetime_and_blank_requests_are_rejected(self):
        for ttl in (0, -1):
            with self.subTest(ttl=ttl), self.assertRaises(ValueError):
                ConfirmationService(ttl_seconds=ttl)
        for capability, request in ((" ", "request"), ("example", " ")):
            with self.subTest(capability=capability, request=request), self.assertRaises(ValueError):
                self.service.create(capability, request)

    def test_matching_token_approves_only_once(self):
        token = self.create().token
        self.assertTrue(self.approve(token).approved)
        self.assertFalse(self.approve(token).approved)

    def test_unknown_token_is_rejected(self):
        self.assertFalse(self.approve("not-issued").approved)

    def test_capability_mismatch_rejects_and_consumes_token(self):
        token = self.create().token
        self.assertFalse(self.approve(token, capability="other").approved)
        self.assertFalse(self.approve(token).approved)

    def test_request_mismatch_rejects_and_consumes_token(self):
        token = self.create().token
        self.assertFalse(self.approve(token, request="different action").approved)
        self.assertFalse(self.approve(token).approved)

    def test_expired_confirmation_cannot_be_reused(self):
        pending = self.create()
        self.clock.now.return_value = pending.expires_at + timedelta(seconds=1)
        self.assertFalse(self.approve(pending.token).approved)
        self.clock.now.return_value = self.now
        self.assertFalse(self.approve(pending.token).approved)

    def test_rejection_cancels_only_the_selected_token(self):
        first, second = self.create(), self.create()
        self.assertFalse(self.service.reject(first.token).approved)
        self.assertFalse(self.approve(first.token).approved)
        self.assertTrue(self.approve(second.token).approved)
