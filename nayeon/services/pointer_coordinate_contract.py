"""Private read-only proof that one proposed point is physical-screen compatible."""
import ctypes
from ctypes import wintypes as W
from dataclasses import dataclass
import sys

from nayeon.services.computer_control import _Redacted
from nayeon.services.pointer_hit_validation import _ProposedPoint
from nayeon.verification.contract import VerificationStatus

__all__ = ()
_PER_MONITOR_AWARE = 2
_DEFAULT_PLATFORM = object()


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private coordinate-contract state cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private coordinate-contract state cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private coordinate-contract state cannot be serialized or copied.")


def _point_snapshot(point):
    if type(point) is not _ProposedPoint:
        raise TypeError("Exact private point required.")
    _ProposedPoint.__post_init__(point)
    return point.x, point.y


def _awareness(value):
    if type(value) is not int:
        raise TypeError("Exact DPI-awareness value required.")
    if value not in (0, 1, 2):
        raise ValueError("Reviewed DPI-awareness value required.")
    return value


@dataclass(frozen=True, slots=True, repr=False)
class _PhysicalCoordinateEvidence(_LocalOnly):
    """Point-in-time proof of physical/logical identity for this thread only."""
    point: _ProposedPoint
    awareness: int

    def __post_init__(self):
        if type(self) is not _PhysicalCoordinateEvidence:
            raise TypeError("Exact private physical-coordinate evidence required.")
        _point_snapshot(self.point)
        if _awareness(self.awareness) != _PER_MONITOR_AWARE:
            raise ValueError("Per-monitor awareness required.")


@dataclass(frozen=True, slots=True, repr=False)
class _PhysicalCoordinateResult(_LocalOnly):
    status: VerificationStatus = VerificationStatus.INDETERMINATE
    evidence: _PhysicalCoordinateEvidence | None = None

    def __post_init__(self):
        if type(self) is not _PhysicalCoordinateResult or type(self.status) is not VerificationStatus:
            raise TypeError("Exact private coordinate-contract result required.")
        if self.status is VerificationStatus.VERIFIED:
            if type(self.evidence) is not _PhysicalCoordinateEvidence:
                raise TypeError("Complete private physical-coordinate evidence required.")
            _PhysicalCoordinateEvidence.__post_init__(self.evidence)
        elif self.status is not VerificationStatus.INDETERMINATE or self.evidence is not None:
            raise ValueError("Uncertified coordinate result must carry no evidence.")


class _DpiCoordinateNative(_LocalOnly):
    """Minimal read-only current-thread DPI-awareness facade."""
    __slots__ = ("_get_context", "_get_awareness")

    def __init__(self):
        if sys.platform != "win32":
            raise OSError("Windows DPI-awareness query unavailable.")
        user32 = ctypes.WinDLL("user32")
        self._get_context = user32.GetThreadDpiAwarenessContext
        self._get_context.argtypes = []
        self._get_context.restype = W.HANDLE
        self._get_awareness = user32.GetAwarenessFromDpiAwarenessContext
        self._get_awareness.argtypes = [W.HANDLE]
        self._get_awareness.restype = ctypes.c_int

    def awareness(self):
        context = self._get_context()
        if not context:
            raise OSError("Current thread DPI-awareness context unavailable.")
        return _awareness(self._get_awareness(context))


class _PhysicalCoordinateContractService(_LocalOnly):
    """Certify only the identity case; never convert, mutate, or grant authority.

    Two ordered awareness reads bracket no mutable native state other than the
    current thread context. A VERIFIED result means only that this exact point
    was interpreted while the calling thread reported per-monitor awareness,
    where Windows defines logical and physical coordinates as identical.
    """
    __slots__ = ("_native", "_platform")

    def __init__(self, *, native=None, platform=_DEFAULT_PLATFORM):
        self._native = native
        self._platform = sys.platform if platform is _DEFAULT_PLATFORM else platform

    def certify(self, point):
        unknown = _PhysicalCoordinateResult()
        try:
            if type(self._platform) is not str or self._platform != "win32":
                return unknown
            coordinates = _point_snapshot(point)
            native = self._native if self._native is not None else _DpiCoordinateNative()
            first = native.awareness()
            second = native.awareness()
            if (_awareness(first) != _PER_MONITOR_AWARE
                    or _awareness(second) != _PER_MONITOR_AWARE
                    or _point_snapshot(point) != coordinates):
                return unknown
            evidence = _PhysicalCoordinateEvidence(point, _PER_MONITOR_AWARE)
            result = _PhysicalCoordinateResult(VerificationStatus.VERIFIED, evidence)
            _PhysicalCoordinateResult.__post_init__(result)
            if evidence.point is not point or _point_snapshot(point) != coordinates:
                return unknown
            return result
        except Exception:
            return unknown
