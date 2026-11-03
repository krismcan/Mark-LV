"""Phase 10.2 SYNTHETIC-ONLY visual-permission lifecycle model.

Not a trusted security broker, consent UI, platform permission, capture adapter,
redaction attestation, or production authorization mechanism. Its public
fixture methods deliberately simulate decisions; an untrusted Python caller
can invoke those methods. No real service must honor any result from here.

All state is in memory. No filesystem, network, platform capture, provider,
credential, threading worker, background observation, or image content exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from threading import RLock
from time import monotonic_ns
from typing import Callable

from .contracts import (
    MAX_CLOCK_MS, ObservationPurpose, ObservationRequest, ObservationSource,
)

MAX_SYNTHETIC_TTL_MS = 30_000
MAX_SYNTHETIC_RECORDS = 256
_TARGET = re.compile(r"[0-9a-f]{32}\Z", re.ASCII)


class SyntheticPermissionDenied(Exception):
    """A constant, content-free denial; never embed user-controlled identity."""

    def __init__(self) -> None:
        super().__init__("Synthetic permission refused")


class SyntheticState(str, Enum):
    ISSUED = "issued"
    ACTIVE = "active"
    USED = "used"
    REVOKED = "revoked"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    CLOSED = "closed"


class _OpaqueHandle:
    """Identity-only fake capability. Cannot be copied using pickle protocols."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<synthetic-only-handle>"

    __str__ = __repr__

    def __reduce__(self):
        raise TypeError("Synthetic handles cannot be serialized")

    def __reduce_ex__(self, protocol):
        raise TypeError("Synthetic handles cannot be serialized")


@dataclass(slots=True, repr=False)
class _Session:
    generation: int
    owner_context: _OpaqueHandle
    active: bool


@dataclass(slots=True, repr=False)
class _Target:
    generation: int
    active: bool


@dataclass(frozen=True, slots=True, repr=False)
class _Scope:
    request: ObservationRequest
    session_generation: int
    owner_context: _OpaqueHandle
    target_id: str
    target_generation: int


@dataclass(slots=True, repr=False)
class _Approval:
    scope: _Scope
    maximum_ttl_ms: int


@dataclass(slots=True, repr=False)
class _Grant:
    scope: _Scope
    expires_at_ms: int
    state: SyntheticState
    lease: _OpaqueHandle | None = None


