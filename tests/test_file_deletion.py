"""Private destructive binding, retained native lifetime and real authority paths."""

from copy import deepcopy
import ctypes
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import os
import platform
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities import delete_file
from nayeon.capabilities.delete_file import DeleteFileCapability
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


REQUEST = 'delete file ' + PATH
IDENTITY = (73, bytes(range(1, 17)))
PARENT_ID = (73, b'p' * 16)


class FakeDeleteWindows(FakeWindows):
    def __init__(self):
        super().__init__(b'fixture')
        self.present = True
        self.pending = False
        self.links = 1
        self.creation = 100
        self.write_time = 200
        self.access_time = 300
        self.identity = IDENTITY
        self.parent_identity = PARENT_ID
        self.closed = set()
        self.accesses = {}
        self.error = 0
        self.fail_path = None
        self.fail_error = 5
        self.close_deletes = True
        self.replace_after_close = False
        self.api.GetFileInformationByHandleEx = Mock(side_effect=self.file_id)
        self.api.SetFileInformationByHandle = Mock(side_effect=self.dispose)
        self.api.CloseHandle.side_effect = self.close

    def open(self, path, access, share, security, disposition, flags, template):
        self.error = 0
        if path == self.fail_path or (path == PATH and (not self.present or self.pending)):
            self.error = self.fail_error if path == self.fail_path else (5 if self.pending else 2)
            return ctypes.c_void_p(-1).value
        assert disposition == 3
        if path == PATH:
            assert access in (0x80, 0x10080) and share == 0
        else:
            assert access == 0x81 and share == 1
        assert flags == fs._OPEN_FLAGS
        handle = super().open(path, access, share, security, disposition, flags, template)
        self.accesses[handle] = access
        return handle

    def info(self, handle, pointer):
        super().info(handle, pointer)
        info = ctypes.cast(pointer, ctypes.POINTER(fs._FileInformation)).contents
        info.links = self.links
        info.creation.dwLowDateTime = self.creation
        info.write.dwLowDateTime = self.write_time
        info.access.dwLowDateTime = self.access_time
        return True

    def file_id(self, handle, kind, pointer, size):
        assert kind == 18 and size == 24
        value = self.identity if self.handles[handle] == PATH else self.parent_identity
        info = ctypes.cast(pointer, ctypes.POINTER(fs._FileIdInfo)).contents
        info.volume, info.identifier[:] = value
        return True

    def dispose(self, handle, kind, pointer, size):
        assert kind == 4 and size == 1
        assert ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ubyte)).contents.value == 1
        assert self.accesses[handle] == 0x10080 and handle not in self.closed
        assert sum(h not in self.closed and path != PATH for h, path in self.handles.items()) == 2
        self.pending = True
        self.events.append(('disposition', handle))
        return True

    def close(self, handle):
        assert handle not in self.closed
        self.closed.add(handle)
        self.events.append(('close', handle))
        if self.handles[handle] == PATH and self.accesses[handle] == 0x10080:
            if self.pending and self.close_deletes:
                self.present = False
                self.pending = False
            if self.replace_after_close:
                self.present = True
                self.pending = False
                self.identity = (73, b'n' * 16)
        return True


class NativeFakeCase(unittest.TestCase):
    def setUp(self):
        self.fake = FakeDeleteWindows()
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, 'system', return_value='Windows'))
        self.enterContext(patch.object(fs, '_kernel32', return_value=self.api))
        self.enterContext(patch.object(ctypes, 'get_last_error', side_effect=lambda: self.fake.error, create=True))
        self.service = fs.FilesystemService()
        self.app = DeleteFileCapability(service=self.service)

    def prepare(self):
        return self.app.validate_arguments({'path': PATH})

    def verify(self, args, output):
        return VerificationService().verify(self.app, request=StructuredCapabilityRequest(REQUEST, args), output=output)

    def assert_all_closed(self):
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        self.assertEqual(self.api.CloseHandle.call_count, len(self.fake.handles))


