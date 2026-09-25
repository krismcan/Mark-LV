"""Fake Win32 redirection/races plus ordinary temporary files; no personal data."""

import ctypes
from dataclasses import FrozenInstanceError
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.dispatch import IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.orchestration import StructuredOrchestrationBridge
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities import read_file
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.read_file import ReadFileCapability
from nayeon.capabilities.structured import StructuredCapability, StructuredCapabilityRequest
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.services import filesystem as fs
from nayeon.verification.contract import VerificationProvider, VerificationStatus
from nayeon.undo.service import UndoService


PATH = r"C:\Temp\notes.txt"


class FakeWindows:
    def __init__(self, data=b"hello"):
        self.data = data
        self.offset = 0
        self.handles = {}
        self.attributes = {}
        self.final_paths = {}
        self.events = []
        self.size = len(data)
        self.api = Mock(spec=["GetDriveTypeW", "CreateFileW", "GetFileType",
                              "GetFileInformationByHandle", "GetFinalPathNameByHandleW",
                              "ReadFile", "CloseHandle"])
        self.api.GetDriveTypeW.return_value = 3
        self.api.CreateFileW.side_effect = self.open
        self.api.GetFileType.return_value = 1
        self.api.GetFileInformationByHandle.side_effect = self.info
        self.api.GetFinalPathNameByHandleW.side_effect = self.final
        self.api.ReadFile.side_effect = self.read
        self.api.CloseHandle.side_effect = lambda h: self.events.append(("close", h)) or True

    def open(self, path, access, share, security, disposition, flags, template):
        handle = len(self.handles) + 10
        self.handles[handle] = path
        self.events.append(("open", handle))
        return handle

    def info(self, handle, pointer):
        self.events.append(("info", handle))
        info = ctypes.cast(pointer, ctypes.POINTER(fs._FileInformation)).contents
        path = self.handles[handle]
        info.attributes = self.attributes.get(path, 0 if path == PATH else fs._DIRECTORY)
        info.size_low = self.size & 0xFFFFFFFF
        info.size_high = self.size >> 32
        return True

    def final(self, handle, buffer, size, flags):
        self.events.append(("identity", handle))
        path = self.handles[handle]
        buffer.value = self.final_paths.get(path, "\\\\?\\" + path)
        return len(buffer.value)

    def read(self, handle, buffer, size, count, overlapped):
        self.events.append(("read", handle))
        chunk = self.data[self.offset:self.offset + size]
        ctypes.memmove(buffer, chunk, len(chunk))
        ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = len(chunk)
        self.offset += len(chunk)
        return True


