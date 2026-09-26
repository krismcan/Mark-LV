"""Single irreversible directory creation; fake Win32 edges and one owned fixture."""

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
from nayeon.capabilities import create_directory
from nayeon.capabilities.create_directory import CreateDirectoryCapability
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
from tests.test_filesystem import FakeWindows


PATH = r"C:\Temp\NewDirectory"
TEXT = "create directory " + PATH


class FakeDirectoryWindows(FakeWindows):
    def __init__(self):
        super().__init__(b"")
        self.closed = set()
        self.created = 0
        self.fail_path = None
        self.api.CreateDirectoryW = Mock(side_effect=self.create)
        self.api.CloseHandle.side_effect = self.close

    def open(self, path, access, share, security, disposition, flags, template):
        assert disposition == 3  # Never create a file or reopen with truncation.
        if path == self.fail_path:
            return ctypes.c_void_p(-1).value
        return super().open(path, access, share, security, disposition, flags, template)

    def create(self, path, security):
        assert path == PATH and security is None
        assert len(self.handles) == 2 and not self.closed
        for handle in self.handles:
            assert ("identity", handle) in self.events
        self.events.append(("create_directory", path))
        self.created += 1
        return True

    def close(self, handle):
        assert handle not in self.closed
        self.closed.add(handle)
        self.events.append(("close", handle))
        return True


class DirectoryCreationContractTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.app = CreateDirectoryCapability(service=self.service)

    def test_discovery_contracts_and_no_resource_ownership(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(create_directory), 1)
        app = registry.get_implementation("create_directory")
        for protocol in (StructuredCapability, IntentArgumentMapper, VerificationProvider):
            self.assertIsInstance(app, protocol)
        for protocol in (UndoProvider, UnregisteredResourceProvider):
            self.assertNotIsInstance(app, protocol)

    def test_metadata_is_local_confirmed_irreversible_with_dedicated_permission(self):
        meta = self.app.capability
        self.assertEqual((meta.name, meta.service, meta.execution_mode), ("create_directory", "filesystem", ExecutionMode.LOCAL))
        self.assertTrue(meta.requires_confirmation)
        self.assertFalse(meta.reversible)
        self.assertFalse(meta.requires_llm)
        self.assertIn("Irreversible", meta.description)
        self.assertEqual(meta.intent_patterns, ("create directory ",))

    def test_explicit_path_wins_and_discards_extras(self):
        self.assertEqual(self.app.map_intent_arguments({"path": PATH, "request": "wrong", "parents": True},
                                                      original_request=TEXT), {"path": PATH})

    def test_invalid_explicit_value_reaches_validation(self):
        for value in (None, "", "relative", [], 42):
            with self.subTest(value=value):
                mapped = self.app.map_intent_arguments({"path": value, "request": TEXT}, original_request=TEXT)
                self.assertIs(mapped["path"], value)
                with self.assertRaises((ValueError, TypeError)):
                    self.app.validate_arguments(mapped)

    def test_exact_binding_and_existing_case_convention(self):
        for text in (TEXT, "CREATE DIRECTORY " + PATH, "  " + TEXT + "  "):
            self.assertEqual(self.app.map_intent_arguments({"request": text}, original_request=text), {"path": PATH})
        with self.assertRaises(ValueError):
            self.app.map_intent_arguments({"request": TEXT}, original_request=" " + TEXT)

    def test_broader_aliases_rejected(self):
        for prefix in ("make directory ", "make folder ", "create folder ", "mkdir ", "new directory ",
                       "new folder ", "create directories ", "create empty file "):
            text = prefix + PATH
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                self.app.map_intent_arguments({"request": text}, original_request=text)

    def test_mapping_validation_no_io(self):
        with patch.object(fs, "_kernel32", side_effect=AssertionError("no IO")):
            self.app.validate_arguments(self.app.map_intent_arguments({"request": TEXT}, original_request=TEXT))
        self.assertEqual(self.service.mock_calls, [])

    def test_only_path_no_recursive_or_options(self):
        for arguments in ({}, [], {"path": PATH, "recursive": False}, {"path": PATH, "parents": True},
                          {"path": PATH, "overwrite": False}, {"path": PATH, "options": {}}, {"path": PATH, "content": ""}):
            with self.subTest(arguments=arguments), self.assertRaises((TypeError, ValueError)):
                self.app.validate_arguments(arguments)

    def test_path_rules_and_final_component_required(self):
        for path in ("", "relative", r"C:relative", "C:\\", "C:\\Temp\\", r"\\server\share\x",
                     r"\\?\C:\x", r"\\.\C:\x", r"C:\Temp\..\x", r"C:\.\x", r"C:\*", r"C:\?",
                     r"C:\%TEMP%\x", r"C:\$env:TEMP\x", r"C:\x:stream", r"C:\CON", r"C:\NUL.txt",
                     r"C:\Temp.\x", "C:\\x ", "C:\\x.", None):
            with self.subTest(path=path), self.assertRaises((TypeError, ValueError)):
                self.app.validate_arguments({"path": path})

    def test_normalizes_without_guessing_or_quote_removal(self):
        self.assertEqual(self.app.validate_arguments({"path": "c:/Temp/NewDirectory"}), {"path": PATH})
        with self.assertRaises(ValueError):
            self.app.validate_arguments({"path": '"' + PATH + '"'})

    def test_legacy_rejects_without_service(self):
        with self.assertRaises(fs.DirectoryCreateError) as caught:
            self.app.execute(TEXT)
        self.assertIs(caught.exception.failure, fs.DirectoryCreateFailure.STRUCTURED_REQUIRED)
        self.assertEqual(self.service.mock_calls, [])

    def test_structured_delegation_and_frozen_redacted_result(self):
        result = fs.DirectoryCreateResult(PATH)
        self.service.create_directory.return_value = result
        self.assertIs(self.app.execute_structured({"path": PATH}), result)
        self.service.create_directory.assert_called_once_with(PATH)
        self.assertEqual(result.state, "created")
        self.assertNotIn(PATH, repr(result))
        self.assertNotIn("_observation", repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.path = "other"
        self.assertFalse(hasattr(result, "handle"))

    def test_wrong_output_or_request_binding_never_observes(self):
        for request, output in ((TEXT, fs.DirectoryCreateResult(PATH)),
                                (StructuredCapabilityRequest(TEXT, {"path": PATH}), object()),
                                (StructuredCapabilityRequest(TEXT, {"path": PATH}), fs.DirectoryCreateResult(r"C:\other"))):
            self.assertIs(VerificationService().verify(self.app, request=request, output=output).status,
                          VerificationStatus.INDETERMINATE)
        self.service.observe_created_directory.assert_not_called()


class DirectoryApiCase(unittest.TestCase):
    def setUp(self):
        self.fake = FakeDirectoryWindows()
        self.api = self.fake.api
        self.service = fs.FilesystemService()
        self.enterContext(patch.object(fs.platform, "system", return_value="Windows"))
        self.loader = self.enterContext(patch.object(fs, "_kernel32", return_value=self.api))
        self.last_error = self.enterContext(patch.object(ctypes, "get_last_error", return_value=5, create=True))

    def assert_closed(self):
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        self.assertEqual(self.api.CloseHandle.call_count, len(self.fake.handles))


class DirectoryCreateHandleTests(DirectoryApiCase):
    def test_one_documented_mutation_with_retained_validated_ancestors(self):
        result = self.service.create_directory(PATH)
        self.assertEqual(result.state, "created")
        self.assertIs(result._observation, fs.DirectoryCreateObservation.PRESENT)
        self.api.CreateDirectoryW.assert_called_once_with(PATH, None)
        self.assertEqual(self.api.CreateDirectoryW.argtypes, [fs.wintypes.LPCWSTR, ctypes.c_void_p])
        self.assertIs(self.api.CreateDirectoryW.restype, fs.wintypes.BOOL)
        self.assertEqual([c.args[0] for c in self.api.CreateFileW.call_args_list], ["C:\\", r"C:\Temp", PATH])
        for call in self.api.CreateFileW.call_args_list:
            self.assertEqual(call.args[1:], (0x81, 1, None, 3, fs._OPEN_FLAGS, None))
        self.assertLess(self.fake.events.index(("create_directory", PATH)), self.fake.events.index(("open", 12)))
        self.assert_closed()

    def test_existing_objects_fail_without_observation_or_replacement(self):
        for kind, error in (("directory", 183), ("file", 183), ("reparse", 80)):
            with self.subTest(kind=kind):
                fake = FakeDirectoryWindows()
                fake.api.CreateDirectoryW.side_effect = None
                fake.api.CreateDirectoryW.return_value = False
                self.last_error.return_value = error
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.DirectoryCreateError) as caught:
                    self.service.create_directory(PATH)
                self.assertIs(caught.exception.failure, fs.DirectoryCreateFailure.ALREADY_EXISTS)
                self.assertEqual(fake.created, 0)
                self.assertEqual(len(fake.api.CreateFileW.call_args_list), 2)
                self.assertEqual(fake.closed, set(fake.handles))

    def test_missing_parent_rejected_without_recursive_creation(self):
        self.fake.fail_path = r"C:\Temp"
        self.last_error.return_value = 3
        with self.assertRaises(fs.DirectoryCreateError) as caught:
            self.service.create_directory(PATH)
        self.assertIs(caught.exception.failure, fs.DirectoryCreateFailure.NOT_FOUND)
        self.api.CreateDirectoryW.assert_not_called()
        self.assert_closed()

    def test_unsafe_ancestor_or_redirected_final_path_never_mutates(self):
        for state in (0, 0x410, 0x1010, 0x40010, 0x400010, "redirected"):
            with self.subTest(state=state):
                fake = FakeDirectoryWindows()
                if state == "redirected":
                    fake.final_paths[r"C:\Temp"] = r"\\?\C:\Elsewhere"
                else:
                    fake.attributes[r"C:\Temp"] = state
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.DirectoryCreateError):
                    self.service.create_directory(PATH)
                fake.api.CreateDirectoryW.assert_not_called()
                self.assertEqual(fake.closed, set(fake.handles))

    def test_unavailable_ancestor_evidence_fails_before_mutation(self):
        self.api.GetFileInformationByHandle.return_value = False
        self.api.GetFileInformationByHandle.side_effect = None
        with self.assertRaises(fs.DirectoryCreateError):
            self.service.create_directory(PATH)
        self.api.CreateDirectoryW.assert_not_called()
        self.assert_closed()

    def test_network_drive_rejected_without_open(self):
        self.api.GetDriveTypeW.return_value = 4
        with self.assertRaises(fs.DirectoryCreateError):
            self.service.create_directory(PATH)
        self.api.CreateFileW.assert_not_called()
        self.api.CreateDirectoryW.assert_not_called()

    def test_create_call_failures_typed_and_redacted(self):
        for code, expected in ((3, fs.DirectoryCreateFailure.NOT_FOUND), (5, fs.DirectoryCreateFailure.ACCESS_DENIED),
                               (32, fs.DirectoryCreateFailure.BUSY), (999, fs.DirectoryCreateFailure.CREATE_ERROR)):
            with self.subTest(code=code):
                fake = FakeDirectoryWindows()
                fake.api.CreateDirectoryW.side_effect = None
                fake.api.CreateDirectoryW.return_value = False
                self.last_error.return_value = code
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.DirectoryCreateError) as caught:
                    self.service.create_directory(PATH)
                self.assertIs(caught.exception.failure, expected)
                self.assertNotIn(PATH, str(caught.exception))
                self.assertEqual(fake.closed, set(fake.handles))

    def test_precommit_os_exception_is_redacted(self):
        self.api.CreateDirectoryW.side_effect = OSError("private Win32 detail")
        with self.assertRaises(fs.DirectoryCreateError) as caught:
            self.service.create_directory(PATH)
        self.assertNotIn("private", str(caught.exception))
        self.assert_closed()

    def test_postcommit_open_failure_does_not_erase_mutation(self):
        self.fake.fail_path = PATH
        result = self.service.create_directory(PATH)
        self.assertEqual(result.state, "created")
        self.assertIs(result._observation, fs.DirectoryCreateObservation.UNKNOWN)
        self.assertEqual(self.fake.created, 1)
        self.assert_closed()

    def test_postcommit_metadata_exceptions_preserve_created_result(self):
        for method_name in ("GetFileType", "GetFileInformationByHandle", "GetFinalPathNameByHandleW"):
            with self.subTest(method=method_name):
                fake = FakeDirectoryWindows()
                method = getattr(fake.api, method_name)
                original = method.side_effect
                def inspect(handle, *args):
                    if fake.handles[handle] == PATH:
                        raise OSError("private metadata")
                    return original(handle, *args) if original else 1
                method.side_effect = inspect
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    result = self.service.create_directory(PATH)
                self.assertEqual(result.state, "created")
                self.assertIs(result._observation, fs.DirectoryCreateObservation.UNKNOWN)
                self.assertEqual(fake.created, 1)
                self.assertEqual(fake.closed, set(fake.handles))

    def test_contradictory_postcreate_snapshot_never_rolls_back(self):
        self.fake.attributes[PATH] = 0x410
        result = self.service.create_directory(PATH)
        self.assertEqual(result.state, "created")
        self.assertIs(result._observation, fs.DirectoryCreateObservation.CONTRADICTED)
        self.assertEqual(self.fake.created, 1)
        self.assert_closed()

    def test_close_diagnostics_preserve_creation_and_attempt_remaining_closes(self):
        original = self.fake.close
        def close(handle):
            original(handle)
            if handle == 11:
                raise OSError("private close")
            return True
        self.api.CloseHandle.side_effect = close
        result = self.service.create_directory(PATH)
        self.assertEqual(result.state, "created")
        self.assertIs(result._observation, fs.DirectoryCreateObservation.UNKNOWN)
        self.assert_closed()

    def test_no_shell_python_mutation_delete_or_enumeration(self):
        with patch.object(Path, "mkdir", side_effect=AssertionError("no mkdir")), \
             patch("os.mkdir", side_effect=AssertionError("no mkdir")), \
             patch("subprocess.Popen", side_effect=AssertionError("no shell")):
            self.service.create_directory(PATH)
        allowed = {"GetDriveTypeW", "CreateFileW", "CreateDirectoryW", "GetFileType",
                   "GetFileInformationByHandle", "GetFinalPathNameByHandleW", "CloseHandle"}
        self.assertTrue(all(call[0] in allowed for call in self.api.mock_calls))
        self.api.ReadFile.assert_not_called()

    def test_invalid_and_nonwindows_requests_do_not_load_api(self):
        with self.assertRaises(fs.DirectoryCreateError):
            self.service.create_directory("C:\\")
        with patch.object(fs.platform, "system", return_value="Linux"), self.assertRaises(fs.DirectoryCreateError) as caught:
            self.service.create_directory(PATH)
        self.assertIs(caught.exception.failure, fs.DirectoryCreateFailure.UNSUPPORTED_PLATFORM)
        self.loader.assert_not_called()


