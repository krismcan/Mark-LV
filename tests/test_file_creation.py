"""Irreversible creation: fake Windows edge cases, one disposable native fixture."""

import ctypes
from dataclasses import FrozenInstanceError
from datetime import timedelta
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities import create_file
from nayeon.capabilities.create_file import CreateFileCapability
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.structured import IntentArgumentMapper, StructuredCapability, StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services import filesystem as fs
from nayeon.undo.contract import UndoProvider, UnregisteredResourceProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationProvider, VerificationStatus
from nayeon.verification.service import VerificationService
from tests.test_filesystem import FakeWindows, PATH


TEXT = "create empty file " + PATH
IDENTITY = (73, bytes(range(1, 17)))


class FakeCreateWindows(FakeWindows):
    def __init__(self):
        super().__init__(b"")
        self.identity = IDENTITY
        self.created = 0
        self.closed = set()
        self.fail_path = None
        self.api.GetFileInformationByHandleEx = Mock(side_effect=self.file_id)
        self.api.CloseHandle.side_effect = self.close

    def open(self, path, access, share, security, disposition, flags, template):
        if path == self.fail_path:
            return ctypes.c_void_p(-1).value
        if disposition == 1:
            self.created += 1
            # Ancestor references still live at the moment of mutation.
            assert len(self.handles) == 2
            assert not self.closed
        return super().open(path, access, share, security, disposition, flags, template)

    def close(self, handle):
        assert handle not in self.closed
        self.closed.add(handle)
        self.events.append(("close", handle))
        return True

    def file_id(self, handle, information_class, pointer, size):
        assert information_class == 18
        assert size == 24
        self.events.append(("file_id", handle))
        info = ctypes.cast(pointer, ctypes.POINTER(fs._FileIdInfo)).contents
        info.volume = self.identity[0]
        info.identifier[:] = self.identity[1]
        return True


class CreationContractTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.app = CreateFileCapability(service=self.service)

    def test_discovery_and_optional_contracts(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(create_file), 1)
        app = registry.get_implementation("create_file")
        for protocol in (StructuredCapability, IntentArgumentMapper, VerificationProvider):
            self.assertIsInstance(app, protocol)
        for protocol in (UndoProvider, UnregisteredResourceProvider):
            self.assertNotIsInstance(app, protocol)

    def test_metadata_has_dedicated_permission_and_no_reversibility(self):
        meta = self.app.capability
        self.assertEqual((meta.name, meta.service, meta.execution_mode), ("create_file", "filesystem", ExecutionMode.LOCAL))
        self.assertFalse(meta.requires_llm)
        self.assertFalse(meta.reversible)
        self.assertTrue(meta.requires_confirmation)
        self.assertIn("Irreversible", meta.description)
        self.assertEqual(meta.intent_patterns, ("create empty file ",))

    def test_explicit_path_wins_and_extras_are_discarded(self):
        self.assertEqual(self.app.map_intent_arguments({"path": PATH, "request": "wrong", "content": "ignore"},
                                                      original_request=TEXT), {"path": PATH})

    def test_invalid_explicit_path_is_not_replaced_by_fallback(self):
        for value in (None, "", "relative", [], 1):
            with self.subTest(value=value):
                mapped = self.app.map_intent_arguments({"path": value, "request": TEXT}, original_request=TEXT)
                self.assertIs(mapped["path"], value)
                with self.assertRaises((TypeError, ValueError)):
                    self.app.validate_arguments(mapped)

    def test_local_mapping_narrow_prefix_and_original_binding(self):
        for text in (TEXT, "CREATE EMPTY FILE " + PATH, "  " + TEXT + "  "):
            self.assertEqual(self.app.map_intent_arguments({"request": text}, original_request=text), {"path": PATH})
        with self.assertRaises(ValueError):
            self.app.map_intent_arguments({"request": TEXT}, original_request=" " + TEXT)

    def test_broader_aliases_do_not_map(self):
        for prefix in ("create file ", "make file ", "new file ", "write file ", "save file ", "touch ", "create document "):
            text = prefix + PATH
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                self.app.map_intent_arguments({"request": text}, original_request=text)

    def test_mapping_and_validation_have_no_io(self):
        with patch.object(fs, "_kernel32", side_effect=AssertionError("no IO")):
            mapped = self.app.map_intent_arguments({"request": TEXT}, original_request=TEXT)
            self.app.validate_arguments(mapped)
        self.assertEqual(self.service.mock_calls, [])

    def test_only_path_field_is_accepted(self):
        for arguments in ({}, {"path": PATH, "content": ""}, {"path": PATH, "overwrite": False},
                          {"path": PATH, "append": False}, {"path": PATH, "options": {}}, []):
            with self.subTest(arguments=arguments), self.assertRaises((TypeError, ValueError)):
                self.app.validate_arguments(arguments)

    def test_unsafe_paths_and_missing_filename_rejected(self):
        for path in ("", "relative", r"C:relative", "C:\\", "C:\\Temp\\", r"\\host\share\x",
                     r"\\?\C:\x", r"\\.\C:\x", r"C:\Temp\..\x", r"C:\*", r"C:\?",
                     r"C:\%TEMP%\x", r"C:\$env:TEMP\x", r"C:\x:stream", r"C:\CON.txt",
                     r"C:\Temp.\x", "C:\\x ", "C:\\x.", None):
            with self.subTest(path=path), self.assertRaises((TypeError, ValueError)):
                self.app.validate_arguments({"path": path})

    def test_normalization_does_not_guess_expand_or_remove_quotes(self):
        self.assertEqual(self.app.validate_arguments({"path": "c:/Temp/notes.txt"}), {"path": PATH})
        self.assertEqual(self.app.validate_arguments({"path": r"C:\Temp\no_extension"}), {"path": r"C:\Temp\no_extension"})
        with self.assertRaises(ValueError):
            self.app.validate_arguments({"path": '"' + PATH + '"'})

    def test_legacy_path_cannot_create(self):
        with self.assertRaises(fs.FileCreateError) as caught:
            self.app.execute(TEXT)
        self.assertIs(caught.exception.failure, fs.FileCreateFailure.STRUCTURED_REQUIRED)
        self.service.create_empty_file.assert_not_called()

    def test_structured_execution_delegates_normalized_path(self):
        output = self.app.execute_structured({"path": "c:/Temp/notes.txt"})
        self.service.create_empty_file.assert_called_once_with(PATH)
        self.assertIs(output, self.service.create_empty_file.return_value)

    def test_result_is_frozen_and_repr_contains_no_identity_or_path(self):
        result = fs.FileCreateResult(PATH, _identity=IDENTITY)
        self.assertEqual((result.path, result.state, result.byte_count), (PATH, "created", 0))
        with self.assertRaises(FrozenInstanceError):
            result.path = "other"
        self.assertNotIn(PATH, repr(result))
        self.assertNotIn(repr(IDENTITY), repr(result))
        self.assertFalse(hasattr(result, "handle"))

    def test_verifier_rejects_unbound_or_malformed_output(self):
        for request, output in ((TEXT, fs.FileCreateResult(PATH)),
                                (StructuredCapabilityRequest(TEXT, {"path": PATH}), object()),
                                (StructuredCapabilityRequest(TEXT, {"path": PATH}), fs.FileCreateResult(r"C:\other"))):
            result = VerificationService().verify(self.app, request=request, output=output)
            self.assertIs(result.status, VerificationStatus.INDETERMINATE)
        self.service.observe_created_file.assert_not_called()


class CreateApiCase(unittest.TestCase):
    def setUp(self):
        self.fake = FakeCreateWindows()
        self.api = self.fake.api
        self.service = fs.FilesystemService()
        self.enterContext(patch.object(fs.platform, "system", return_value="Windows"))
        self.loader = self.enterContext(patch.object(fs, "_kernel32", return_value=self.api))
        self.last_error = self.enterContext(patch.object(ctypes, "get_last_error", return_value=5, create=True))

    def assert_closed(self):
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        self.assertEqual(self.api.CloseHandle.call_count, len(self.fake.handles))