class DeleteContractTests(NativeFakeCase):
    def test_metadata(self):
        meta = self.app.capability
        self.assertEqual((meta.name, meta.service, meta.execution_mode), ('delete_file', 'filesystem', ExecutionMode.LOCAL))
        self.assertEqual(meta.description, 'Permanently delete one file. Irreversible; no undo.')
        self.assertTrue(meta.requires_confirmation)
        self.assertFalse(meta.reversible)
        self.assertFalse(meta.requires_llm)
        self.assertEqual(meta.intent_patterns, ('delete file ',))

    def test_discovery_and_protocols(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(delete_file), 1)
        app = registry.get_implementation('delete_file')
        for protocol in (StructuredCapability, IntentArgumentMapper, VerificationProvider):
            self.assertIsInstance(app, protocol)
        for protocol in (UndoProvider, UnregisteredResourceProvider):
            self.assertNotIsInstance(app, protocol)

    def test_exact_mapping_case_and_whitespace_without_io(self):
        for request in (REQUEST, '  DELETE FILE ' + PATH + '  '):
            self.assertEqual(self.app.map_intent_arguments({'request': request}, original_request=request), {'path': PATH})
        self.api.CreateFileW.assert_not_called()

    def test_aliases_and_wrong_original_binding_rejected(self):
        for request in (REQUEST.replace('delete file', 'delete'), REQUEST.replace('delete file', 'remove file'),
                        REQUEST.replace('delete file', 'delete files')):
            with self.assertRaises(ValueError):
                self.app.map_intent_arguments({'request': request}, original_request=request)
        with self.assertRaises(ValueError):
            self.app.map_intent_arguments({'request': REQUEST + 'x'}, original_request=REQUEST)

    def test_explicit_invalid_path_never_repaired_from_prose(self):
        for value in ('', None, 'relative', []):
            args = self.app.map_intent_arguments({'path': value, 'request': REQUEST}, original_request=REQUEST)
            self.assertEqual(args, {'path': value})
            with self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments(args)
        self.api.CreateFileW.assert_not_called()

    def test_caller_private_evidence_rejected_even_if_previously_generated(self):
        args = self.prepare()
        for binding in (args['_binding'], None, {}, 'pretend'):
            with self.assertRaises(ValueError):
                self.app.validate_arguments({'path': PATH, '_binding': binding})
            with self.assertRaises(ValueError):
                self.app.map_intent_arguments({'path': PATH, '_binding': binding}, original_request=REQUEST)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_raw_schema_exactly_path(self):
        for args in ({}, [], {'path': PATH, 'identity': IDENTITY}, {'path': PATH, 'force': True}):
            with self.assertRaises((TypeError, ValueError)):
                self.app.validate_arguments(args)

    def test_all_unsafe_path_forms_rejected_without_io(self):
        for path in ('', 'relative', 'C:relative', 'C:\\', r'\\host\share\x', r'\\?\C:\x', r'\\.\C:\x',
                     r'C:\x:ads', r'C:\*.bin', r'C:\?.bin', r'C:\%TEMP%\x', r'C:\$env:TEMP\x',
                     r'C:\..\x', r'C:\CON', '"' + PATH + '"', r'C:\x.', PATH + ' :: ' + PATH):
            with self.subTest(path=path), self.assertRaises((TypeError, ValueError)):
                self.app.validate_arguments({'path': path})
        self.api.CreateFileW.assert_not_called()

    def test_binding_immutable_deepcopy_equality_and_redaction(self):
        binding = self.prepare()['_binding']
        self.assertEqual(binding, deepcopy(binding))
        self.assertIsNot(binding, deepcopy(binding))
        with self.assertRaises(FrozenInstanceError):
            binding.size = 0
        for value in (PATH, repr(IDENTITY), repr(PARENT_ID), 'creation_time', 'write_time', 'HANDLE'):
            self.assertNotIn(value, repr(binding))

    def test_preparation_releases_every_handle_without_mutation_or_content_read(self):
        self.prepare()
        self.assert_all_closed()
        self.api.SetFileInformationByHandle.assert_not_called()
        self.api.ReadFile.assert_not_called()
        self.assertTrue(self.fake.present)
        self.assertEqual(self.api.CreateFileW.call_args_list[-1].args[1:6], (0x80, 0, None, 3, fs._OPEN_FLAGS))

    def test_execution_requires_enriched_saved_arguments(self):
        with self.assertRaises(fs.FileDeleteError):
            self.app.execute_structured({'path': PATH})
        with self.assertRaises(fs.FileDeleteError):
            self.app.execute(REQUEST)
        self.api.SetFileInformationByHandle.assert_not_called()


