"""Application capability tests never reach an OS launch implementation."""

import unittest
from unittest.mock import patch

from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapability


class OpenAppStructuredTests(unittest.TestCase):
    def setUp(self):
        service = self.enterContext(patch("nayeon.capabilities.open_app.ApplicationService"))
        self.launch = service.return_value.launch
        self.capability = OpenAppCapability()

    def test_contract_and_validation_normalize_without_launch(self):
        self.assertIsInstance(self.capability, StructuredCapability)
        arguments = {"application": "  Example App  "}
        self.assertEqual(self.capability.validate_arguments(arguments),
                         {"application": "Example App"})
        self.assertEqual(arguments["application"], "  Example App  ")
        self.launch.assert_not_called()

    def test_missing_blank_non_string_and_unknown_arguments_rejected(self):
        for arguments in ({}, {"application": ""}, {"application": " \t"},
                          {"application": None}, {"application": 42},
                          {"application": []}, {"application": "app", "extra": True}):
            with self.subTest(arguments=arguments):
                with self.assertRaises((ValueError, TypeError)):
                    self.capability.validate_arguments(arguments)
        self.launch.assert_not_called()

    def test_non_mapping_is_rejected(self):
        with self.assertRaises(TypeError):
            self.capability.validate_arguments([("application", "app")])
        self.launch.assert_not_called()

    def test_structured_execution_launches_validated_target_once(self):
        result = self.capability.execute_structured({"application": " Example App "})
        self.launch.assert_called_once_with("Example App")
        self.assertIs(result, self.launch.return_value)

    def test_structured_execution_revalidates_invalid_input(self):
        with self.assertRaises(ValueError):
            self.capability.execute_structured({"application": "app", "command": "ignored?"})
        self.launch.assert_not_called()

    def test_legacy_prefixes_and_direct_target_remain_supported(self):
        for request in ("open Example App", " LAUNCH Example App ",
                        "start Example App", " Example App "):
            with self.subTest(request=request):
                self.launch.reset_mock()
                self.capability.execute(request)
                self.launch.assert_called_once_with("Example App")

    def test_legacy_empty_request_still_delegates_to_service(self):
        self.capability.execute("  ")
        self.launch.assert_called_once_with("")
