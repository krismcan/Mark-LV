"""Fake App Paths, exact-file checks, launches, snapshots, and waits only."""

from dataclasses import FrozenInstanceError
import unittest
from unittest.mock import MagicMock, Mock, call, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.audit.service import AuditEventType
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.service import PolicyService
from nayeon.services.application_observation import DEFAULT_APPLICATIONS, ProcessIdentity
from nayeon.services.applications import ApplicationService
from nayeon.services.notepad_app_paths import NOTEPAD_APP_PATHS_KEY, resolve_notepad_definition
from nayeon.verification.contract import VerificationStatus
from tests import test_open_app_observation as observation_tests


TRUSTED = r"c:\trusted\notepad.exe"


def fake_registration(test):
    test.enterContext(patch("nayeon.services.notepad_app_paths.platform.system", return_value="Windows"))
    test.win_registry = Mock(spec=["OpenKey", "QueryValueEx", "HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE",
                               "REG_SZ", "KEY_READ"])
    test.win_registry.HKEY_CURRENT_USER = "user"
    test.win_registry.HKEY_LOCAL_MACHINE = "machine"
    test.win_registry.REG_SZ = 1
    test.win_registry.KEY_READ = 0x20019
    test.values = {"user": ("C:/Trusted/Notepad.exe", 1)}
    test.handles = []
    def open_key(hive, key, reserved, access):
        test.assertEqual((key, reserved, access), (NOTEPAD_APP_PATHS_KEY, 0, test.win_registry.KEY_READ))
        handle = MagicMock()
        handle.__enter__.return_value = hive
        test.handles.append(handle)
        return handle
    def query(hive, value_name):
        test.assertEqual(value_name, "")
        value = test.values.get(hive, FileNotFoundError())
        if isinstance(value, Exception):
            raise value
        return value
    test.win_registry.OpenKey.side_effect = open_key
    test.win_registry.QueryValueEx.side_effect = query
    test.loader = test.enterContext(patch("nayeon.services.notepad_app_paths._registry",
                                         return_value=test.win_registry))
    test.is_file = test.enterContext(patch("nayeon.services.notepad_app_paths.Path.is_file", return_value=True))
    # Any accidental search rather than the exact-file check fails the test.
    for name in ("glob", "rglob", "iterdir"):
        test.enterContext(patch("pathlib.Path." + name, side_effect=AssertionError("No scanning")))
    test.enterContext(patch("shutil.which", side_effect=AssertionError("No PATH trust")))