class DeletePreparationTests(NativeFakeCase):
    def test_missing_target(self):
        self.fake.present = False
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_all_closed()

    def test_directory_reparse_readonly_system_offline_rejected(self):
        for flags in (0x10, 0x400, 0x410, 1, 4, 0x1000, 0x40000, 0x400000):
            self.fake.attributes[PATH] = flags
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                self.prepare()
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assert_all_closed()

    def test_unsafe_ancestor_rejected(self):
        self.fake.attributes[r'C:\Temp'] = 0x410
        with self.assertRaises(ValueError):
            self.prepare()

    def test_size_zero_and_boundary_allowed(self):
        for size in (0, 65536):
            self.fake.size = size
            self.assertEqual(self.prepare()['_binding'].size, size)

    def test_oversize_rejected(self):
        self.fake.size = 65537
        with self.assertRaises(ValueError):
            self.prepare()

    def test_zero_and_multiple_links_rejected(self):
        for links in (0, 2, 100):
            self.fake.links = links
            with self.assertRaises(ValueError):
                self.prepare()

    def test_identity_unavailable_or_malformed_rejected(self):
        self.fake.identity = (0, b'\0' * 16)
        with self.assertRaises(ValueError):
            self.prepare()
        self.api.GetFileInformationByHandleEx.side_effect = None
        self.api.GetFileInformationByHandleEx.return_value = False
        with self.assertRaises(ValueError):
            self.prepare()

    def test_wrong_final_path_rejected(self):
        self.fake.final_paths[PATH] = r'\\?\C:\Other'
        with self.assertRaises(ValueError):
            self.prepare()

    def test_metadata_unavailable_rejected(self):
        self.api.GetFileInformationByHandle.side_effect = None
        self.api.GetFileInformationByHandle.return_value = False
        with self.assertRaises(ValueError):
            self.prepare()

    def test_access_time_noise_not_bound(self):
        args = self.prepare()
        self.fake.access_time += 1
        self.assertEqual(self.prepare(), args)

    def test_creation_write_size_attributes_volume_and_namespace_are_bound(self):
        original = self.prepare()['_binding']
        for attr, value in (('creation', 101), ('write_time', 201), ('size', 8),
                            ('identity', (74, IDENTITY[1])), ('parent_identity', (73, b'q' * 16))):
            old = getattr(self.fake, attr)
            setattr(self.fake, attr, value)
            self.assertNotEqual(self.prepare()['_binding'], original)
            setattr(self.fake, attr, old)
        self.fake.attributes[PATH] = 0x20
        self.assertNotEqual(self.prepare()['_binding'], original)

    def test_close_failure_prevents_binding_escape(self):
        def close(handle):
            self.fake.close(handle)
            return False
        self.api.CloseHandle.side_effect = close
        with self.assertRaises(ValueError):
            self.prepare()
        self.assert_all_closed()

    def test_unsupported_platform(self):
        with patch.object(fs.platform, 'system', return_value='Linux'), self.assertRaises(ValueError):
            self.prepare()
        self.api.CreateFileW.assert_not_called()


