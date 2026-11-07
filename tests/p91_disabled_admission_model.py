"""P91 fake-only service admission *specification model*, never a credential gate.

No Windows APIs, threads, IPC, native calls, persistence, keys, approval tickets,
external callbacks or production registration. This model states the ordering
rules a future qualified reviewer must require in a distinct native component.
An application MUST NOT import or compose this tests-only model as authority.
"""
from dataclasses import dataclass
from enum import Enum
from threading import get_ident
import re


class ModelDenied(RuntimeError):
    """Constant non-secret refusal. No callback or error text from a caller."""


class FakeOperation(Enum):
    SAVE_PENDING = "fake_save_pending"
    REPLACE_PENDING = "fake_replace_pending"
    DELETE_PENDING = "fake_delete_pending"


class FakeStage(Enum):
    EMPTY = "fixture_empty"
    PREPARED = "fixture_prepared"
    INTENT_RECORDED = "fixture_intent_acknowledged"
    DISPATCH_STARTED = "fixture_may_have_effected"
    NATIVE_SUCCESS = "fixture_reported_native_success"
    CLOSED_UNVERIFIED = "fixture_terminal_unverified"
    BLOCKED = "fixture_recovery_only"


_ID = re.compile(r"[a-f0-9]{32}\Z")


@dataclass(frozen=True, slots=True, repr=False)
class FakeBinding:
    """Opaque, non-secret fixture identity; never a key or key digest."""

    operation: FakeOperation
    session_fixture_id: str
    candidate_fixture_id: str

    def __post_init__(self):
        if type(self.operation) is not FakeOperation:
            raise ModelDenied("Invalid synthetic operation")
        for label in (self.session_fixture_id, self.candidate_fixture_id):
            if type(label) is not str or _ID.fullmatch(label) is None:
                raise ModelDenied("Invalid synthetic fixture identity")

    def __repr__(self):
        return "FakeBinding(<nonsecret synthetic fixture only>)"


@dataclass(frozen=True, slots=True, repr=False)
class FakeSnapshot:
    stage: FakeStage
    attempts: int
    approved: bool
    revoked: bool
    faulted: bool
    product_verified: bool = False
    production_eligible: bool = False

    def __repr__(self):
        return "FakeSnapshot(<disabled model, no custody or authority>)"


class DisabledAdmissionModel:
    """Single-owner deterministic state model; NEVER a native effect actor.

    Caller-supplied events model journal/native acknowledgements but do NOT
    persist, invoke, authenticate, or attest any underlying effect.
    """

    def __init__(self):
        self._owner_thread = get_ident()
        self._stage = FakeStage.EMPTY
        self._binding = None
        self._approved = False
        self._revoked = False
        self._faulted = False
        self._attempts = 0
        self._entered = False

    def _enter(self):
        if get_ident() != self._owner_thread or self._entered:
            raise ModelDenied("Synthetic owner-thread or reentry refusal")
        self._entered = True

    def _leave(self):
        self._entered = False

    def _deny(self):
        raise ModelDenied("Synthetic admission refused; no operation allowed")

    def prepare(self, binding: FakeBinding):
        self._enter()
        try:
            if self._stage is not FakeStage.EMPTY or type(binding) is not FakeBinding:
                self._deny()
            # Explicit service-model-owned *copy*; no caller alias is held.
            self._binding = FakeBinding(
                binding.operation, binding.session_fixture_id,
                binding.candidate_fixture_id)
            self._stage = FakeStage.PREPARED
        finally:
            self._leave()

    def synthetic_consent_fixture(self, binding: FakeBinding):
        self._enter()
        try:
            if (self._stage is not FakeStage.PREPARED or self._approved
                    or self._revoked or self._faulted or
                    type(binding) is not FakeBinding or
                    binding != self._binding):
                self._deny()
            self._approved = True
        finally:
            self._leave()

    def record_fake_durable_intent(self):
        self._enter()
        try:
            if self._stage is not FakeStage.PREPARED or not self._approved:
                self._deny()
            if self._revoked or self._faulted:
                self._deny()
            self._stage = FakeStage.INTENT_RECORDED
        finally:
            self._leave()

    def begin_fake_dispatch(self, binding: FakeBinding):
        """Record EXACTLY ONE possible attempt; performs no underlying call."""
        self._enter()
        try:
            if (self._stage is not FakeStage.INTENT_RECORDED
                    or type(binding) is not FakeBinding
                    or binding != self._binding or not self._approved
                    or self._revoked or self._faulted or self._attempts != 0):
                self._deny()
            self._attempts = 1
            self._stage = FakeStage.DISPATCH_STARTED
            return "FAKE_ATTEMPT_RECORDED__NO_EFFECT"
        finally:
            self._leave()

    def fake_native_result(self, definitely_succeeded: bool):
        self._enter()
        try:
            if self._stage is not FakeStage.DISPATCH_STARTED:
                self._deny()
            if type(definitely_succeeded) is not bool:
                self._deny()
            if definitely_succeeded and not self._revoked and not self._faulted:
                self._stage = FakeStage.NATIVE_SUCCESS
            else:
                self._faulted = True
                self._stage = FakeStage.BLOCKED
        finally:
            self._leave()

    def record_fake_terminal(self, persisted: bool):
        self._enter()
        try:
            if self._stage is not FakeStage.NATIVE_SUCCESS or type(persisted) is not bool:
                self._deny()
            if persisted and not self._revoked and not self._faulted:
                self._stage = FakeStage.CLOSED_UNVERIFIED
            else:
                self._faulted = True
                self._stage = FakeStage.BLOCKED
        finally:
            self._leave()

    def revoke_fixture_consent(self):
        self._enter()
        try:
            self._revoked = True
            self._approved = False
            if self._stage not in (FakeStage.EMPTY, FakeStage.CLOSED_UNVERIFIED):
                self._stage = FakeStage.BLOCKED
        finally:
            self._leave()

    def fault_fixture(self):
        self._enter()
        try:
            self._faulted = True
            if self._stage is not FakeStage.EMPTY:
                self._stage = FakeStage.BLOCKED
        finally:
            self._leave()

    def restart_fixture(self):
        """No trusted persistence exists: any nonempty history becomes blocked."""
        self._enter()
        try:
            if self._stage is not FakeStage.EMPTY:
                self._faulted = True
                self._approved = False
                self._stage = FakeStage.BLOCKED
        finally:
            self._leave()

    def snapshot(self):
        self._enter()
        try:
            return FakeSnapshot(self._stage, self._attempts, self._approved,
                                self._revoked, self._faulted)
        finally:
            self._leave()
