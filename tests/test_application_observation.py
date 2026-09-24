"""Service-owned observation: explicit identities, fake OS snapshots only."""

import ctypes
import unittest
from unittest.mock import Mock, patch

from nayeon.services.application_observation import (
    ApplicationDefinition, ApplicationState, windows_process_names,
)
from nayeon.services.applications import ApplicationService


class ApplicationObservationTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nayeon.services.applications.platform.system", return_value="Windows"))
        self.snapshot = self.enterContext(patch("nayeon.services.applications.windows_process_names",
                                               return_value=frozenset({"notepad.exe", "system"})))
        self.service = ApplicationService()
        self.launch = self.enterContext(patch.object(self.service, "launch",
                                                     side_effect=AssertionError("No launch")))

    def test_explicit_aliases_observe_one_canonical_identity(self):
        for target in ("notepad", "NOTEPAD.EXE"):
            with self.subTest(target=target):
                result = self.service.observe(target)
                self.assertEqual(result.state, ApplicationState.OBSERVED_OPEN)
                self.assertEqual(result.application_id, "notepad")
                self.assertEqual(result.target, target)
                self.assertEqual(result.expected_process_names, ("notepad.exe",))
                self.assertNotIn("system", repr(result))
        self.launch.assert_not_called()

    def test_complete_snapshot_without_exact_process_is_closed(self):
        self.snapshot.return_value = frozenset({"system", "notepad.exe.backup", "mynotepad.exe"})
        self.assertEqual(self.service.observe("notepad").state, ApplicationState.OBSERVED_CLOSED)
        self.snapshot.assert_called_once_with()

    def test_unknown_targets_never_trigger_process_inspection(self):
        for target in ("editor", "notepad app", "open notepad", r"C:\other\notepad.exe", "note", "*"):
            with self.subTest(target=target):
                self.assertEqual(self.service.observe(target).state, ApplicationState.UNKNOWN)
        self.snapshot.assert_not_called()

    def test_unsupported_platform_never_inspects_processes(self):
        with patch("nayeon.services.applications.platform.system", return_value="Linux"):
            self.assertEqual(self.service.observe("notepad").state, ApplicationState.UNKNOWN)
        self.snapshot.assert_not_called()

    def test_missing_optional_metadata_is_unknown(self):
        service = ApplicationService(applications=(ApplicationDefinition("editor", ("Editor",)),))
        self.assertEqual(service.observe("Editor").state, ApplicationState.UNKNOWN)
        self.snapshot.assert_not_called()

    def test_missing_catalogue_entry_is_unknown(self):
        self.assertEqual(ApplicationService(applications=()).observe("notepad").state,
                         ApplicationState.UNKNOWN)
        self.snapshot.assert_not_called()

    def test_inspection_errors_are_unknown_and_redacted(self):
        self.snapshot.side_effect = OSError("fake-sensitive-error")
        result = self.service.observe("notepad")
        self.assertEqual(result.state, ApplicationState.UNKNOWN)
        self.assertNotIn("fake-sensitive-error", repr(result))

    def test_incomplete_empty_or_malformed_snapshots_are_unknown(self):
        for snapshot in (None, frozenset(), [], "notepad.exe", frozenset({None}), frozenset({""})):
            with self.subTest(snapshot=snapshot):
                self.snapshot.return_value = snapshot
                self.assertEqual(self.service.observe("notepad").state, ApplicationState.UNKNOWN)

    def test_metadata_is_copied_and_requires_exact_safe_identities(self):
        targets, names = ["Editor"], ["Editor.EXE"]
        definition = ApplicationDefinition("editor", targets, names)
        targets.append("other")
        names.append("other.exe")
        self.assertEqual(definition.targets, ("editor",))
        self.assertEqual(definition.expected_process_names, ("editor.exe",))
        for identity, targets, names in (("../bad", ("app",), ("app.exe",)),
                                         ("app", (), ("app.exe",)),
                                         ("app", ("app",), ("*.exe",)),
                                         ("app", ("app",), (r"C:\app.exe",))):
            with self.subTest(identity=identity, names=names), self.assertRaises(ValueError):
                ApplicationDefinition(identity, targets, names)

    def test_conflicting_alias_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            ApplicationService(applications=(ApplicationDefinition("one", ("App",)),
                                             ApplicationDefinition("two", ("APP",))))

    def test_trusted_custom_metadata_uses_exact_case_insensitive_names(self):
        service = ApplicationService(applications=(ApplicationDefinition(
            "editor", ("Editor",), ("editor.exe", "editor-helper.exe")),))
        self.snapshot.return_value = frozenset({"EDITOR-HELPER.EXE"})
        result = service.observe("Editor")
        self.assertEqual(result.state, ApplicationState.OBSERVED_OPEN)
        self.assertEqual(result.application_id, "editor")
        self.launch.assert_not_called()


class WindowsSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.api = Mock(spec=["CreateToolhelp32Snapshot", "Process32FirstW", "Process32NextW", "CloseHandle"])
        self.api.CreateToolhelp32Snapshot.return_value = 123
        self.enterContext(patch("nayeon.services.application_observation._kernel32", return_value=self.api))
        self.last_error = self.enterContext(patch(
            "nayeon.services.application_observation.ctypes.get_last_error", return_value=18))

    def entries(self, names):
        iterator = iter(names)

        def read(handle, pointer):
            self.assertEqual(handle, 123)
            self.assertEqual(pointer._obj.dwSize, ctypes.sizeof(pointer._obj))
            try:
                pointer._obj.szExeFile = next(iterator)
                return True
            except StopIteration:
                return False

        self.api.Process32FirstW.side_effect = read
        self.api.Process32NextW.side_effect = read

    def test_one_read_only_snapshot_is_closed_and_inventory_stays_internal(self):
        self.entries(["System", "NOTEPAD.EXE"])
        self.assertEqual(windows_process_names(), frozenset({"system", "notepad.exe"}))
        self.api.CreateToolhelp32Snapshot.assert_called_once_with(2, 0)
        self.api.CloseHandle.assert_called_once_with(123)
        self.assertEqual([call[0] for call in self.api.mock_calls], [
            "CreateToolhelp32Snapshot", "Process32FirstW", "Process32NextW",
            "Process32NextW", "CloseHandle",
        ])

    def test_invalid_handle_is_unknown_without_close_or_read(self):
        self.api.CreateToolhelp32Snapshot.return_value = ctypes.c_void_p(-1).value
        self.assertIsNone(windows_process_names())
        self.api.Process32FirstW.assert_not_called()
        self.api.CloseHandle.assert_not_called()

    def test_first_read_failure_is_unknown_even_with_no_more_files(self):
        self.api.Process32FirstW.return_value = False
        self.assertIsNone(windows_process_names())
        self.api.CloseHandle.assert_called_once_with(123)

    def test_incomplete_snapshot_is_unknown_even_after_a_match(self):
        self.entries(["notepad.exe"])
        self.last_error.return_value = 5
        self.assertIsNone(windows_process_names())
        self.api.CloseHandle.assert_called_once_with(123)

    def test_malformed_entry_is_unknown(self):
        self.entries([""])
        self.assertIsNone(windows_process_names())
        self.api.CloseHandle.assert_called_once_with(123)

    def test_possible_truncated_name_is_unknown(self):
        self.entries(["x" * 259])
        self.assertIsNone(windows_process_names())

    def test_exception_still_closes_handle(self):
        self.api.Process32FirstW.side_effect = OSError("fake read error")
        with self.assertRaises(OSError):
            windows_process_names()
        self.api.CloseHandle.assert_called_once_with(123)