class CreationHandleTests(CreateApiCase):
    def test_create_new_once_with_no_mutating_open_existing_target(self):
        result = self.service.create_empty_file(PATH)
        self.assertEqual(result._identity, IDENTITY)
        calls = self.api.CreateFileW.call_args_list
        self.assertEqual([call.args[0] for call in calls], ["C:\\", r"C:\Temp", PATH])
        self.assertEqual([call.args[4] for call in calls], [3, 3, 1])
        self.assertEqual(calls[-1].args[1:], (0x81, 1, None, 1, 0x00300080, None))
        self.assertEqual(self.fake.created, 1)
        self.assert_closed()

    def test_ancestors_remain_open_validated_and_deny_write_delete_sharing(self):
        self.service.create_empty_file(PATH)
        for call in self.api.CreateFileW.call_args_list[:-1]:
            self.assertEqual(call.args[1:], (0x81, 1, None, 3, fs._OPEN_FLAGS, None))
        for handle in (10, 11):
            self.assertLess(self.fake.events.index(("identity", handle)), self.fake.events.index(("open", 12)))
            self.assertGreater(self.fake.events.index(("close", handle)), self.fake.events.index(("file_id", 12)))

    def test_creation_evidence_uses_returned_handle_without_reopen(self):
        self.service.create_empty_file(PATH)
        self.assertEqual([h for event, h in self.fake.events if event == "file_id"], [12])
        self.assertEqual([h for event, h in self.fake.events if event == "close"], [12, 11, 10])
        self.api.ReadFile.assert_not_called()

    def test_existing_file_directory_or_reparse_fails_without_overwrite(self):
        for kind, error in (("file", 80), ("directory", 183), ("reparse", 80)):
            with self.subTest(kind=kind):
                fake = FakeCreateWindows()
                fake.fail_path = PATH
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    self.last_error.return_value = error
                    with self.assertRaises(fs.FileCreateError) as caught:
                        self.service.create_empty_file(PATH)
                self.assertIs(caught.exception.failure, fs.FileCreateFailure.ALREADY_EXISTS)
                self.assertEqual(fake.created, 0)
                self.assertEqual(len([c for c in fake.api.CreateFileW.call_args_list if c.args[0] == PATH]), 1)
                self.assertEqual(fake.closed, set(fake.handles))

    def test_missing_parent_prevents_create(self):
        self.fake.fail_path = r"C:\Temp"
        self.last_error.return_value = 3
        with self.assertRaises(fs.FileCreateError) as caught:
            self.service.create_empty_file(PATH)
        self.assertIs(caught.exception.failure, fs.FileCreateFailure.NOT_FOUND)
        self.assertEqual(self.fake.created, 0)
        self.assert_closed()

    def test_unsafe_or_redirected_ancestor_prevents_create(self):
        for changed in ("reparse", "offline", "redirected", "not_directory"):
            with self.subTest(changed=changed):
                fake = FakeCreateWindows()
                if changed == "redirected":
                    fake.final_paths[r"C:\Temp"] = r"\\?\C:\Other"
                else:
                    fake.attributes[r"C:\Temp"] = {"reparse": 0x410, "offline": 0x1010, "not_directory": 0}[changed]
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.FileCreateError):
                    self.service.create_empty_file(PATH)
                self.assertEqual(fake.created, 0)
                self.assertEqual(fake.closed, set(fake.handles))

    def test_network_drive_rejected_before_any_open(self):
        self.api.GetDriveTypeW.return_value = 4
        with self.assertRaises(fs.FileCreateError):
            self.service.create_empty_file(PATH)
        self.api.CreateFileW.assert_not_called()

    def test_create_failure_categories_are_redacted(self):
        for code, expected in ((2, fs.FileCreateFailure.NOT_FOUND), (5, fs.FileCreateFailure.ACCESS_DENIED),
                               (32, fs.FileCreateFailure.BUSY), (999, fs.FileCreateFailure.CREATE_ERROR)):
            with self.subTest(code=code):
                fake = FakeCreateWindows()
                fake.fail_path = PATH
                self.last_error.return_value = code
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.FileCreateError) as caught:
                    self.service.create_empty_file(PATH)
                self.assertIs(caught.exception.failure, expected)
                self.assertNotIn(PATH, str(caught.exception))
                self.assertEqual(fake.created, 0)

    def test_precommit_os_exception_is_typed_and_ancestors_close(self):
        original = self.fake.open
        def open_file(path, *args):
            if path == PATH:
                raise OSError("private-OS-detail")
            return original(path, *args)
        self.api.CreateFileW.side_effect = open_file
        with self.assertRaises(fs.FileCreateError) as caught:
            self.service.create_empty_file(PATH)
        self.assertNotIn("private-OS-detail", str(caught.exception))
        self.assert_closed()

    def test_metadata_exception_after_commit_returns_created(self):
        self.api.GetFileInformationByHandleEx.side_effect = OSError("private-OS-detail")
        result = self.service.create_empty_file(PATH)
        self.assertEqual(result.state, "created")
        self.assertIsNone(result._identity)
        self.assertEqual(self.fake.created, 1)
        self.assert_closed()

    def test_unsupported_file_id_does_not_use_legacy_index(self):
        self.api.GetFileInformationByHandleEx.return_value = False
        self.api.GetFileInformationByHandleEx.side_effect = None
        result = self.service.create_empty_file(PATH)
        self.assertIsNone(result._identity)
        self.assertEqual(result.state, "created")
        self.assert_closed()

    def test_each_optional_metadata_failure_preserves_commit_and_closes(self):
        for failed_call in ("GetFileType", "GetFileInformationByHandle", "GetFinalPathNameByHandleW"):
            with self.subTest(failed_call=failed_call):
                fake = FakeCreateWindows()
                method = getattr(fake.api, failed_call)
                original = method.side_effect
                def inspect(handle, *args):
                    if fake.handles[handle] == PATH:
                        raise OSError("private optional evidence")
                    return original(handle, *args) if original else 1
                method.side_effect = inspect
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    result = self.service.create_empty_file(PATH)
                self.assertEqual(result.state, "created")
                self.assertIsNone(result._identity)
                self.assertEqual(fake.created, 1)
                self.assertEqual(fake.closed, set(fake.handles))

    def test_postcommit_contradictions_do_not_rollback(self):
        for changed in ("nonzero", "reparse", "directory", "path"):
            with self.subTest(changed=changed):
                fake = FakeCreateWindows()
                if changed == "nonzero":
                    fake.size = 1
                elif changed == "path":
                    fake.final_paths[PATH] = r"\\?\C:\Other"
                else:
                    fake.attributes[PATH] = 0x400 if changed == "reparse" else 0x10
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    result = self.service.create_empty_file(PATH)
                self.assertEqual(result.state, "created")
                self.assertIsNone(result._identity)
                self.assertEqual(fake.closed, set(fake.handles))

    def test_close_diagnostic_cannot_reclassify_committed_creation(self):
        original = self.fake.close
        def close(handle):
            original(handle)
            if handle == 12:
                raise OSError("private close diagnostic")
            return True
        self.api.CloseHandle.side_effect = close
        result = self.service.create_empty_file(PATH)
        self.assertEqual(result.state, "created")
        self.assertIsNone(result._identity)
        self.assert_closed()

    def test_no_delete_disposition_shell_or_python_file_write(self):
        with patch("builtins.open", side_effect=AssertionError("no open")), \
             patch.object(Path, "touch", side_effect=AssertionError("no touch")), \
             patch("subprocess.Popen", side_effect=AssertionError("no shell")):
            self.service.create_empty_file(PATH)
        allowed = {"GetDriveTypeW", "CreateFileW", "GetFileType", "GetFileInformationByHandle",
                   "GetFileInformationByHandleEx", "GetFinalPathNameByHandleW", "CloseHandle"}
        self.assertTrue(all(call[0] in allowed for call in self.api.mock_calls))

    def test_invalid_path_and_nonwindows_never_load_api(self):
        with self.assertRaises(fs.FileCreateError):
            self.service.create_empty_file("relative")
        with patch.object(fs.platform, "system", return_value="Linux"), self.assertRaises(fs.FileCreateError) as caught:
            self.service.create_empty_file(PATH)
        self.assertIs(caught.exception.failure, fs.FileCreateFailure.UNSUPPORTED_PLATFORM)
        self.loader.assert_not_called()


