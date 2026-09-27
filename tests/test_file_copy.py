"""Bounded binary copying, private receipts, authority flow and owned native fixture."""

import ctypes
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import hashlib
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities import copy_file
from nayeon.capabilities.copy_file import CopyFileCapability
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


SOURCE = r'C:\Source\original.bin'
DESTINATION = r'C:\Target\copy.bin'
SOURCE_ID = (73, bytes(range(1, 17)))
DESTINATION_ID = (73, bytes(range(17, 33)))
DATA = b'\x00\xff\x80\xfe\r\n\x01binary'
ARGS = {'source_path': SOURCE, 'destination_path': DESTINATION}
REQUEST = 'copy file ' + SOURCE + ' :: ' + DESTINATION


def receipt(**changes):
    return replace(fs.FileCopyResult(
        SOURCE, DESTINATION, len(DATA), fs.CopyOutcome.COMPLETE, fs.CopyFlushOutcome.COMPLETE,
        len(DATA), _source_identity=SOURCE_ID, _destination_identity=DESTINATION_ID,
        _digest=hashlib.sha256(DATA).digest()), **changes)


class FakeCopyWindows(FakeWindows):
    """Separate objects, positions and identities; assert handle lifetime at IO."""
    def __init__(self, data=DATA):
        super().__init__()
        self.contents = {SOURCE: data}
        self.sizes = {SOURCE: len(data)}
        self.identities = {SOURCE: SOURCE_ID, DESTINATION: DESTINATION_ID}
        self.offsets = {}
        self.closed = set()
        self.created = 0
        self.fail_path = None
        self.write_count = None
        self.write_success = True
        self.read_chunk = None
        self.api.GetFileInformationByHandleEx = Mock(side_effect=self.file_id)
        self.api.WriteFile = Mock(side_effect=self.write)
        self.api.FlushFileBuffers = Mock(side_effect=self.flush)
        self.api.CloseHandle.side_effect = self.close

    def open(self, path, access, share, security, disposition, flags, template):
        if path == self.fail_path:
            return ctypes.c_void_p(-1).value
        if disposition == 1:
            if path in self.contents:
                return ctypes.c_void_p(-1).value
            assert path == DESTINATION
            assert not self.closed
            assert any(event[0] == 'read' for event in self.events)
            self.created += 1
            self.contents[path] = b''
            self.sizes.setdefault(path, 0)
        handle = super().open(path, access, share, security, disposition, flags, template)
        self.offsets[handle] = 0
        return handle

    def info(self, handle, pointer):
        info = ctypes.cast(pointer, ctypes.POINTER(fs._FileInformation)).contents
        path = self.handles[handle]
        info.attributes = self.attributes.get(path, 0 if path in (SOURCE, DESTINATION) else fs._DIRECTORY)
        size = self.sizes.get(path, 0)
        info.size_low, info.size_high = size & 0xffffffff, size >> 32
        return True

    def file_id(self, handle, information_class, pointer, size):
        assert information_class == 18 and size == 24
        identity = self.identities.get(self.handles[handle], (73, b'p' * 16))
        info = ctypes.cast(pointer, ctypes.POINTER(fs._FileIdInfo)).contents
        info.volume, info.identifier[:] = identity
        self.events.append(('file_id', handle))
        return True

    def read(self, handle, buffer, size, count, overlapped):
        assert handle not in self.closed and overlapped is None
        self.events.append(('read', handle))
        position = self.offsets[handle]
        limit = size if self.read_chunk is None else min(size, self.read_chunk)
        chunk = self.contents[self.handles[handle]][position:position + limit]
        ctypes.memmove(buffer, chunk, len(chunk))
        ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = len(chunk)
        self.offsets[handle] += len(chunk)
        return True

    def write(self, handle, buffer, size, count, overlapped):
        assert self.handles[handle] == DESTINATION and not self.closed
        assert ('file_id', handle) in self.events and overlapped is None
        reported = size if self.write_count is None else self.write_count
        ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = reported
        self.contents[DESTINATION] = ctypes.string_at(buffer, min(size, reported))
        self.sizes[DESTINATION] = len(self.contents[DESTINATION])
        self.events.append(('write', handle))
        return self.write_success

    def flush(self, handle):
        assert not self.closed
        self.events.append(('flush', handle))
        return True

    def close(self, handle):
        assert handle not in self.closed
        self.closed.add(handle)
        return True


class CopyContractTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.app = CopyFileCapability(service=self.service)

    def map(self, request=REQUEST, args=None):
        return self.app.map_intent_arguments({'request': request} if args is None else args,
                                             original_request=request)

    def test_metadata(self):
        meta = self.app.capability
        self.assertEqual((meta.name, meta.service, meta.execution_mode), ('copy_file', 'filesystem', ExecutionMode.LOCAL))
        self.assertEqual(meta.intent_patterns, ('copy file ',))
        self.assertTrue(meta.requires_confirmation)
        self.assertFalse(meta.requires_llm)
        self.assertFalse(meta.reversible)

    def test_discovery_and_protocols(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(copy_file), 1)
        app = registry.get_implementation('copy_file')
        for protocol in (StructuredCapability, IntentArgumentMapper, VerificationProvider):
            self.assertIsInstance(app, protocol)
        for protocol in (UndoProvider, UnregisteredResourceProvider):
            self.assertNotIsInstance(app, protocol)

    def test_exact_prefix_separator_and_whitespace(self):
        self.assertEqual(self.map(), ARGS)
        for separator in ('::', ' :: ', '\t::\t'):
            self.assertEqual(self.map('  COPY FILE ' + SOURCE + separator + DESTINATION + '  '), ARGS)

    def test_missing_or_extra_separator_and_aliases(self):
        for request in ('copy file ' + SOURCE, REQUEST + ' :: extra', 'copy file :: ' + DESTINATION,
                        'copy file ' + SOURCE + ' :: ', REQUEST.replace('copy file ', 'copy '),
                        REQUEST.replace('copy file ', 'copy files ')):
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.map(request)

    def test_explicit_fields_override_prose_and_discard_extras(self):
        self.assertEqual(self.map(args={**ARGS, 'request': 'bad', 'overwrite': True}), ARGS)

    def test_incomplete_or_invalid_explicit_values_never_repaired(self):
        for args in ({'source_path': SOURCE}, {'destination_path': DESTINATION},
                     {'source_path': None, 'destination_path': DESTINATION},
                     {'source_path': SOURCE, 'destination_path': []}):
            self.assertEqual(self.map(args={**args, 'request': REQUEST}), args)
            with self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments(args)

    def test_original_request_binding(self):
        with self.assertRaises(ValueError):
            self.map(args={'request': REQUEST + ' '})

    def test_exact_fields_validation_is_io_free(self):
        with patch.object(fs, '_kernel32', side_effect=AssertionError('IO')):
            self.assertEqual(self.app.validate_arguments(self.map()), ARGS)
            for args in ({}, [], {**ARGS, 'overwrite': False}):
                with self.assertRaises((ValueError, TypeError)):
                    self.app.validate_arguments(args)
        self.assertEqual(self.service.mock_calls, [])

    def test_unsafe_paths_and_quotes_are_not_repaired(self):
        for path in ('', 'relative', 'C:relative', 'C:\\', r'\\host\share\x', r'\\?\C:\x',
                     r'C:\x:ads', r'C:\*.bin', r'C:\%TEMP%\x', r'C:\$env:TEMP\x',
                     r'C:\..\x', r'C:\CON', '"' + SOURCE + '"', r'C:\x.'):
            for key in ARGS:
                with self.subTest(path=path, key=key), self.assertRaises((TypeError, ValueError)):
                    self.app.validate_arguments({**ARGS, key: path})

    def test_obvious_same_path_including_case_only(self):
        for destination in (SOURCE, SOURCE.lower(), SOURCE.replace('\\', '/')):
            with self.assertRaises(ValueError):
                self.app.validate_arguments({**ARGS, 'destination_path': destination})
            with patch.object(fs, '_kernel32') as api, self.assertRaises(fs.FileCopyError):
                fs.FilesystemService().copy_file(SOURCE, destination)
            api.assert_not_called()

    def test_legacy_rejected(self):
        with self.assertRaises(fs.FileCopyError) as caught:
            self.app.execute(REQUEST)
        self.assertIs(caught.exception.failure, fs.FileCopyFailure.STRUCTURED_REQUIRED)
        self.assertEqual(self.service.mock_calls, [])

    def test_frozen_receipt_and_private_repr_no_content(self):
        result = receipt()
        with self.assertRaises(FrozenInstanceError):
            result.destination_path = 'changed'
        self.assertNotIn(DATA, vars(result).values())
        for private in (SOURCE, DESTINATION, repr(SOURCE_ID), repr(DESTINATION_ID),
                        repr(result._digest), result._digest.hex(), '_digest'):
            self.assertNotIn(private, repr(result))

    def test_verification_binds_both_paths(self):
        request = StructuredCapabilityRequest(REQUEST, ARGS)
        for output in (object(), receipt(source_path=r'C:\Other'), receipt(destination_path=r'C:\Other')):
            self.assertIs(VerificationService().verify(self.app, request=request, output=output).status,
                          VerificationStatus.INDETERMINATE)
        self.service.observe_copied_file.assert_not_called()


class CopyWindowsTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeCopyWindows()
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, 'system', return_value='Windows'))
        self.enterContext(patch.object(fs, '_kernel32', return_value=self.api))
        self.error = self.enterContext(patch.object(ctypes, 'get_last_error', return_value=5, create=True))
        self.service = fs.FilesystemService()

    def copy(self):
        return self.service.copy_file(SOURCE, DESTINATION)

    def assert_no_creation(self):
        with self.assertRaises(fs.FileCopyError) as caught:
            self.copy()
        self.assertEqual(self.fake.created, 0)
        self.api.WriteFile.assert_not_called()
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        return caught.exception

    def test_binary_read_then_one_write_and_flush_with_all_handles_retained(self):
        result = self.copy()
        self.assertEqual(self.fake.contents[SOURCE], DATA)
        self.assertEqual(self.fake.contents[DESTINATION], DATA)
        self.assertEqual(result._digest, hashlib.sha256(DATA).digest())
        self.assertEqual(result._source_identity, SOURCE_ID)
        self.assertEqual(result._destination_identity, DESTINATION_ID)
        self.assertIs(result.copy_outcome, fs.CopyOutcome.COMPLETE)
        self.assertIs(result.flush_outcome, fs.CopyFlushOutcome.COMPLETE)
        self.assertEqual(result.written_byte_count, len(DATA))
        self.api.WriteFile.assert_called_once()
        self.api.FlushFileBuffers.assert_called_once_with(self.api.WriteFile.call_args.args[0])
        opens = self.api.CreateFileW.call_args_list
        self.assertEqual([c.args for c in opens if c.args[0] == SOURCE],
                         [(SOURCE, fs._GENERIC_READ, 1, None, 3, fs._OPEN_FLAGS, None)])
        self.assertEqual(opens[-1].args, (DESTINATION, 0x40000081, 1, None, 1, 0x00300080, None))
        for c in opens:
            if c.args[0] not in (SOURCE, DESTINATION):
                self.assertEqual(c.args[1:6], (0x81, 1, None, 3, fs._OPEN_FLAGS))
        read_handles = {c.args[0] for c in self.api.ReadFile.call_args_list}
        self.assertEqual(len(read_handles), 1)
        self.assertEqual(self.fake.handles[read_handles.pop()], SOURCE)
        self.assertEqual(self.fake.closed, set(self.fake.handles))

    def test_zero_one_and_maximum_binary_size(self):
        for data in (b'', b'\xff', bytes(range(256)) * 256):
            with self.subTest(size=len(data)):
                fake = FakeCopyWindows(data)
                with patch.object(fs, '_kernel32', return_value=fake.api):
                    result = self.copy()
                self.assertEqual(fake.contents[DESTINATION], data)
                self.assertEqual(result.written_byte_count, len(data))
                self.assertIs(result.copy_outcome, fs.CopyOutcome.COMPLETE)
                self.assertEqual(fake.api.WriteFile.call_count, int(bool(data)))
                fake.api.FlushFileBuffers.assert_called_once()

    def test_oversized_source_rejected_before_read_or_create(self):
        self.fake.sizes[SOURCE] = 65537
        self.assertIs(self.assert_no_creation().failure, fs.FileCopyFailure.TOO_LARGE)
        self.api.ReadFile.assert_not_called()

    def test_missing_source(self):
        self.fake.fail_path = SOURCE
        self.error.return_value = 2
        self.assertIs(self.assert_no_creation().failure, fs.FileCopyFailure.NOT_FOUND)

    def test_directory_reparse_and_unsafe_source(self):
        for attributes in (0x10, 0x400, 0x410, 0x1000, 0x40000, 0x400000):
            with self.subTest(attributes=attributes):
                fake = FakeCopyWindows()
                fake.attributes[SOURCE] = attributes
                with patch.object(fs, '_kernel32', return_value=fake.api), self.assertRaises(fs.FileCopyError):
                    self.copy()
                self.assertEqual(fake.created, 0)
                fake.api.ReadFile.assert_not_called()

    def test_unsafe_source_and_destination_ancestors(self):
        for path in (r'C:\Source', r'C:\Target'):
            self.fake.attributes[path] = 0x410
            self.assert_no_creation()
            self.fake.attributes.clear()

    def test_wrong_source_path(self):
        self.fake.final_paths[SOURCE] = r'\\?\C:\Other'
        self.assert_no_creation()

    def test_redirected_destination_parent(self):
        self.fake.final_paths[r'C:\Target'] = r'\\?\C:\Other'
        self.assert_no_creation()

    def test_cross_volume_from_native_parent_identity_not_drive_spelling(self):
        self.fake.identities[r'C:\Target'] = (99, b'p' * 16)
        self.assertIs(self.assert_no_creation().failure, fs.FileCopyFailure.CROSS_VOLUME)
        self.api.ReadFile.assert_not_called()

    def test_missing_native_parent_volume_evidence(self):
        self.fake.identities[r'C:\Target'] = (0, b'p' * 16)
        self.assert_no_creation()

    def test_missing_source_identity(self):
        self.fake.identities[SOURCE] = (73, b'\0' * 16)
        self.assert_no_creation()

    def test_growth_detected_with_n_plus_one_ceiling(self):
        self.fake.contents[SOURCE] += b'x' * 100000
        self.assert_no_creation()
        self.assertEqual(max(self.fake.offsets.values()), len(DATA) + 1)

    def test_truncation_detected_before_creation(self):
        self.fake.contents[SOURCE] = DATA[:-1]
        self.assert_no_creation()

    def test_fragmented_reads_have_finite_call_bound_and_require_eof(self):
        self.fake.read_chunk = 1
        self.copy()
        self.assertEqual(self.api.ReadFile.call_count, len(DATA) + 1)

    def test_source_metadata_changes_after_read(self):
        original = self.fake.read
        def read(*args):
            answer = original(*args)
            self.fake.sizes[SOURCE] += 1
            return answer
        self.api.ReadFile.side_effect = read
        self.assert_no_creation()

    def test_read_failure_and_malformed_counts(self):
        def bad_count(handle, buffer, size, count, overlapped):
            ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = size + 1
            return True
        for effect in (lambda *args: False, bad_count, OSError('private read')):
            self.api.ReadFile.side_effect = effect
            self.assert_no_creation()

    def test_collision_after_successful_source_read_never_overwrites(self):
        self.fake.contents[DESTINATION] = b'existing'
        self.error.return_value = 183
        self.assertIs(self.assert_no_creation().failure, fs.FileCopyFailure.ALREADY_EXISTS)
        self.assertGreater(self.api.ReadFile.call_count, 0)
        self.assertEqual(self.fake.contents[DESTINATION], b'existing')

    def test_new_destination_identity_equal_to_source_blocks_write(self):
        self.fake.identities[DESTINATION] = SOURCE_ID
        result = self.copy()
        self.assertEqual(result.state, 'created')
        self.assertIs(result.copy_outcome, fs.CopyOutcome.UNKNOWN)
        self.api.WriteFile.assert_not_called()

    def test_invalid_created_metadata_preserves_commit_without_write(self):
        for kind in ('directory', 'wrong_path', 'nonempty', 'missing_identity', 'wrong_volume'):
            fake = FakeCopyWindows()
            if kind == 'directory':
                fake.attributes[DESTINATION] = fs._DIRECTORY
            elif kind == 'wrong_path':
                fake.final_paths[DESTINATION] = r'\\?\C:\Other'
            elif kind == 'nonempty':
                fake.sizes[DESTINATION] = 1
            elif kind == 'missing_identity':
                fake.identities[DESTINATION] = (0, b'\0' * 16)
            else:
                fake.identities[DESTINATION] = (99, DESTINATION_ID[1])
            with self.subTest(kind=kind), patch.object(fs, '_kernel32', return_value=fake.api):
                result = self.copy()
            self.assertEqual(result.state, 'created')
            self.assertIs(result.copy_outcome, fs.CopyOutcome.UNKNOWN)
            fake.api.WriteFile.assert_not_called()

    def test_short_write_preserves_count_without_continuation_or_flush(self):
        for count in (0, 1, len(DATA) - 1):
            fake = FakeCopyWindows()
            fake.write_count = count
            with patch.object(fs, '_kernel32', return_value=fake.api):
                result = self.copy()
            self.assertIs(result.copy_outcome, fs.CopyOutcome.PARTIAL)
            self.assertEqual(result.written_byte_count, count)
            self.assertIs(result.flush_outcome, fs.CopyFlushOutcome.NOT_ATTEMPTED)
            fake.api.WriteFile.assert_called_once()
            fake.api.FlushFileBuffers.assert_not_called()

    def test_false_write_is_unknown_even_if_bytes_were_written(self):
        self.fake.write_success = False
        result = self.copy()
        self.assertEqual(self.fake.contents[DESTINATION], DATA)
        self.assertIs(result.copy_outcome, fs.CopyOutcome.UNKNOWN)
        self.assertIsNone(result.written_byte_count)
        self.api.FlushFileBuffers.assert_not_called()

    def test_impossible_write_count_is_unknown(self):
        self.fake.write_count = len(DATA) + 1
        self.assertIs(self.copy().copy_outcome, fs.CopyOutcome.UNKNOWN)
        self.api.FlushFileBuffers.assert_not_called()

    def test_write_exception_preserves_creation_and_closes_every_handle(self):
        self.api.WriteFile.side_effect = OSError('private')
        result = self.copy()
        self.assertEqual(result.state, 'created')
        self.assertIs(result.copy_outcome, fs.CopyOutcome.UNKNOWN)
        self.assertEqual(self.fake.closed, set(self.fake.handles))

    def test_flush_false_or_exception_preserves_complete_copy(self):
        for effect in (lambda h: False, OSError('private')):
            fake = FakeCopyWindows()
            fake.api.FlushFileBuffers.side_effect = effect
            with patch.object(fs, '_kernel32', return_value=fake.api):
                result = self.copy()
            self.assertEqual(result.state, 'created')
            self.assertIs(result.copy_outcome, fs.CopyOutcome.COMPLETE)
            self.assertIs(result.flush_outcome, fs.CopyFlushOutcome.UNKNOWN)
            fake.api.FlushFileBuffers.assert_called_once()

    def test_postcommit_metadata_exception_preserves_creation(self):
        def inspect(handle, pointer):
            if self.fake.handles[handle] == DESTINATION:
                raise OSError('private metadata')
            return self.fake.info(handle, pointer)
        self.api.GetFileInformationByHandle.side_effect = inspect
        self.assertEqual(self.copy().state, 'created')
        self.api.WriteFile.assert_not_called()

    def test_close_failure_preserves_complete_receipt_but_invalidates_verification(self):
        def close(handle):
            self.fake.close(handle)
            return False
        self.api.CloseHandle.side_effect = close
        result = self.copy()
        self.assertIs(result.copy_outcome, fs.CopyOutcome.COMPLETE)
        self.assertIs(result.flush_outcome, fs.CopyFlushOutcome.COMPLETE)
        self.assertEqual(result.state, 'created')
        self.assertIsNone(result._destination_identity)
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        self.assertIs(self.service.observe_copied_file(result), fs.FileCreateObservation.UNKNOWN)

    def test_no_delete_rollback_or_high_level_mutation(self):
        self.fake.write_count = 1
        self.copy()
        allowed = {'GetDriveTypeW', 'CreateFileW', 'GetFileType', 'GetFileInformationByHandle',
                   'GetFileInformationByHandleEx', 'GetFinalPathNameByHandleW', 'ReadFile',
                   'WriteFile', 'FlushFileBuffers', 'CloseHandle'}
        self.assertTrue({c[0] for c in self.api.mock_calls} <= allowed)
        self.assertIn(DESTINATION, self.fake.contents)

    def test_unsupported_platform_no_native_io(self):
        with patch.object(fs.platform, 'system', return_value='Linux'), self.assertRaises(fs.FileCopyError):
            self.copy()
        self.api.CreateFileW.assert_not_called()


class CopyObservationTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeCopyWindows()
        self.fake.contents[DESTINATION] = DATA
        self.fake.sizes[DESTINATION] = len(DATA)
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, 'system', return_value='Windows'))
        self.enterContext(patch.object(fs, '_kernel32', return_value=self.api))
        self.error = self.enterContext(patch.object(ctypes, 'get_last_error', return_value=5, create=True))
        self.service = fs.FilesystemService()
        self.app = CopyFileCapability(service=self.service)

    def verify(self, result=None):
        return VerificationService().verify(self.app, request=StructuredCapabilityRequest(REQUEST, ARGS),
                                             output=receipt() if result is None else result).status

    def test_destination_matches_execution_digest_without_source_open(self):
        self.assertIs(self.verify(), VerificationStatus.VERIFIED)
        self.assertNotIn(SOURCE, self.fake.handles.values())
        self.assertEqual({self.fake.handles[c.args[0]] for c in self.api.ReadFile.call_args_list}, {DESTINATION})
        self.assertTrue(all(c.args[4] == 3 for c in self.api.CreateFileW.call_args_list))
        self.api.WriteFile.assert_not_called()
        self.api.FlushFileBuffers.assert_not_called()
        self.assertEqual(self.fake.closed, set(self.fake.handles))

    def test_source_later_changed_or_unavailable_does_not_invalidate_copy(self):
        self.fake.contents[SOURCE] = b'later changed'
        self.fake.identities[SOURCE] = (99, b'z' * 16)
        self.fake.fail_path = SOURCE
        self.assertIs(self.verify(), VerificationStatus.VERIFIED)

    def test_same_length_digest_mismatch_not_verified(self):
        self.fake.contents[DESTINATION] = b'X' + DATA[1:]
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_both_files_changed_to_same_bytes_cannot_verify(self):
        self.fake.contents[SOURCE] = self.fake.contents[DESTINATION] = b'X' * len(DATA)
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_length_mismatch_not_verified_without_read(self):
        self.fake.sizes[DESTINATION] += 1
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)
        self.api.ReadFile.assert_not_called()

    def test_destination_identity_mismatch_not_verified(self):
        self.fake.identities[DESTINATION] = (73, b'x' * 16)
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_destination_matching_source_identity_not_verified(self):
        self.fake.identities[DESTINATION] = SOURCE_ID
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)
        self.assertIs(self.verify(receipt(_destination_identity=SOURCE_ID)), VerificationStatus.NOT_VERIFIED)

    def test_trustworthy_missing_destination_not_verified(self):
        self.fake.fail_path = DESTINATION
        self.error.return_value = 2
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_missing_destination_parent_not_verified(self):
        self.fake.fail_path = r'C:\Target'
        self.error.return_value = 3
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_directory_and_unsafe_destination_not_verified(self):
        for attributes in (0x10, 0x400, 0x1000, 0x40000, 0x400000):
            self.fake.attributes[DESTINATION] = attributes
            self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_wrong_destination_final_path_not_verified(self):
        self.fake.final_paths[DESTINATION] = r'\\?\C:\Other'
        self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_unsafe_ancestor_is_indeterminate_without_read(self):
        self.fake.attributes[r'C:\Target'] = 0x410
        self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)
        self.api.ReadFile.assert_not_called()

    def test_partial_unknown_and_unflushed_receipts_indeterminate_without_observation(self):
        for result in (receipt(copy_outcome=fs.CopyOutcome.PARTIAL, written_byte_count=1),
                       receipt(copy_outcome=fs.CopyOutcome.UNKNOWN, written_byte_count=None),
                       receipt(flush_outcome=fs.CopyFlushOutcome.UNKNOWN),
                       receipt(flush_outcome=fs.CopyFlushOutcome.NOT_ATTEMPTED)):
            self.assertIs(self.verify(result), VerificationStatus.INDETERMINATE)
        self.api.CreateFileW.assert_not_called()

    def test_malformed_receipts_are_indeterminate(self):
        for changes in ({'expected_byte_count': True}, {'expected_byte_count': 65537},
                        {'written_byte_count': True}, {'written_byte_count': 1},
                        {'copy_outcome': 'complete'}, {'flush_outcome': 'complete'},
                        {'_digest': None}, {'_digest': b'bad'}, {'_digest': 'a' * 32},
                        {'_source_identity': None}, {'_destination_identity': (0, b'')},
                        {'_destination_identity': None}):
            self.assertIs(self.verify(receipt(**changes)), VerificationStatus.INDETERMINATE)
        self.api.CreateFileW.assert_not_called()

    def test_unavailable_current_identity_indeterminate(self):
        self.api.GetFileInformationByHandleEx.side_effect = None
        self.api.GetFileInformationByHandleEx.return_value = False
        self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)

    def test_access_sharing_and_other_open_errors_indeterminate(self):
        self.fake.fail_path = DESTINATION
        for error in (5, 32, 999):
            self.error.return_value = error
            self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)

    def test_growth_or_truncation_at_read_contradicts_receipt(self):
        for data in (DATA[:-1], DATA + b'growth'):
            self.fake.contents[DESTINATION] = data
            self.assertIs(self.verify(), VerificationStatus.NOT_VERIFIED)

    def test_native_read_error_or_malformed_count_indeterminate(self):
        def bad_count(handle, buffer, size, count, overlapped):
            ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = size + 1
            return True
        for effect in (lambda *args: False, OSError('private'), bad_count):
            self.api.ReadFile.side_effect = effect
            self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)

    def test_malformed_final_path_metadata_indeterminate(self):
        self.api.GetFinalPathNameByHandleW.side_effect = None
        self.api.GetFinalPathNameByHandleW.return_value = 0
        self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)

    def test_observation_close_error_indeterminate(self):
        def close(handle):
            self.fake.close(handle)
            return False
        self.api.CloseHandle.side_effect = close
        self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)
        self.assertEqual(self.fake.closed, set(self.fake.handles))

    def test_unsupported_platform_indeterminate(self):
        with patch.object(fs.platform, 'system', return_value='Linux'):
            self.assertIs(self.verify(), VerificationStatus.INDETERMINATE)
        self.api.CreateFileW.assert_not_called()


class CopySessionTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.service.copy_file.return_value = receipt()
        self.service.observe_copied_file.return_value = fs.FileCreateObservation.MATCHED
        self.app = CopyFileCapability(service=self.service)
        self.mapper = self.enterContext(patch.object(self.app, 'map_intent_arguments', wraps=self.app.map_intent_arguments))
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant('copy_file')
        self.policy = PolicyService(self.permissions)
        self.audit, self.undo = AuditService(), UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, ConfirmationService(), self.audit, self.undo)
        self.semantic = Mock(spec=['resolve'])
        self.semantic.resolve.return_value = IntentResolution(None, IntentSource.NONE, 0)
        resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)), semantic=self.semantic)
        self.session = ConversationSession(resolver=resolver, registry=self.registry, executor=self.executor)

    def pending(self):
        result = self.session.request(REQUEST)
        self.assertIs(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertEqual(self.service.mock_calls, [])
        return result

    def test_approval_exact_pair_without_remap_or_model_call(self):
        self.pending()
        self.mapper.side_effect = AssertionError('no remap')
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.service.copy_file.assert_called_once_with(SOURCE, DESTINATION)
        self.semantic.resolve.assert_not_called()
        self.assertEqual(self.undo.count(), 0)
        self.assertFalse(self.session.has_pending)

    def test_semantic_argument_snapshot_isolated_and_extras_discarded(self):
        resolution = IntentResolution('copy_file', IntentSource.SEMANTIC, .95, {**ARGS, 'overwrite': True})
        self.semantic.resolve.return_value = resolution
        self.assertIs(self.session.request('semantic fake').status, ExecutionStatus.REQUIRES_CONFIRMATION)
        resolution.arguments.update(source_path=r'C:\Other', destination_path=r'C:\OtherTarget')
        self.session.approve_pending()
        self.service.copy_file.assert_called_once_with(SOURCE, DESTINATION)

    def test_explicit_incomplete_semantics_fail_validation(self):
        self.semantic.resolve.return_value = IntentResolution('copy_file', IntentSource.SEMANTIC, .95,
                                                              {'source_path': SOURCE, 'request': REQUEST})
        self.assertIs(self.session.request('semantic fake').status, ExecutionStatus.FAILED)
        self.assertEqual(self.service.mock_calls, [])

    def test_other_permissions_do_not_grant_copy(self):
        self.permissions.revoke('copy_file')
        for name in ('read_file', 'create_file', 'create_text_file', 'create_directory'):
            self.permissions.grant(name)
        self.assertIs(self.session.request(REQUEST).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_policy_block_prevents_copy_and_verification(self):
        self.policy._blocked_capabilities.add('copy_file')
        self.assertIs(self.session.request(REQUEST).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_rejection_prevents_copy_and_verification(self):
        self.pending()
        self.session.reject_pending()
        self.assertEqual(self.service.mock_calls, [])

    def test_cancel_prevents_copy_and_verification(self):
        self.pending()
        self.session.request('cancel')
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.service.mock_calls, [])

    def test_permission_revocation_before_approval(self):
        self.pending()
        self.permissions.revoke('copy_file')
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_confirmation_expiry(self):
        pending = self.pending()
        with patch('nayeon.agent.executor.datetime') as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_confirmation_replay_cannot_copy_twice(self):
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.copy_file.assert_called_once_with(SOURCE, DESTINATION)

    def test_changed_pending_source_denies_approval(self):
        self.pending()
        self.session._pending.request.arguments['source_path'] = r'C:\Other'
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_changed_pending_destination_denies_approval(self):
        self.pending()
        self.session._pending.request.arguments['destination_path'] = r'C:\Other'
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_changed_implementation_denies_approval(self):
        self.pending()
        self.registry.unregister('copy_file')
        self.registry.register(self.app.capability, CopyFileCapability(service=self.service))
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_undo_history_and_resources_unchanged(self):
        callback, cleanup = Mock(), Mock()
        prior = self.undo.register(capability='prior', description='prior', callback=callback, cleanup=cleanup)
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.undo.peek(), prior)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()
        cleanup.assert_not_called()
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [e.event_type for e in self.audit.all()])

    def test_precommit_failure_is_failed_and_never_verified(self):
        self.service.copy_file.side_effect = fs.FileCopyError(fs.FileCopyFailure.CROSS_VOLUME)
        self.pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.FAILED)
        self.service.observe_copied_file.assert_not_called()

    def test_private_values_absent_from_audit_repr_and_verification(self):
        self.pending()
        result = self.session.approve_pending()
        public = repr(result) + repr(self.audit.all()) + repr(result.verification)
        for secret in (SOURCE, DESTINATION, repr(DATA), repr(SOURCE_ID), repr(DESTINATION_ID),
                       repr(receipt()._digest), receipt()._digest.hex(), '_digest', 'HANDLE'):
            self.assertNotIn(secret, public)

    def test_raw_service_error_redacted(self):
        self.service.copy_file.side_effect = OSError(SOURCE + receipt()._digest.hex())
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.FAILED)
        self.assertNotIn(SOURCE, repr(result) + repr(self.audit.all()))
        self.assertNotIn(receipt()._digest.hex(), repr(result) + repr(self.audit.all()))
        self.service.observe_copied_file.assert_not_called()

    def test_verifier_exception_redacted_preserving_execution(self):
        self.service.observe_copied_file.side_effect = OSError(receipt()._digest.hex())
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn(receipt()._digest.hex(), repr(result) + repr(self.audit.all()))

    def test_actual_partial_receipt_remains_executed_indeterminate(self):
        fake = FakeCopyWindows()
        fake.write_count = 1
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, 'system', return_value='Windows'), patch.object(fs, '_kernel32', return_value=fake.api):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.output.copy_outcome, fs.CopyOutcome.PARTIAL)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(fake.created, 1)
        self.assertEqual(self.undo.count(), 0)

    def test_postcommit_audit_failure_never_retries_or_rolls_back(self):
        original = self.audit.record
        def record(event, **kwargs):
            if event is AuditEventType.EXECUTION_SUCCEEDED:
                raise OSError('audit unavailable')
            return original(event, **kwargs)
        self.pending()
        with patch.object(self.audit, 'record', side_effect=record), self.assertRaises(OSError):
            self.session.approve_pending()
        self.service.copy_file.assert_called_once_with(SOURCE, DESTINATION)
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.undo.count(), 0)


