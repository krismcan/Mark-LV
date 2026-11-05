"""PRIVATE test harness: content-free synthetic origin/redaction experiment.

No OS attestation, permission issuance, content accessor or product export.
Underscored methods are trusted inert test setup, never application APIs.
Python reflection/monkeypatching/malicious trusted memory access is outside
this in-process experiment. Clearing references is not memory zeroization.
"""
from dataclasses import dataclass
from enum import Enum
import re
from threading import RLock

from nayeon.perception.contracts import (
    ObservationRequest, ObservationSource, ObservationPurpose,
)
from tests.phase10_3_independent_redaction_oracle import OracleStatus, verify_fixture

MAX_RECORDS = 32
MAX_GENERATION = 256
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z", re.ASCII)


class FixtureStatus(str, Enum):
    READY = "synthetic_ready"
    ISSUED = "synthetic_issued"
    CONSUMED = "synthetic_consumed"
    INVALIDATED = "synthetic_invalidated"
    DENIED = "synthetic_denied"
    CLOSED = "synthetic_closed"


class _Hidden:
    __slots__ = ()

    def __repr__(self):
        return "<synthetic-private>"

    __str__ = __repr__

    def __reduce__(self):
        raise TypeError("Synthetic serialization refused")

    def __reduce_ex__(self, protocol):
        raise TypeError("Synthetic serialization refused")

    def __copy__(self):
        raise TypeError("Synthetic serialization refused")

    def __deepcopy__(self, memo):
        raise TypeError("Synthetic serialization refused")


class _Handle(_Hidden):
    __slots__ = ()


@dataclass(frozen=True, slots=True, repr=False)
class _Scope(_Hidden):
    request: ObservationRequest
    target_id: str
    operation: _Handle
    fixture_id: str
    source_identity: _Handle
    registry_identity: _Handle
    source_generation: int
    observation_generation: int
    policy_version: int


@dataclass(frozen=True, slots=True, repr=False)
class _Proposal(_Hidden):
    source: tuple
    classifications: tuple
    output: tuple


@dataclass(slots=True, repr=False)
class _Record(_Hidden):
    scope: _Scope | None
    proposal: _Proposal | None
    state: FixtureStatus = FixtureStatus.ISSUED


def _proposal(fixture_id):
    # Generator-owned source/classification, independent of oracle truth.
    if fixture_id == "single":
        cells, labels = (("SECRET_A",),), (("SENSITIVE",),)
    elif fixture_id == "small":
        cells = (("SAFE_A", "SECRET_A", "SAFE_B"), ("SECRET_B", "SAFE_B", "SECRET_A"))
        labels = (("SAFE", "SENSITIVE", "SAFE"), ("SENSITIVE", "SAFE", "SENSITIVE"))
    elif fixture_id == "limit":
        cells = (tuple(["SAFE_A", "SECRET_A", "SAFE_B", "SECRET_B"] * 4),) * 16
        labels = (tuple(["SAFE", "SENSITIVE"] * 8),) * 16
    else:
        return None
    # UNVERIFIED private redactor output; this expression is not oracle proof.
    output = tuple(tuple("PRIVATE_MASK" if label == "SENSITIVE" else cell
                         for cell, label in zip(row, classes))
                   for row, classes in zip(cells, labels))
    return _Proposal(cells, labels, output)


def _valid_request(value):
    return (type(value) is ObservationRequest
            and type(value.request_id) is str and _ID.fullmatch(value.request_id) is not None
            and type(value.session_id) is str and _ID.fullmatch(value.session_id) is not None
            and type(value.source) is ObservationSource
            and type(value.purpose) is ObservationPurpose)