class DeleteExecutionTests(NativeFakeCase):
    def test_real_primitive_abi_flags_and_retained_ancestor_lifetime(self):
        args = self.prepare()
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.source_close, fs.DeleteClose.COMPLETE)
        self.assertIs(result.observation, fs.DeleteObservation.CONFIRMED_ABSENT)
        self.assertEqual(ctypes.sizeof(fs._FileDispositionInfo), 1)
        self.assertEqual(fs._FileDispositionInfo.delete_file.size, 1)
        self.api.SetFileInformationByHandle.assert_called_once()
        self.api.ReadFile.assert_not_called()
        opens = [c.args for c in self.api.CreateFileW.call_args_list if c.args[1] == 0x10080]
        self.assertEqual(opens, [(PATH, 0x10080, 0, None, 3, fs._OPEN_FLAGS, None)])
        self.assert_all_closed()
        self.assertIs(self.verify(args, result).status, VerificationStatus.VERIFIED)

    def test_replacement_after_preparation_never_deleted(self):
        args = self.prepare()
        self.fake.identity = (73, b'n' * 16)
        with self.assertRaises(fs.FileDeleteError):
            self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assertTrue(self.fake.present)
        self.assert_all_closed()

    def test_parent_namespace_change_never_deletes(self):
        args = self.prepare()
        self.fake.parent_identity = (73, b'n' * 16)
        with self.assertRaises(fs.FileDeleteError):
            self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_disappeared_or_renamed_before_execution(self):
        args = self.prepare()
        self.fake.present = False
        with self.assertRaises(fs.FileDeleteError):
            self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_link_and_stable_metadata_change_before_execution(self):
        args = self.prepare()
        for attr, value in (('links', 2), ('links', 0), ('size', 10), ('creation', 101), ('write_time', 201)):
            old = getattr(self.fake, attr)
            setattr(self.fake, attr, value)
            with self.assertRaises(fs.FileDeleteError):
                self.app.execute_structured(args)
            setattr(self.fake, attr, old)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_attribute_change_before_execution(self):
        args = self.prepare()
        for flags in (1, 4, 0x20, 0x400):
            self.fake.attributes[PATH] = flags
            with self.assertRaises(fs.FileDeleteError):
                self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_target_open_sharing_failure_no_disposition(self):
        args = self.prepare()
        self.fake.fail_path, self.fake.fail_error = PATH, 32
        with self.assertRaises(fs.FileDeleteError):
            self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_normal_false_is_not_acknowledged_and_not_verified(self):
        args = self.prepare()
        self.api.SetFileInformationByHandle.side_effect = None
        self.api.SetFileInformationByHandle.return_value = False
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.NOT_ACKNOWLEDGED)
        self.assertIs(result.source_close, fs.DeleteClose.COMPLETE)
        self.assertIs(result.observation, fs.DeleteObservation.PRESENT_SAME_IDENTITY)
        self.assertIs(self.verify(args, result).status, VerificationStatus.NOT_VERIFIED)
        self.assertTrue(self.fake.present)
        self.api.SetFileInformationByHandle.assert_called_once()
        self.assert_all_closed()

    def test_ambiguous_disposition_preserves_unknown_without_retry(self):
        args = self.prepare()
        def ambiguous(*call):
            self.fake.dispose(*call)
            raise OSError('private native detail')
        self.api.SetFileInformationByHandle.side_effect = ambiguous
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.UNKNOWN)
        self.assertIs(result.observation, fs.DeleteObservation.CONFIRMED_ABSENT)
        self.assertIs(self.verify(args, result).status, VerificationStatus.INDETERMINATE)
        self.api.SetFileInformationByHandle.assert_called_once()
        self.assert_all_closed()

    def test_source_close_false_keeps_acknowledgement_and_never_double_closes(self):
        args = self.prepare()
        def close(handle):
            self.fake.close(handle)
            return self.fake.accesses[handle] != 0x10080
        self.api.CloseHandle.side_effect = close
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.source_close, fs.DeleteClose.UNKNOWN)
        self.assertIs(self.verify(args, result).status, VerificationStatus.INDETERMINATE)
        self.assert_all_closed()

    def test_source_close_exception_preserves_acknowledgement(self):
        args = self.prepare()
        def close(handle):
            self.fake.close(handle)
            if self.fake.accesses[handle] == 0x10080:
                raise OSError('private')
            return True
        self.api.CloseHandle.side_effect = close
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.source_close, fs.DeleteClose.UNKNOWN)
        self.assert_all_closed()

    def test_ancestor_close_failure_cannot_erase_acknowledgement(self):
        args = self.prepare()
        def close(handle):
            self.fake.close(handle)
            return self.fake.handles[handle] == PATH
        self.api.CloseHandle.side_effect = close
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.source_close, fs.DeleteClose.COMPLETE)
        self.assertIs(self.verify(args, result).status, VerificationStatus.INDETERMINATE)
        self.assert_all_closed()

    def test_delete_pending_access_denied_is_not_absence(self):
        args = self.prepare()
        self.fake.close_deletes = False
        result = self.app.execute_structured(args)
        self.assertIs(result.observation, fs.DeleteObservation.UNKNOWN)
        self.assertIs(self.verify(args, result).status, VerificationStatus.INDETERMINATE)

    def test_same_identity_present_after_acknowledgement_is_not_verified(self):
        args = self.prepare()
        self.api.SetFileInformationByHandle.side_effect = lambda *call: True
        result = self.app.execute_structured(args)
        self.assertIs(result.observation, fs.DeleteObservation.PRESENT_SAME_IDENTITY)
        self.assertIs(self.verify(args, result).status, VerificationStatus.NOT_VERIFIED)

    def test_different_identity_reuse_after_close_is_indeterminate(self):
        args = self.prepare()
        self.fake.replace_after_close = True
        result = self.app.execute_structured(args)
        self.assertIs(result.observation, fs.DeleteObservation.PRESENT_DIFFERENT_IDENTITY)
        self.assertIs(self.verify(args, result).status, VerificationStatus.INDETERMINATE)

    def test_observation_exception_after_commit_preserves_receipt(self):
        args = self.prepare()
        original = self.fake.open
        def open_file(*call):
            if call[0] == PATH and not self.fake.present:
                raise OSError('private')
            return original(*call)
        self.api.CreateFileW.side_effect = open_file
        result = self.app.execute_structured(args)
        self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.observation, fs.DeleteObservation.UNKNOWN)
        self.assert_all_closed()

    def test_no_rollback_restore_backup_read_or_alternate_api(self):
        args = self.prepare()
        self.app.execute_structured(args)
        allowed = {'GetDriveTypeW', 'CreateFileW', 'GetFileType', 'GetFileInformationByHandle',
                   'GetFileInformationByHandleEx', 'GetFinalPathNameByHandleW', 'CloseHandle',
                   'SetFileInformationByHandle'}
        self.assertTrue({c[0] for c in self.api.mock_calls} <= allowed)
        self.assertTrue(all(c.args[4] == 3 for c in self.api.CreateFileW.call_args_list))


