"""Bounded read-only pointer receipts. Private samples are never action authority."""
from dataclasses import dataclass, field
from enum import Enum
import ctypes

from nayeon.services.computer_control import DesktopContext, WindowIdentity, _Redacted


class PointerState(str, Enum):
    OBSERVED = "observed"
    NO_TARGET = "no_target"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class PointerReason(str, Enum):
    CONSISTENT = "bounded_snapshot_consistent"
    NO_TARGET = "no_target_sampled"
    CONTEXT = "supported_context_unavailable"
    INCOMPLETE = "required_evidence_incomplete"
    CHANGED = "required_evidence_changed"


def _point_valid(point):
    return (type(point) is tuple and len(point) == 2
            and all(type(x) is int and -(2 ** 31) <= x < 2 ** 31 for x in point))


@dataclass(frozen=True, slots=True, repr=False)
class _PointerSample(_Redacted):
    point: tuple[int, int]
    window: int
    root: int
    foreground_root: int
    identity: WindowIdentity | None
    foreground_identity: WindowIdentity | None

    def __post_init__(self):
        if (not _point_valid(self.point)
                or any(type(x) is not int or not 0 <= x < 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8) for x in
                       (self.window, self.root, self.foreground_root))
                or any(x is not None and type(x) is not WindowIdentity for x in
                       (self.identity, self.foreground_identity))):
            raise TypeError("Immutable typed pointer sample required.")

    def valid(self, context):
        return (type(context) is DesktopContext and context.valid()
                and (not self.root or self.root != self.foreground_root
                     or self.identity == self.foreground_identity)
                and ((self.foreground_root == 0 and self.foreground_identity is None)
                     or (self.foreground_root > 0
                         and type(self.foreground_identity) is WindowIdentity
                         and self.foreground_identity.hwnd == self.foreground_root
                         and self.foreground_identity.valid(context)))
                and ((self.window == self.root == 0 and self.identity is None)
                     or (self.window > 0 and self.root > 0
                         and type(self.identity) is WindowIdentity
                         and self.identity.hwnd == self.root and self.identity.valid(context))))


@dataclass(frozen=True, slots=True, repr=False)
class _PointerEvidence(_Redacted):
    early: _PointerSample
    late: _PointerSample
    context: DesktopContext
    late_context: DesktopContext
    started_ns: int
    ended_ns: int

    def __post_init__(self):
        if (type(self.early) is not _PointerSample or type(self.late) is not _PointerSample
                or type(self.context) is not DesktopContext or type(self.late_context) is not DesktopContext
                or type(self.started_ns) is not int or type(self.ended_ns) is not int):
            raise TypeError("Immutable typed pointer evidence required.")

    def complete(self):
        return (self.early.valid(self.context) and self.late.valid(self.late_context)
                and 0 <= self.started_ns <= self.ended_ns)

    def consistent(self):
        return self.complete() and self.context == self.late_context and self.early == self.late


@dataclass(frozen=True, slots=True)
class PointerObservation:
    state: PointerState
    reason: PointerReason
    _evidence: _PointerEvidence | None = field(default=None, repr=False)

    def __post_init__(self):
        if (type(self.state) is not PointerState or type(self.reason) is not PointerReason
                or (self._evidence is not None and type(self._evidence) is not _PointerEvidence)):
            raise TypeError("Typed pointer receipt required.")


class PointerObservationService:
    def __init__(self, *, adapter=None):
        if adapter is None:
            from nayeon.services.windows_pointer import WindowsPointerAdapter
            adapter = WindowsPointerAdapter()
        self._adapter = adapter

    def observe_pointer(self):
        try:
            result = self._adapter.observe_pointer()
            if type(result) is PointerObservation:
                return result
        except Exception:
            pass
        return PointerObservation(PointerState.UNAVAILABLE, PointerReason.CONTEXT)
