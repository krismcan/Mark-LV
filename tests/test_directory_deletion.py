"""Bounded empty-directory deletion: native fakes, real authority, owned fixtures."""
from copy import deepcopy
import ctypes
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import os
import platform
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus as E
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService, AuditEventType
from nayeon.capabilities import delete_directory
from nayeon.capabilities.delete_directory import DeleteDirectoryCapability
from nayeon.capabilities.loader import CapabilityLoader
from nayeon.capabilities.structured import StructuredCapabilityRequest, StructuredCapability, IntentArgumentMapper
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry, ExecutionMode
from nayeon.services import filesystem as fs
from nayeon.undo.contract import UndoProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationProvider, VerificationStatus as V
from nayeon.verification.service import VerificationService
from tests.test_file_deletion import FakeDeleteWindows, IDENTITY, PARENT_ID
from tests.test_filesystem import FakeWindows, PATH
from tests.test_directory_listing import records

TEXT = 'delete directory ' + PATH

class DirectoryWindows(FakeDeleteWindows):
    def __init__(self):
        super().__init__()
        self.attributes[PATH] = 0x10
        self.children = []
        self.batches = None
        self.enum_error = 18
        self.enumerations = []
        self.api.GetFileInformationByHandleEx.side_effect = self.query

    def open(self, path, access, share, security, disposition, flags, template):
        self.error = 0
        if path == self.fail_path or (path == PATH and (not self.present or self.pending)):
            self.error = self.fail_error if path == self.fail_path else (5 if self.pending else 2)
            return ctypes.c_void_p(-1).value
        assert disposition == 3 and flags == 0x02300000
        assert (access in (0x80, 0x81, 0x10081) and share == 0) if path == PATH else (access == 0x81 and share == 1)
        h = FakeWindows.open(self, path, access, share, security, disposition, flags, template)
        self.accesses[h] = access
        return h

    def query(self, h, kind, pointer, size):
        if kind == 18:
            return self.file_id(h, kind, pointer, size)
        assert kind in (14, 15) and size == 4096
        assert self.handles[h] == PATH and h not in self.closed
        assert self.accesses[h] in (0x81, 0x10081)
        assert sum(x not in self.closed and p != PATH for x, p in self.handles.items()) == 2
        self.enumerations.append((h, kind))
        if self.batches is not None:
            batch = self.batches.pop(0) if self.batches else None
        else:
            batch = records(*self.children) if self.children else None
        if batch is None:
            self.error = self.enum_error
            return False
        ctypes.memmove(pointer, batch, len(batch))
        return True

    def dispose(self, h, kind, pointer, size):
        assert (kind, size) == (4, 1)
        assert ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ubyte)).contents.value == 1
        assert self.accesses[h] == 0x10081 and h not in self.closed
        assert sum(x not in self.closed and p != PATH for x, p in self.handles.items()) == 2
        if self.children:
            self.error = 145
            return False
        self.pending = True
        return True

    def close(self, h):
        assert h not in self.closed
        self.closed.add(h)
        if self.handles[h] == PATH and self.accesses[h] == 0x10081:
            if self.pending and self.close_deletes:
                self.present, self.pending = False, False
            if self.replace_after_close:
                self.present, self.pending = True, False
                self.identity = (73, b'n' * 16)
        return True

class DirectoryCase(unittest.TestCase):
    def setUp(self):
        self.fake = DirectoryWindows()
        self.api = self.fake.api
        self.enterContext(patch.object(fs.platform, 'system', return_value='Windows'))
        self.enterContext(patch.object(fs, '_kernel32', return_value=self.api))
        self.enterContext(patch.object(ctypes, 'get_last_error', side_effect=lambda: self.fake.error, create=True))
        self.app = DeleteDirectoryCapability()
    def prepare(self):
        return self.app.validate_arguments({'path': PATH})
    def verify(self, args, result):
        return VerificationService().verify(self.app, request=StructuredCapabilityRequest(TEXT, args), output=result)
    def closed(self):
        self.assertEqual(set(self.fake.handles), self.fake.closed)
        self.assertEqual(self.api.CloseHandle.call_count, len(self.fake.handles))