class PathTests(unittest.TestCase):
    def test_normalizes_drive_and_separators_only(self):
        self.assertEqual(fs.normalize_file_path("c:/Temp/notes.txt"), PATH)

    def test_preserves_component_case_and_unicode(self):
        path = "C:\\Temp\\Notes-é.txt"
        self.assertEqual(fs.normalize_file_path(path), path)

    def test_rejects_empty_and_non_string(self):
        for path in ("", " ", None, 1, Path("notes.txt")):
            with self.subTest(path=path), self.assertRaises((ValueError, TypeError)):
                fs.normalize_file_path(path)

    def test_rejects_ambiguous_and_nonlocal_forms(self):
        for path in ("notes.txt", r"C:notes.txt", r"\notes.txt", r"\\host\share\notes.txt",
                     r"\\?\C:\notes.txt", r"\\.\C:\notes.txt", "C:\\", "C:\\Temp\\",
                     r"C:\Temp\..\notes.txt", r"C:\.\notes.txt", r"C:\\Temp\notes.txt"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                fs.normalize_file_path(path)

    def test_rejects_wildcards_variables_streams_and_controls(self):
        for path in (r"C:\Temp\*.txt", r"C:\Temp\?.txt", r"C:\Temp\[ab].txt", r"C:\%TEMP%\x", r"C:\$env:TEMP\x",
                     r"C:\${TEMP}\x", r"C:\x:secret", 'C:\\"x"', "C:\\x\x00", "C:\\x\n",
                     "C:\\x\ud800", "C:\\Temp.\\x", "C:\\Temp \\x"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                fs.normalize_file_path(path)

    def test_rejects_dos_devices_in_any_component(self):
        for name in ("CON", "nul.txt", "CON .txt", "AUX", "PRN", "COM1", "LPT9.txt", "COM¹", "CONOUT$"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                fs.normalize_file_path("C:\\" + name + "\\x")

    def test_path_length_is_bounded_in_utf16_units(self):
        for name in ("x" * 257, "😀" * 129):
            with self.subTest(name=name), self.assertRaises(ValueError):
                fs.normalize_file_path("C:\\" + name)


class HandleReadTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeWindows()
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, "system", return_value="Windows"))
        self.loader = self.enterContext(patch.object(fs, "_kernel32", return_value=self.api))
        self.last_error = self.enterContext(patch.object(ctypes, "get_last_error", return_value=5, create=True))
        self.service = fs.FilesystemService()

    def assert_read_failure(self, expected):
        with self.assertRaises(fs.FileReadError) as caught:
            self.service.read_file(PATH)
        self.assertEqual(caught.exception.failure, expected)
        self.assertNotIn(PATH, str(caught.exception))
        self.assertEqual(self.api.CloseHandle.call_count, len(self.fake.handles))

    def test_success_metadata_and_same_handle_sequence(self):
        result = self.service.read_file(PATH)
        self.assertEqual((result.path, result.text, result.byte_count, result.state), (PATH, "hello", 5, "read"))
        final_handle = max(self.fake.handles)
        self.assertEqual([h for op, h in self.fake.events if op == "read"], [final_handle, final_handle])
        self.assertLess(self.fake.events.index(("identity", final_handle)), self.fake.events.index(("read", final_handle)))
        self.assertEqual([c.args[0] for c in self.api.CreateFileW.call_args_list], ["C:\\", r"C:\Temp", PATH])
        self.assertEqual([c.args[0] for c in self.api.CloseHandle.call_args_list], [12, 11, 10])
        self.assertNotIn("hello", repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.text = "changed"

    def test_open_flags_are_read_only_no_follow_and_no_recall(self):
        self.service.read_file(PATH)
        for i, call in enumerate(self.api.CreateFileW.call_args_list):
            self.assertEqual(call.args[1:], (fs._READ_ATTRIBUTES if i < 2 else fs._GENERIC_READ,
                             1, None, 3, 0x02300000, None))
        self.api.GetDriveTypeW.assert_called_once_with("C:\\")

    def test_final_reparse_is_rejected_before_read(self):
        self.fake.attributes[PATH] = 0x400
        self.assert_read_failure(fs.FileReadFailure.UNSAFE_PATH)
        self.api.ReadFile.assert_not_called()

    def test_ancestor_reparse_is_rejected_without_opening_target(self):
        self.fake.attributes[r"C:\Temp"] = 0x410
        self.assert_read_failure(fs.FileReadFailure.UNSAFE_PATH)
        self.assertNotIn(PATH, self.fake.handles.values())
        self.api.ReadFile.assert_not_called()

    def test_ancestor_identity_redirection_is_rejected(self):
        self.fake.final_paths[r"C:\Temp"] = r"\\?\C:\Other"
        self.assert_read_failure(fs.FileReadFailure.UNSAFE_PATH)
        self.api.ReadFile.assert_not_called()

    def test_safe_ancestors_cannot_authorize_mismatched_final_handle(self):
        self.fake.final_paths[PATH] = r"\\?\C:\private\secret.txt"
        self.assert_read_failure(fs.FileReadFailure.UNSAFE_PATH)
        self.api.ReadFile.assert_not_called()

    def test_final_identity_case_alias_fails_closed(self):
        self.fake.final_paths[PATH] = r"\\?\C:\Temp\Notes.txt"
        self.assert_read_failure(fs.FileReadFailure.UNSAFE_PATH)

    def test_unc_or_device_final_identity_is_rejected(self):
        for final in (r"\\?\UNC\server\x", r"\Device\HarddiskVolume1\x", r"C:\Temp\notes.txt"):
            with self.subTest(final=final):
                self.fake.final_paths[PATH] = final
                with self.assertRaises(fs.FileReadError) as caught:
                    self.service.read_file(PATH)
                self.assertEqual(caught.exception.failure, fs.FileReadFailure.UNSAFE_PATH)
        self.api.ReadFile.assert_not_called()

    def test_unavailable_or_truncated_identity_never_reads(self):
        for length in (0, 264, 300):
            with self.subTest(length=length):
                self.api.GetFinalPathNameByHandleW.side_effect = None
                self.api.GetFinalPathNameByHandleW.return_value = length
                with self.assertRaises(fs.FileReadError):
                    self.service.read_file(PATH)
        self.api.ReadFile.assert_not_called()

    def test_network_or_unknown_drive_is_rejected_before_open(self):
        for kind in (0, 1, 4, 5):
            with self.subTest(kind=kind):
                self.api.GetDriveTypeW.return_value = kind
                with self.assertRaises(fs.FileReadError):
                    self.service.read_file(PATH)
        self.api.CreateFileW.assert_not_called()

    def test_directory_as_file_is_invalid(self):
        self.fake.attributes[PATH] = 0x10
        self.assert_read_failure(fs.FileReadFailure.INVALID_TARGET)
        self.api.ReadFile.assert_not_called()

    def test_non_directory_ancestor_is_invalid(self):
        self.fake.attributes[r"C:\Temp"] = 0
        self.assert_read_failure(fs.FileReadFailure.INVALID_TARGET)

    def test_non_disk_object_is_invalid(self):
        self.api.GetFileType.return_value = 3
        self.assert_read_failure(fs.FileReadFailure.INVALID_TARGET)
        self.api.ReadFile.assert_not_called()

    def test_offline_and_recall_files_are_rejected(self):
        for attributes in (0x1000, 0x40000, 0x400000):
            with self.subTest(attributes=attributes):
                self.fake.attributes[PATH] = attributes
                with self.assertRaises(fs.FileReadError):
                    self.service.read_file(PATH)
        self.api.ReadFile.assert_not_called()

    def test_missing_file_has_typed_failure(self):
        self.api.CreateFileW.side_effect = lambda *args: ctypes.c_void_p(-1).value
        self.last_error.return_value = 2
        self.assert_read_failure(fs.FileReadFailure.NOT_FOUND)

    def test_access_denied_has_typed_failure(self):
        self.api.CreateFileW.side_effect = lambda *args: ctypes.c_void_p(-1).value
        self.assert_read_failure(fs.FileReadFailure.ACCESS_DENIED)

    def test_sharing_conflict_fails_closed(self):
        self.api.CreateFileW.side_effect = lambda *args: ctypes.c_void_p(-1).value
        self.last_error.return_value = 32
        self.assert_read_failure(fs.FileReadFailure.BUSY)

    def test_failed_target_open_closes_ancestor_handles(self):
        original = self.fake.open
        self.api.CreateFileW.side_effect = lambda *args: ctypes.c_void_p(-1).value if args[0] == PATH else original(*args)
        self.assert_read_failure(fs.FileReadFailure.ACCESS_DENIED)

    def test_metadata_failure_never_reads_and_closes(self):
        self.api.GetFileInformationByHandle.side_effect = None
        self.api.GetFileInformationByHandle.return_value = False
        self.assert_read_failure(fs.FileReadFailure.ACCESS_DENIED)
        self.api.ReadFile.assert_not_called()

    def test_oversize_metadata_prevents_read(self):
        for size in (fs.MAX_FILE_BYTES + 1, 2**32):
            with self.subTest(size=size):
                self.fake.size = size
                with self.assertRaises(fs.FileReadError) as caught:
                    self.service.read_file(PATH)
                self.assertEqual(caught.exception.failure, fs.FileReadFailure.TOO_LARGE)
        self.api.ReadFile.assert_not_called()

    def test_growth_is_bounded_by_one_overflow_byte(self):
        self.fake.data = b"x" * (fs.MAX_FILE_BYTES + 10)
        self.assert_read_failure(fs.FileReadFailure.TOO_LARGE)
        self.assertEqual(self.fake.offset, fs.MAX_FILE_BYTES + 1)
        self.assertEqual(self.api.ReadFile.call_count, 1)

    def test_exact_limit_is_accepted(self):
        self.fake.data = b"x" * fs.MAX_FILE_BYTES
        self.fake.size = len(self.fake.data)
        self.assertEqual(self.service.read_file(PATH).byte_count, fs.MAX_FILE_BYTES)

    def test_empty_file_is_valid(self):
        self.fake.data = b""
        self.assertEqual(self.service.read_file(PATH).text, "")

    def test_short_reads_continue_on_same_handle(self):
        original = self.fake.read
        self.api.ReadFile.side_effect = lambda h, b, n, c, o: original(h, b, min(n, 2), c, o)
        self.assertEqual(self.service.read_file(PATH).text, "hello")
        self.assertEqual(self.api.ReadFile.call_count, 4)

    def test_read_error_closes_handles(self):
        self.api.ReadFile.side_effect = None
        self.api.ReadFile.return_value = False
        self.last_error.return_value = 1117
        self.assert_read_failure(fs.FileReadFailure.READ_ERROR)

    def test_utf8_byte_count_differs_from_character_count(self):
        self.fake.data = "é\ttext\r\n".encode("utf-8")
        result = self.service.read_file(PATH)
        self.assertEqual(result.text, "é\ttext\r\n")
        self.assertEqual(result.byte_count, len(self.fake.data))

    def test_decode_failure_is_safe(self):
        self.fake.data = b"\xff\xfe"
        self.assert_read_failure(fs.FileReadFailure.UNSUPPORTED_CONTENT)

    def test_binary_controls_are_rejected(self):
        for data in (b"a\x00b", b"\x1b[0m", b"\x7f", "\u0085".encode()):
            with self.subTest(data=data):
                self.fake.data, self.fake.offset = data, 0
                with self.assertRaises(fs.FileReadError) as caught:
                    self.service.read_file(PATH)
                self.assertEqual(caught.exception.failure, fs.FileReadFailure.UNSUPPORTED_CONTENT)

    def test_invalid_path_never_loads_windows_api(self):
        with self.assertRaises(fs.FileReadError) as caught:
            self.service.read_file("relative.txt")
        self.assertEqual(caught.exception.failure, fs.FileReadFailure.INVALID_TARGET)
        self.loader.assert_not_called()

    def test_non_windows_is_deterministically_unsupported(self):
        with patch.object(fs.platform, "system", return_value="Linux"):
            self.assert_read_failure(fs.FileReadFailure.UNSUPPORTED_PLATFORM)
        self.loader.assert_not_called()

    def test_no_shell_search_normal_open_or_precheck_is_used(self):
        with patch("builtins.open", side_effect=AssertionError("no reopen")), \
             patch("pathlib.Path.open", side_effect=AssertionError("no reopen")), \
             patch("pathlib.Path.is_symlink", return_value=False), \
             patch("pathlib.Path.glob", side_effect=AssertionError("no discovery")), \
             patch("os.scandir", side_effect=AssertionError("no discovery")), \
             patch("subprocess.Popen", side_effect=AssertionError("no shell")), \
             patch("shutil.which", side_effect=AssertionError("no lookup")):
            self.fake.final_paths[PATH] = r"\\?\C:\secret.txt"
            self.assert_read_failure(fs.FileReadFailure.UNSAFE_PATH)
        self.api.ReadFile.assert_not_called()


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.service.read_file.return_value = fs.FileReadResult(PATH, "private contents", 16)
        self.app = ReadFileCapability(service=self.service)
        self.capability = self.app.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("read_file")
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions),
                                       ConfirmationService(), self.audit, self.undo)
        self.request = StructuredCapabilityRequest("read explicit file", {"path": PATH})

    def pending(self):
        result = self.executor.execute_structured(self.capability, self.request)
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.service.read_file.assert_not_called()
        return result.confirmation_request.token

    def approve(self, token, request=None):
        return self.executor.approve_and_execute_structured(token, capability=self.capability,
                                      request=self.request if request is None else request)

    def test_discovery_registers_capability_without_io(self):
        registry = CapabilityRegistry()
        with patch.object(fs, "_kernel32", side_effect=AssertionError("no IO")):
            self.assertEqual(CapabilityLoader(registry)._load_module(read_file), 1)
        self.assertIsInstance(registry.get_implementation("read_file"), StructuredCapability)
        self.assertTrue(registry.get("read_file").requires_confirmation)

    def test_validation_copies_and_normalizes_without_service_call(self):
        original = {"path": "c:/Temp/notes.txt"}
        validated = self.app.validate_arguments(original)
        self.assertEqual(validated, {"path": PATH})
        self.assertEqual(original["path"], "c:/Temp/notes.txt")
        self.assertIsNot(original, validated)
        self.service.read_file.assert_not_called()

    def test_extra_missing_nested_and_invalid_arguments_are_rejected(self):
        for arguments in ({}, {"path": PATH, "extra": True}, {"path": {"path": PATH}}, [], {"path": ""}):
            with self.subTest(arguments=arguments), self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments(arguments)
        self.service.read_file.assert_not_called()

    def test_permission_denial_never_calls_service(self):
        self.permissions.revoke("read_file")
        self.assertEqual(self.executor.execute_structured(self.capability, self.request).status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_policy_block_never_calls_service(self):
        executor = ActionExecutor(self.registry, PolicyService(self.permissions, {"read_file"}),
                                  ConfirmationService(), self.audit, self.undo)
        self.assertEqual(executor.execute_structured(self.capability, self.request).status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_confirmed_structured_read_returns_result_once_without_verifier(self):
        result = self.approve(self.pending())
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.output.text, "private contents")
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertFalse(isinstance(self.app, VerificationProvider))
        self.service.read_file.assert_called_once_with(PATH)
        self.assertEqual(self.undo.count(), 0)

    def test_full_confirmed_flow_uses_real_service_with_fake_windows(self):
        fake = FakeWindows(b"approved text")
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, "system", return_value="Windows"), \
             patch.object(fs, "_kernel32", return_value=fake.api):
            token = self.pending()
            fake.api.CreateFileW.assert_not_called()
            result = self.approve(token)
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.output.text, "approved text")
        self.assertEqual(result.output.byte_count, 13)
        self.assertEqual(sum(c.args[0] == PATH for c in fake.api.CreateFileW.call_args_list), 1)

    def test_failed_file_conditions_all_reach_failed_execution(self):
        for failure in (fs.FileReadFailure.NOT_FOUND, fs.FileReadFailure.ACCESS_DENIED,
                        fs.FileReadFailure.INVALID_TARGET, fs.FileReadFailure.TOO_LARGE,
                        fs.FileReadFailure.UNSUPPORTED_CONTENT):
            with self.subTest(failure=failure):
                self.service.read_file.reset_mock()
                self.service.read_file.side_effect = fs.FileReadError(failure)
                result = self.approve(self.pending())
                self.assertEqual(result.status, ExecutionStatus.FAILED)
                self.service.read_file.assert_called_once_with(PATH)

    def test_changed_request_cannot_use_pending_approval(self):
        token = self.pending()
        self.request.arguments["path"] = r"C:\Temp\other.txt"
        self.assertEqual(self.approve(token).status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_saved_snapshot_survives_caller_mutation(self):
        token = self.pending()
        self.request.arguments["path"] = r"C:\Temp\other.txt"
        original = StructuredCapabilityRequest("read explicit file", {"path": PATH})
        self.assertEqual(self.approve(token, original).status, ExecutionStatus.EXECUTED)
        self.service.read_file.assert_called_once_with(PATH)

    def test_rejection_and_replay_never_read(self):
        token = self.pending()
        self.assertEqual(self.executor.reject(token, capability=self.capability).status, ExecutionStatus.DENIED)
        self.assertEqual(self.approve(token).status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_revocation_before_approval_is_enforced(self):
        token = self.pending()
        self.permissions.revoke("read_file")
        self.assertEqual(self.approve(token).status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_domain_failure_is_failed_with_no_verifier(self):
        self.service.read_file.side_effect = fs.FileReadError(fs.FileReadFailure.UNSAFE_PATH)
        result = self.approve(self.pending())
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertNotIn(AuditEventType.VERIFICATION_OUTCOME, [e.event_type for e in self.audit.all()])

    def test_audit_never_contains_path_or_contents(self):
        self.approve(self.pending())
        log = repr(self.audit.all())
        self.assertNotIn(PATH, log)
        self.assertNotIn("private contents", log)
        self.assertEqual(self.audit.all()[-1].event_type, AuditEventType.VERIFICATION_OUTCOME)

    def test_unsafe_error_details_are_not_exposed(self):
        self.service.read_file.side_effect = OSError(r"C:\private\secret.txt sensitive text")
        result = self.approve(self.pending())
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertNotIn("secret.txt", repr(result) + repr(self.audit.all()))

    def test_legacy_execution_is_explicitly_unsupported(self):
        with self.assertRaises(fs.FileReadError) as caught:
            self.app.execute("read " + PATH)
        self.assertEqual(caught.exception.failure, fs.FileReadFailure.STRUCTURED_REQUIRED)
        self.service.read_file.assert_not_called()

    def test_bridge_still_denies_read_file_plans(self):
        plan = IntentDispatcher(registry=self.registry).plan(IntentResolution(
            "read_file", IntentSource.LOCAL, 1.0, {"path": PATH}))
        result = StructuredOrchestrationBridge(registry=self.registry, executor=self.executor).execute(
            plan, original_request="read explicit file")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()


@unittest.skipUnless(platform.system() == "Windows", "Native ordinary-file test requires Windows")
class TemporaryWindowsFileTests(unittest.TestCase):
    def test_reads_only_created_temporary_file_through_native_handles(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "notes.txt"
            path.write_bytes("temporary café\n".encode("utf-8"))
            result = fs.FilesystemService().read_file(str(path))
            self.assertEqual(result.text, "temporary café\n")
            self.assertEqual(result.byte_count, 16)