class DeleteVerificationTests(NativeFakeCase):
    def setUp(self):
        super().setUp()
        self.args = self.prepare()
        self.result = self.app.execute_structured(self.args)

    def test_frozen_receipt_repr_redacted(self):
        with self.assertRaises(FrozenInstanceError):
            self.result.observation = fs.DeleteObservation.UNKNOWN
        for text in (PATH, repr(IDENTITY), repr(PARENT_ID), '_binding', 'HANDLE', 'creation_time'):
            self.assertNotIn(text, repr(self.result))

    def test_absence_cannot_override_known_failed_disposition(self):
        result = replace(self.result, disposition=fs.DeleteDisposition.NOT_ACKNOWLEDGED)
        self.assertIs(self.verify(self.args, result).status, VerificationStatus.NOT_VERIFIED)

    def test_later_different_identity_reuse_is_indeterminate(self):
        self.fake.present = True
        self.fake.identity = (73, b'n' * 16)
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.INDETERMINATE)

    def test_later_same_identity_contradiction(self):
        self.fake.present = True
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.NOT_VERIFIED)

    def test_changed_parent_namespace_is_indeterminate(self):
        self.fake.parent_identity = (73, b'n' * 16)
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.INDETERMINATE)

    def test_missing_or_unsafe_ancestor_not_trustworthy_absence(self):
        self.fake.fail_path, self.fake.fail_error = r'C:\Temp', 3
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.INDETERMINATE)
        self.fake.fail_path = None
        self.fake.attributes[r'C:\Temp'] = 0x410
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.INDETERMINATE)

    def test_sharing_or_access_error_indeterminate(self):
        self.fake.fail_path = PATH
        for code in (5, 32, 999):
            self.fake.fail_error = code
            self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.INDETERMINATE)

    def test_current_identity_unavailable_indeterminate(self):
        self.fake.present = True
        self.fake.identity = (0, b'\0' * 16)
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.INDETERMINATE)

    def test_malformed_receipts_indeterminate(self):
        for changes in ({'disposition': 'acknowledged'}, {'source_close': 'complete'},
                        {'observation': 'confirmed_absent'}, {'_binding': None}, {'_cleanup_complete': None}):
            self.assertIs(self.verify(self.args, replace(self.result, **changes)).status, VerificationStatus.INDETERMINATE)

    def test_unbound_request_or_raw_request_indeterminate_without_repreparation(self):
        for request in (REQUEST, StructuredCapabilityRequest(REQUEST, {'path': PATH}),
                        StructuredCapabilityRequest(REQUEST, {**self.args, 'path': r'C:\Other'})):
            result = VerificationService().verify(self.app, request=request, output=self.result)
            self.assertIs(result.status, VerificationStatus.INDETERMINATE)

    def test_later_verification_is_read_only(self):
        count = self.api.SetFileInformationByHandle.call_count
        self.assertIs(self.verify(self.args, self.result).status, VerificationStatus.VERIFIED)
        self.assertEqual(self.api.SetFileInformationByHandle.call_count, count)
        self.api.ReadFile.assert_not_called()