class DirectoryDeletionContractTests(DirectoryCase):
    def test_metadata_discovery_protocols(self):
        registry = CapabilityRegistry()
        self.assertEqual(CapabilityLoader(registry)._load_module(delete_directory), 1)
        app = registry.get_implementation('delete_directory')
        meta = app.capability
        self.assertEqual((meta.name, meta.service, meta.execution_mode), ('delete_directory','filesystem',ExecutionMode.LOCAL))
        self.assertEqual(meta.description, 'Permanently delete one empty directory. Irreversible; no undo.')
        self.assertTrue(meta.requires_confirmation)
        self.assertFalse(meta.requires_llm or meta.reversible)
        for protocol in (StructuredCapability, IntentArgumentMapper, VerificationProvider):
            self.assertIsInstance(app, protocol)
        self.assertNotIsInstance(app, UndoProvider)

    def test_exact_mapping_case_whitespace(self):
        for text in (TEXT, '  DELETE DIRECTORY ' + PATH + '  '):
            self.assertEqual(self.app.map_intent_arguments({'request':text},original_request=text), {'path':PATH})
        self.api.CreateFileW.assert_not_called()

    def test_mapping_rejects_aliases_and_mismatched_original(self):
        for text in ('remove directory '+PATH,'delete folder '+PATH,'delete directories '+PATH):
            with self.assertRaises(ValueError):
                self.app.map_intent_arguments({'request':text},original_request=text)
        with self.assertRaises(ValueError):
            self.app.map_intent_arguments({'request':TEXT+'x'},original_request=TEXT)

    def test_explicit_invalid_path_never_falls_back(self):
        for path in (None,'','relative',[],'"'+PATH+'"'):
            args = self.app.map_intent_arguments({'path':path,'request':TEXT},original_request=TEXT)
            self.assertEqual(args,{'path':path})
            with self.assertRaises((TypeError,ValueError)): self.app.validate_arguments(args)
        self.api.CreateFileW.assert_not_called()

    def test_raw_schema_and_private_evidence_rejected(self):
        binding=self.prepare()['_binding']
        for args in ({},[],{'path':PATH,'recursive':True},{'path':PATH,'_binding':binding}):
            with self.assertRaises((TypeError,ValueError)): self.app.validate_arguments(args)
        with self.assertRaises(ValueError):
            self.app.map_intent_arguments({'path':PATH,'_binding':binding},original_request=TEXT)

    def test_unsafe_paths_and_root_spellings_never_open(self):
        for path in ('C:\\','C:/','C:\\\\',r'C:\.',r'C:\..',r'C:\x\..',r'\\?\C:'+'\\',
                     r'\\?\Volume{00000000-0000-0000-0000-000000000000}'+'\\','relative','C:relative',
                     r'\\host\share',r'\\.\C:\x',r'C:\x:ads',r'C:\*',r'C:\?',r'C:\%TEMP%\x',r'C:\$env:TEMP\x'):
            with self.subTest(path=path), self.assertRaises((ValueError,TypeError)):
                self.app.validate_arguments({'path':path})
        self.api.CreateFileW.assert_not_called()

    def test_binding_frozen_deepcopy_and_private(self):
        binding=self.prepare()['_binding']
        self.assertEqual(binding,deepcopy(binding))
        with self.assertRaises(FrozenInstanceError): binding.empty=False
        for secret in (PATH,repr(IDENTITY),repr(PARENT_ID),'creation_time','write_time'):
            self.assertNotIn(secret,repr(binding))

    def test_legacy_and_unvalidated_execution_rejected(self):
        with self.assertRaises(fs.DirectoryDeleteError): self.app.execute(TEXT)
        with self.assertRaises(fs.DirectoryDeleteError): self.app.execute_structured({'path':PATH})
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_preparation_has_no_mutation_and_releases_handles(self):
        args=self.prepare()
        self.assertTrue(args['_binding'].empty)
        self.assertEqual(self.api.CreateFileW.call_args_list[-1].args[1:6],(0x81,0,None,3,0x02300000))
        self.api.SetFileInformationByHandle.assert_not_called()
        self.api.ReadFile.assert_not_called()
        self.closed()

    def test_file_reparse_readonly_system_targets_rejected(self):
        for attrs in (0,0x410,0x11,0x14,0x1010,0x40010):
            self.fake.attributes[PATH]=attrs
            with self.subTest(attrs=attrs),self.assertRaises(ValueError): self.prepare()
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_readonly_system_ancestors_accepted(self):
        self.fake.attributes['C:\\']=0x16
        self.fake.attributes[r'C:\Temp']=0x11
        self.prepare()
        self.closed()

    def test_unsafe_or_changed_final_path_ancestor_rejected(self):
        self.fake.attributes[r'C:\Temp']=0x410
        with self.assertRaises(ValueError): self.prepare()
        self.fake.attributes[r'C:\Temp']=0x10
        self.fake.final_paths[PATH]=r'\\?\C:\Other'
        with self.assertRaises(ValueError): self.prepare()

    def test_native_ancestor_alias_rejected_without_delete_access(self):
        self.fake.identity=PARENT_ID
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(any(c.args[1] & 0x10000 for c in self.api.CreateFileW.call_args_list))

    def test_missing_identity_and_target_fail_closed(self):
        self.fake.present=False
        with self.assertRaises(ValueError): self.prepare()
        self.fake.present=True; self.fake.identity=(0,b'\0'*16)
        with self.assertRaises(ValueError): self.prepare()

    def test_unsupported_platform(self):
        with patch.object(fs.platform,'system',return_value='Linux'),self.assertRaises(ValueError): self.prepare()
        self.api.CreateFileW.assert_not_called()

    def test_creation_write_and_attributes_bound_access_time_excluded(self):
        original=self.prepare()
        self.fake.access_time+=1
        self.assertEqual(original,self.prepare())
        for attr in ('creation','write_time'):
            setattr(self.fake,attr,getattr(self.fake,attr)+1)
            self.assertNotEqual(original,self.prepare())
            setattr(self.fake,attr,getattr(self.fake,attr)-1)

