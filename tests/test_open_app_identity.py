"""Trusted identity checks using fake snapshots and mocked Win32 calls only."""

from copy import deepcopy
import ctypes
import unittest
from unittest.mock import Mock, call, patch

from nayeon.agent.executor import ExecutionStatus
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.services.application_observation import (
    ApplicationDefinition, ApplicationIdentity, ApplicationObservation, ApplicationState,
    ProcessIdentity, normalize_executable_path, windows_process_identities,
    _kernel32 as load_kernel32,
)
from nayeon.services.applications import ApplicationService
from nayeon.verification.contract import VerificationStatus
from tests import test_open_app_observation as observation_tests


class OpenAppIdentityTests(unittest.TestCase):
    # Reuse the real executor/policy/audit harness without rediscovering its tests.
    setUp = observation_tests.OpenAppObservationTests.setUp
    execute = observation_tests.OpenAppObservationTests.execute

    def observe_paths(self, *paths):
        self.snapshot.return_value = tuple(ProcessIdentity("notepad.exe", path) for path in paths)
        return self.execute()

    def test_exact_trusted_identity_is_verified(self):
        result = self.observe_paths(r"C:\Trusted\notepad.exe")
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.snapshot.assert_called_once_with(("notepad.exe",))

    def test_case_and_separator_equivalent_path_is_verified(self):
        self.assertEqual(self.observe_paths("c:/TRUSTED/NOTEPAD.EXE").verification.status,
                         VerificationStatus.VERIFIED)

    def test_readable_same_name_path_mismatch_is_not_verified(self):
        result = self.observe_paths(r"C:\Other\notepad.exe")
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(result.verification.evidence["identity"], "mismatched")
        self.assertEqual(self.audit.all()[-1].outcome, "not_verified")

    def test_unavailable_path_is_indeterminate(self):
        self.assertEqual(self.observe_paths(None).verification.status, VerificationStatus.INDETERMINATE)

    def test_access_error_is_indeterminate_and_redacted(self):
        self.snapshot.side_effect = PermissionError("fake-private-path")
        result = self.execute()
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn("fake-private-path", repr(result.verification) + repr(self.audit.all()))

    def test_malformed_path_never_becomes_negative(self):
        for path in ("", 42, r"C:notepad.exe", r"\notepad.exe", r"C:\Trusted\..\notepad.exe",
                     "C:\\Trusted\\notepad.exe\x00", r"C:\Trusted\notepad.exe:stream",
                     r"\\?\C:\Trusted\notepad.exe", r"\\host\share\notepad.exe"):
            with self.subTest(path=path):
                self.assertEqual(self.observe_paths(path).verification.status, VerificationStatus.INDETERMINATE)

    def test_default_metadata_without_trusted_paths_cannot_verify(self):
        self.observe.side_effect = ApplicationService().observe
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.snapshot.assert_not_called()

    def test_empty_complete_candidate_snapshot_is_indeterminate(self):
        self.assertEqual(self.observe_paths().verification.status, VerificationStatus.INDETERMINATE)

    def test_unreadable_candidate_prevents_all_mismatch_claim(self):
        self.assertEqual(self.observe_paths(r"C:\Other\notepad.exe", None).verification.status,
                         VerificationStatus.INDETERMINATE)

    def test_exact_positive_survives_an_unreadable_other_candidate(self):
        self.assertEqual(self.observe_paths(None, r"C:\Trusted\notepad.exe").verification.status,
                         VerificationStatus.VERIFIED)

    def test_all_readable_candidates_mismatch(self):
        self.assertEqual(self.observe_paths(r"C:\One\notepad.exe", r"C:\Two\notepad.exe").verification.status,
                         VerificationStatus.NOT_VERIFIED)

    def test_one_exact_identity_among_mismatches_is_verified(self):
        self.assertEqual(self.observe_paths(r"C:\Other\notepad.exe", r"C:\Trusted\notepad.exe").verification.status,
                         VerificationStatus.VERIFIED)

    def test_inconsistent_candidate_basename_is_indeterminate(self):
        # PID reuse or inconsistent provider evidence must not create a mismatch claim.
        self.assertEqual(self.observe_paths(r"C:\Other\editor.exe").verification.status,
                         VerificationStatus.INDETERMINATE)

    def test_fuzzy_process_records_are_not_accepted(self):
        for name in ("mynotepad.exe", "notepad.exe.backup", "note", None):
            with self.subTest(name=name):
                self.snapshot.return_value = (ProcessIdentity(name, r"C:\Trusted\notepad.exe"),)
                self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_parent_and_substring_paths_are_not_matches(self):
        for path in (r"C:\Trusted-extra\notepad.exe", r"C:\Trusted\Subdir\notepad.exe",
                     r"D:\Trusted\notepad.exe"):
            with self.subTest(path=path):
                self.assertEqual(self.observe_paths(path).verification.status, VerificationStatus.NOT_VERIFIED)

    def test_raw_request_does_not_supply_trusted_identity(self):
        self.request = StructuredCapabilityRequest(r"open C:\Other\notepad.exe", {"application": "notepad"})
        self.assertEqual(self.observe_paths(r"C:\Other\notepad.exe").verification.status,
                         VerificationStatus.NOT_VERIFIED)
        self.observe.assert_called_once_with("notepad")

    def test_metadata_and_structured_request_are_not_mutated(self):
        definition = self.service._applications["notepad"]
        original = deepcopy((definition, self.request))
        self.execute()
        self.assertEqual((definition, self.request), original)

    def test_full_paths_do_not_escape_into_evidence_or_audit(self):
        result = self.observe_paths(r"C:\PrivateUser\notepad.exe")
        self.assertEqual(result.verification.evidence, {
            "application_id": "notepad", "state": "observed_open", "identity": "mismatched",
        })
        for private in ("PrivateUser", "Trusted", "C:\\"):
            self.assertNotIn(private, repr(result.verification) + repr(self.audit.all()))

    def test_name_only_or_malformed_typed_observation_cannot_verify(self):
        for identity in (ApplicationIdentity.UNKNOWN, "matched", None):
            with self.subTest(identity=identity):
                self.observe.return_value = ApplicationObservation(
                    "Notepad.EXE", ApplicationState.OBSERVED_OPEN, "notepad", ("notepad.exe",), identity,
                )
                self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)