class DeleteSessionTests(NativeFakeCase):
    def setUp(self):
        super().setUp()
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant('delete_file')
        self.policy = PolicyService(self.permissions)
        self.audit, self.undo = AuditService(), UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, ConfirmationService(), self.audit, self.undo)
        self.semantic = Mock(spec=['resolve'])
        self.semantic.resolve.return_value = IntentResolution(None, IntentSource.NONE, 0)
        resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)), semantic=self.semantic)
        self.session = ConversationSession(resolver=resolver, registry=self.registry, executor=self.executor)
        self.mapper = self.enterContext(patch.object(self.app, 'map_intent_arguments', wraps=self.app.map_intent_arguments))

    def pending(self):
        result = self.session.request(REQUEST)
        self.assertIs(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assert_all_closed()
        self.api.SetFileInformationByHandle.assert_not_called()
        return result

    def test_saved_private_binding_survives_approval_without_remap(self):
        self.pending()
        self.mapper.side_effect = AssertionError('no remap')
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.api.SetFileInformationByHandle.assert_called_once()
        self.semantic.resolve.assert_not_called()
        self.assertFalse(self.session.has_pending)
        self.assert_all_closed()

    def test_replacement_before_approval_denied_not_rebased(self):
        self.pending()
        self.fake.identity = (73, b'n' * 16)
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assertTrue(self.fake.present)

    def test_replacement_after_approval_revalidation_before_execution(self):
        self.pending()
        original = self.policy.evaluate
        def evaluate(meta):
            self.fake.identity = (73, b'n' * 16)
            return original(meta)
        with patch.object(self.policy, 'evaluate', side_effect=evaluate):
            self.assertIs(self.session.approve_pending().status, ExecutionStatus.FAILED)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assertTrue(self.fake.present)

    def test_missing_target_at_approval_denied(self):
        self.pending()
        self.fake.present = False
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_link_count_changed_at_approval_denied(self):
        self.pending()
        self.fake.links = 2
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_write_metadata_changed_at_approval_denied(self):
        self.pending()
        self.fake.write_time += 1
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_rejection_zero_mutation(self):
        self.pending()
        self.assertIs(self.session.reject_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assertTrue(self.fake.present)
        self.assertFalse(self.session.has_pending)

    def test_other_permissions_do_not_grant_delete(self):
        self.permissions.revoke('delete_file')
        for name in ('read_file', 'create_file', 'create_text_file', 'copy_file'):
            self.permissions.grant(name)
        self.assertIs(self.session.request(REQUEST).status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assert_all_closed()

    def test_policy_block_no_mutation(self):
        self.policy._blocked_capabilities.add('delete_file')
        self.assertIs(self.session.request(REQUEST).status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_revocation_before_approval(self):
        self.pending()
        self.permissions.revoke('delete_file')
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_expiry_before_approval(self):
        pending = self.pending()
        with patch('nayeon.agent.executor.datetime') as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_replay_no_second_disposition(self):
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_called_once()

    def test_changed_pending_path_denied(self):
        self.pending()
        self.session._pending.request.arguments['path'] = r'C:\Other'
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_private_evidence_in_pending_candidate_denied(self):
        self.pending()
        self.session._pending.request.arguments['_binding'] = self.prepare()['_binding']
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_model_cannot_approve_or_inject_private_binding(self):
        self.semantic.resolve.return_value = IntentResolution('delete_file', IntentSource.SEMANTIC, .95,
                                                              {'path': PATH, 'approved': True})
        self.assertIs(self.session.request('model fake').status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.session.reject_pending()
        self.semantic.resolve.return_value = IntentResolution('delete_file', IntentSource.SEMANTIC, .95,
                                                              {'path': PATH, '_binding': self.prepare()['_binding']})
        self.assertIs(self.session.request('model fake').status, ExecutionStatus.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_undo_history_untouched(self):
        callback, cleanup = Mock(), Mock()
        prior = self.undo.register(capability='prior', description='prior', callback=callback, cleanup=cleanup)
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.undo.peek(), prior)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()
        cleanup.assert_not_called()
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [e.event_type for e in self.audit.all()])

    def test_result_audit_and_verification_privacy(self):
        self.pending()
        result = self.session.approve_pending()
        public = repr(result) + repr(self.audit.all())
        for secret in (PATH, 'notes.txt', repr(IDENTITY), repr(PARENT_ID), '_binding', 'HANDLE', 'creation_time', 'write_time'):
            self.assertNotIn(secret, public)
        self.assertEqual(result.verification.reason, 'Bound deletion and target absence are confirmed.')

    def test_raw_native_error_not_leaked(self):
        self.pending()
        self.api.SetFileInformationByHandle.side_effect = OSError('secret-path Win32 private')
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn('secret-path', repr(result) + repr(self.audit.all()))

    def test_failed_disposition_executed_receipt_not_verified(self):
        self.pending()
        self.api.SetFileInformationByHandle.side_effect = lambda *args: False
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.output.disposition, fs.DeleteDisposition.NOT_ACKNOWLEDGED)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)


@unittest.skipUnless(platform.system() == 'Windows', 'Native fixture requires Windows')
class NativeDeletionTests(unittest.TestCase):
    def test_owned_fixture_real_binding_disposition_close_and_absence(self):
        root = os.path.abspath(tempfile.mkdtemp(prefix='nayeon-delete-test-'))
        path = os.path.join(root, 'victim.bin')
        self.assertEqual(os.path.dirname(os.path.abspath(path)), root)
        with open(path, 'xb') as fixture:
            fixture.write(bytes(range(32)))
        app = DeleteFileCapability()
        api = fs._kernel32()
        active = {}
        close_calls = []
        disposition_calls = []
        class NativeTrace:
            def __getattr__(self, name):
                return getattr(api, name)
            def CreateFileW(inner, *args):
                handle = api.CreateFileW(*args)
                if handle not in (None, 0, ctypes.c_void_p(-1).value):
                    if args[0] == path:
                        self.assertIn(args[1], (0x80, 0x10080))
                        self.assertEqual(args[2:6], (0, None, 3, fs._OPEN_FLAGS))
                    else:
                        self.assertEqual(args[1:6], (0x81, 1, None, 3, fs._OPEN_FLAGS))
                    active[handle] = args
                elif args[0] == path and disposition_calls:
                    self.assertTrue(any(a[0] != path for a in active.values()))
                return handle
            def CloseHandle(inner, handle):
                self.assertIn(handle, active)
                active.pop(handle)
                close_calls.append(handle)
                return api.CloseHandle(handle)
        trace = NativeTrace()
        native_set = api.SetFileInformationByHandle
        native_set.argtypes = [fs.wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, fs.wintypes.DWORD]
        native_set.restype = fs.wintypes.BOOL
        def dispose(handle, kind, value, size):
            self.assertEqual(active[handle][1], 0x10080)
            self.assertEqual((kind, size), (4, 1))
            self.assertTrue(any(a[0] != path for a in active.values()))
            disposition_calls.append(handle)
            return native_set(handle, kind, value, size)
        trace.SetFileInformationByHandle = Mock(side_effect=dispose)
        try:
            with patch.object(fs, '_kernel32', return_value=trace):
                args = app.validate_arguments({'path': path})
                self.assertFalse(active)
                self.assertEqual(args['_binding'].links, 1)
                self.assertEqual(args, app.validate_arguments({'path': path}))
                result = app.execute_structured(args)
                self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
                self.assertIs(result.source_close, fs.DeleteClose.COMPLETE)
                self.assertIs(result.observation, fs.DeleteObservation.CONFIRMED_ABSENT)
                self.assertFalse(active)
                self.assertEqual(len(disposition_calls), 1)
                self.assertFalse(os.path.exists(path))
                verified = VerificationService().verify(app, request=StructuredCapabilityRequest('owned fixture', args), output=result)
                self.assertIs(verified.status, VerificationStatus.VERIFIED)
                self.assertFalse(active)
        finally:
            # Only the owned test artifact; cleanup is not capability rollback.
            if os.path.exists(path):
                handle = api.CreateFileW(path, 0x10080, 0, None, 3, fs._OPEN_FLAGS, None)
                self.assertNotIn(handle, (None, 0, ctypes.c_void_p(-1).value))
                try:
                    fs._inspect_handle(api, handle, path, directory=False)
                    info = fs._FileDispositionInfo(1)
                    self.assertTrue(native_set(handle, 4, ctypes.byref(info), 1))
                finally:
                    self.assertTrue(api.CloseHandle(handle))
            remove = api.RemoveDirectoryW
            remove.argtypes, remove.restype = [fs.wintypes.LPCWSTR], fs.wintypes.BOOL
            self.assertTrue(remove(root))
            self.assertFalse(os.path.exists(root))