@unittest.skipUnless(platform.system() == 'Windows', 'Native test requires Windows')
class NativeCopyTests(unittest.TestCase):
    def test_owned_binary_copy_no_overwrite_and_source_change_after_execution(self):
        # Cleanup is owned by this disposable test fixture, never the capability.
        with tempfile.TemporaryDirectory() as parent:
            source = Path(parent) / 'source.bin'
            destination = Path(parent) / 'destination.bin'
            source.write_bytes(DATA)
            service = fs.FilesystemService()
            result = service.copy_file(str(source), str(destination))
            self.assertEqual(source.read_bytes(), DATA)
            self.assertEqual(destination.read_bytes(), DATA)
            self.assertIs(result.copy_outcome, fs.CopyOutcome.COMPLETE)
            self.assertIs(result.flush_outcome, fs.CopyFlushOutcome.COMPLETE)
            self.assertIs(service.observe_copied_file(result), fs.FileCreateObservation.MATCHED)
            source.write_bytes(b'legitimate later change')
            self.assertIs(service.observe_copied_file(result), fs.FileCreateObservation.MATCHED)
            with self.assertRaises(fs.FileCopyError) as caught:
                service.copy_file(str(source), str(destination))
            self.assertIs(caught.exception.failure, fs.FileCopyFailure.ALREADY_EXISTS)
            self.assertEqual(destination.read_bytes(), DATA)
