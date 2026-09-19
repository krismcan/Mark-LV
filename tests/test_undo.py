"""Undo contracts and bounded in-memory callbacks."""

import unittest
from unittest.mock import Mock

from nayeon.undo.contract import UndoProvider, UndoRegistration
from nayeon.undo.service import UndoService


class UndoTests(unittest.TestCase):
    def setUp(self):
        self.service = UndoService(max_depth=2)

    def register(self, callback, description="Restore test state"):
        return self.service.register(capability="example", description=description,
                                     callback=callback)

    def test_empty_stack_has_no_undo(self):
        self.assertEqual(self.service.count(), 0)
        self.assertIsNone(self.service.peek())
        result = self.service.undo_last()
        self.assertFalse(result.success)
        self.assertIsNone(result.operation_id)

    def test_register_does_not_execute_and_undo_returns_output(self):
        callback = Mock(return_value="restored")
        operation = self.register(callback)
        callback.assert_not_called()
        self.assertIs(self.service.peek(), operation)
        result = self.service.undo_last()
        callback.assert_called_once_with()
        self.assertTrue(result.success)
        self.assertEqual(result.operation_id, operation.operation_id)
        self.assertEqual(result.capability, "example")
        self.assertEqual(result.output, "restored")
        self.assertEqual(self.service.count(), 0)

    def test_capacity_discards_oldest_and_undo_is_lifo(self):
        calls = []
        for number in (1, 2, 3):
            self.register(lambda number=number: calls.append(number))
        self.assertEqual(self.service.count(), 2)
        self.service.undo_last()
        self.service.undo_last()
        self.assertEqual(calls, [3, 2])
        self.assertFalse(self.service.undo_last().success)

    def test_callback_exception_is_reported_without_retry(self):
        callback = Mock(side_effect=RuntimeError("test failure"))
        operation = self.register(callback)
        result = self.service.undo_last()
        self.assertFalse(result.success)
        self.assertEqual(result.operation_id, operation.operation_id)
        self.assertIn("test failure", result.message)
        self.assertEqual(self.service.count(), 0)
        self.assertFalse(self.service.undo_last().success)
        callback.assert_called_once_with()

    def test_clear_drops_callbacks_without_invoking_them(self):
        callback = Mock()
        self.register(callback)
        self.service.clear()
        self.assertEqual(self.service.count(), 0)
        callback.assert_not_called()

    def test_invalid_depth_and_registrations_are_rejected(self):
        for depth in (0, -1):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                UndoService(max_depth=depth)
        for capability, description, callback, error in (
            (" ", "restore", lambda: None, ValueError),
            ("example", " ", lambda: None, ValueError),
            ("example", "restore", None, TypeError),
        ):
            with self.subTest(capability=capability, description=description), self.assertRaises(error):
                self.service.register(capability=capability, description=description, callback=callback)
        self.assertEqual(self.service.count(), 0)

    def test_undo_registration_requires_description_and_callable(self):
        with self.assertRaises(ValueError):
            UndoRegistration(" ", lambda: None)
        with self.assertRaises(TypeError):
            UndoRegistration("restore", None)
        callback = Mock()
        registration = UndoRegistration("restore", callback)
        self.assertIs(registration.callback, callback)
        callback.assert_not_called()

    def test_undo_provider_is_a_structural_contract(self):
        class Provider:
            def build_undo(self, request, output):
                raise AssertionError("Detection must not construct undo")

        self.assertIsInstance(Provider(), UndoProvider)
        self.assertNotIsInstance(object(), UndoProvider)