class CreationObservationTests(CreateApiCase):
    def observe(self):
        return self.service.observe_created_file(fs.FileCreateResult(PATH, _identity=IDENTITY))

    def test_matching_supported_128_bit_identity_is_matched(self):
        self.assertIs(self.observe(), fs.FileCreateObservation.MATCHED)
        self.assertTrue(all(c.args[4] == 3 for c in self.api.CreateFileW.call_args_list))
        self.assertEqual(self.fake.created, 0)
        self.assert_closed()

    def test_mismatched_volume_or_full_identifier_is_changed(self):
        for identity in ((74, IDENTITY[1]), (73, b"\xff" + IDENTITY[1][1:])):
            with self.subTest(identity=identity):
                fake = FakeCreateWindows()
                fake.identity = identity
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_missing_creation_identity_never_claims_match(self):
        self.assertIs(self.service.observe_created_file(fs.FileCreateResult(PATH)), fs.FileCreateObservation.UNKNOWN)
        self.loader.assert_not_called()

    def test_malformed_creation_identity_is_inconclusive_without_io(self):
        for identity in ((0, IDENTITY[1]), (73, b"short"), (True, IDENTITY[1]), [73, IDENTITY[1]],
                         (73, bytes(16)), (2**64, IDENTITY[1])):
            with self.subTest(identity=identity):
                self.assertIs(self.service.observe_created_file(fs.FileCreateResult(PATH, _identity=identity)),
                              fs.FileCreateObservation.UNKNOWN)
        self.loader.assert_not_called()

    def test_unsupported_observed_file_id_is_unknown(self):
        self.api.GetFileInformationByHandleEx.side_effect = None
        self.api.GetFileInformationByHandleEx.return_value = False
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.assert_closed()

    def test_malformed_observed_file_id_is_unknown(self):
        self.fake.identity = (0, bytes(16))
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_nonzero_default_stream_is_changed(self):
        self.fake.size = 1
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_wrong_final_path_is_changed(self):
        self.fake.final_paths[PATH] = r"\\?\C:\Other"
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_unsafe_or_directory_state_is_changed(self):
        for attributes in (0x400, 0x1000, 0x40000, 0x400000, 0x10):
            with self.subTest(attributes=attributes):
                fake = FakeCreateWindows()
                fake.attributes[PATH] = attributes
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_missing_target_is_changed(self):
        self.fake.fail_path = PATH
        self.last_error.return_value = 2
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)
        self.assert_closed()

    def test_missing_parent_is_changed(self):
        self.fake.fail_path = r"C:\Temp"
        self.last_error.return_value = 3
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_sharing_access_and_unknown_failures_are_inconclusive(self):
        for code in (5, 32, 999):
            with self.subTest(code=code):
                fake = FakeCreateWindows()
                fake.fail_path = PATH
                self.last_error.return_value = code
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_observer_exception_closes_handles_and_is_inconclusive(self):
        self.api.GetFileInformationByHandleEx.side_effect = OSError("private")
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.assert_closed()

    def test_malformed_final_path_is_inconclusive(self):
        self.fake.final_paths[PATH] = "broken"
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_non_disk_or_unavailable_metadata_is_inconclusive(self):
        self.api.GetFileType.return_value = 0
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_unavailable_target_metadata_is_inconclusive(self):
        original = self.fake.info
        self.api.GetFileInformationByHandle.side_effect = lambda handle, pointer: (
            False if self.fake.handles[handle] == PATH else original(handle, pointer))
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.assert_closed()

    def test_truncated_final_path_is_inconclusive(self):
        original = self.fake.final
        self.api.GetFinalPathNameByHandleW.side_effect = lambda handle, *args: (
            1000 if self.fake.handles[handle] == PATH else original(handle, *args))
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.assert_closed()

    def test_snapshot_never_uses_write_or_delete_calls(self):
        self.observe()
        self.assertEqual(self.fake.created, 0)
        self.assertTrue(all(call.args[1] == 0x81 and call.args[4] == 3 for call in self.api.CreateFileW.call_args_list))
        self.api.ReadFile.assert_not_called()


class CreationSessionTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.service.create_empty_file.return_value = fs.FileCreateResult(PATH, _identity=IDENTITY)
        self.service.observe_created_file.return_value = fs.FileCreateObservation.MATCHED
        self.app = CreateFileCapability(service=self.service)
        self.mapper = self.enterContext(patch.object(self.app, "map_intent_arguments", wraps=self.app.map_intent_arguments))
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("create_file")
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
        self.assertIs(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertEqual(self.service.mock_calls, [])
        return result

    def test_approval_creates_once_without_remapping_or_undo(self):
        self.pending()
        self.semantic.resolve.assert_not_called()
        self.mapper.side_effect = AssertionError("no remapping")
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(result.output.state, "created")
        self.service.create_empty_file.assert_called_once_with(PATH)
        self.assertEqual(self.undo.count(), 0)
        self.assertEqual([c[0] for c in self.service.mock_calls], ["create_empty_file", "observe_created_file"])

    def test_semantic_extras_discarded_and_saved_path_isolated(self):
        resolution = IntentResolution("create_file", IntentSource.SEMANTIC, .95,
                                      {"path": PATH, "request": "wrong", "content": "discard"})
        self.semantic.resolve.return_value = resolution
        self.assertIs(self.session.request("semantic fake").status, ExecutionStatus.REQUIRES_CONFIRMATION)
        resolution.arguments["path"] = r"C:\Other"
        self.session.approve_pending()
        self.service.create_empty_file.assert_called_once_with(PATH)

    def test_invalid_explicit_path_reaches_authoritative_validation(self):
        self.semantic.resolve.return_value = IntentResolution("create_file", IntentSource.SEMANTIC, .95,
                                                              {"path": "relative", "request": TEXT})
        self.assertIs(self.session.request("semantic fake").status, ExecutionStatus.FAILED)
        self.assertEqual(self.audit.all()[-1].outcome, "validation_failed")
        self.assertEqual(self.service.mock_calls, [])

    def test_read_or_list_permission_cannot_authorize_creation(self):
        self.permissions.revoke("create_file")
        self.permissions.grant("read_file")
        self.permissions.grant("list_directory")
        self.assertIs(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_policy_denial_prevents_create_and_verification(self):
        self.policy._blocked_capabilities.add("create_file")
        self.assertIs(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_rejection_has_no_mutation_or_verification(self):
        self.pending()
        self.session.reject_pending()
        self.assertEqual(self.service.mock_calls, [])

    def test_cancel_has_no_mutation_or_verification(self):
        self.pending()
        self.session.request("cancel")
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.service.mock_calls, [])

    def test_expiry_prevents_mutation(self):
        pending = self.pending()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_replay_cannot_create_twice(self):
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.create_empty_file.assert_called_once_with(PATH)

    def test_registration_change_blocks_approval(self):
        self.pending()
        self.registry.unregister("create_file")
        self.registry.register(self.app.capability, CreateFileCapability(service=self.service))
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_revoked_permission_blocks_approval(self):
        self.pending()
        self.permissions.revoke("create_file")
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_execution_failure_never_verifies(self):
        self.service.create_empty_file.side_effect = fs.FileCreateError(fs.FileCreateFailure.ALREADY_EXISTS)
        self.pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.FAILED)
        self.service.observe_created_file.assert_not_called()
        self.assertEqual(self.undo.count(), 0)

    def test_all_observation_states_preserve_executed_creation(self):
        for observation, expected in ((fs.FileCreateObservation.MATCHED, VerificationStatus.VERIFIED),
                                      (fs.FileCreateObservation.CHANGED, VerificationStatus.NOT_VERIFIED),
                                      (fs.FileCreateObservation.UNKNOWN, VerificationStatus.INDETERMINATE)):
            with self.subTest(observation=observation):
                self.service.reset_mock()
                self.service.observe_created_file.return_value = observation
                self.pending()
                result = self.session.approve_pending()
                self.assertIs(result.status, ExecutionStatus.EXECUTED)
                self.assertIs(result.verification.status, expected)
                self.assertEqual(self.undo.count(), 0)

    def test_verifier_exception_leaves_execution_committed(self):
        self.service.observe_created_file.side_effect = OSError("private")
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)

    def test_audit_omits_path_identity_and_internal_evidence(self):
        self.pending()
        self.session.approve_pending()
        log = repr(self.audit.all())
        for private in (PATH, repr(IDENTITY), "_identity", "HANDLE"):
            self.assertNotIn(private, log)
        events = [e.event_type for e in self.audit.all()]
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, events)
        self.assertEqual(events[-1], AuditEventType.VERIFICATION_OUTCOME)

    def test_raw_execution_error_is_redacted(self):
        self.service.create_empty_file.side_effect = OSError("private raw Win32 detail")
        self.pending()
        result = self.session.approve_pending()
        self.assertNotIn("private", repr(result) + repr(self.audit.all()))

    def test_existing_resource_registration_remains_untouched(self):
        callback, cleanup = Mock(), Mock()
        previous = self.undo.register(capability="prior", description="prior", callback=callback, cleanup=cleanup)
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.undo.peek(), previous)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()
        cleanup.assert_not_called()

    def test_real_service_metadata_failure_after_create_is_executed_without_undo(self):
        fake = FakeCreateWindows()
        fake.api.GetFileInformationByHandleEx.side_effect = OSError("private snapshot")
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, "system", return_value="Windows"), patch.object(fs, "_kernel32", return_value=fake.api):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(fake.created, 1)
        self.assertEqual(fake.closed, set(fake.handles))
        self.assertEqual(self.undo.count(), 0)

    def test_real_service_confirmed_creation_and_readonly_verification(self):
        fake = FakeCreateWindows()
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, "system", return_value="Windows"), patch.object(fs, "_kernel32", return_value=fake.api):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(fake.created, 1)
        self.assertEqual(fake.closed, set(fake.handles))
        self.assertEqual(self.undo.count(), 0)
        self.assertNotIn(repr(IDENTITY), repr(self.audit.all()))

    def test_postcommit_audit_exception_does_not_delete_or_retry(self):
        original = self.audit.record
        def record(event, **kwargs):
            if event is AuditEventType.EXECUTION_SUCCEEDED:
                raise OSError("audit sink unavailable")
            return original(event, **kwargs)
        self.pending()
        with patch.object(self.audit, "record", side_effect=record), self.assertRaises(OSError):
            self.session.approve_pending()
        self.service.create_empty_file.assert_called_once_with(PATH)
        self.service.observe_created_file.assert_not_called()
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.undo.count(), 0)


@unittest.skipUnless(platform.system() == "Windows", "Native test requires Windows")
class NativeCreationTests(unittest.TestCase):
    def test_creates_only_one_self_owned_empty_temporary_file(self):
        # TemporaryDirectory cleanup is test infrastructure, never capability undo.
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "nayeon-empty.txt")
            service = fs.FilesystemService()
            result = service.create_empty_file(path)
            self.assertEqual(result.state, "created")
            self.assertTrue(Path(path).is_file())
            self.assertEqual(Path(path).stat().st_size, 0)
            observation = service.observe_created_file(result)
            self.assertIs(observation, fs.FileCreateObservation.MATCHED if result._identity else fs.FileCreateObservation.UNKNOWN)
            with self.assertRaises(fs.FileCreateError) as caught:
                service.create_empty_file(path)
            self.assertIs(caught.exception.failure, fs.FileCreateFailure.ALREADY_EXISTS)
            self.assertEqual(Path(path).stat().st_size, 0)
