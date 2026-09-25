"""Capability-owned mapping and generic orchestration, with fake services only."""

from datetime import timedelta
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.dispatch import DispatchKind, DispatchPlan
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.orchestration import StructuredOrchestrationBridge
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService, AuditEventType
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.read_file import ReadFileCapability
from nayeon.capabilities.structured import IntentArgumentMapper, StructuredCapability, StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.services.filesystem import FileReadResult, FilesystemService
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationStatus


PATH = r"C:\Temp\notes.txt"
TEXT = "read file " + PATH


class Uncopyable:
    def __deepcopy__(self, memo):
        raise ValueError("fake-private-path-and-content")


class StructuredOnly:
    def validate_arguments(self, arguments):
        return dict(arguments)

    def execute_structured(self, arguments):
        return arguments


class SyntheticCapability(StructuredOnly):
    def map_intent_arguments(self, arguments, *, original_request):
        return {"colour": arguments["candidate"]}


class CapabilityMappingTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=FilesystemService)
        self.read = ReadFileCapability(service=self.service)
        self.application_service = Mock(spec=["launch"])
        self.app = OpenAppCapability(service=self.application_service)

    def test_protocols_are_independent_and_structural(self):
        class MapperOnly:
            def map_intent_arguments(self, arguments, *, original_request):
                raise AssertionError("detection must not invoke")
        self.assertIsInstance(MapperOnly(), IntentArgumentMapper)
        self.assertNotIsInstance(MapperOnly(), StructuredCapability)
        self.assertIsInstance(StructuredOnly(), StructuredCapability)
        self.assertNotIsInstance(StructuredOnly(), IntentArgumentMapper)
        for capability in (self.read, self.app, SyntheticCapability()):
            self.assertIsInstance(capability, IntentArgumentMapper)
            self.assertIsInstance(capability, StructuredCapability)

    def test_explicit_candidates_win_and_extras_are_discarded(self):
        for capability, field, value in ((self.app, "application", "App"), (self.read, "path", PATH)):
            with self.subTest(field=field):
                arguments = {field: value, "request": "different", "secret": "fake"}
                self.assertEqual(capability.map_intent_arguments(arguments, original_request=TEXT), {field: value})
                self.assertEqual(arguments["secret"], "fake")

    def test_invalid_explicit_candidates_are_not_validated_or_replaced(self):
        for capability, field, text in ((self.app, "application", "open App"), (self.read, "path", TEXT)):
            with patch.object(capability, "validate_arguments", side_effect=AssertionError("not mapping")):
                for value in (None, "", " ", 42, []):
                    with self.subTest(field=field, value=value):
                        self.assertEqual(capability.map_intent_arguments(
                            {field: value, "request": text}, original_request=text), {field: value})

    def test_fallback_requires_exact_untrimmed_original_text(self):
        for capability, text in ((self.app, "open App"), (self.read, TEXT)):
            for candidate in (text + " ", " " + text, "different", None):
                with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                    capability.map_intent_arguments({"request": candidate}, original_request=text)

    def test_open_app_prefixes_and_outer_whitespace_remain_compatible(self):
        for text in ("open App", " LAUNCH App ", "start App"):
            self.assertEqual(self.app.map_intent_arguments({"request": text}, original_request=text),
                             {"application": "App"})

    def test_read_file_has_only_one_local_prefix_and_does_not_parse_quotes(self):
        text = " READ FILE " + PATH + " "
        self.assertEqual(self.read.map_intent_arguments({"request": text}, original_request=text), {"path": PATH})
        quoted = 'read file "' + PATH + '"'
        self.assertEqual(self.read.map_intent_arguments({"request": quoted}, original_request=quoted),
                         {"path": '"' + PATH + '"'})
        for text in ("read " + PATH, "open " + PATH, "find notes", "read file"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.read.map_intent_arguments({"request": text}, original_request=text)

    def test_mappers_perform_no_service_io(self):
        self.read.map_intent_arguments({"request": TEXT}, original_request=TEXT)
        self.app.map_intent_arguments({"request": "open App"}, original_request="open App")
        self.assertEqual(self.service.mock_calls, [])
        self.assertEqual(self.application_service.mock_calls, [])


class GenericBridgeMappingTests(unittest.TestCase):
    def setUp(self):
        self.capability = Capability("paint", "Synthetic", ExecutionMode.LOCAL, "fake")
        self.implementation = SyntheticCapability()
        self.registry = CapabilityRegistry()
        self.registry.register(self.capability, self.implementation)
        self.executor = Mock(spec=ActionExecutor)
        self.bridge = StructuredOrchestrationBridge(registry=self.registry, executor=self.executor)
        self.plan = DispatchPlan(DispatchKind.CAPABILITY, "paint", self.capability, {"candidate": "blue"})

    def execute(self):
        return self.bridge.execute(self.plan, original_request="paint blue")

    def assert_preparation_denied(self):
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertNotIn("fake-private", result.message)
        self.executor.execute_structured.assert_not_called()
        self.executor.execute.assert_not_called()

    def replace_implementation(self, implementation):
        self.registry.unregister("paint")
        self.registry.register(self.capability, implementation)

    def test_synthetic_third_capability_uses_existing_executor(self):
        permissions = PermissionService(default_allowed=False)
        permissions.grant("paint")
        executor = ActionExecutor(self.registry, PolicyService(permissions), ConfirmationService(),
                                  AuditService(), UndoService())
        result = StructuredOrchestrationBridge(registry=self.registry, executor=executor).execute(
            self.plan, original_request="paint blue")
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.output, {"colour": "blue"})

    def test_structured_only_still_works_directly_but_not_through_bridge(self):
        self.replace_implementation(StructuredOnly())
        self.assert_preparation_denied()
        executor = ActionExecutor(self.registry, PolicyService(), ConfirmationService(), AuditService(), UndoService())
        result = executor.execute_structured(self.capability, StructuredCapabilityRequest("direct", {"colour": "blue"}))
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)

    def test_mapper_exception_is_redacted_without_fallback(self):
        with patch.object(self.implementation, "map_intent_arguments", side_effect=ValueError("fake-private")):
            self.assert_preparation_denied()

    def test_non_dict_mapper_outputs_fail_closed(self):
        for output in (None, [], "fake-private", 17, [("colour", "blue")]):
            with self.subTest(output=output), patch.object(self.implementation, "map_intent_arguments", return_value=output):
                self.assert_preparation_denied()

    def test_uncopyable_incoming_extra_fails_before_mapper(self):
        self.plan.arguments["extra"] = Uncopyable()
        with patch.object(self.implementation, "map_intent_arguments") as mapper:
            self.assert_preparation_denied()
        mapper.assert_not_called()

    def test_uncopyable_output_fails_without_executor(self):
        with patch.object(self.implementation, "map_intent_arguments", return_value={"colour": Uncopyable()}):
            self.assert_preparation_denied()

    def test_mapper_input_and_output_are_deeply_isolated(self):
        self.plan.arguments["candidate"] = {"nested": ["blue"]}
        output = {"colour": {"nested": ["green"]}}
        def mapping(arguments, *, original_request):
            self.assertEqual(original_request, "paint blue")
            arguments["candidate"]["nested"].append("changed")
            return output
        with patch.object(self.implementation, "map_intent_arguments", side_effect=mapping):
            self.execute()
        request = self.executor.execute_structured.call_args.args[1]
        output["colour"]["nested"].append("changed")
        self.assertEqual(request.arguments, {"colour": {"nested": ["green"]}})
        self.assertEqual(self.plan.arguments["candidate"], {"nested": ["blue"]})

    def test_removed_registration_during_mapping_is_denied(self):
        def mapping(*args, **kwargs):
            self.registry.unregister("paint")
            return {"colour": "blue"}
        with patch.object(self.implementation, "map_intent_arguments", side_effect=mapping):
            self.assert_preparation_denied()

    def test_replaced_implementation_during_mapping_is_denied(self):
        def mapping(*args, **kwargs):
            self.replace_implementation(SyntheticCapability())
            return {"colour": "blue"}
        with patch.object(self.implementation, "map_intent_arguments", side_effect=mapping):
            self.assert_preparation_denied()

    def test_metadata_mutation_during_mapping_is_denied(self):
        def mapping(*args, **kwargs):
            self.capability.metadata["changed"] = True
            return {"colour": "blue"}
        with patch.object(self.implementation, "map_intent_arguments", side_effect=mapping):
            self.assert_preparation_denied()

    def test_open_app_uncopyable_discarded_extra_is_conservatively_denied(self):
        app = OpenAppCapability(service=Mock(spec=["launch"]))
        self.registry.register(app.capability, app)
        plan = DispatchPlan(DispatchKind.CAPABILITY, "open_app", app.capability,
                            {"application": "App", "extra": Uncopyable()})
        result = self.bridge.execute(plan, original_request="open App")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.executor.execute_structured.assert_not_called()


class ReadFileSessionMappingTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=FilesystemService)
        self.service.read_file.return_value = FileReadResult(PATH, "fake-private-contents", 21)
        self.app = ReadFileCapability(service=self.service)
        self.mapper = self.enterContext(patch.object(self.app, "map_intent_arguments", wraps=self.app.map_intent_arguments))
        self.registry = CapabilityRegistry()
        self.registry.register(self.app.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("read_file")
        self.policy = PolicyService(self.permissions)
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, self.confirmation, self.audit, self.undo)
        self.semantic = Mock(spec=["resolve"])
        self.semantic.resolve.return_value = IntentResolution(None, IntentSource.NONE, 0)
        self.resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)), semantic=self.semantic)
        self.session = ConversationSession(resolver=self.resolver, registry=self.registry, executor=self.executor)

    def pending(self):
        result = self.session.request(TEXT)
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertTrue(self.session.has_pending)
        self.service.read_file.assert_not_called()
        return result

    def test_local_read_approval_maps_once_and_preserves_results(self):
        self.pending()
        self.semantic.resolve.assert_not_called()
        self.mapper.assert_called_once_with({"request": TEXT}, original_request=TEXT)
        self.mapper.side_effect = AssertionError("must not remap")
        with patch.object(self.resolver, "resolve", side_effect=AssertionError("must not resolve")), \
             patch.object(self.session._dispatcher, "plan", side_effect=AssertionError("must not dispatch")):
            result = self.session.approve_pending()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.output.text, "fake-private-contents")
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertFalse(self.session.has_pending)
        self.service.read_file.assert_called_once_with(PATH)
        self.assertEqual(self.mapper.call_count, 1)

    def test_semantic_explicit_path_discards_extras_and_isolates_pending(self):
        resolution = IntentResolution("read_file", IntentSource.SEMANTIC, .95,
            {"path": PATH, "request": "different", "extra": {"secret": "fake"}})
        self.semantic.resolve.return_value = resolution
        self.assertEqual(self.session.request("please read my notes").status, ExecutionStatus.REQUIRES_CONFIRMATION)
        resolution.arguments["path"] = r"C:\Other\notes.txt"
        self.session.approve_pending()
        self.service.read_file.assert_called_once_with(PATH)
        self.assertEqual(self.mapper.call_count, 1)

    def test_invalid_explicit_path_reaches_validator_without_fallback(self):
        self.semantic.resolve.return_value = IntentResolution("read_file", IntentSource.SEMANTIC, .95,
            {"path": "relative.txt", "request": TEXT})
        result = self.session.request("please read notes")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(self.audit.all()[-1].outcome, "validation_failed")
        self.service.read_file.assert_not_called()

    def test_read_rejection_does_not_call_service_or_remap(self):
        self.pending()
        self.assertEqual(self.session.reject_pending().status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()
        self.assertEqual(self.mapper.call_count, 1)

    def test_read_cancellation_does_not_call_service_or_remap(self):
        self.pending()
        self.assertEqual(self.session.request("cancel").status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.service.read_file.assert_not_called()
        self.assertEqual(self.mapper.call_count, 1)

    def test_registration_change_blocks_approval(self):
        self.pending()
        self.registry.unregister("read_file")
        self.registry.register(self.app.capability, ReadFileCapability(service=self.service))
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_replay_cannot_read_twice(self):
        self.pending()
        self.session.approve_pending()
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.read_file.assert_called_once_with(PATH)

    def test_expired_pending_read_cannot_execute(self):
        pending = self.pending()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_revoked_permission_blocks_pending_approval(self):
        self.pending()
        self.permissions.revoke("read_file")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_new_policy_block_prevents_pending_approval(self):
        self.pending()
        self.policy._blocked_capabilities.add("read_file")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_permission_denial_prevents_service(self):
        self.permissions.revoke("read_file")
        self.assertEqual(self.session.request(TEXT).status, ExecutionStatus.DENIED)
        self.service.read_file.assert_not_called()

    def test_audit_omits_path_contents_and_mapping_extras(self):
        self.pending()
        self.session.approve_pending()
        events = self.audit.all()
        self.assertNotIn(PATH, repr(events))
        self.assertNotIn("fake-private-contents", repr(events))
        self.assertEqual([e.event_type for e in events], [
            AuditEventType.POLICY_DECISION, AuditEventType.CONFIRMATION_CREATED,
            AuditEventType.CONFIRMATION_APPROVED, AuditEventType.POLICY_DECISION,
            AuditEventType.EXECUTION_STARTED, AuditEventType.EXECUTION_SUCCEEDED,
            AuditEventType.VERIFICATION_OUTCOME,
        ])

    def test_mapping_failure_has_no_execution_audit_or_private_details(self):
        self.mapper.side_effect = ValueError("fake-private-path")
        result = self.session.request(TEXT)
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertNotIn("fake-private", repr(result))
        self.assertEqual(self.audit.all(), ())
        self.service.read_file.assert_not_called()

    def test_existing_undo_entry_survives_read(self):
        callback = Mock()
        self.undo.register(capability="prior", description="prior", callback=callback)
        self.pending()
        self.session.approve_pending()
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()

    def test_text_or_model_approval_cannot_execute_pending_read(self):
        self.pending()
        self.semantic.resolve.return_value = IntentResolution("approve", IntentSource.SEMANTIC, .95)
        self.assertEqual(self.session.request("yes approve").status, ExecutionStatus.DENIED)
        self.assertTrue(self.session.has_pending)
        self.service.read_file.assert_not_called()