class AppPathsTests(unittest.TestCase):
    def setUp(self):
        fake_registration(self)

    def test_valid_hkcu_supplies_only_notepad_identity(self):
        definition = resolve_notepad_definition()
        self.assertEqual(definition.application_id, "notepad")
        self.assertEqual(definition.targets, ("notepad", "notepad.exe"))
        self.assertEqual(definition.expected_process_names, ("notepad.exe",))
        self.assertEqual(definition.accepted_executable_paths, (TRUSTED,))
        self.win_registry.QueryValueEx.assert_called_once_with("user", "")
        self.handles[0].__exit__.assert_called_once()

    def test_valid_hkcu_precedes_machine_without_merging(self):
        self.values["machine"] = (r"D:\Machine\notepad.exe", 1)
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, (TRUSTED,))
        self.win_registry.OpenKey.assert_called_once_with("user", NOTEPAD_APP_PATHS_KEY, 0, self.win_registry.KEY_READ)

    def test_missing_hkcu_uses_machine(self):
        self.values = {"machine": (r"D:\Machine\notepad.exe", 1)}
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, (r"d:\machine\notepad.exe",))
        self.assertEqual(self.win_registry.QueryValueEx.call_args_list, [call("user", ""), call("machine", "")])

    def test_empty_hkcu_falls_back_to_valid_machine(self):
        self.values = {"user": ("", 1), "machine": (TRUSTED, 1)}
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, (TRUSTED,))

    def test_invalid_hkcu_falls_back_to_valid_machine(self):
        self.values = {"user": ("relative.exe", 1), "machine": (TRUSTED, 1)}
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, (TRUSTED,))

    def test_absent_registrations_leave_identity_unavailable(self):
        self.values.clear()
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, ())
        self.is_file.assert_not_called()

    def test_malformed_paths_are_rejected(self):
        for value in ("", " ", None, 17, r"notepad.exe", r"C:notepad.exe", r"%WINDIR%\notepad.exe",
                      r"C:\*\notepad.exe", r"\\host\share\notepad.exe", r"\\?\C:\notepad.exe",
                      r"C:\Apps\..\notepad.exe", r"C:\Apps\notepad.exe:stream",
                      '"C:\\Apps\\notepad.exe"', r"C:\Apps\other.exe", r"C:\Apps\notepad.exe --flag"):
            with self.subTest(value=value):
                self.values = {"user": (value, 1)}
                self.assertEqual(resolve_notepad_definition().accepted_executable_paths, ())
        self.is_file.assert_not_called()

    def test_non_reg_sz_values_are_rejected_without_expansion(self):
        for kind in (2, 3, 4, 7):
            with self.subTest(kind=kind):
                self.values = {"user": (TRUSTED, kind)}
                self.assertEqual(resolve_notepad_definition().accepted_executable_paths, ())

    def test_missing_exact_file_is_unavailable(self):
        self.is_file.return_value = False
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, ())
        self.is_file.assert_called_once()

    def test_missing_user_file_allows_valid_machine_file(self):
        self.values["machine"] = (r"D:\Machine\notepad.exe", 1)
        self.is_file.side_effect = [False, True]
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, (r"d:\machine\notepad.exe",))

    def test_registry_or_file_access_errors_fail_safely(self):
        self.values["user"] = PermissionError("fake-private")
        self.values["machine"] = (TRUSTED, 1)
        self.is_file.side_effect = OSError("fake-private")
        definition = resolve_notepad_definition()
        self.assertEqual(definition.accepted_executable_paths, ())
        self.assertNotIn("fake-private", repr(definition))

    def test_open_key_error_allows_machine_fallback(self):
        original = self.win_registry.OpenKey.side_effect
        def open_key(hive, *args):
            if hive == "user":
                raise PermissionError("fake")
            return original(hive, *args)
        self.win_registry.OpenKey.side_effect = open_key
        self.values["machine"] = (TRUSTED, 1)
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, (TRUSTED,))

    def test_non_windows_never_loads_registry(self):
        with patch("nayeon.services.notepad_app_paths.platform.system", return_value="Linux"):
            self.assertEqual(resolve_notepad_definition().accepted_executable_paths, ())
        self.loader.assert_not_called()

    def test_missing_registry_api_is_unavailable(self):
        self.loader.side_effect = ImportError("fake")
        self.assertEqual(resolve_notepad_definition().accepted_executable_paths, ())

    def test_definition_is_immutable_and_not_rebuilt_from_registry_changes(self):
        definition = resolve_notepad_definition()
        self.values["user"] = (r"C:\Changed\notepad.exe", 1)
        self.assertEqual(definition.accepted_executable_paths, (TRUSTED,))
        with self.assertRaises(FrozenInstanceError):
            definition.accepted_executable_paths = ()

    def test_explicit_definitions_do_not_read_registry(self):
        service = ApplicationService(applications=DEFAULT_APPLICATIONS)
        self.assertIsNone(service.trusted_notepad_path)
        self.loader.assert_not_called()