class IdentityMetadataTests(unittest.TestCase):
    def test_paths_are_normalized_and_copied(self):
        paths = ["C:/Trusted//NOTEPAD.EXE", r"D:\Apps\notepad.exe"]
        definition = ApplicationDefinition("notepad", ("notepad",), ("notepad.exe",), paths)
        paths.clear()
        self.assertEqual(definition.accepted_executable_paths,
                         (r"c:\trusted\notepad.exe", r"d:\apps\notepad.exe"))

    def test_ambiguous_metadata_paths_rejected_without_resolution(self):
        for path in ("notepad.exe", r"C:notepad.exe", r"\notepad.exe", r"C:\..\notepad.exe",
                     r"C:\.\notepad.exe", r"C:\Bad.\notepad.exe", r"C:\Bad \notepad.exe",
                     r"C:\%Apps%\notepad.exe", r"C:\*\notepad.exe", r"C:\Apps\notepad.exe:stream",
                     r"\\?\C:\Apps\notepad.exe", r"\\host\share\notepad.exe", r"C:\Apps\editor.exe"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                ApplicationDefinition("notepad", ("notepad",), ("notepad.exe",), (path,))

    def test_paths_collection_not_a_single_string(self):
        with self.assertRaises(ValueError):
            ApplicationDefinition("notepad", ("notepad",), ("notepad.exe",), r"C:\notepad.exe")

    def test_no_environment_or_filesystem_lookup_for_normalization(self):
        with patch("os.path.realpath", side_effect=AssertionError("No filesystem")), \
                patch("os.path.expandvars", side_effect=AssertionError("No environment")):
            self.assertEqual(normalize_executable_path("C:/Apps/notepad.exe"), r"c:\apps\notepad.exe")

    def test_multiple_explicit_paths_are_accepted(self):
        definition = ApplicationDefinition("notepad", ("notepad",), ("notepad.exe",),
                                           (r"C:\Apps\notepad.exe", r"D:\Apps\notepad.exe"))
        with patch("nayeon.services.applications.platform.system", return_value="Windows"), \
                patch("nayeon.services.applications.windows_process_identities",
                      return_value=(ProcessIdentity("notepad.exe", r"D:\Apps\notepad.exe"),)):
            self.assertEqual(ApplicationService(applications=(definition,)).observe("notepad").identity,
                             ApplicationIdentity.MATCHED)


class WindowsIdentityTests(unittest.TestCase):
    def setUp(self):
        self.api = Mock(spec=["CreateToolhelp32Snapshot", "Process32FirstW", "Process32NextW",
                              "OpenProcess", "QueryFullProcessImageNameW", "CloseHandle"])
        self.api.CreateToolhelp32Snapshot.return_value = 123
        self.api.OpenProcess.return_value = 456
        self.enterContext(patch("nayeon.services.application_observation._kernel32", return_value=self.api))
        self.last_error = self.enterContext(patch("nayeon.services.application_observation.ctypes.get_last_error",
                                                 return_value=18))
        self.entries(((11, "NOTEPAD.EXE"),))
        self.path(r"C:\Trusted\notepad.exe")

    def entries(self, entries):
        iterator = iter(entries)

        def read(handle, pointer):
            self.assertEqual(handle, 123)
            try:
                pid, name = next(iterator)
            except StopIteration:
                return False
            pointer._obj.th32ProcessID = pid
            pointer._obj.szExeFile = name
            return True

        self.api.Process32FirstW.side_effect = read
        self.api.Process32NextW.side_effect = read

    def path(self, value):
        def query(handle, flags, buffer, size):
            self.assertEqual((handle, flags, size._obj.value), (456, 0, 32768))
            buffer.value = value
            size._obj.value = len(value)
            return True
        self.api.QueryFullProcessImageNameW.side_effect = query

    def observe(self):
        return windows_process_identities(("notepad.exe",))

    def test_only_exact_candidates_are_opened_with_query_only_rights(self):
        self.entries(((9, "System"), (10, "mynotepad.exe"), (11, "NOTEPAD.EXE"),
                      (12, "notepad.exe.backup")))
        self.assertEqual(self.observe(), (ProcessIdentity("notepad.exe", r"C:\Trusted\notepad.exe"),))
        self.api.OpenProcess.assert_called_once_with(0x1000, False, 11)
        self.api.QueryFullProcessImageNameW.assert_called_once()
        self.api.CreateToolhelp32Snapshot.assert_called_once_with(2, 0)
        self.assertEqual(self.api.CloseHandle.call_args_list, [call(456), call(123)])

    def test_access_denied_is_unavailable_not_mismatch(self):
        self.api.OpenProcess.return_value = None
        self.assertEqual(self.observe(), (ProcessIdentity("notepad.exe", None),))
        self.api.QueryFullProcessImageNameW.assert_not_called()
        self.api.CloseHandle.assert_called_once_with(123)

    def test_query_failure_does_not_retry_and_closes_handles(self):
        self.api.QueryFullProcessImageNameW.side_effect = None
        self.api.QueryFullProcessImageNameW.return_value = False
        self.assertEqual(self.observe(), (ProcessIdentity("notepad.exe", None),))
        self.api.QueryFullProcessImageNameW.assert_called_once()
        self.assertEqual(self.api.CloseHandle.call_args_list, [call(456), call(123)])

    def test_exception_closes_process_and_snapshot_handles(self):
        self.api.QueryFullProcessImageNameW.side_effect = OSError("fake")
        with self.assertRaises(OSError):
            self.observe()
        self.assertEqual(self.api.CloseHandle.call_args_list, [call(456), call(123)])

    def test_incomplete_snapshot_discards_even_positive_path(self):
        self.last_error.return_value = 5
        self.assertIsNone(self.observe())
        self.assertEqual(self.api.CloseHandle.call_args_list, [call(456), call(123)])

    def test_no_candidates_returns_empty_without_opening_processes(self):
        self.entries(((1, "System"), (2, "notepad.exe.backup")))
        self.assertEqual(self.observe(), ())
        self.api.OpenProcess.assert_not_called()

    def test_malformed_length_is_unavailable(self):
        for length in (0, 32768, 90000, 2):
            with self.subTest(length=length):
                self.entries(((11, "notepad.exe"),))
                def query(handle, flags, buffer, size):
                    buffer.value = r"C:\Trusted\notepad.exe"
                    size._obj.value = length
                    return True
                self.api.QueryFullProcessImageNameW.side_effect = query
                self.assertEqual(self.observe(), (ProcessIdentity("notepad.exe", None),))

    def test_loader_declares_pointer_safe_query_signatures(self):
        # Load only a fake DLL; checking declarations must never call Windows.
        with patch.object(ctypes, "WinDLL", return_value=self.api) as loader:
            load_kernel32()
        loader.assert_called_once_with("kernel32", use_last_error=True)
        self.assertIs(self.api.OpenProcess.restype, ctypes.wintypes.HANDLE)
        self.assertEqual(len(self.api.QueryFullProcessImageNameW.argtypes), 4)