class DirectoryEmptinessTests(DirectoryCase):
    def test_exact_dot_entries_and_normal_completion(self):
        self.fake.batches=[records(('.',0x10)),records(('..',0x10)),None]
        self.prepare()
        self.assertEqual([kind for _,kind in self.fake.enumerations],[15,14,14])
        self.assertEqual(len({h for h,_ in self.fake.enumerations}),1)

    def test_any_real_child_rejected_immediately(self):
        for name,attrs in (('file',0),('folder',0x10),('hidden',2),('system',4),('link',0x410),('...',0x10)):
            self.fake.batches=[records((name,attrs)),None]
            count=len(self.fake.enumerations)
            with self.subTest(name=name),self.assertRaises(ValueError): self.prepare()
            self.assertEqual(len(self.fake.enumerations),count+1)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_malformed_and_repeated_dot_records_fail_closed(self):
        for batch in (b'\0'*100,records(('.',0)),records(('.',0x410)),records(('\ud800',0x10))):
            self.fake.batches=[batch]
            with self.assertRaises(ValueError): self.prepare()
        self.fake.batches=[records(('.',0x10)),records(('.',0x10))]
        with self.assertRaises(ValueError): self.prepare()

    def test_no_more_files_is_only_valid_terminal_error(self):
        for code in (0,2,3,5,32,234):
            self.fake.enum_error=code
            with self.subTest(code=code),self.assertRaises(ValueError): self.prepare()

    def test_incomplete_enumeration_never_proves_empty(self):
        self.fake.batches=[records(('.',0x10)),records(('..',0x10)),None]
        self.fake.enum_error=5
        with self.assertRaises(ValueError): self.prepare()
        self.assertLessEqual(len(self.fake.enumerations),3)

