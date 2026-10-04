"""Private same-worker physical-coordinate and bounded UIA observation."""
from dataclasses import dataclass
import sys

from nayeon.services.computer_control import _Redacted
from nayeon.services.dpi_execution_context import _ScopedDpiExecutionContext, _ScopedDpiResult
from nayeon.services.pointer_coordinate_contract import (
    _PhysicalCoordinateContractService, _PhysicalCoordinateResult,
    _awareness, _point_snapshot,
)
from nayeon.services.pointer_hit_validation import _ProposedPoint
from nayeon.services.ui_element_observation import _UIANative, _sample_valid
from nayeon.verification.contract import VerificationStatus

__all__ = ()
_DEFAULT_PLATFORM = object()
MAX_RUNTIME_ID_INTS = _UIANative.MAX_RUNTIME_ID_INTS


def _runtime_id_valid(runtime_id):
    if (type(runtime_id) is not tuple
            or not 1 <= len(runtime_id) <= MAX_RUNTIME_ID_INTS):
        raise ValueError("Exact bounded runtime sample required.")
    for value in runtime_id:
        if type(value) is not int or not -(2**31) <= value < 2**31:
            raise ValueError("Exact runtime integer required.")


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private composite observation cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private composite observation cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private composite observation cannot be serialized or copied.")


@dataclass(frozen=True, slots=True, repr=False)
class _ScopedUIElementEvidence(_LocalOnly):
    point: _ProposedPoint
    awareness: int
    control_type: int
    enabled: bool
    runtime_id: tuple[int, ...]
    clickable: bool

    def __post_init__(self):
        if type(self) is not _ScopedUIElementEvidence:
            raise TypeError("Exact private composite evidence required.")
        _point_snapshot(self.point)
        if _awareness(self.awareness) != 2:
            raise ValueError("Per-monitor awareness required.")
        _sample_valid(self.control_type, self.enabled)
        _runtime_id_valid(self.runtime_id)
        if type(self.clickable) is not bool:
            raise TypeError("Exact clickability state required.")


@dataclass(frozen=True, slots=True, repr=False)
class _ScopedUIElementResult(_LocalOnly):
    status: VerificationStatus = VerificationStatus.INDETERMINATE
    evidence: _ScopedUIElementEvidence | None = None

    def __post_init__(self):
        if type(self) is not _ScopedUIElementResult or type(self.status) is not VerificationStatus:
            raise TypeError("Exact private composite result required.")
        if self.status is VerificationStatus.VERIFIED:
            if type(self.evidence) is not _ScopedUIElementEvidence:
                raise TypeError("Complete private composite evidence required.")
            _ScopedUIElementEvidence.__post_init__(self.evidence)
        elif self.status is not VerificationStatus.INDETERMINATE or self.evidence is not None:
            raise ValueError("Unavailable composite observation carries no evidence.")


class _ScopedUIElementObservationService(_LocalOnly):
    """One joined PMv2/MTA worker; descriptive evidence, never authority.

    VERIFIED describes only same-point physical certification and one bounded
    sample of control type, enabled, opaque runtime ID and provider-reported
    clickability availability with clean UIA teardown and DPI restoration.
    Either availability value is descriptive only. Factories are trusted
    private test seams. Native calls have no hard deadline.
    """
    __slots__ = ("_scope_factory", "_contract_factory", "_native_factory", "_platform")

    def __init__(self, *, scope_factory=None, contract_factory=None,
                 native_factory=None, platform=_DEFAULT_PLATFORM):
        self._scope_factory = _ScopedDpiExecutionContext if scope_factory is None else scope_factory
        self._contract_factory = (
            _PhysicalCoordinateContractService if contract_factory is None else contract_factory)
        self._native_factory = _UIANative if native_factory is None else native_factory
        self._platform = sys.platform if platform is _DEFAULT_PLATFORM else platform

    def observe(self, point):
        unknown = _ScopedUIElementResult()
        try:
            if type(self._platform) is not str or self._platform != "win32":
                return unknown
            coordinates = _point_snapshot(point)

            def unchanged():
                if _point_snapshot(point) != coordinates:
                    raise ValueError("Observation point changed.")

            def task():
                native = None
                sample = None
                clean = True
                try:
                    contract = self._contract_factory()
                    unchanged()
                    certified = contract.certify(point)
                    unchanged()
                    if type(certified) is not _PhysicalCoordinateResult:
                        raise TypeError("Exact coordinate result required.")
                    _PhysicalCoordinateResult.__post_init__(certified)
                    if (certified.status is not VerificationStatus.VERIFIED
                            or certified.evidence.point is not point):
                        raise ValueError("Same-point physical certification required.")
                    native = self._native_factory()
                    native.initialize()
                    native.activate()
                    unchanged()
                    native.element_from_point(*coordinates)
                    control_type = native.control_type()
                    enabled = native.is_enabled()
                    runtime_id = native.runtime_id()
                    clickable = native.clickable_point_available()
                    _sample_valid(control_type, enabled)
                    _runtime_id_valid(runtime_id)
                    if type(clickable) is not bool:
                        raise TypeError("Exact clickability state required.")
                    unchanged()
                    sample = (control_type, enabled, runtime_id, clickable)
                except BaseException:
                    clean = False
                finally:
                    if native is not None:
                        for name in ("release_element", "release_automation", "uninitialize"):
                            try:
                                getattr(native, name)()
                            except BaseException:
                                clean = False
                unchanged()
                if not clean or sample is None:
                    return unknown
                evidence = _ScopedUIElementEvidence(point, 2, *sample)
                result = _ScopedUIElementResult(VerificationStatus.VERIFIED, evidence)
                unchanged()
                return result

            scoped = self._scope_factory().run(task)
            if type(scoped) is not _ScopedDpiResult:
                return unknown
            _ScopedDpiResult.__post_init__(scoped)
            unchanged()
            if not scoped.completed or type(scoped.value) is not _ScopedUIElementResult:
                return unknown
            result = scoped.value
            _ScopedUIElementResult.__post_init__(result)
            if (result.status is not VerificationStatus.VERIFIED
                    or result.evidence.point is not point):
                return unknown
            unchanged()
            return result
        except BaseException:
            return unknown