class TrustedNotepadTests(unittest.TestCase):
    execute = observation_tests.OpenAppObservationTests.execute
    protected = observation_tests.OpenAppObservationTests.protected
    approve = observation_tests.OpenAppObservationTests.approve
    session = observation_tests.OpenAppObservationTests.session

    def setUp(self):
        observation_tests.OpenAppObservationTests.setUp(self)
        fake_registration(self)
        self.service = ApplicationService(sleeper=self.sleeper)
        self.app._service = self.service
        self.launch = self.enterContext(patch.object(self.service, "launch", wraps=self.service.launch))
        self.observe = self.enterContext(patch.object(self.service, "observe_readiness",
                                                     wraps=self.service.observe_readiness))
        self.popen = self.enterContext(patch("nayeon.services.applications.subprocess.Popen"))
        self.startfile = self.enterContext(patch("nayeon.services.applications.os.startfile"))
        self.enterContext(patch("nayeon.services.applications.Path.exists", return_value=False))

    def test_default_configuration_launches_registered_path_once_and_verifies(self):
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.service.trusted_notepad_path, TRUSTED)
        self.assertEqual(self.popen.call_args.args, ([TRUSTED],))
        self.assertEqual(result.output.target, "Notepad.EXE")
        self.popen.assert_called_once()
        self.verify.assert_called_once()
        self.startfile.assert_not_called()

    def test_case_equivalent_observed_identity_verifies(self):
        self.snapshot.return_value = (ProcessIdentity("notepad.exe", "C:/TRUSTED/NOTEPAD.EXE"),)
        self.assertEqual(self.execute().verification.status, VerificationStatus.VERIFIED)

    def test_wrong_path_never_redefines_trusted_identity(self):
        self.snapshot.return_value = (ProcessIdentity("notepad.exe", r"C:\Other\notepad.exe"),)
        self.assertEqual(self.execute().verification.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(self.snapshot.call_count, 3)
        self.assertEqual(self.service.trusted_notepad_path, TRUSTED)
        self.popen.assert_called_once()

    def test_unavailable_identity_remains_indeterminate(self):
        self.snapshot.return_value = (ProcessIdentity("notepad.exe", None),)
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_absence_throughout_window_is_indeterminate_without_relaunch(self):
        self.snapshot.return_value = ()
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(self.snapshot.call_count, 3)
        self.assertEqual(self.sleeper.call_args_list, [call(0.1), call(0.1)])
        self.popen.assert_called_once()

    def test_missing_registration_preserves_launch_but_cannot_verify(self):
        self.values.clear()
        service = ApplicationService(sleeper=self.sleeper)
        self.app._service = service
        self.assertIsNone(service.trusted_notepad_path)
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(self.popen.call_args.args, (["Notepad.EXE"],))
        self.snapshot.assert_not_called()

    def test_trusted_launch_failure_has_no_fallback_or_verification(self):
        self.popen.side_effect = FileNotFoundError("fake-private")
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.popen.assert_called_once()
        self.verify.assert_not_called()
        self.snapshot.assert_not_called()
        self.assertNotIn("fake-private", repr(result))

    def test_raw_wording_cannot_override_registered_identity(self):
        self.request = StructuredCapabilityRequest(r"open C:\Other\notepad.exe", {"application": "notepad"})
        self.assertEqual(self.execute().verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.popen.call_args.args, ([TRUSTED],))

    def test_unregistered_user_path_gets_no_notepad_trust(self):
        self.request = StructuredCapabilityRequest("open it", {"application": r"C:\Other\notepad.exe"})
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(self.service.trusted_notepad_path, TRUSTED)
        self.snapshot.assert_not_called()

    def test_fuzzy_path_or_process_never_verifies(self):
        self.snapshot.return_value = (ProcessIdentity("notepad.exe", r"C:\Trusted-extra\notepad.exe"),)
        self.assertEqual(self.execute().verification.status, VerificationStatus.NOT_VERIFIED)
        self.snapshot.return_value = (ProcessIdentity("mynotepad.exe", TRUSTED),)
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_registry_is_frozen_for_execution_and_verification(self):
        self.values["user"] = (r"C:\Changed\notepad.exe", 1)
        self.execute()
        self.assertEqual(self.popen.call_args.args, ([TRUSTED],))
        self.win_registry.QueryValueEx.assert_called_once()

    def test_permission_denial_never_launches_or_verifies(self):
        self.permissions.revoke("open_app")
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.popen.assert_not_called()
        self.verify.assert_not_called()

    def test_policy_denial_never_launches_or_verifies(self):
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions, {"open_app"}),
                                       ConfirmationService(), self.audit, self.undo)
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.popen.assert_not_called()
        self.verify.assert_not_called()

    def test_confirmation_approval_uses_frozen_identity_once(self):
        self.protected()
        pending = self.execute()
        self.popen.assert_not_called()
        self.verify.assert_not_called()
        self.values.clear()
        self.assertEqual(self.approve(pending).verification.status, VerificationStatus.VERIFIED)
        self.popen.assert_called_once()
        self.assertEqual(self.approve(pending).status, ExecutionStatus.DENIED)

    def test_audit_and_evidence_are_minimal_and_undo_unchanged(self):
        callback = Mock()
        self.undo.register(capability="prior", description="prior", callback=callback)
        result = self.execute()
        self.assertEqual(result.verification.evidence, {
            "application_id": "notepad", "state": "observed_open", "identity": "matched",
        })
        self.assertEqual([e.event_type for e in self.audit.all()], [
            AuditEventType.POLICY_DECISION, AuditEventType.EXECUTION_STARTED,
            AuditEventType.EXECUTION_SUCCEEDED, AuditEventType.VERIFICATION_OUTCOME,
        ])
        self.assertNotIn("trusted", repr(self.audit.all()).lower())
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()

    def test_session_launches_registered_identity(self):
        self.assertEqual(self.session().request("open notepad").verification.status, VerificationStatus.VERIFIED)
        self.popen.assert_called_once()
        self.assertEqual(self.popen.call_args.args, ([TRUSTED],))

    def test_legacy_launch_preserves_receipt_target(self):
        result = self.executor.execute(self.capability, "open notepad")
        self.assertEqual(result.output.target, "notepad")
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.popen.assert_called_once()
