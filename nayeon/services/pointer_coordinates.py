"""Private read-only virtual-desktop coordinate foundation; no execution route."""
import ctypes
from dataclasses import dataclass
import sys

from nayeon.services.computer_control import _Redacted
from nayeon.services.pointer_hit_validation import _ProposedPoint
from nayeon.verification.contract import VerificationStatus

__all__ = ()
_LONG_MIN = -(2 ** 31)
_LONG_MAX = 2 ** 31 - 1
_METRICS = (76, 77, 78, 79)  # SM_X/Y/CX/CYVIRTUALSCREEN, in this order.


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private coordinate state cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private coordinate state cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private coordinate state cannot be serialized or copied.")


def _long(value):
    if type(value) is not int:
        raise TypeError("Exact integer geometry required.")
    if not _LONG_MIN <= value <= _LONG_MAX:
        raise ValueError("Geometry must fit Windows LONG.")


def _axis(coordinate, origin, extent):
    # Inclusive endpoints; Python integer intermediates cannot overflow LONG.
    return 0 if extent == 1 else ((coordinate - origin) * 65535) // (extent - 1)


@dataclass(frozen=True, slots=True, repr=False)
class _CoordinateEvidence(_LocalOnly):
    point: _ProposedPoint
    left: int
    top: int
    width: int
    height: int
    normalized_x: int
    normalized_y: int

    def __post_init__(self):
        if type(self) is not _CoordinateEvidence or type(self.point) is not _ProposedPoint:
            raise TypeError("Exact private coordinate types required.")
        self.point.__post_init__()
        for value in (self.left, self.top, self.width, self.height):
            _long(value)
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Positive virtual extents required.")
        # The last addressable coordinate must fit LONG. The exclusive edge may
        # be LONG_MAX + 1 when the final valid coordinate itself is LONG_MAX.
        right = self.left + self.width - 1
        bottom = self.top + self.height - 1
        _long(right)
        _long(bottom)
        if not (self.left <= self.point.x <= right
                and self.top <= self.point.y <= bottom):
            raise ValueError("Proposed point outside sampled virtual rectangle.")
        for value, coordinate, origin, extent in (
            (self.normalized_x, self.point.x, self.left, self.width),
            (self.normalized_y, self.point.y, self.top, self.height),
        ):
            if type(value) is not int:
                raise TypeError("Exact normalized integers required.")
            if not 0 <= value <= 65535 or value != _axis(coordinate, origin, extent):
                raise ValueError("Normalized coordinate does not match evidence.")


@dataclass(frozen=True, slots=True, repr=False)
class _CoordinateResult(_LocalOnly):
    status: VerificationStatus = VerificationStatus.INDETERMINATE
    evidence: _CoordinateEvidence | None = None

    def __post_init__(self):
        if type(self) is not _CoordinateResult or type(self.status) is not VerificationStatus:
            raise TypeError("Exact private coordinate result required.")
        if self.status is VerificationStatus.VERIFIED:
            if type(self.evidence) is not _CoordinateEvidence:
                raise TypeError("Complete coordinate evidence required.")
            self.evidence.__post_init__()
        elif self.status is not VerificationStatus.INDETERMINATE or self.evidence is not None:
            raise ValueError("Unavailable coordinate result must carry no evidence.")


class _CoordinateNative(_LocalOnly):
    __slots__ = ("_metrics",)

    def __init__(self):
        if sys.platform != "win32":
            raise OSError("Windows coordinate query unavailable.")
        self._metrics = ctypes.WinDLL("user32").GetSystemMetrics
        self._metrics.argtypes = [ctypes.c_int]
        self._metrics.restype = ctypes.c_int

    def metric(self, index):
        return self._metrics(index)


class _PointerCoordinateService(_LocalOnly):
    """Four ordered metric reads, once; native/platform injection is a trusted seam.

    A successful result concerns only this sampled bounding rectangle and its
    integer normalization. No freshness, monitor coverage, or effect is proved.
    """
    __slots__ = ("_native", "_platform")

    def __init__(self, *, native=None, platform=None):
        self._native = native
        self._platform = sys.platform if platform is None else platform

    def normalize(self, point):
        unknown = _CoordinateResult()
        try:
            if (type(self._platform) is not str or self._platform != "win32"
                    or type(point) is not _ProposedPoint):
                return unknown
            point.__post_init__()
            native = self._native if self._native is not None else _CoordinateNative()
            left, top, width, height = (native.metric(index) for index in _METRICS)
            # Validate before division. Inclusive last coordinates are
            # origin + extent - 1; the exclusive edge need not fit LONG.
            for value in (left, top, width, height):
                _long(value)
            if width <= 0 or height <= 0:
                return unknown
            right = left + width - 1
            bottom = top + height - 1
            _long(right)
            _long(bottom)
            if not (left <= point.x <= right and top <= point.y <= bottom):
                return unknown
            evidence = _CoordinateEvidence(
                point, left, top, width, height,
                _axis(point.x, left, width), _axis(point.y, top, height))
            return _CoordinateResult(VerificationStatus.VERIFIED, evidence)
        except Exception:
            return unknown