class SyntheticPermissionModel:
    """Fake broker + in-memory grant state; NEVER authoritative outside tests.

    The fixture owns session and target generations, policy and confirmation
    events, and the monotonically checked clock. Python callers can create
    fake approval events, hence no real OS adapter may consume its handles.
    """

    def __init__(self, *, fake_monotonic_ms: Callable[[], int] | None = None):
        if fake_monotonic_ms is not None and not callable(fake_monotonic_ms):
            raise TypeError("Synthetic clock must be callable")
        self._clock = (fake_monotonic_ms if fake_monotonic_ms is not None
                       else lambda: monotonic_ns() // 1_000_000)
        self._lock = RLock()
        self._high_water = -1
        self._closed = False
        self._sessions: dict[str, _Session] = {}
        self._targets: dict[tuple[ObservationSource, str], _Target] = {}
        self._policy: dict[_OpaqueHandle, _Scope] = {}
        self._approvals: dict[_OpaqueHandle, _Approval] = {}
        self._grants: dict[_OpaqueHandle, _Grant] = {}
        self._leases: dict[_OpaqueHandle, _Grant] = {}
        self._issued_requests: set[str] = set()

    @staticmethod
    def _request(value: object) -> ObservationRequest:
        if type(value) is not ObservationRequest:
            raise SyntheticPermissionDenied()
        return value

    @staticmethod
    def _target_id(value: object) -> str:
        if type(value) is not str or _TARGET.fullmatch(value) is None:
            raise SyntheticPermissionDenied()
        return value

    @staticmethod
    def _ttl(value: object) -> int:
        if type(value) is not int or not 1 <= value <= MAX_SYNTHETIC_TTL_MS:
            raise SyntheticPermissionDenied()
        return value

    def _must_open(self) -> None:
        if self._closed:
            raise SyntheticPermissionDenied()

    @staticmethod
    def _capacity(records) -> None:
        # Bounded lifetime registry; never evict replay tombstones.
        if len(records) >= MAX_SYNTHETIC_RECORDS:
            raise SyntheticPermissionDenied()

    def _invalidate(self, state: SyntheticState) -> None:
        for grant in self._grants.values():
            if grant.state in (SyntheticState.ISSUED, SyntheticState.ACTIVE):
                grant.state = state
        self._policy.clear()
        self._approvals.clear()

    def _close_unsafe(self) -> None:
        self._closed = True
        self._invalidate(SyntheticState.CLOSED)

    def _now(self) -> int:
        self._must_open()
        try:
            current = self._clock()
        except Exception:
            self._close_unsafe()
            raise SyntheticPermissionDenied() from None
        if (type(current) is not int or not 0 <= current <= MAX_CLOCK_MS
                or current < self._high_water):
            self._close_unsafe()
            raise SyntheticPermissionDenied()
        self._high_water = current
        return current

    def _current_scope(self, request: ObservationRequest, target_id: str) -> _Scope:
        session = self._sessions.get(request.session_id)
        target = self._targets.get((request.source, target_id))
        if (session is None or not session.active
                or target is None or not target.active):
            raise SyntheticPermissionDenied()
        return _Scope(request, session.generation, session.owner_context,
                      target_id, target.generation)

    def _same_current_scope(self, recorded: _Scope, request: ObservationRequest,
                            target_id: str) -> None:
        if (recorded.request != request or recorded.target_id != target_id
                or self._current_scope(request, target_id) != recorded):
            raise SyntheticPermissionDenied()

    def fake_open_session(self, session_id: str) -> None:
        """Fake platform fixture action, not actual user/session authentication."""
        if type(session_id) is not str or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", session_id, re.ASCII):
            raise SyntheticPermissionDenied()
        with self._lock:
            self._must_open()
            old = self._sessions.get(session_id)
            if old is not None and old.active:
                raise SyntheticPermissionDenied()
            if old is None:
                self._capacity(self._sessions)
            generation = 1 if old is None else old.generation + 1
            self._sessions[session_id] = _Session(
                generation, _OpaqueHandle(), True)

    def fake_end_session(self, session_id: str) -> None:
        with self._lock:
            self._must_open()
            session = self._sessions.get(session_id)
            if session is None or not session.active:
                raise SyntheticPermissionDenied()
            session.active = False
            for grant in self._grants.values():
                if grant.scope.request.session_id == session_id and grant.state in (
                        SyntheticState.ISSUED, SyntheticState.ACTIVE):
                    grant.state = SyntheticState.CANCELLED
            self._policy.clear()
            self._approvals.clear()

    def fake_bind_target(self, source: ObservationSource, target_id: str) -> None:
        """Simulate OS-owned target generation; NEVER proves an OS target."""
        if type(source) is not ObservationSource:
            raise SyntheticPermissionDenied()
        target_id = self._target_id(target_id)
        with self._lock:
            self._must_open()
            key = (source, target_id)
            old = self._targets.get(key)
            if old is not None and old.active:
                raise SyntheticPermissionDenied()
            if old is None:
                self._capacity(self._targets)
            self._targets[key] = _Target(
                1 if old is None else old.generation + 1, True)

    def fake_replace_target(self, source: ObservationSource, target_id: str) -> None:
        if type(source) is not ObservationSource:
            raise SyntheticPermissionDenied()
        target_id = self._target_id(target_id)
        with self._lock:
            self._must_open()
            current = self._targets.get((source, target_id))
            if current is None or not current.active:
                raise SyntheticPermissionDenied()
            current.generation += 1
            for grant in self._grants.values():
                if (grant.scope.request.source is source
                        and grant.scope.target_id == target_id
                        and grant.state in (SyntheticState.ISSUED, SyntheticState.ACTIVE)):
                    grant.state = SyntheticState.CANCELLED
            self._policy.clear()
            self._approvals.clear()

    def fake_policy_allow(self, request: ObservationRequest,
                          target_id: str) -> _OpaqueHandle:
        """Only a synthetic fixture event; no real policy approval."""
        request = self._request(request)
        target_id = self._target_id(target_id)
        with self._lock:
            self._must_open()
            scope = self._current_scope(request, target_id)
            self._capacity(self._policy)
            handle = _OpaqueHandle()
            self._policy[handle] = scope
            return handle

    def fake_user_confirm(self, policy_event: _OpaqueHandle,
                          request: ObservationRequest, target_id: str,
                          *, maximum_ttl_ms: int) -> _OpaqueHandle:
        """Second independent fake event; consumes the policy event exactly once."""
        with self._lock:
            self._must_open()
            scope = self._policy.pop(policy_event, None) if type(
                policy_event) is _OpaqueHandle else None
            request = self._request(request)
            target_id = self._target_id(target_id)
            max_ttl = self._ttl(maximum_ttl_ms)
            if scope is None:
                raise SyntheticPermissionDenied()
            self._same_current_scope(scope, request, target_id)
            self._capacity(self._approvals)
            handle = _OpaqueHandle()
            self._approvals[handle] = _Approval(scope, max_ttl)
            return handle

    def issue(self, approval_event: _OpaqueHandle,
              request: ObservationRequest, target_id: str,
              *, ttl_ms: int) -> _OpaqueHandle:
        """Consume a fake approval atomically, including on failed attempts."""
        with self._lock:
            self._must_open()
            record = self._approvals.pop(approval_event, None) if type(
                approval_event) is _OpaqueHandle else None
            request = self._request(request)
            target_id = self._target_id(target_id)
            if record is None:
                raise SyntheticPermissionDenied()
            # Only an exact fixture-issued approval can reserve a request.
            # Reserve once for this ledger's entire lifetime, EVEN on a later
            # bad TTL or clock failure. Never allow cross-session replay.
            self._same_current_scope(record.scope, request, target_id)
            if request.request_id in self._issued_requests:
                raise SyntheticPermissionDenied()
            self._capacity(self._issued_requests)
            self._capacity(self._grants)
            self._issued_requests.add(request.request_id)
            ttl = self._ttl(ttl_ms)
            if ttl > record.maximum_ttl_ms:
                raise SyntheticPermissionDenied()
            now = self._now()
            # Fixture-owned callbacks can re-enter this RLock: revalidate
            # closure and target/session generation after invoking clock.
            self._must_open()
            self._same_current_scope(record.scope, request, target_id)
            if now + ttl > MAX_CLOCK_MS:
                self._close_unsafe()
                raise SyntheticPermissionDenied()
            handle = _OpaqueHandle()
            self._grants[handle] = _Grant(
                record.scope, now + ttl, SyntheticState.ISSUED)
            return handle

    def _verify(self, grant: _Grant, request: ObservationRequest,
                target_id: str, expected: SyntheticState) -> None:
        self._must_open()
        now = self._now()
        self._must_open()  # Callback may have closed this fake registry.
        if now >= grant.expires_at_ms and grant.state in (
                SyntheticState.ISSUED, SyntheticState.ACTIVE):
            grant.state = SyntheticState.EXPIRED
        if grant.state is not expected:
            raise SyntheticPermissionDenied()
        self._same_current_scope(grant.scope, request, target_id)

    def begin(self, grant_handle: _OpaqueHandle,
              request: ObservationRequest, target_id: str) -> _OpaqueHandle:
        with self._lock:
            self._must_open()
            grant = self._grants.get(grant_handle) if type(
                grant_handle) is _OpaqueHandle else None
            request = self._request(request)
            target_id = self._target_id(target_id)
            if grant is None:
                raise SyntheticPermissionDenied()
            self._verify(grant, request, target_id, SyntheticState.ISSUED)
            lease = _OpaqueHandle()
            grant.state = SyntheticState.ACTIVE
            grant.lease = lease
            self._leases[lease] = grant
            return lease

    def _active(self, lease: _OpaqueHandle, request: ObservationRequest,
                target_id: str) -> _Grant:
        grant = self._leases.get(lease) if type(lease) is _OpaqueHandle else None
        if grant is None or grant.lease is not lease:
            raise SyntheticPermissionDenied()
        self._verify(grant, self._request(request), self._target_id(target_id),
                     SyntheticState.ACTIVE)
        return grant

    def validate_active(self, lease: _OpaqueHandle,
                        request: ObservationRequest, target_id: str) -> bool:
        """Validation is ephemeral; it never authorizes later completion."""
        with self._lock:
            self._active(lease, request, target_id)
            return True

    def complete(self, lease: _OpaqueHandle,
                 request: ObservationRequest, target_id: str) -> bool:
        """Atomic final fake marker: recheck all conditions under revoke lock."""
        with self._lock:
            grant = self._active(lease, request, target_id)
            grant.state = SyntheticState.USED
            return True  # No image, evidence, content or OS effect is produced.

    def revoke(self, grant_handle: _OpaqueHandle) -> bool:
        with self._lock:
            grant = self._grants.get(grant_handle) if type(
                grant_handle) is _OpaqueHandle else None
            if grant is None or grant.state not in (
                    SyntheticState.ISSUED, SyntheticState.ACTIVE):
                return False
            grant.state = SyntheticState.REVOKED
            return True

    def cancel(self, handle: _OpaqueHandle) -> bool:
        """Fake operation fault/timeout path, always terminal."""
        with self._lock:
            grant = (self._grants.get(handle) or self._leases.get(handle)) if type(
                handle) is _OpaqueHandle else None
            if grant is None or grant.state not in (
                    SyntheticState.ISSUED, SyntheticState.ACTIVE):
                return False
            grant.state = SyntheticState.CANCELLED
            return True

    def synthetic_state(self, grant_handle: _OpaqueHandle) -> SyntheticState:
        """Returns only a fixed status, never tokens, user text or metadata."""
        with self._lock:
            grant = self._grants.get(grant_handle) if type(
                grant_handle) is _OpaqueHandle else None
            if grant is None:
                raise SyntheticPermissionDenied()
            if grant.state in (SyntheticState.ISSUED, SyntheticState.ACTIVE):
                now = self._now()
                # A fixture clock may re-enter and revoke, cancel or close.
                # Never rewrite such terminal transitions as EXPIRED.
                if (grant.state in (SyntheticState.ISSUED, SyntheticState.ACTIVE)
                        and now >= grant.expires_at_ms):
                    grant.state = SyntheticState.EXPIRED
            return grant.state

    def close(self) -> None:
        with self._lock:
            self._close_unsafe()