class SyntheticFixtureRegistry(_Hidden):
    """Only fixed statuses cross public methods. Handles stay in private tests.

    No clock or other external callback runs under this registry's lock. There
    is deliberately no synchronization contract with the permission ledger.
    """

    def __init__(self):
        self._lock = RLock()
        self._identity = _Handle()
        self._source = _Handle()
        self._source_generation = 1
        self._observation_generation = 0
        self._closed = False
        self._records = {}
        self._requests = set()

    def _issue(self, request, target_id, operation, *, fixture_id="small", policy_version=1):
        """Private test setup. Returns an opaque handle, never fixture cells."""
        with self._lock:
            if (self._closed or len(self._records) >= MAX_RECORDS
                    or self._observation_generation >= MAX_GENERATION
                    or not _valid_request(request)
                    or type(target_id) is not str or _ID.fullmatch(target_id) is None
                    or type(operation) is not _Handle
                    or type(fixture_id) is not str
                    or type(policy_version) is not int or not 1 <= policy_version <= MAX_GENERATION):
                return FixtureStatus.DENIED
            if request.request_id in self._requests:
                return FixtureStatus.DENIED
            proposal = _proposal(fixture_id)
            if proposal is None:
                return FixtureStatus.DENIED
            self._requests.add(request.request_id)
            self._observation_generation += 1
            scope = _Scope(request, target_id, operation, fixture_id, self._source,
                           self._identity, self._source_generation,
                           self._observation_generation, policy_version)
            handle = _Handle()
            self._records[handle] = _Record(scope, proposal)
            return handle

    @staticmethod
    def _terminal(record, state):
        record.state = state
        record.scope = None
        record.proposal = None

    def verify(self, handle, request, target_id, operation, *, fixture_id="small", policy_version=1):
        with self._lock:
            record = self._records.get(handle) if type(handle) is _Handle else None
            if record is None or record.state is not FixtureStatus.ISSUED:
                return FixtureStatus.DENIED
            scope, proposal = record.scope, record.proposal
            # Burn before validation: an owned receipt never gets a retry.
            self._terminal(record, FixtureStatus.INVALIDATED)
            if (self._closed or scope is None or proposal is None
                    or not _valid_request(request)
                    or type(target_id) is not str or type(fixture_id) is not str
                    or type(policy_version) is not int
                    or request != scope.request or target_id != scope.target_id
                    or type(operation) is not _Handle or operation is not scope.operation
                    or fixture_id != scope.fixture_id or policy_version != scope.policy_version
                    or scope.registry_identity is not self._identity
                    or scope.source_identity is not self._source
                    or scope.source_generation != self._source_generation
                    or not 1 <= scope.observation_generation <= self._observation_generation
                    or type(proposal) is not _Proposal):
                return FixtureStatus.DENIED
            result = verify_fixture(scope.fixture_id, proposal.source,
                                    proposal.classifications, proposal.output)
            if result is not OracleStatus.VERIFIED:
                return FixtureStatus.DENIED
            self._terminal(record, FixtureStatus.CONSUMED)
            return FixtureStatus.CONSUMED

    def state(self, handle):
        with self._lock:
            record = self._records.get(handle) if type(handle) is _Handle else None
            return FixtureStatus.DENIED if record is None else record.state

    def invalidate(self, handle):
        with self._lock:
            record = self._records.get(handle) if type(handle) is _Handle else None
            if record is None or record.state is not FixtureStatus.ISSUED:
                return FixtureStatus.DENIED
            self._terminal(record, FixtureStatus.INVALIDATED)
            return FixtureStatus.INVALIDATED

    def _invalidate_all(self):
        for record in self._records.values():
            if record.state is FixtureStatus.ISSUED:
                self._terminal(record, FixtureStatus.INVALIDATED)

    def replace_source(self):
        with self._lock:
            if self._closed:
                return FixtureStatus.DENIED
            self._invalidate_all()
            if self._source_generation >= MAX_GENERATION:
                self._closed = True
                return FixtureStatus.CLOSED
            self._source_generation += 1
            self._source = _Handle()
            return FixtureStatus.READY

    def close(self):
        with self._lock:
            self._closed = True
            self._invalidate_all()
            return FixtureStatus.CLOSED
