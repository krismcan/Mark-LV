"""Bounded listing with fake Win32 records and one self-created native directory."""

import ctypes
from dataclasses import FrozenInstanceError
from datetime import timedelta
from pathlib import Path
import platform
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService, AuditEventType
from nayeon.capabilities import list_directory
from nayeon.capabilities.list_directory import ListDirectoryCapability
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.structured import IntentArgumentMapper, StructuredCapability
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services import filesystem as fs
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationProvider, VerificationStatus
from tests.test_filesystem import FakeWindows


PATH = r"C:\Temp\Listing"
TEXT = "list directory " + PATH


def records(*items):
    """Build independent FILE_FULL_DIR_INFO wire fixtures with 8-byte alignment."""
    result = bytearray()
    for index, (name, attributes) in enumerate(items):
        name = name.encode("utf-16-le", errors="surrogatepass")
        size = (68 + len(name) + 7) & ~7
        record = bytearray(size)
        struct.pack_into("<I", record, 0, size if index < len(items) - 1 else 0)
        struct.pack_into("<II", record, 56, attributes, len(name))
        record[68:68 + len(name)] = name
        result.extend(record)
    return bytes(result)


class DirectoryContractTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.app = ListDirectoryCapability(service=self.service)

    def test_discovery_registers_both_optional_protocols(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(list_directory), 1)
        implementation = registry.get_implementation("list_directory")
        self.assertIsInstance(implementation, ListDirectoryCapability)
        self.assertIsInstance(implementation, StructuredCapability)
        self.assertIsInstance(implementation, IntentArgumentMapper)
        self.assertNotIsInstance(implementation, VerificationProvider)

    def test_metadata_is_local_protected_and_nonreversible(self):
        capability = self.app.capability
        self.assertEqual(capability.name, "list_directory")
        self.assertEqual(capability.service, "filesystem")
        self.assertEqual(capability.execution_mode, ExecutionMode.LOCAL)
        self.assertTrue(capability.requires_confirmation)
        self.assertFalse(capability.reversible)
        self.assertFalse(capability.requires_llm)

    def test_explicit_path_wins_and_discards_extras(self):
        args = {"path": PATH, "request": "mismatch", "extra": [1]}
        self.assertEqual(self.app.map_intent_arguments(args, original_request=TEXT), {"path": PATH})
        self.assertEqual(args["extra"], [1])

    def test_invalid_explicit_candidates_are_forwarded_without_validation(self):
        with patch.object(self.app, "validate_arguments", side_effect=AssertionError("not mapping")):
            for value in (None, 1, "", "relative", [], {}):
                with self.subTest(value=value):
                    self.assertEqual(self.app.map_intent_arguments(
                        {"path": value, "request": TEXT}, original_request=TEXT), {"path": value})

    def test_exact_original_match_required_before_trimming(self):
        for candidate in (TEXT + " ", " " + TEXT, "other", None):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                self.app.map_intent_arguments({"request": candidate}, original_request=TEXT)

    def test_only_narrow_local_prefix_maps(self):
        text = " LIST DIRECTORY " + PATH + " "
        self.assertEqual(self.app.map_intent_arguments({"request": text}, original_request=text), {"path": PATH})
        for prefix in ("list folders ", "show me files in ", "what is inside ", "find ", "list "):
            text = prefix + PATH
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                self.app.map_intent_arguments({"request": text}, original_request=text)

    def test_mapper_and_validation_perform_no_service_io(self):
        self.app.map_intent_arguments({"request": TEXT}, original_request=TEXT)
        self.app.validate_arguments({"path": PATH})
        self.assertEqual(self.service.mock_calls, [])

    def test_only_path_argument_is_accepted(self):
        for args in (None, [], {}, {"path": PATH, "recursive": False}):
            with self.subTest(args=args), self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments(args)

    def test_legacy_execution_fails_without_service(self):
        with self.assertRaises(fs.DirectoryListError) as caught:
            self.app.execute(TEXT)
        self.assertEqual(caught.exception.failure, fs.DirectoryListFailure.STRUCTURED_REQUIRED)
        self.assertEqual(self.service.mock_calls, [])

    def test_lexical_normalization_and_drive_root(self):
        self.assertEqual(fs.normalize_directory_path("c:/Temp/Listing"), PATH)
        self.assertEqual(fs.normalize_directory_path("c:/"), "C:\\")
        self.assertEqual(fs.normalize_directory_path("C:\\é"), "C:\\é")
        with self.assertRaises(ValueError):
            fs.normalize_file_path("C:\\")  # ReadFile contract remains stricter

    def test_unsafe_lexical_paths_rejected_without_io(self):
        for path in ("", " ", None, 4, "relative", r"C:relative", r"\rooted",
                     r"\\server\share", r"\\?\C:\Temp", r"\\.\C:\Temp",
                     r"C:\*", r"C:\?", r"C:\[ab]", r"C:\%TEMP%", r"C:\$var",
                     r"C:\Temp\..\x", r"C:\.\x", r"C:\\Temp", "C:\\Temp\\",
                     r"C:\x:stream", r"C:\NUL", r"C:\Temp.", r"C:\Temp ",
                     "C:\\x\x00", "C:\\x\ud800", "C:\\" + "a" * 257):
            with self.subTest(path=path), self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments({"path": path})
        self.assertEqual(self.service.mock_calls, [])

    def test_result_is_immutable_isolated_and_repr_redacted(self):
        entry = fs.DirectoryEntry("private-name", "file")
        original = [entry]
        result = fs.DirectoryListResult(PATH, original)
        original.clear()
        self.assertEqual(result.entries, (entry,))
        self.assertEqual(result.entry_count, 1)
        self.assertEqual(result.state, "listed")
        with self.assertRaises(FrozenInstanceError):
            entry.name = "changed"
        with self.assertRaises(FrozenInstanceError):
            result.entries = ()
        self.assertNotIn(PATH, repr(result))
        self.assertNotIn("private-name", repr(result) + repr(entry))


class DirectoryHandleTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeWindows()
        self.api = self.fake.api
        self.api.GetFileInformationByHandleEx = Mock(side_effect=self.enumerate)
        self.batches = [records(("one.txt", 0), ("child", 0x10))]
        self.error = 18
        self.enterContext(patch.object(fs, "_kernel32", return_value=self.api))
        self.enterContext(patch.object(fs.platform, "system", return_value="Windows"))
        self.enterContext(patch.object(fs.ctypes, "get_last_error", side_effect=lambda: self.error, create=True))
        self.service = fs.FilesystemService()

    def enumerate(self, handle, information_class, buffer, size):
        self.fake.events.append(("enumerate", handle))
        self.assertEqual(self.fake.handles[handle], PATH)
        self.assertNotIn(("close", handle), self.fake.events)
        for retained in (handle - 2, handle - 1, handle):
            self.assertNotIn(("close", retained), self.fake.events)
        self.assertEqual(size, 4096)
        self.assertEqual(ctypes.addressof(buffer) % 8, 0)
        if not self.batches:
            return False
        batch = self.batches.pop(0)
        self.assertLessEqual(len(batch), size)
        ctypes.memmove(buffer, batch, len(batch))
        return True

    def failure(self, failure):
        with self.assertRaises(fs.DirectoryListError) as caught:
            self.service.list_directory(PATH)
        self.assertEqual(caught.exception.failure, failure)
        self.assertNotIn(PATH, str(caught.exception))
        self.assertEqual(self.api.CloseHandle.call_count, len(self.fake.handles))

    def test_exact_target_opened_once_and_enumerated_after_validation(self):
        result = self.service.list_directory(PATH)
        self.assertEqual([call.args[0] for call in self.api.CreateFileW.call_args_list],
                         ["C:\\", r"C:\Temp", PATH])
        target = next(h for h, path in self.fake.handles.items() if path == PATH)
        self.assertLess(self.fake.events.index(("info", target)), self.fake.events.index(("enumerate", target)))
        self.assertLess(self.fake.events.index(("identity", target)), self.fake.events.index(("enumerate", target)))
        self.assertEqual(self.fake.events[-3:], [("close", target), ("close", 11), ("close", 10)])
        self.assertEqual(result.path, PATH)
        self.api.ReadFile.assert_not_called()

    def test_readonly_no_follow_open_flags_and_rights(self):
        self.service.list_directory(PATH)
        for i, call in enumerate(self.api.CreateFileW.call_args_list):
            self.assertEqual(call.args[1:], (0x81 if i == 2 else 0x80, 1, None, 3, 0x02300000, None))

    def test_restart_then_continuation_on_same_handle(self):
        self.batches = [records(("a", 0)), records(("b", 0))]
        self.assertEqual(self.service.list_directory(PATH).entry_count, 2)
        self.assertEqual([c.args[:2] for c in self.api.GetFileInformationByHandleEx.call_args_list],
                         [(12, 15), (12, 14), (12, 14)])

    def test_no_pathname_enumeration_shell_or_child_open(self):
        with patch("os.listdir", side_effect=AssertionError("pathname")), \
             patch("os.scandir", side_effect=AssertionError("pathname")), \
             patch("pathlib.Path.iterdir", side_effect=AssertionError("pathname")), \
             patch("glob.glob", side_effect=AssertionError("glob")), \
             patch("subprocess.Popen", side_effect=AssertionError("shell")):
            self.service.list_directory(PATH)
        self.assertEqual(self.api.CreateFileW.call_count, 3)
        self.assertEqual(self.api.GetFileInformationByHandle.call_count, 3)

    def test_empty_directory(self):
        self.batches = []
        result = self.service.list_directory(PATH)
        self.assertEqual(result.entries, ())
        self.assertEqual(result.entry_count, 0)

    def test_file_directory_and_unicode_names(self):
        self.batches = [records(("café.txt", 0), ("child", 0x10), ("📝", 0))]
        self.assertEqual(self.service.list_directory(PATH).entries,
                         (fs.DirectoryEntry("café.txt", "file"), fs.DirectoryEntry("child", "directory"),
                          fs.DirectoryEntry("📝", "file")))

    def test_dot_entries_excluded(self):
        self.batches = [records((".", 0x10), ("..", 0x10), ("a", 0))]
        self.assertEqual(self.service.list_directory(PATH).entries, (fs.DirectoryEntry("a", "file"),))

    def test_exact_256_entries_succeed(self):
        self.batches = [records((str(i), 0)) for i in range(256)]
        result = self.service.list_directory(PATH)
        self.assertEqual(result.entry_count, 256)
        self.assertEqual(self.api.GetFileInformationByHandleEx.call_count, 257)

    def test_257th_entry_stops_without_consuming_remaining_batches(self):
        self.batches = [records((str(i), 0)) for i in range(1000)]
        self.failure(fs.DirectoryListFailure.TOO_MANY_ENTRIES)
        self.assertEqual(self.api.GetFileInformationByHandleEx.call_count, 257)
        self.assertEqual(len(self.batches), 743)

    def test_overflow_stops_parsing_current_batch(self):
        self.batches = [records((str(i), 0)) for i in range(256)]
        batch = bytearray(records(("overflow", 0), ("unread", 0)))
        # Malformed subsequent record must not be examined after entry 257.
        next_offset = struct.unpack_from("<I", batch)[0]
        struct.pack_into("<I", batch, next_offset + 60, 0)
        self.batches.append(bytes(batch))
        self.failure(fs.DirectoryListFailure.TOO_MANY_ENTRIES)

    def test_repeated_dot_record_fails_instead_of_unbounded_loop(self):
        self.batches = [records((".", 0x10))] * 20
        self.failure(fs.DirectoryListFailure.LIST_ERROR)
        self.assertEqual(self.api.GetFileInformationByHandleEx.call_count, 2)

    def test_duplicate_child_name_is_malformed(self):
        self.batches = [records(("a", 0), ("a", 0))]
        self.failure(fs.DirectoryListFailure.LIST_ERROR)

    def test_invalid_record_lengths_and_offsets_fail_closed(self):
        for field, value in ((60, 0), (60, 1), (60, 512), (60, 0xFFFFFFFF),
                             (0, 1), (0, 64), (0, 4096), (0, 0xFFFFFFF8)):
            with self.subTest(field=field, value=value):
                batch = bytearray(records(("a", 0)))
                struct.pack_into("<I", batch, field, value)
                self.batches = [bytes(batch)]
                with self.assertRaises(fs.DirectoryListError) as caught:
                    self.service.list_directory(PATH)
                self.assertEqual(caught.exception.failure, fs.DirectoryListFailure.LIST_ERROR)

    def test_invalid_names_fail_closed(self):
        for name in ("", "\ud800", "a\x00b", "a/b", "a\\b", "a:b", "\n", "a*", 'a"'):
            with self.subTest(name=repr(name)):
                self.batches = [records((name, 0))]
                with self.assertRaises(fs.DirectoryListError) as caught:
                    self.service.list_directory(PATH)
                self.assertEqual(caught.exception.failure, fs.DirectoryListFailure.LIST_ERROR)

    def test_child_reparse_is_not_followed_or_mislabeled(self):
        self.batches = [records(("link", 0x410))]
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.assertEqual(self.api.CreateFileW.call_count, 3)

    def test_target_reparse_rejected_before_enumeration(self):
        self.fake.attributes[PATH] = 0x410
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_ancestor_reparse_rejected_before_target_open(self):
        self.fake.attributes[r"C:\Temp"] = 0x410
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.assertNotIn(PATH, self.fake.handles.values())

    def test_redirected_ancestor_rejected(self):
        self.fake.final_paths[r"C:\Temp"] = r"\\?\C:\Other"
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_mismatched_target_identity_rejected(self):
        self.fake.final_paths[PATH] = r"\\?\C:\Temp\listing"
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_unavailable_identity_rejected(self):
        self.api.GetFinalPathNameByHandleW.side_effect = None
        self.api.GetFinalPathNameByHandleW.return_value = 0
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_metadata_failure_closes_handle_without_enumeration(self):
        self.api.GetFileInformationByHandle.side_effect = None
        self.api.GetFileInformationByHandle.return_value = False
        self.error = 5
        self.failure(fs.DirectoryListFailure.ACCESS_DENIED)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_truncated_or_nonlocal_final_identity_rejected(self):
        for value in (r"\\?\UNC\host\share", r"\Device\HarddiskVolume1\x", "C:\\" + "a" * 258):
            with self.subTest(value=value):
                self.fake.final_paths[PATH] = value
                with self.assertRaises(fs.DirectoryListError) as caught:
                    self.service.list_directory(PATH)
                self.assertEqual(caught.exception.failure, fs.DirectoryListFailure.UNSAFE_PATH)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_file_target_rejected(self):
        self.fake.attributes[PATH] = 0
        self.failure(fs.DirectoryListFailure.INVALID_TARGET)
        self.api.GetFileInformationByHandleEx.assert_not_called()

    def test_non_disk_target_rejected(self):
        self.api.GetFileType.return_value = 3
        self.failure(fs.DirectoryListFailure.INVALID_TARGET)

    def test_network_drive_rejected_before_open(self):
        self.api.GetDriveTypeW.return_value = 4
        self.failure(fs.DirectoryListFailure.UNSAFE_PATH)
        self.api.CreateFileW.assert_not_called()

    def test_open_failures_are_typed_and_close_ancestors(self):
        original = self.fake.open
        self.api.CreateFileW.side_effect = lambda *args: ctypes.c_void_p(-1).value if args[0] == PATH else original(*args)
        for code, failure in ((2, fs.DirectoryListFailure.NOT_FOUND), (3, fs.DirectoryListFailure.NOT_FOUND),
                              (5, fs.DirectoryListFailure.ACCESS_DENIED), (32, fs.DirectoryListFailure.BUSY),
                              (999, fs.DirectoryListFailure.LIST_ERROR)):
            with self.subTest(code=code):
                self.error = code
                self.failure(failure)

    def test_enumeration_failure_does_not_return_partial_success(self):
        self.error = 5
        self.failure(fs.DirectoryListFailure.ACCESS_DENIED)

    def test_os_exception_redacted_and_handles_closed(self):
        self.api.GetFileInformationByHandleEx.side_effect = OSError("private-path raw-OS-detail")
        self.failure(fs.DirectoryListFailure.LIST_ERROR)

    def test_unknown_enumeration_error_is_not_normal_eof(self):
        self.batches = []
        self.error = 38  # ERROR_HANDLE_EOF is not directory enumeration completion
        self.failure(fs.DirectoryListFailure.LIST_ERROR)

    def test_nonwindows_has_typed_failure_without_api_calls(self):
        with patch.object(fs.platform, "system", return_value="Linux"):
            self.failure(fs.DirectoryListFailure.UNSUPPORTED_PLATFORM)
        self.api.CreateFileW.assert_not_called()

    def test_invalid_service_path_has_typed_failure(self):
        with self.assertRaises(fs.DirectoryListError) as caught:
            self.service.list_directory("relative")
        self.assertEqual(caught.exception.failure, fs.DirectoryListFailure.INVALID_TARGET)
        self.api.CreateFileW.assert_not_called()

    def test_root_directory_is_opened_only_once(self):
        self.api.GetFileInformationByHandleEx.side_effect = None
        self.api.GetFileInformationByHandleEx.return_value = False
        self.assertEqual(self.service.list_directory("C:\\").entry_count, 0)
        self.api.CreateFileW.assert_called_once_with("C:\\", 0x81, 1, None, 3, 0x02300000, None)


class DirectorySessionTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.service.list_directory.return_value = fs.DirectoryListResult(
            PATH, (fs.DirectoryEntry("private-child.txt", "file"),))
        self.app = ListDirectoryCapability(service=self.service)
        self.mapper = self.enterContext(patch.object(self.app, "map_intent_arguments", wraps=self.app.map_intent_arguments))
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("list_directory")
        self.policy = PolicyService(self.permissions)
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, ConfirmationService(), self.audit, self.undo)
        self.semantic = Mock(spec=["resolve"])
        self.semantic.resolve.return_value = IntentResolution(None, IntentSource.NONE, 0)
        self.resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)), semantic=self.semantic)
        self.session = ConversationSession(resolver=self.resolver, registry=self.registry, executor=self.executor)

    def pending(self):
        result = self.session.request(TEXT)
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertTrue(self.session.has_pending)
        self.assertEqual(self.service.mock_calls, [])
        return result

    def test_local_approval_maps_once_and_lists_once_without_verifier_or_undo(self):
        self.pending()
        self.semantic.resolve.assert_not_called()
        self.mapper.assert_called_once_with({"request": TEXT}, original_request=TEXT)
        self.mapper.side_effect = AssertionError("must not remap")
        with patch.object(self.resolver, "resolve", side_effect=AssertionError("must not resolve")), \
             patch.object(self.session._dispatcher, "plan", side_effect=AssertionError("must not dispatch")):
            result = self.session.approve_pending()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.output.entry_count, 1)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertFalse(self.session.has_pending)
        self.service.list_directory.assert_called_once_with(PATH)
        self.assertEqual(len(self.service.mock_calls), 1)
        self.assertEqual(self.undo.count(), 0)

    def test_semantic_pending_snapshot_isolated_and_extras_discarded(self):
        resolution = IntentResolution("list_directory", IntentSource.SEMANTIC, .95,
                                      {"path": PATH, "request": "different", "extra": ["private"]})
        self.semantic.resolve.return_value = resolution
        self.assertEqual(self.session.request("fake semantic request").status, ExecutionStatus.REQUIRES_CONFIRMATION)
        resolution.arguments["path"] = r"C:\Other"
        self.session.approve_pending()
        self.service.list_directory.assert_called_once_with(PATH)

    def test_invalid_explicit_path_reaches_executor_validation(self):
        self.semantic.resolve.return_value = IntentResolution("list_directory", IntentSource.SEMANTIC, .95,
                                                              {"path": "relative", "request": TEXT})
        result = self.session.request("fake semantic request")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(self.audit.all()[-1].outcome, "validation_failed")
        self.service.list_directory.assert_not_called()

    def test_read_file_permission_does_not_authorize_listing(self):
        self.permissions.revoke("list_directory")
        self.permissions.grant("read_file")
        self.assertEqual(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_policy_block_prevents_listing(self):
        self.policy._blocked_capabilities.add("list_directory")
        self.assertEqual(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_rejection_never_lists(self):
        self.pending()
        self.assertEqual(self.session.reject_pending().status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_cancellation_never_lists(self):
        self.pending()
        self.assertEqual(self.session.request("cancel").status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.service.list_directory.assert_not_called()

    def test_registration_change_blocks_approval(self):
        self.pending()
        self.registry.unregister("list_directory")
        self.registry.register(self.app.capability, ListDirectoryCapability(service=self.service))
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_replay_cannot_list_twice(self):
        self.pending()
        self.session.approve_pending()
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_called_once_with(PATH)

    def test_expired_token_never_lists(self):
        result = self.pending()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = result.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_revoked_permission_blocks_approval(self):
        self.pending()
        self.permissions.revoke("list_directory")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_new_policy_block_prevents_approval(self):
        self.pending()
        self.policy._blocked_capabilities.add("list_directory")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.list_directory.assert_not_called()

    def test_audit_omits_path_names_and_listing(self):
        self.pending()
        self.session.approve_pending()
        log = repr(self.audit.all())
        self.assertNotIn(PATH, log)
        self.assertNotIn("private-child", log)
        self.assertEqual(self.audit.all()[-1].event_type, AuditEventType.VERIFICATION_OUTCOME)

    def test_failures_do_not_verify_or_leak_os_details(self):
        self.service.list_directory.side_effect = OSError("private-child raw-OS-detail")
        self.pending()
        result = self.session.approve_pending()
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertNotIn("private-child", repr(result) + repr(self.audit.all()))
        self.assertNotIn(AuditEventType.VERIFICATION_OUTCOME, [e.event_type for e in self.audit.all()])

    def test_existing_undo_entry_survives(self):
        callback = Mock()
        original = self.undo.register(capability="prior", description="prior", callback=callback)
        self.pending()
        self.session.approve_pending()
        self.assertEqual(self.undo.count(), 1)
        self.assertEqual(self.undo.peek(), original)
        callback.assert_not_called()


@unittest.skipUnless(platform.system() == "Windows", "Native temporary-directory test requires Windows")
class TemporaryWindowsDirectoryTests(unittest.TestCase):
    def test_lists_only_self_created_temporary_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "notes.txt").write_bytes(b"harmless")
            (root / "child").mkdir()
            (root / "child" / "not-recursive.txt").write_bytes(b"harmless")
            result = fs.FilesystemService().list_directory(str(root))
            self.assertEqual({(e.name, e.kind) for e in result.entries},
                             {("notes.txt", "file"), ("child", "directory")})
            self.assertEqual(result.entry_count, 2)
