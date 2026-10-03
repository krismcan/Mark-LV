"""Private invocation-local sampled equality; never input or approval authority."""
import ctypes
from dataclasses import dataclass
import sys
from time import perf_counter_ns

from nayeon.services.computer_control import DesktopContext, WindowIdentity, _Redacted
from nayeon.verification.contract import VerificationStatus


MAX_AGE_NS = 1_000_000_000


def _timestamp(value):
    return type(value) is int and value >= 0


def _handle(value):
    return type(value) is int and 0 < value < 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8)


def _identity_valid(identity, context):
    return (type(identity) is WindowIdentity and identity.valid(context)
            and _handle(identity.hwnd) and _handle(identity.root))


@dataclass(frozen=True, slots=True, repr=False)
class _TargetBinding(_Redacted):
    identity: WindowIdentity
    context: DesktopContext
    acquired_from_ns: int
    acquired_to_ns: int

    def __post_init__(self):
        if (type(self.identity) is not WindowIdentity or type(self.context) is not DesktopContext
                or type(self.acquired_from_ns) is not int or type(self.acquired_to_ns) is not int):
            raise TypeError("Immutable typed private target evidence required.")
        if not _valid_target_binding(self):
            raise ValueError("Valid private target acquisition required.")


def _valid_target_binding(binding):
    return (type(binding) is _TargetBinding
            and _timestamp(binding.acquired_from_ns) and _timestamp(binding.acquired_to_ns)
            and binding.acquired_from_ns <= binding.acquired_to_ns
            and _identity_valid(binding.identity, binding.context))


@dataclass(frozen=True, slots=True, repr=False)
class _TargetVerificationResult(_Redacted):
    status: VerificationStatus = VerificationStatus.INDETERMINATE

    def __post_init__(self):
        if type(self.status) is not VerificationStatus:
            raise TypeError("Typed private validation status required.")


class _TargetVerificationService:
    """Use acquire_target then verify_target in the same trusted invocation.

    Both reads use this service's single process-local perf_counter_ns clock.
    Injected clocks/native facades are trusted test seams, never caller data.
    No binding is retained, cached, serialized, registered, or promoted to an
    approval token. Legacy focus/text bindings cannot be converted here.
    Fixed cardinality is not an OS deadline; equality is not continuity.
    """
    def __init__(self, *, native=None, platform=None, clock=perf_counter_ns):
        self._native = native
        self._platform = sys.platform if platform is None else platform
        self._clock = clock

    def _native_reader(self):
        if self._platform != "win32":
            raise ValueError("Supported target context unavailable.")
        if self._native is not None:
            return self._native
        from nayeon.services.windows_desktop import _WindowsNative
        return _WindowsNative()

    def _sample(self, hwnd=None):
        # The very first operation brackets even native setup and C0. The last
        # clock follows all queries and their scoped native resource cleanup.
        t0 = self._clock()
        if not _timestamp(t0):
            raise ValueError("Required acquisition time unavailable.")
        native = self._native_reader()
        c0 = native.context()
        f0 = native.foreground()
        target = f0 if hwnd is None else hwnd
        if not _handle(target):
            raise ValueError("Required target unavailable.")
        i0 = native.identity(target)
        i1 = native.identity(target)
        f1 = native.foreground()
        c1 = native.context()
        t1 = self._clock()
        return t0, c0, f0, i0, i1, f1, c1, t1

    @staticmethod
    def _complete(sample):
        t0, c0, f0, i0, i1, f1, c1, t1 = sample
        return (_timestamp(t0) and _timestamp(t1) and t0 <= t1
                and type(c0) is DesktopContext and c0.valid()
                and type(c1) is DesktopContext and c1.valid()
                and _handle(f0) and _handle(f1)
                and _identity_valid(i0, c0) and _identity_valid(i1, c1))

    def acquire_target(self):
        """Return one genuinely bracketed baseline, or a fixed sanitized error."""
        try:
            sample = self._sample()
            t0, c0, f0, i0, i1, f1, c1, t1 = sample
            if (self._complete(sample) and c0 == c1 and i0 == i1
                    and f0 == f1 == i0.hwnd):
                return _TargetBinding(i0, c0, t0, t1)
        except Exception:
            pass
        raise ValueError("Target baseline acquisition could not be established.") from None

    def verify_target(self, binding):
        """Only complete fresh evidence may establish equality or contradiction.

        acquired_from <= acquired_to <= t0 <= t1 <= acquired_to + MAX_AGE_NS.
        Equal clock samples are allowed; types are exact int, never bool.
        No retry, replacement baseline, or timestamp substitution occurs.
        """
        unknown = _TargetVerificationResult()
        try:
            if not _valid_target_binding(binding):
                return unknown
            sample = self._sample(binding.identity.hwnd)
            t0, c0, f0, i0, i1, f1, c1, t1 = sample
            if (not self._complete(sample) or t0 < binding.acquired_to_ns
                    or t1 > binding.acquired_to_ns + MAX_AGE_NS):
                return unknown
            matches = (c0 == c1 == binding.context and i0 == i1 == binding.identity
                       and f0 == f1 == binding.identity.hwnd)
            return _TargetVerificationResult(
                VerificationStatus.VERIFIED if matches else VerificationStatus.NOT_VERIFIED)
        except Exception:
            return unknown