class DirectoryCreateObservationTests(DirectoryApiCase):
    def observe(self):
        return self.service.observe_created_directory(fs.DirectoryCreateResult(PATH))

    def test_safe_path_is_present_not_created_identity_proof(self):
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.PRESENT)
        self.api.CreateDirectoryW.assert_not_called()
        self.assertTrue(all(c.args[4] == 3 for c in self.api.CreateFileW.call_args_list))
        self.assert_closed()

    def test_missing_target_is_contradicted(self):
        self.fake.fail_path = PATH
        self.last_error.return_value = 2
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.CONTRADICTED)
        self.assert_closed()

    def test_missing_parent_is_contradicted(self):
        self.fake.fail_path = r"C:\Temp"
        self.last_error.return_value = 3
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.CONTRADICTED)

    def test_file_or_unsafe_target_is_contradicted(self):
        for attrs in (0, 0x410, 0x1010, 0x40010, 0x400010):
            with self.subTest(attrs=attrs):
                fake = FakeDirectoryWindows()
                fake.attributes[PATH] = attrs
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    self.assertIs(self.observe(), fs.DirectoryCreateObservation.CONTRADICTED)

    def test_wrong_final_path_is_contradicted(self):
        self.fake.final_paths[PATH] = r"\\?\C:\Other"
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.CONTRADICTED)

    def test_access_sharing_and_other_errors_are_unknown(self):
        for code in (5, 32, 999):
            with self.subTest(code=code):
                fake = FakeDirectoryWindows()
                fake.fail_path = PATH
                self.last_error.return_value = code
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)

    def test_unavailable_metadata_unknown_and_closed(self):
        original = self.fake.info
        self.api.GetFileInformationByHandle.side_effect = lambda handle, pointer: (
            False if self.fake.handles[handle] == PATH else original(handle, pointer))
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)
        self.assert_closed()

    def test_malformed_final_path_unknown(self):
        self.fake.final_paths[PATH] = "malformed"
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)

    def test_truncated_final_path_unknown(self):
        original = self.fake.final
        self.api.GetFinalPathNameByHandleW.side_effect = lambda handle, *args: (
            1000 if self.fake.handles[handle] == PATH else original(handle, *args))
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)

    def test_observation_exception_never_mutates(self):
        self.api.GetFileInformationByHandle.side_effect = OSError("private")
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)
        self.api.CreateDirectoryW.assert_not_called()
        self.assert_closed()

    def test_non_disk_or_unsafe_ancestor_unknown(self):
        self.api.GetFileType.return_value = 0
        self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)

    def test_unsupported_platform_and_invalid_result_do_not_open(self):
        self.assertIs(self.service.observe_created_directory(object()), fs.DirectoryCreateObservation.UNKNOWN)
        with patch.object(fs.platform, "system", return_value="Linux"):
            self.assertIs(self.observe(), fs.DirectoryCreateObservation.UNKNOWN)
        self.loader.assert_not_called()


class DirectoryCreationSessionTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.service.create_directory.return_value = fs.DirectoryCreateResult(PATH)
        self.service.observe_created_directory.return_value = fs.DirectoryCreateObservation.PRESENT
        self.app = CreateDirectoryCapability(service=self.service)
        self.mapper = self.enterContext(patch.object(self.app, "map_intent_arguments", wraps=self.app.map_intent_arguments))
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("create_directory")
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
        self.mapper.side_effect = AssertionError("no remap")
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.service.create_directory.assert_called_once_with(PATH)
        self.assertEqual([c[0] for c in self.service.mock_calls], ["create_directory", "observe_created_directory"])
        self.assertEqual(self.undo.count(), 0)

    def test_semantic_candidate_is_saved_and_extras_discarded(self):
        resolution = IntentResolution("create_directory", IntentSource.SEMANTIC, .95,
                                      {"path": PATH, "request": "wrong", "parents": True})
        self.semantic.resolve.return_value = resolution
        self.assertIs(self.session.request("fake semantic").status, ExecutionStatus.REQUIRES_CONFIRMATION)
        resolution.arguments["path"] = r"C:\Other"
        self.session.approve_pending()
        self.service.create_directory.assert_called_once_with(PATH)

    def test_invalid_explicit_path_is_authoritatively_rejected(self):
        self.semantic.resolve.return_value = IntentResolution("create_directory", IntentSource.SEMANTIC, .95,
                                                              {"path": "relative", "request": TEXT})
        self.assertIs(self.session.request("fake semantic").status, ExecutionStatus.FAILED)
        self.assertEqual(self.audit.all()[-1].outcome, "validation_failed")
        self.assertEqual(self.service.mock_calls, [])

    def test_other_filesystem_permissions_do_not_grant_creation(self):
        self.permissions.revoke("create_directory")
        for name in ("read_file", "list_directory", "create_file"):
            self.permissions.grant(name)
        self.assertIs(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_policy_denial_never_creates_or_verifies(self):
        self.policy._blocked_capabilities.add("create_directory")
        self.assertIs(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_rejection_never_creates(self):
        self.pending()
        self.session.reject_pending()
        self.assertEqual(self.service.mock_calls, [])

    def test_cancel_never_creates(self):
        self.pending()
        self.session.request("cancel")
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.service.mock_calls, [])

    def test_expiry_never_creates(self):
        pending = self.pending()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_replay_cannot_create_twice(self):
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.create_directory.assert_called_once_with(PATH)

    def test_changed_registration_blocks_approval(self):
        self.pending()
        self.registry.unregister("create_directory")
        self.registry.register(self.app.capability, CreateDirectoryCapability(service=self.service))
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_revoked_permission_blocks_approval(self):
        self.pending()
        self.permissions.revoke("create_directory")
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_execution_failure_does_not_verify(self):
        self.service.create_directory.side_effect = fs.DirectoryCreateError(fs.DirectoryCreateFailure.ALREADY_EXISTS)
        self.pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.FAILED)
        self.service.observe_created_directory.assert_not_called()
        self.assertEqual(self.undo.count(), 0)

    def test_positive_unbound_snapshot_never_becomes_verified(self):
        self.service.create_directory.return_value = fs.DirectoryCreateResult(PATH, _observation=fs.DirectoryCreateObservation.PRESENT)
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertIn("continuity", result.verification.reason)

    def test_contradictory_observation_is_not_verified_but_creation_stays_executed(self):
        self.service.observe_created_directory.return_value = fs.DirectoryCreateObservation.CONTRADICTED
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)

    def test_unknown_or_malformed_observation_stays_indeterminate(self):
        for observation in (fs.DirectoryCreateObservation.UNKNOWN, "present", object()):
            with self.subTest(observation=observation):
                self.service.reset_mock()
                self.service.observe_created_directory.return_value = observation
                self.pending()
                result = self.session.approve_pending()
                self.assertIs(result.status, ExecutionStatus.EXECUTED)
                self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)

    def test_verifier_exception_does_not_undo_execution(self):
        self.service.observe_created_directory.side_effect = OSError("private observation")
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)

    def test_audit_omits_path_snapshot_and_raw_errors(self):
        self.pending()
        self.session.approve_pending()
        log = repr(self.audit.all())
        for private in (PATH, "_observation", "HANDLE"):
            self.assertNotIn(private, log)
        events = [e.event_type for e in self.audit.all()]
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, events)
        self.assertEqual(events[-1], AuditEventType.VERIFICATION_OUTCOME)

    def test_execution_exception_is_redacted(self):
        self.service.create_directory.side_effect = OSError("private OS detail")
        self.pending()
        result = self.session.approve_pending()
        self.assertNotIn("private", repr(result) + repr(self.audit.all()))

    def test_existing_undo_resource_untouched(self):
        callback, cleanup = Mock(), Mock()
        original = self.undo.register(capability="prior", description="prior", callback=callback, cleanup=cleanup)
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.undo.peek(), original)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()
        cleanup.assert_not_called()

    def test_real_service_confirmed_flow_never_claims_exact_creation_identity(self):
        fake = FakeDirectoryWindows()
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, "system", return_value="Windows"), patch.object(fs, "_kernel32", return_value=fake.api):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(fake.created, 1)
        self.assertEqual(fake.closed, set(fake.handles))
        self.assertEqual(self.undo.count(), 0)

    def test_real_postcommit_observation_failure_remains_executed(self):
        fake = FakeDirectoryWindows()
        fake.fail_path = PATH
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, "system", return_value="Windows"), \
             patch.object(fs, "_kernel32", return_value=fake.api), \
             patch.object(ctypes, "get_last_error", return_value=5, create=True):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(fake.created, 1)
        self.assertEqual(fake.closed, set(fake.handles))

    def test_postcommit_audit_failure_does_not_retry_or_delete(self):
        original = self.audit.record
        def record(event, **kwargs):
            if event is AuditEventType.EXECUTION_SUCCEEDED:
                raise OSError("sink unavailable")
            return original(event, **kwargs)
        self.pending()
        with patch.object(self.audit, "record", side_effect=record), self.assertRaises(OSError):
            self.session.approve_pending()
        self.service.create_directory.assert_called_once_with(PATH)
        self.service.observe_created_directory.assert_not_called()
        self.assertFalse(self.session.has_pending)


@unittest.skipUnless(platform.system() == "Windows", "Native test requires Windows")
class NativeDirectoryCreationTests(unittest.TestCase):
    def test_only_self_owned_single_child_directory(self):
        # This cleanup is test infrastructure, not capability undo/rollback.
        with tempfile.TemporaryDirectory() as parent:
            child = Path(parent) / "nayeon-child"
            service = fs.FilesystemService()
            result = service.create_directory(str(child))
            self.assertEqual(result.state, "created")
            self.assertTrue(child.is_dir())
            self.assertEqual(list(child.iterdir()), [])
            self.assertIs(service.observe_created_directory(result), fs.DirectoryCreateObservation.PRESENT)
            app = CreateDirectoryCapability(service=service)
            verified = VerificationService().verify(app, request=StructuredCapabilityRequest(
                "create directory " + str(child), {"path": str(child)}), output=result)
            self.assertIs(verified.status, VerificationStatus.INDETERMINATE)
            with self.assertRaises(fs.DirectoryCreateError) as caught:
                service.create_directory(str(child))
            self.assertIs(caught.exception.failure, fs.DirectoryCreateFailure.ALREADY_EXISTS)
            self.assertTrue(child.is_dir())
