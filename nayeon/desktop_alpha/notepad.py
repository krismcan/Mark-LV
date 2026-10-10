"""Personal Alpha milestone 3: one trusted local Notepad action.

The model cannot use this controller. The caller-supplied text is restricted to
one exact local command; real approval is delegated to ConversationSession's
saved confirmation candidate and existing ActionExecutor.
"""
from dataclasses import replace

from nayeon.agent.executor import ActionExecutor, ExecutionResult, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.desktop_alpha.controller import ChatOutcome, ChatReply
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.services.applications import ApplicationService
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationStatus


class NotepadController:
    """Never exposes arbitrary launch targets, prompts, tokens or platform output."""

    mode = "LOCAL NOTEPAD | APPROVAL REQUIRED"

    def __init__(self, *, session: ConversationSession, service: ApplicationService):
        if type(session) is not ConversationSession:
            raise TypeError("Exact trusted session required")
        self._session = session
        self._service = service

    @property
    def has_pending(self) -> bool:
        return self._session.has_pending

    def _registered(self) -> bool:
        try:
            value = self._service.trusted_notepad_path
            return type(value) is str and bool(value)
        except Exception:
            return False

    def send(self, text: str) -> ChatReply:
        if self.has_pending:
            return ChatReply("Resolve the pending action using the buttons first.",
                             ChatOutcome.BLOCKED)
        if type(text) is not str or len(text) > 512 or text.strip().casefold() != "open notepad":
            return ChatReply("Only the exact local command 'open notepad' is supported.",
                             ChatOutcome.BLOCKED)
        if not self._registered():
            return ChatReply("Trusted Notepad registration is unavailable. No launch attempted.",
                             ChatOutcome.BLOCKED)
        try:
            result = self._session.request("open notepad")
        except Exception:
            return ChatReply("The request failed safely. No verified action.",
                             ChatOutcome.BLOCKED)
        if (type(result) is ExecutionResult and
                result.status is ExecutionStatus.REQUIRES_CONFIRMATION and self.has_pending):
            return ChatReply("Open Notepad? Choose Approve action or Reject action.",
                             ChatOutcome.PENDING)
        # A protected action must never execute directly in this alpha.
        if type(result) is ExecutionResult and result.status is ExecutionStatus.EXECUTED:
            return ChatReply("The action did not require expected approval. Result is not trusted.",
                             ChatOutcome.BLOCKED)
        return ChatReply("Notepad request denied or unavailable.", ChatOutcome.BLOCKED)

    def approve(self) -> ChatReply:
        if not self.has_pending:
            return ChatReply("No action is awaiting approval.", ChatOutcome.BLOCKED)
        if not self._registered():
            self._session.reject_pending()
            return ChatReply("Trusted Notepad registration disappeared. Action cancelled.",
                             ChatOutcome.BLOCKED)
        try:
            result = self._session.approve_pending()
        except Exception:
            return ChatReply("Execution failed safely. Result not verified.", ChatOutcome.BLOCKED)
        if type(result) is not ExecutionResult or result.capability != "open_app":
            return ChatReply("An unexpected action result was rejected.", ChatOutcome.BLOCKED)
        if result.status is not ExecutionStatus.EXECUTED:
            return ChatReply("Notepad was not successfully launched.", ChatOutcome.BLOCKED)
        verify = result.verification
        evidence = verify.evidence
        if (verify.status is VerificationStatus.VERIFIED
                and type(evidence) is dict
                and evidence.get("application_id") == "notepad"
                and evidence.get("state") == "observed_open"
                and evidence.get("identity") == "matched"):
            return ChatReply("Notepad opened; its trusted executable identity was verified.",
                             ChatOutcome.VERIFIED)
        return ChatReply("Launch was attempted, but Notepad's identity was not verified.",
                         ChatOutcome.EXECUTED_UNVERIFIED)

    def reject(self) -> ChatReply:
        if not self.has_pending:
            return ChatReply("No action is awaiting rejection.", ChatOutcome.BLOCKED)
        try:
            result = self._session.reject_pending()
        except Exception:
            return ChatReply("Rejection was not confirmed. No verified action.",
                             ChatOutcome.BLOCKED)
        if type(result) is not ExecutionResult:
            return ChatReply("Rejection result could not be checked.", ChatOutcome.BLOCKED)
        return ChatReply("Notepad request rejected. No action launched.",
                         ChatOutcome.BLOCKED)


def build_notepad_controller(*, application_service=None) -> NotepadController:
    """Trusted host composition only; injecting a fake is solely a test seam.

    No live provider or credential reads, no automatic permission grants beyond
    this one registered local capability, and no model-selectable entry.
    """
    service = application_service if application_service is not None else ApplicationService()
    registry = CapabilityRegistry()
    app = OpenAppCapability(service=service)
    metadata = replace(app.capability, requires_confirmation=True)
    registry.register(metadata, app)
    permissions = PermissionService(default_allowed=False)
    permissions.grant("open_app")
    executor = ActionExecutor(
        registry, PolicyService(permissions), ConfirmationService(),
        AuditService(), UndoService(),
    )
    resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(registry)),
                              semantic=None)
    session = ConversationSession(resolver=resolver, registry=registry,
                                  executor=executor)
    return NotepadController(session=session, service=service)
