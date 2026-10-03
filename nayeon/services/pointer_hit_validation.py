"""Private sampled root equality for a proposed native screen-space point."""
from dataclasses import dataclass
import sys
from time import perf_counter_ns

from nayeon.services.computer_control import DesktopContext, _Redacted
from nayeon.services.target_validation import (
    MAX_AGE_NS, _handle, _identity_valid, _timestamp, _valid_target_binding,
)
from nayeon.verification.contract import VerificationStatus

__all__ = ()


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private hit validation state cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private hit validation state cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private hit validation state cannot be serialized or copied.")


@dataclass(frozen=True, slots=True, repr=False)
class _ProposedPoint(_LocalOnly):
    """Native screen-space coordinates interpreted by this Windows process."""
    x: int
    y: int

    def __post_init__(self):
        if type(self.x) is not int or type(self.y) is not int:
            raise TypeError("Exact integer proposed coordinates required.")
        if not all(-(2 ** 31) <= value < 2 ** 31 for value in (self.x, self.y)):
            raise ValueError("Proposed coordinates must fit Windows LONG.")


@dataclass(frozen=True, slots=True, repr=False)
class _PointerHitResult(_LocalOnly):
    status: VerificationStatus = VerificationStatus.INDETERMINATE

    def __post_init__(self):
        if type(self.status) is not VerificationStatus:
            raise TypeError("Exact private verification status required.")


class _PointerHitValidationService(_LocalOnly):
    """Fixed read sequence, no retries, target acquisition, or execution route.

    The original trusted binding and a point are the only validation inputs.
    Native and clock injection are trusted test seams. All production timing
    uses the same process-local perf_counter_ns domain as Phase 6.5.
    Bounded means fixed cardinality, not an OS deadline or atomicity.
    """
    __slots__ = ("_native", "_platform", "_clock")

    def __init__(self, *, native=None, platform=None, clock=perf_counter_ns):
        self._native = native
        self._platform = sys.platform if platform is None else platform
        self._clock = clock

    @staticmethod
    def _hit(native, coordinates):
        window = native.window_at(coordinates)
        if not _handle(window):
            raise ValueError("Required hit unavailable.")
        root = native.root(window)
        if not _handle(root):
            raise ValueError("Required root unavailable.")
        identity = native.identity(root)
        return root, identity

    def validate_hit(self, point, target):
        """Stable complete mismatch is NOT_VERIFIED; drift is INDETERMINATE.

        Foreground is neither read nor required: the claim concerns hit roots.
        No cursor read is needed for an immutable proposed point.
        """
        unknown = _PointerHitResult()
        try:
            if (type(point) is not _ProposedPoint or not _valid_target_binding(target)
                    or self._platform != "win32"):
                return unknown
            point.__post_init__()
            coordinates = (point.x, point.y)
            t0 = self._clock()
            if (not _timestamp(t0) or t0 < target.acquired_to_ns
                    or t0 > target.acquired_to_ns + MAX_AGE_NS):
                return unknown
            native = self._native
            if native is None:
                from nayeon.services.windows_pointer import _HitTestNative
                native = _HitTestNative()
            c0 = native.context()
            if (type(c0) is not DesktopContext or not c0.valid() or c0 != target.context):
                return unknown
            r0, i0 = self._hit(native, coordinates)
            r1, i1 = self._hit(native, coordinates)
            c1 = native.context()
            t1 = self._clock()  # Includes native query resource cleanup.
            if (not _timestamp(t1) or t1 < t0
                    or t1 > target.acquired_to_ns + MAX_AGE_NS
                    or type(c0) is not DesktopContext or not c0.valid()
                    or type(c1) is not DesktopContext or not c1.valid()
                    or c0 != c1 or c0 != target.context
                    or not _identity_valid(i0, c0) or not _identity_valid(i1, c1)
                    or i0.hwnd != r0 or i1.hwnd != r1
                    or r0 != r1 or i0 != i1):
                return unknown
            matches = r0 == target.identity.hwnd and i0 == target.identity
            return _PointerHitResult(VerificationStatus.VERIFIED if matches
                                     else VerificationStatus.NOT_VERIFIED)
        except Exception:
            return unknown
