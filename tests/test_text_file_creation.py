"""One-write receipts, conservative observation, real authority flow, owned fixture."""

import ctypes
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import json
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities import create_text_file
from nayeon.capabilities.create_text_file import CreateTextFileCapability
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
from tests.test_file_creation import FakeCreateWindows, IDENTITY
from tests.test_filesystem import PATH


CONTENT = "  Hello\nworld\r\n\té \U0001f600  "
DATA = CONTENT.encode("utf-8")
REQUEST = "create text file " + PATH + " :: " + json.dumps(CONTENT)


def receipt(**changes):
    return replace(fs.TextFileCreateResult(
        PATH, len(DATA), fs.TextWriteOutcome.COMPLETE, fs.TextFlushOutcome.COMPLETE,
        len(DATA), _identity=IDENTITY), **changes)


class FakeTextWindows(FakeCreateWindows):
    def __init__(self):
        super().__init__()
        self.api.WriteFile = Mock(side_effect=self.write)
        self.api.FlushFileBuffers = Mock(side_effect=self.flush)
        self.write_count = None
        self.write_success = True

    def write(self, handle, buffer, length, count, overlapped):
        assert self.handles[handle] == PATH and handle not in self.closed
        assert all(h not in self.closed for h in self.handles)
        assert ("file_id", handle) in self.events
        assert overlapped is None
        self.events.append(("write", handle))
        reported = length if self.write_count is None else self.write_count
        ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = reported
        # A FALSE return can still leave content; never assume absence of mutation.
        self.data = ctypes.string_at(buffer, min(length, max(0, reported)))
        self.size = len(self.data)
        return self.write_success

    def flush(self, handle):
        self.events.append(("flush", handle))
        assert handle not in self.closed
        return True


class TextContractTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.app = CreateTextFileCapability(service=self.service)

    def map(self, request=REQUEST, arguments=None):
        return self.app.map_intent_arguments(
            {"request": request} if arguments is None else arguments, original_request=request)

    def test_discovery_and_protocols(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(create_text_file), 1)
        app = registry.get_implementation("create_text_file")
        for protocol in (StructuredCapability, IntentArgumentMapper, VerificationProvider):
            self.assertIsInstance(app, protocol)
        for protocol in (UndoProvider, UnregisteredResourceProvider):
            self.assertNotIsInstance(app, protocol)

    def test_metadata(self):
        meta = self.app.capability
        self.assertEqual((meta.name, meta.service, meta.execution_mode),
                         ("create_text_file", "filesystem", ExecutionMode.LOCAL))
        self.assertTrue(meta.requires_confirmation)
        self.assertFalse(meta.requires_llm)
        self.assertFalse(meta.reversible)
        self.assertEqual(meta.intent_patterns, ("create text file ",))

    def test_exact_syntax_preserves_decoded_content(self):
        self.assertEqual(self.map(), {"path": PATH, "text": CONTENT})
        for content in ('"quoted" \\ backslash', 'a :: b', '\t\r\n', ' leading and trailing '):
            command = "create text file " + PATH + " :: " + json.dumps(content)
            self.assertEqual(self.map(command)["text"], content)

    def test_case_convention_and_outer_whitespace(self):
        command = "  CREATE TEXT FILE " + PATH + " :: " + json.dumps(CONTENT) + "  "
        self.assertEqual(self.map(command), {"path": PATH, "text": CONTENT})

    def test_original_binding_required(self):
        with self.assertRaises(ValueError):
            self.map(arguments={"request": REQUEST + " "})

    def test_explicit_pair_wins_and_extras_discarded(self):
        self.assertEqual(self.map(arguments={"path": PATH, "text": "explicit", "request": "bad", "encoding": "bad"}),
                         {"path": PATH, "text": "explicit"})

    def test_missing_or_invalid_explicit_values_never_repaired(self):
        for candidate in ({"path": PATH}, {"text": CONTENT}, {"path": None, "text": CONTENT},
                          {"path": PATH, "text": None}, {"path": 1}, {"text": []}):
            with self.subTest(candidate=candidate):
                mapped = self.map(arguments={**candidate, "request": REQUEST})
                self.assertEqual(mapped, candidate)
                with self.assertRaises((ValueError, TypeError)):
                    self.app.validate_arguments(mapped)

    def test_aliases_and_wrong_separators_rejected(self):
        for command in ('write text file ', 'create file ', 'make text file ', 'create text files '):
            with self.assertRaises(ValueError):
                self.map(command + PATH + ' :: "x"')
        for separator in ('::', ' ::', ':: ', ' : ', '\t::\t'):
            with self.assertRaises(ValueError):
                self.map('create text file ' + PATH + separator + '"x"')

    def test_malformed_json_and_trailing_data_rejected(self):
        for suffix in ('', '"unclosed', '"a" "b"', '"x" junk', '"\n"', '"\\q"'):
            with self.assertRaises(ValueError):
                self.map('create text file ' + PATH + ' :: ' + suffix)

    def test_non_string_json_rejected(self):
        for suffix in ('1', 'true', 'null', '[]', '{}'):
            with self.assertRaises(ValueError):
                self.map('create text file ' + PATH + ' :: ' + suffix)

    def test_path_is_not_json_decoded_or_unquoted(self):
        mapped = self.map('create text file "' + PATH + '" :: "x"')
        with self.assertRaises(ValueError):
            self.app.validate_arguments(mapped)

    def test_exact_arguments_only(self):
        for args in ({}, {"path": PATH}, {"text": CONTENT}, {"path": PATH, "text": CONTENT, "append": False}, []):
            with self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments(args)

    def test_validation_and_mapping_are_io_free(self):
        with patch.object(fs, "_kernel32", side_effect=AssertionError("IO")):
            self.assertEqual(self.app.validate_arguments(self.map()), {"path": PATH, "text": CONTENT})
        self.assertEqual(self.service.mock_calls, [])

    def test_ascii_byte_bounds(self):
        for count in (1, 65536):
            self.assertEqual(len(fs.encode_creation_text("a" * count)), count)
        for text in ("", "a" * 65537):
            with self.assertRaises(ValueError):
                fs.encode_creation_text(text)

    def test_multibyte_bounds_are_bytes_not_characters(self):
        for text in ("é" * 32768, "\U0001f600" * 16384):
            self.assertEqual(len(fs.encode_creation_text(text)), 65536)
            with self.assertRaises(ValueError):
                fs.encode_creation_text(text + "a")

    def test_lf_cr_tab_and_spaces_preserved(self):
        self.assertEqual(fs.encode_creation_text(CONTENT), DATA)
        self.assertEqual(fs.encode_creation_text("\t\r\n"), b"\t\r\n")

    def test_controls_and_invalid_unicode_rejected(self):
        for text in ('\0', '\x01', '\x0b', '\x0c', '\x1f', '\x7f', '\x80', '\x9f', '\ud800', '\udfff'):
            with self.assertRaises(ValueError):
                fs.encode_creation_text(text)
        for text in (None, b"abc", 1, [], {}):
            with self.assertRaises(TypeError):
                fs.encode_creation_text(text)

    def test_unsafe_paths_rejected_without_io(self):
        for path in ('', 'file.txt', 'C:file', 'C:\\', r'\\host\share\file', r'\\?\C:\file',
                     r'C:\Temp\..\file', r'C:\Temp\file:ads', r'C:\Temp\*.txt', r'C:\%TEMP%\x',
                     r'C:\Temp\CON', 'C:\\Temp\\file. ', 'C:\\Temp\\file.'):
            with self.assertRaises((ValueError, TypeError)):
                self.app.validate_arguments({"path": path, "text": CONTENT})
        self.assertEqual(self.service.mock_calls, [])

    def test_legacy_execution_rejected(self):
        with self.assertRaises(fs.TextFileCreateError):
            self.app.execute(REQUEST)
        self.service.create_text_file.assert_not_called()

    def test_frozen_receipt_omits_content_and_private_repr(self):
        result = receipt()
        with self.assertRaises(FrozenInstanceError):
            result.path = "changed"
        self.assertNotIn("text", vars(result))
        for secret in (PATH, CONTENT, repr(IDENTITY), "_identity"):
            self.assertNotIn(secret, repr(result))

    def test_verifier_rejects_unbound_receipts(self):
        for request, output in ((REQUEST, receipt()), (StructuredCapabilityRequest(REQUEST, {"path": PATH, "text": CONTENT}), object()),
                                (StructuredCapabilityRequest(REQUEST, {"path": PATH, "text": CONTENT}), receipt(path=r'C:\Other'))):
            result = VerificationService().verify(self.app, request=request, output=output)
            self.assertIs(result.status, VerificationStatus.INDETERMINATE)
        self.service.observe_created_text_file.assert_not_called()


class TextWindowsTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeTextWindows()
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, "system", return_value="Windows"))
        self.enterContext(patch.object(fs, "_kernel32", return_value=self.api))
        self.error = self.enterContext(patch.object(ctypes, "get_last_error", return_value=5, create=True))
        self.service = fs.FilesystemService()

    def create(self):
        return self.service.create_text_file(PATH, CONTENT)

    def assert_committed(self, result, write=fs.TextWriteOutcome.UNKNOWN, flush=fs.TextFlushOutcome.NOT_ATTEMPTED):
        self.assertEqual(result.state, "created")
        self.assertIs(result.write_outcome, write)
        self.assertIs(result.flush_outcome, flush)
        self.assertEqual(self.fake.created, 1)
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        self.assertLessEqual(self.api.WriteFile.call_count, 1)
        self.assertLessEqual(self.api.FlushFileBuffers.call_count, 1)

    def test_complete_same_handle_write_and_flush(self):
        result = self.create()
        self.assert_committed(result, fs.TextWriteOutcome.COMPLETE, fs.TextFlushOutcome.COMPLETE)
        self.assertEqual((result.expected_byte_count, result.written_byte_count), (len(DATA), len(DATA)))
        self.assertEqual(result._identity, IDENTITY)
        self.assertEqual(self.fake.data, DATA)
        handle = self.api.WriteFile.call_args.args[0]
        self.api.FlushFileBuffers.assert_called_once_with(handle)
        self.assertEqual(len(self.api.CreateFileW.call_args_list), 3)
        self.assertEqual(self.api.CreateFileW.call_args_list[-1].args,
                         (PATH, 0x40000081, 1, None, 1, 0x00300080, None))
        for call in self.api.CreateFileW.call_args_list[:-1]:
            self.assertEqual(call.args[1:6], (0x81, 1, None, 3, fs._OPEN_FLAGS))

    def test_partial_and_zero_write_never_continue_or_flush(self):
        for count in (0, 1, len(DATA) - 1):
            with self.subTest(count=count):
                fake = FakeTextWindows()
                fake.write_count = count
                with patch.object(fs, "_kernel32", return_value=fake.api):
                    result = self.create()
                self.assertIs(result.write_outcome, fs.TextWriteOutcome.PARTIAL)
                self.assertEqual(result.written_byte_count, count)
                self.assertIs(result.flush_outcome, fs.TextFlushOutcome.NOT_ATTEMPTED)
                fake.api.WriteFile.assert_called_once()
                fake.api.FlushFileBuffers.assert_not_called()
                self.assertEqual(fake.closed, set(fake.handles))

    def test_failed_write_does_not_claim_zero_mutation(self):
        self.fake.write_success = False
        result = self.create()
        self.assert_committed(result)
        self.assertIsNone(result.written_byte_count)
        self.assertEqual(self.fake.data, DATA)
        self.api.FlushFileBuffers.assert_not_called()

    def test_write_exception_returns_unknown(self):
        self.api.WriteFile.side_effect = OSError("private write failure")
        self.assert_committed(self.create())
        self.api.FlushFileBuffers.assert_not_called()

    def test_impossible_count_returns_unknown(self):
        self.fake.write_count = len(DATA) + 1
        result = self.create()
        self.assert_committed(result)
        self.assertIsNone(result.written_byte_count)
        self.api.FlushFileBuffers.assert_not_called()

    def test_flush_failure_preserves_complete_write(self):
        self.api.FlushFileBuffers.side_effect = None
        self.api.FlushFileBuffers.return_value = False
        result = self.create()
        self.assert_committed(result, fs.TextWriteOutcome.COMPLETE, fs.TextFlushOutcome.UNKNOWN)
        self.assertEqual(result.written_byte_count, len(DATA))

    def test_flush_exception_preserves_complete_write(self):
        self.api.FlushFileBuffers.side_effect = OSError("private flush failure")
        self.assert_committed(self.create(), fs.TextWriteOutcome.COMPLETE, fs.TextFlushOutcome.UNKNOWN)

    def test_missing_parent_fails_before_creation(self):
        self.fake.fail_path = r'C:\Temp'
        self.error.return_value = 3
        with self.assertRaises(fs.TextFileCreateError) as caught:
            self.create()
        self.assertIs(caught.exception.failure, fs.TextFileCreateFailure.NOT_FOUND)
        self.assertEqual(self.fake.created, 0)
        self.api.WriteFile.assert_not_called()

    def test_unsafe_ancestors_never_create(self):
        for attribute in (0x410, 0x1010, 0x40010, 0x400010, 0):
            with self.subTest(attribute=attribute):
                fake = FakeTextWindows()
                fake.attributes[r'C:\Temp'] = attribute
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.TextFileCreateError):
                    self.create()
                self.assertEqual(fake.created, 0)
                fake.api.WriteFile.assert_not_called()
                self.assertEqual(fake.closed, set(fake.handles))

    def test_redirected_parent_never_creates(self):
        self.fake.final_paths[r'C:\Temp'] = r'\\?\C:\Elsewhere'
        with self.assertRaises(fs.TextFileCreateError):
            self.create()
        self.assertEqual(self.fake.created, 0)

    def test_existing_target_and_other_create_failures(self):
        self.fake.fail_path = PATH
        for code, failure in ((80, fs.TextFileCreateFailure.ALREADY_EXISTS), (183, fs.TextFileCreateFailure.ALREADY_EXISTS),
                              (5, fs.TextFileCreateFailure.ACCESS_DENIED), (32, fs.TextFileCreateFailure.BUSY),
                              (999, fs.TextFileCreateFailure.CREATE_ERROR)):
            with self.subTest(code=code):
                fake = FakeTextWindows()
                fake.fail_path = PATH
                self.error.return_value = code
                with patch.object(fs, "_kernel32", return_value=fake.api), self.assertRaises(fs.TextFileCreateError) as caught:
                    self.create()
                self.assertIs(caught.exception.failure, failure)
                self.assertNotIn(PATH, str(caught.exception))
                self.assertEqual(fake.created, 0)
                fake.api.WriteFile.assert_not_called()

    def test_created_handle_contradiction_stops_write_but_keeps_creation(self):
        for attribute in (fs._DIRECTORY, 0x400, 0x1000, 0x40000, 0x400000):
            fake = FakeTextWindows()
            fake.attributes[PATH] = attribute
            with patch.object(fs, "_kernel32", return_value=fake.api):
                result = self.create()
            self.assertEqual(result.state, "created")
            self.assertIs(result.write_outcome, fs.TextWriteOutcome.UNKNOWN)
            fake.api.WriteFile.assert_not_called()

    def test_created_handle_wrong_path_stops_write(self):
        self.fake.final_paths[PATH] = r'\\?\C:\Other'
        self.assert_committed(self.create())
        self.api.WriteFile.assert_not_called()

    def test_nonempty_created_handle_stops_write(self):
        self.fake.size = 1
        self.assert_committed(self.create())
        self.api.WriteFile.assert_not_called()

    def test_created_identity_unavailable_stops_write(self):
        self.api.GetFileInformationByHandleEx.side_effect = None
        self.api.GetFileInformationByHandleEx.return_value = False
        self.assert_committed(self.create())
        self.api.WriteFile.assert_not_called()

    def test_postcommit_metadata_exceptions_return_receipt(self):
        for method_name in ('GetFileType', 'GetFileInformationByHandle', 'GetFinalPathNameByHandleW', 'GetFileInformationByHandleEx'):
            fake = FakeTextWindows()
            method = getattr(fake.api, method_name)
            original = method.side_effect
            def inspect(handle, *args):
                if fake.handles[handle] == PATH:
                    raise OSError("private metadata")
                return original(handle, *args) if original else 1
            method.side_effect = inspect
            with patch.object(fs, "_kernel32", return_value=fake.api):
                result = self.create()
            self.assertEqual(result.state, "created")
            self.assertIs(result.write_outcome, fs.TextWriteOutcome.UNKNOWN)
            self.assertEqual(fake.created, 1)
            self.assertEqual(fake.closed, set(fake.handles))
            fake.api.WriteFile.assert_not_called()

    def test_final_metadata_failure_preserves_write_and_flush(self):
        original = self.fake.file_id
        def file_id(*args):
            if self.api.WriteFile.called:
                raise OSError("private final metadata")
            return original(*args)
        self.api.GetFileInformationByHandleEx.side_effect = file_id
        result = self.create()
        self.assert_committed(result, fs.TextWriteOutcome.COMPLETE, fs.TextFlushOutcome.COMPLETE)
        self.assertIsNone(result._identity)

    def test_final_identity_change_invalidates_creation_evidence(self):
        original = self.fake.flush
        def flush(handle):
            self.fake.identity = (74, IDENTITY[1])
            return original(handle)
        self.api.FlushFileBuffers.side_effect = flush
        result = self.create()
        self.assert_committed(result, fs.TextWriteOutcome.COMPLETE, fs.TextFlushOutcome.COMPLETE)
        self.assertIsNone(result._identity)

    def test_precommit_native_exception_is_typed_without_mutation(self):
        self.api.CreateFileW.side_effect = OSError('private path and OS error')
        with self.assertRaises(fs.TextFileCreateError) as caught:
            self.create()
        self.assertEqual(self.fake.created, 0)
        self.assertNotIn('private', str(caught.exception))
        self.api.WriteFile.assert_not_called()

    def test_close_failure_or_exception_preserves_commit_and_attempts_all(self):
        for raises in (False, True):
            fake = FakeTextWindows()
            def close(handle):
                fake.close(handle)
                if raises:
                    raise OSError("private close")
                return False
            fake.api.CloseHandle.side_effect = close
            with patch.object(fs, "_kernel32", return_value=fake.api):
                result = self.create()
            self.assertEqual(result.state, "created")
            self.assertIs(result.write_outcome, fs.TextWriteOutcome.COMPLETE)
            self.assertIsNone(result._identity)
            self.assertEqual(fake.closed, set(fake.handles))

    def test_invalid_input_never_loads_windows_api(self):
        with patch.object(fs, "_kernel32") as api:
            for path, text in (("relative", CONTENT), (PATH, ''), (PATH, '\0'), (PATH, '\ud800'), (PATH, 'x' * 65537)):
                with self.assertRaises(fs.TextFileCreateError):
                    self.service.create_text_file(path, text)
            api.assert_not_called()

    def test_nonwindows_never_loads_api(self):
        with patch.object(fs.platform, "system", return_value="Linux"), patch.object(fs, "_kernel32") as api:
            with self.assertRaises(fs.TextFileCreateError) as caught:
                self.create()
            self.assertIs(caught.exception.failure, fs.TextFileCreateFailure.UNSUPPORTED_PLATFORM)
            api.assert_not_called()

    def test_only_allowed_native_calls_no_high_level_mutation(self):
        with patch('builtins.open', side_effect=AssertionError('no open')), \
             patch.object(Path, 'write_text', side_effect=AssertionError('no write_text')), \
             patch('os.open', side_effect=AssertionError('no os.open')), \
             patch('subprocess.Popen', side_effect=AssertionError('no shell')):
            self.create()
        allowed = {'GetDriveTypeW', 'CreateFileW', 'GetFileType', 'GetFileInformationByHandle',
                   'GetFileInformationByHandleEx', 'GetFinalPathNameByHandleW', 'WriteFile',
                   'FlushFileBuffers', 'CloseHandle'}
        self.assertTrue({call[0] for call in self.api.mock_calls} <= allowed)


class TextObservationTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeTextWindows()
        self.fake.data, self.fake.size = DATA, len(DATA)
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, 'system', return_value='Windows'))
        self.enterContext(patch.object(fs, '_kernel32', return_value=self.api))
        self.error = self.enterContext(patch.object(ctypes, 'get_last_error', return_value=5, create=True))
        self.service = fs.FilesystemService()

    def observe(self, result=None):
        return self.service.observe_created_text_file(receipt() if result is None else result, CONTENT)

    def test_exact_identity_content_length_match(self):
        self.assertIs(self.observe(), fs.FileCreateObservation.MATCHED)
        handle = self.api.ReadFile.call_args.args[0]
        self.assertEqual({call.args[0] for call in self.api.ReadFile.call_args_list}, {handle})
        self.assertEqual(self.api.ReadFile.call_args_list[0].args[2], len(DATA) + 1)
        self.assertEqual(self.fake.closed, set(self.fake.handles))
        self.api.WriteFile.assert_not_called()
        self.api.FlushFileBuffers.assert_not_called()
        self.assertTrue(all(call.args[4] == 3 for call in self.api.CreateFileW.call_args_list))

    def test_missing_target_is_contradiction(self):
        self.fake.fail_path = PATH
        self.error.return_value = 2
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_missing_parent_is_contradiction(self):
        self.fake.fail_path = r'C:\Temp'
        self.error.return_value = 3
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_identity_mismatch_is_contradiction(self):
        self.fake.identity = (74, IDENTITY[1])
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)
        self.api.ReadFile.assert_not_called()

    def test_same_length_different_bytes_is_contradiction(self):
        self.fake.data = b'X' + DATA[1:]
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_length_difference_is_contradiction_without_read(self):
        self.fake.size += 1
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)
        self.api.ReadFile.assert_not_called()

    def test_read_detects_extra_data_despite_reported_size(self):
        self.fake.data += b'x' * 100000
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)
        self.assertEqual(self.fake.offset, len(DATA) + 1)

    def test_early_eof_is_contradiction(self):
        self.fake.data = DATA[:-1]
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_unsafe_or_directory_target_is_contradiction(self):
        for attributes in (0x10, 0x400, 0x1000, 0x40000, 0x400000):
            self.fake.attributes[PATH] = attributes
            self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_wrong_final_path_is_contradiction(self):
        self.fake.final_paths[PATH] = r'\\?\C:\Elsewhere'
        self.assertIs(self.observe(), fs.FileCreateObservation.CHANGED)

    def test_access_conflict_is_inconclusive(self):
        self.fake.fail_path = PATH
        for code in (5, 32, 999):
            self.error.return_value = code
            self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_unsafe_ancestor_is_inconclusive(self):
        self.fake.attributes[r'C:\Temp'] = 0x410
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.api.ReadFile.assert_not_called()

    def test_missing_creation_identity_cannot_verify(self):
        self.assertIs(self.observe(receipt(_identity=None)), fs.FileCreateObservation.UNKNOWN)
        self.api.ReadFile.assert_not_called()

    def test_unavailable_current_identity_cannot_verify(self):
        self.api.GetFileInformationByHandleEx.side_effect = None
        self.api.GetFileInformationByHandleEx.return_value = False
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_partial_unknown_and_unflushed_receipts_cannot_verify(self):
        for result in (receipt(write_outcome=fs.TextWriteOutcome.PARTIAL, written_byte_count=1, flush_outcome=fs.TextFlushOutcome.NOT_ATTEMPTED),
                       receipt(write_outcome=fs.TextWriteOutcome.UNKNOWN, written_byte_count=None, flush_outcome=fs.TextFlushOutcome.NOT_ATTEMPTED),
                       receipt(flush_outcome=fs.TextFlushOutcome.UNKNOWN)):
            self.fake.offset = 0
            self.assertIs(self.observe(result), fs.FileCreateObservation.UNKNOWN)

    def test_partial_with_observed_contradiction_is_not_verified(self):
        self.fake.data, self.fake.size = b'x', 1
        self.assertIs(self.observe(receipt(write_outcome=fs.TextWriteOutcome.PARTIAL, written_byte_count=1,
                                           flush_outcome=fs.TextFlushOutcome.NOT_ATTEMPTED)), fs.FileCreateObservation.CHANGED)

    def test_malformed_receipts_cannot_verify(self):
        for result in (receipt(write_outcome='complete'), receipt(flush_outcome='complete'),
                       receipt(expected_byte_count=True), receipt(written_byte_count=True), receipt(_identity=(0, b''))):
            self.fake.offset = 0
            self.assertIs(self.observe(result), fs.FileCreateObservation.UNKNOWN)

    def test_malformed_or_truncated_path_is_inconclusive(self):
        self.api.GetFinalPathNameByHandleW.side_effect = None
        for count in (0, 264, 300):
            self.api.GetFinalPathNameByHandleW.return_value = count
            self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_read_failure_and_impossible_count_inconclusive(self):
        def bad_count(handle, buffer, size, count, overlapped):
            ctypes.cast(count, ctypes.POINTER(fs.wintypes.DWORD)).contents.value = size + 1
            return True
        for effect in (OSError('private'), bad_count, lambda *args: False):
            self.api.ReadFile.side_effect = effect
            self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)

    def test_unsupported_platform_is_inconclusive(self):
        with patch.object(fs.platform, 'system', return_value='Linux'):
            self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.api.CreateFileW.assert_not_called()

    def test_close_diagnostics_make_observation_inconclusive_and_close_all(self):
        def close(handle):
            self.fake.close(handle)
            return False
        self.api.CloseHandle.side_effect = close
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.assertEqual(self.fake.closed, set(self.fake.handles))

    def test_non_disk_and_malformed_identity_never_read(self):
        self.api.GetFileType.return_value = 2
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.api.ReadFile.assert_not_called()
        self.api.GetFileType.return_value = 1
        self.fake.identity = (0, b'\0' * 16)
        self.assertIs(self.observe(), fs.FileCreateObservation.UNKNOWN)
        self.api.ReadFile.assert_not_called()


class TextSessionTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=fs.FilesystemService)
        self.service.create_text_file.return_value = receipt()
        self.service.observe_created_text_file.return_value = fs.FileCreateObservation.MATCHED
        self.app = CreateTextFileCapability(service=self.service)
        self.mapper = self.enterContext(patch.object(self.app, 'map_intent_arguments', wraps=self.app.map_intent_arguments))
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant('create_text_file')
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

    def test_approval_exact_content_without_remap(self):
        self.pending()
        self.mapper.side_effect = AssertionError('no remap')
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.VERIFIED)
        self.service.create_text_file.assert_called_once_with(PATH, CONTENT)
        self.semantic.resolve.assert_not_called()
        self.assertEqual(self.undo.count(), 0)
        self.assertFalse(self.session.has_pending)

    def test_semantic_snapshot_preserves_both_fields_and_discards_extras(self):
        resolution = IntentResolution('create_text_file', IntentSource.SEMANTIC, .95,
                                      {'path': PATH, 'text': CONTENT, 'encoding': 'bad'})
        self.semantic.resolve.return_value = resolution
        self.assertIs(self.session.request('semantic fake').status, ExecutionStatus.REQUIRES_CONFIRMATION)
        resolution.arguments.update(path=r'C:\Other', text='other')
        self.session.approve_pending()
        self.service.create_text_file.assert_called_once_with(PATH, CONTENT)

    def test_explicit_incomplete_semantics_fail_validation(self):
        self.semantic.resolve.return_value = IntentResolution('create_text_file', IntentSource.SEMANTIC, .95,
                                                              {'path': PATH, 'request': REQUEST})
        self.assertIs(self.session.request('semantic fake').status, ExecutionStatus.FAILED)
        self.assertEqual(self.audit.all()[-1].outcome, 'validation_failed')
        self.assertEqual(self.service.mock_calls, [])

    def test_other_permissions_do_not_grant_creation(self):
        self.permissions.revoke('create_text_file')
        for name in ('read_file', 'list_directory', 'create_file', 'create_directory'):
            self.permissions.grant(name)
        self.assertIs(self.session.request(REQUEST).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_policy_blocks_creation(self):
        self.policy._blocked_capabilities.add('create_text_file')
        self.assertIs(self.session.request(REQUEST).status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_rejection_no_mutation_or_verification(self):
        self.pending()
        self.session.reject_pending()
        self.assertEqual(self.service.mock_calls, [])

    def test_cancel_no_mutation_or_verification(self):
        self.pending()
        self.session.request('cancel')
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.service.mock_calls, [])

    def test_expired_confirmation_no_mutation(self):
        pending = self.pending()
        with patch('nayeon.agent.executor.datetime') as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_revoked_permission_blocks_approval(self):
        self.pending()
        self.permissions.revoke('create_text_file')
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_changed_registration_blocks_approval(self):
        self.pending()
        self.registry.unregister('create_text_file')
        self.registry.register(self.app.capability, CreateTextFileCapability(service=self.service))
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_replay_cannot_create_twice(self):
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.create_text_file.assert_called_once_with(PATH, CONTENT)

    def test_changed_pending_text_denies_approval(self):
        self.pending()
        self.session._pending.request.arguments['text'] = 'different'
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertEqual(self.service.mock_calls, [])

    def test_prior_undo_resource_untouched(self):
        callback, cleanup = Mock(), Mock()
        prior = self.undo.register(capability='prior', description='prior', callback=callback, cleanup=cleanup)
        self.pending()
        self.session.approve_pending()
        self.assertIs(self.undo.peek(), prior)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()
        cleanup.assert_not_called()

    def test_precommit_failure_is_failed_without_verification(self):
        self.service.create_text_file.side_effect = fs.TextFileCreateError(fs.TextFileCreateFailure.ALREADY_EXISTS)
        self.pending()
        self.assertIs(self.session.approve_pending().status, ExecutionStatus.FAILED)
        self.service.observe_created_text_file.assert_not_called()

    def test_verifier_failure_preserves_execution_and_redacts(self):
        self.service.observe_created_text_file.side_effect = OSError(CONTENT)
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn(CONTENT, repr(result))

    def test_raw_execution_exception_redacted(self):
        self.service.create_text_file.side_effect = OSError('private Win32 ' + CONTENT)
        self.pending()
        result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.FAILED)
        self.assertNotIn('private Win32', repr(result) + repr(self.audit.all()))
        self.service.observe_created_text_file.assert_not_called()

    def test_audit_and_results_omit_sensitive_values(self):
        self.pending()
        result = self.session.approve_pending()
        combined = repr(result) + repr(self.audit.all())
        for secret in (PATH, CONTENT, json.dumps(CONTENT), repr(DATA), repr(IDENTITY), '_identity', 'HANDLE'):
            self.assertNotIn(secret, combined)
        self.assertNotIn(AuditEventType.UNDO_REGISTERED, [e.event_type for e in self.audit.all()])

    def test_real_partial_receipt_remains_executed_with_contradiction(self):
        fake = FakeTextWindows()
        fake.write_count = 1
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, 'system', return_value='Windows'), patch.object(fs, '_kernel32', return_value=fake.api):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.output.write_outcome, fs.TextWriteOutcome.PARTIAL)
        self.assertIs(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(fake.created, 1)

    def test_real_unknown_receipt_remains_executed(self):
        fake = FakeTextWindows()
        fake.api.WriteFile.side_effect = OSError('private write')
        self.app._service = fs.FilesystemService()
        with patch.object(fs.platform, 'system', return_value='Windows'), patch.object(fs, '_kernel32', return_value=fake.api):
            self.pending()
            result = self.session.approve_pending()
        self.assertIs(result.status, ExecutionStatus.EXECUTED)
        self.assertIs(result.output.write_outcome, fs.TextWriteOutcome.UNKNOWN)
        self.assertIs(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(fake.created, 1)

    def test_postcommit_audit_failure_does_not_retry_or_undo(self):
        original = self.audit.record
        def record(event, **kwargs):
            if event is AuditEventType.EXECUTION_SUCCEEDED:
                raise OSError('audit sink unavailable')
            return original(event, **kwargs)
        self.pending()
        with patch.object(self.audit, 'record', side_effect=record), self.assertRaises(OSError):
            self.session.approve_pending()
        self.service.create_text_file.assert_called_once_with(PATH, CONTENT)
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.undo.count(), 0)


@unittest.skipUnless(platform.system() == 'Windows', 'Native test requires Windows')
class NativeTextCreationTests(unittest.TestCase):
    def test_owned_child_exact_utf8_and_no_overwrite(self):
        # Removal belongs exclusively to this test fixture, never the capability.
        with tempfile.TemporaryDirectory() as parent:
            child = Path(parent) / 'nayeon-text.txt'
            self.assertFalse(child.exists())
            service = fs.FilesystemService()
            result = service.create_text_file(str(child), CONTENT)
            self.assertEqual(child.read_bytes(), DATA)
            self.assertEqual(result.state, 'created')
            self.assertIs(result.write_outcome, fs.TextWriteOutcome.COMPLETE)
            self.assertIs(result.flush_outcome, fs.TextFlushOutcome.COMPLETE)
            app = CreateTextFileCapability(service=service)
            verified = VerificationService().verify(app, request=StructuredCapabilityRequest(
                'owned fixture', {'path': str(child), 'text': CONTENT}), output=result)
            self.assertIs(verified.status, VerificationStatus.VERIFIED)
            with self.assertRaises(fs.TextFileCreateError) as caught:
                service.create_text_file(str(child), 'different')
            self.assertIs(caught.exception.failure, fs.TextFileCreateFailure.ALREADY_EXISTS)
            self.assertEqual(child.read_bytes(), DATA)