class DirectoryExecutionTests(DirectoryCase):
    def test_happy_flags_abi_observation_and_verification(self):
        args=self.prepare(); result=self.app.execute_structured(args)
        self.assertIs(result.disposition,fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.target_close,fs.DeleteClose.COMPLETE)
        self.assertIs(result.observation,fs.DeleteObservation.CONFIRMED_ABSENT)
        self.assertIs(self.verify(args,result).status,V.VERIFIED)
        self.assertEqual(ctypes.sizeof(fs._FileDispositionInfo),1)
        calls=[c.args for c in self.api.CreateFileW.call_args_list if c.args[1]==0x10081]
        self.assertEqual(calls,[(PATH,0x10081,0,None,3,0x02300000,None)])
        self.api.SetFileInformationByHandle.assert_called_once()
        self.closed()

    def test_execution_preflight_root_alias_never_requests_delete(self):
        args=self.prepare(); self.fake.identity=PARENT_ID
        with self.assertRaises(fs.DirectoryDeleteError): self.app.execute_structured(args)
        self.assertFalse(any(c.args[1]&0x10000 for c in self.api.CreateFileW.call_args_list))

    def test_changed_namespace_missing_target_and_replacement(self):
        args=self.prepare()
        for attr,value in (('parent_identity',(73,b'x'*16)),('identity',(74,IDENTITY[1])),('present',False),('creation',101),('write_time',201)):
            old=getattr(self.fake,attr); setattr(self.fake,attr,value)
            with self.subTest(attr=attr),self.assertRaises(fs.DirectoryDeleteError): self.app.execute_structured(args)
            setattr(self.fake,attr,old)
        self.api.SetFileInformationByHandle.assert_not_called()

    def test_final_handle_rechecks_replacement_after_readonly_preflight(self):
        args=self.prepare(); original=self.fake.open
        def opened(*call):
            if call[1]==0x10081: self.fake.identity=(73,b'n'*16)
            return original(*call)
        self.api.CreateFileW.side_effect=opened
        with self.assertRaises(fs.DirectoryDeleteError): self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.closed()

    def test_final_handle_emptiness_rechecked(self):
        args=self.prepare(); original=self.fake.open
        def opened(*call):
            if call[1]==0x10081: self.fake.children=[('child',0)]
            return original(*call)
        self.api.CreateFileW.side_effect=opened
        with self.assertRaises(fs.DirectoryDeleteError): self.app.execute_structured(args)
        self.api.SetFileInformationByHandle.assert_not_called()
        self.assertTrue(self.fake.present)

    def test_child_file_and_directory_races_are_not_acknowledged(self):
        args=self.prepare()
        for attrs in (0,0x10):
            self.fake.children=[]
            def race(*call):
                self.fake.children=[('child',attrs)]
                return self.fake.dispose(*call)
            self.api.SetFileInformationByHandle.side_effect=race
            before=self.api.SetFileInformationByHandle.call_count
            result=self.app.execute_structured(args)
            self.assertIs(result.disposition,fs.DeleteDisposition.NOT_ACKNOWLEDGED)
            self.assertIs(self.verify(args,result).status,V.NOT_VERIFIED)
            self.assertTrue(self.fake.present)
            self.assertEqual(self.fake.children,[('child',attrs)])
            self.assertEqual(self.api.SetFileInformationByHandle.call_count,before+1)
        self.closed()

    def test_metadata_handle_delay_is_unknown_not_absence(self):
        args=self.prepare(); self.fake.close_deletes=False
        result=self.app.execute_structured(args)
        self.assertIs(result.disposition,fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.target_close,fs.DeleteClose.COMPLETE)
        self.assertIs(result.observation,fs.DeleteObservation.UNKNOWN)
        self.assertIs(self.verify(args,result).status,V.INDETERMINATE)
        self.api.SetFileInformationByHandle.assert_called_once()

    def test_ambiguous_disposition_preserves_unknown_without_retry(self):
        args=self.prepare()
        def ambiguous(*call):
            self.fake.dispose(*call); raise OSError('private Win32')
        self.api.SetFileInformationByHandle.side_effect=ambiguous
        result=self.app.execute_structured(args)
        self.assertIs(result.disposition,fs.DeleteDisposition.UNKNOWN)
        self.assertIs(self.verify(args,result).status,V.INDETERMINATE)
        self.api.SetFileInformationByHandle.assert_called_once()
        self.closed()

    def test_close_failure_and_exception_preserve_acknowledgement(self):
        for throws in (False,True):
            self.fake.present=True; self.fake.pending=False
            args=self.prepare(); native=self.fake.close
            def close(h):
                native(h)
                if self.fake.accesses[h]==0x10081:
                    if throws: raise OSError('private')
                    return False
                return True
            self.api.CloseHandle.side_effect=close
            result=self.app.execute_structured(args)
            self.assertIs(result.disposition,fs.DeleteDisposition.ACKNOWLEDGED)
            self.assertIs(result.target_close,fs.DeleteClose.UNKNOWN)
            self.assertIs(self.verify(args,result).status,V.INDETERMINATE)
            self.closed()
            self.api.CloseHandle.side_effect=native

    def test_preflight_close_failure_blocks_delete_open(self):
        args=self.prepare()
        def close(h): self.fake.close(h); return self.fake.handles[h]!=PATH
        self.api.CloseHandle.side_effect=close
        with self.assertRaises(fs.DirectoryDeleteError): self.app.execute_structured(args)
        self.assertFalse(any(c.args[1]&0x10000 for c in self.api.CreateFileW.call_args_list))
        self.closed()

    def test_ancestor_close_failure_keeps_receipt(self):
        args=self.prepare()
        def close(h): self.fake.close(h); return self.fake.handles[h]==PATH
        self.api.CloseHandle.side_effect=close
        result=self.app.execute_structured(args)
        self.assertIs(result.disposition,fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(self.verify(args,result).status,V.INDETERMINATE)
        self.closed()

    def test_observation_exception_preserves_acknowledgement(self):
        args=self.prepare()
        with patch.object(fs,'_observe_directory_deletion',side_effect=OSError('private')):
            result=self.app.execute_structured(args)
        self.assertIs(result.disposition,fs.DeleteDisposition.ACKNOWLEDGED)
        self.assertIs(result.observation,fs.DeleteObservation.UNKNOWN)

    def test_no_alternate_mutation_read_retry_or_restore(self):
        self.app.execute_structured(self.prepare())
        allowed={'CreateFileW','GetDriveTypeW','GetFileType','GetFileInformationByHandle','GetFileInformationByHandleEx','GetFinalPathNameByHandleW','CloseHandle','SetFileInformationByHandle'}
        self.assertTrue({c[0] for c in self.api.mock_calls}<=allowed)
        self.assertTrue(all(c.args[4]==3 for c in self.api.CreateFileW.call_args_list))

class DirectoryVerificationTests(DirectoryCase):
    def setUp(self):
        super().setUp(); self.args=self.prepare(); self.result=self.app.execute_structured(self.args)
    def test_different_directory_or_file_reuse_indeterminate(self):
        for attrs in (0x10,0):
            self.fake.present=True; self.fake.identity=(73,b'n'*16); self.fake.attributes[PATH]=attrs
            self.assertIs(self.verify(self.args,self.result).status,V.INDETERMINATE)
    def test_same_identity_is_trustworthy_contradiction(self):
        self.fake.present=True
        self.assertIs(self.verify(self.args,self.result).status,V.NOT_VERIFIED)
    def test_missing_or_changed_namespace_is_not_absence(self):
        self.fake.parent_identity=(73,b'n'*16)
        self.assertIs(self.verify(self.args,self.result).status,V.INDETERMINATE)
    def test_malformed_receipt_and_raw_request_indeterminate(self):
        for changes in ({'disposition':'acknowledged'},{'target_close':'complete'},{'observation':'confirmed_absent'},{'_binding':None},{'_cleanup_complete':False}):
            self.assertIs(self.verify(self.args,replace(self.result,**changes)).status,V.INDETERMINATE)
        self.assertIs(VerificationService().verify(self.app,request=TEXT,output=self.result).status,V.INDETERMINATE)
    def test_absence_never_overrides_known_failure(self):
        self.assertIs(self.verify(self.args,replace(self.result,disposition=fs.DeleteDisposition.NOT_ACKNOWLEDGED)).status,V.NOT_VERIFIED)
    def test_receipt_frozen_redacted_and_verification_readonly(self):
        with self.assertRaises(FrozenInstanceError): self.result.observation=fs.DeleteObservation.UNKNOWN
        self.assertNotIn(PATH,repr(self.result))
        count=self.api.SetFileInformationByHandle.call_count
        self.assertIs(self.verify(self.args,self.result).status,V.VERIFIED)
        self.assertEqual(count,self.api.SetFileInformationByHandle.call_count)

class DirectorySessionTests(DirectoryCase):
    def setUp(self):
        super().setUp()
        registry=CapabilityRegistry(); registry.register(self.app.capability,self.app)
        self.permissions=PermissionService(default_allowed=False); self.permissions.grant('delete_directory')
        self.policy=PolicyService(self.permissions); self.audit=AuditService(); self.undo=UndoService()
        self.executor=ActionExecutor(registry,self.policy,ConfirmationService(),self.audit,self.undo)
        self.semantic=Mock(spec=['resolve']); self.semantic.resolve.return_value=IntentResolution(None,IntentSource.NONE,0)
        resolver=IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(registry)),semantic=self.semantic)
        self.session=ConversationSession(resolver=resolver,registry=registry,executor=self.executor)
    def pending(self):
        result=self.session.request(TEXT)
        self.assertIs(result.status,E.REQUIRES_CONFIRMATION)
        self.api.SetFileInformationByHandle.assert_not_called(); self.closed()
        return result
    def test_approval_saved_binding_no_remapping(self):
        self.pending()
        with patch.object(self.app,'map_intent_arguments',side_effect=AssertionError('remap')):
            result=self.session.approve_pending()
        self.assertIs(result.status,E.EXECUTED); self.assertIs(result.verification.status,V.VERIFIED)
        self.assertFalse(self.session.has_pending); self.semantic.resolve.assert_not_called()
    def test_substitution_at_approval_denied_no_rebase(self):
        self.pending(); self.fake.identity=(73,b'n'*16)
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called(); self.assertTrue(self.fake.present)
    def test_nonempty_before_approval_denied(self):
        self.pending(); self.fake.children=[('child',0x10)]
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_nonempty_at_preparation_cannot_become_pending(self):
        self.fake.children=[('child',0)]
        self.assertIs(self.session.request(TEXT).status,E.FAILED)
        self.fake.children=[]
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_missing_at_approval_denied(self):
        self.pending(); self.fake.present=False
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_reject_zero_mutation(self):
        self.pending(); self.assertIs(self.session.reject_pending().status,E.DENIED)
        self.assertFalse(self.session.has_pending); self.assertTrue(self.fake.present)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_other_permissions_do_not_grant_directory_deletion(self):
        self.permissions.revoke('delete_directory')
        for name in ('delete_file','create_directory','list_directory','copy_file'): self.permissions.grant(name)
        self.assertIs(self.session.request(TEXT).status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_policy_block_and_revocation(self):
        self.policy._blocked_capabilities.add('delete_directory')
        self.assertIs(self.session.request(TEXT).status,E.DENIED)
        self.policy._blocked_capabilities.clear(); self.pending(); self.permissions.revoke('delete_directory')
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_expiry(self):
        pending=self.pending()
        with patch('nayeon.agent.executor.datetime') as clock:
            clock.now.return_value=pending.confirmation_request.expires_at+timedelta(seconds=1)
            self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_replay_and_undo_unchanged(self):
        callback=Mock(); prior=self.undo.register(capability='prior',description='prior',callback=callback)
        self.pending(); self.session.approve_pending()
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_called_once()
        self.assertEqual(self.undo.count(),1); self.assertIs(self.undo.peek(),prior); callback.assert_not_called()
        self.assertNotIn(AuditEventType.UNDO_REGISTERED,[e.event_type for e in self.audit.all()])
    def test_changed_pending_request_denied(self):
        self.pending(); self.session._pending.request.arguments['path']=r'C:\Other'
        self.assertIs(self.session.approve_pending().status,E.DENIED)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_model_approval_is_not_authority(self):
        self.semantic.resolve.return_value=IntentResolution('delete_directory',IntentSource.SEMANTIC,.99,{'path':PATH,'approved':True})
        self.assertIs(self.session.request('semantic fake').status,E.REQUIRES_CONFIRMATION)
        self.api.SetFileInformationByHandle.assert_not_called()
    def test_pending_result_and_audit_privacy(self):
        pending=self.pending(); result=self.session.approve_pending()
        text=repr(pending)+str(pending)+repr(result)+repr(self.audit.all())
        for private in (PATH,'notes.txt',repr(IDENTITY),repr(PARENT_ID),'_binding','creation_time','write_time','HANDLE'):
            self.assertNotIn(private,text)
        self.assertEqual(result.verification.reason,'Bound deletion and target absence are confirmed.')

@unittest.skipUnless(platform.system() == 'Windows', 'Native fixture requires Windows')
class NativeDirectoryDeletionTests(unittest.TestCase):
    def test_owned_native_success_and_child_races_with_exact_handle_lifetime(self):
        from contextlib import ExitStack
        root = fs.normalize_file_path(os.path.abspath(tempfile.mkdtemp(prefix='nayeon-directory-delete-test-')))
        raw = fs._kernel32()
        raw.CreateDirectoryW.argtypes = [fs.wintypes.LPCWSTR, ctypes.c_void_p]
        raw.CreateDirectoryW.restype = fs.wintypes.BOOL
        native_set = raw.SetFileInformationByHandle
        native_set.argtypes = [fs.wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, fs.wintypes.DWORD]
        native_set.restype = fs.wintypes.BOOL
        tracked = {}
        active = {}
        totals = [0, 0]
        attempts = []
        enumeration_handles = set()
        mode = None
        target_path = None
        class Trace:
            def __getattr__(inner, name): return getattr(raw, name)
            def CreateFileW(inner, *args):
                h = raw.CreateFileW(*args)
                if h not in (None, 0, ctypes.c_void_p(-1).value):
                    self.assertNotIn(h, active)
                    active[h] = args
                    totals[0] += 1
                    if args[0] == target_path:
                        self.assertIn(args[1], (0x80, 0x81, 0x10081))
                        self.assertEqual(args[2:6], (0, None, 3, 0x02300000))
                    else:
                        self.assertEqual(args[1:6], (0x81, 1, None, 3, 0x02300000))
                elif args[0] == target_path and attempts:
                    self.assertTrue(any(a[0] != target_path for a in active.values()))
                return h
            def CloseHandle(inner, h):
                self.assertIn(h, active)
                active.pop(h)
                ok = raw.CloseHandle(h)
                self.assertTrue(ok)
                totals[1] += 1
                return ok
            def GetFileInformationByHandleEx(inner, h, kind, pointer, size):
                if kind in (14, 15):
                    self.assertIn(h, active)
                    self.assertEqual(active[h][0], target_path)
                    self.assertIn(active[h][1], (0x81, 0x10081))
                    enumeration_handles.add(h)
                return raw.GetFileInformationByHandleEx(h, kind, pointer, size)
        def remember(path, directory):
            h = raw.CreateFileW(path, 0x80, 7, None, 3, fs._OPEN_FLAGS, None)
            self.assertNotIn(h, (None, 0, ctypes.c_void_p(-1).value))
            try:
                fs._inspect_handle(raw, h, path, directory=directory)
                identity = fs._delete_identity(raw, h)
                tracked[path] = (identity, directory)
                return identity
            finally: self.assertTrue(raw.CloseHandle(h))
        def dispose(h, kind, pointer, size):
            self.assertEqual((kind, size), (4, 1))
            self.assertEqual(active[h][1], 0x10081)
            self.assertIn(h, enumeration_handles)
            ancestors = [a for a in active.values() if a[0] != target_path]
            self.assertEqual(len(ancestors), len(target_path[3:].split('\\')))
            if mode is not None:
                child = os.path.join(target_path, 'child-dir' if mode else 'child.bin')
                if mode:
                    self.assertTrue(raw.CreateDirectoryW(child, None))
                else:
                    ch = raw.CreateFileW(child, 0x80, 7, None, 1, fs._OPEN_FLAGS, None)
                    self.assertNotIn(ch, (None, 0, ctypes.c_void_p(-1).value))
                    self.assertTrue(raw.CloseHandle(ch))
                remember(child, mode)
            ok = native_set(h, kind, pointer, size)
            error = 0 if ok else ctypes.get_last_error()
            attempts.append((bool(ok), error))
            return ok
        trace = Trace()
        trace.SetFileInformationByHandle = Mock(side_effect=dispose)
        def cleanup(path):
            self.assertTrue(path == root or path.startswith(root + '\\'))
            expected, directory = tracked[path]
            with ExitStack() as handles:
                fs._create_ancestors(raw, path, handles, lambda h: self.assertTrue(raw.CloseHandle(h)))
                h = raw.CreateFileW(path, 0x10081 if directory else 0x10080, 0, None, 3, fs._OPEN_FLAGS, None)
                self.assertNotIn(h, (None, 0, ctypes.c_void_p(-1).value))
                try:
                    fs._inspect_handle(raw, h, path, directory=directory)
                    self.assertEqual(fs._delete_identity(raw, h), expected)
                    if directory: self.assertEqual(fs._enumerate_directory(raw, h), ())
                    info = fs._FileDispositionInfo(1)
                    self.assertTrue(native_set(h, 4, ctypes.byref(info), 1))
                finally: self.assertTrue(raw.CloseHandle(h))
            self.assertFalse(os.path.exists(path))
            tracked.pop(path)
        remember(root, True)
        try:
            for mode, name in ((None, 'empty'), (False, 'file-race'), (True, 'directory-race')):
                with self.subTest(name=name):
                    target_path = os.path.join(root, name)
                    self.assertTrue(raw.CreateDirectoryW(target_path, None))
                    original = remember(target_path, True)
                    attempts.clear()
                    with patch.object(fs, '_kernel32', return_value=trace):
                        service = fs.FilesystemService()
                        binding = service.prepare_directory_deletion(target_path)
                        self.assertEqual(binding.identity, original)
                        self.assertFalse(active)
                        result = service.delete_directory(binding)
                        self.assertIs(result.target_close, fs.DeleteClose.COMPLETE)
                        self.assertFalse(active)
                        if mode is None:
                            self.assertEqual(attempts, [(True, 0)])
                            self.assertIs(result.disposition, fs.DeleteDisposition.ACKNOWLEDGED)
                            self.assertIs(result.observation, fs.DeleteObservation.CONFIRMED_ABSENT)
                            self.assertFalse(os.path.exists(target_path))
                            tracked.pop(target_path)
                        else:
                            self.assertEqual(attempts, [(False, 145)])
                            self.assertIs(result.disposition, fs.DeleteDisposition.NOT_ACKNOWLEDGED)
                            self.assertIs(result.observation, fs.DeleteObservation.PRESENT_SAME_IDENTITY)
                            for path, (identity, directory) in list(tracked.items()):
                                self.assertEqual(remember(path, directory), identity)
                    for path in sorted([p for p in tracked if p != root], key=len, reverse=True):
                        cleanup(path)
            self.assertEqual(totals[0], totals[1])
        finally:
            self.assertFalse(active)
            for path in sorted(tracked, key=len, reverse=True):
                cleanup(path)
            self.assertFalse(os.path.exists(root))
