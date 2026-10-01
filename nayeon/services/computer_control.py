"""Read-only foreground snapshots; private evidence is never mutation authority."""
from dataclasses import dataclass, field
from enum import Enum


class ForegroundState(str, Enum):
    OBSERVED = "observed"
    NO_FOREGROUND = "no_foreground"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class ObservationReason(str, Enum):
    CONSISTENT = "bounded_snapshot_consistent"
    NO_FOREGROUND = "no_foreground_sampled"
    CONTEXT = "supported_context_unavailable"
    INCOMPLETE = "required_evidence_incomplete"
    CHANGED = "foreground_changed"
    CONTRADICTORY = "required_evidence_changed"


class _Redacted:
    __slots__ = ()

    def __repr__(self):
        return f"{type(self).__name__}(<private>)"

    __str__ = __repr__


@dataclass(frozen=True, slots=True, repr=False)
class DesktopContext(_Redacted):
    session: int
    input_desktop: str
    thread_desktop: str
    station: str
    active: bool

    def __post_init__(self):
        if (type(self.session) is not int or type(self.active) is not bool
                or any(type(x) is not str for x in
                       (self.input_desktop, self.thread_desktop, self.station))):
            raise TypeError("Immutable desktop context fields required.")

    def valid(self):
        return (type(self.session) is int and self.session > 0 and self.active is True
                and self.station == "WinSta0"
                and self.input_desktop == self.thread_desktop == "Default")


@dataclass(frozen=True, slots=True, repr=False)
class WindowIdentity(_Redacted):
    hwnd: int  # Borrowed identifier, recyclable; never an owned handle.
    pid: int
    tid: int
    creation_time: int
    executable: str  # Provenance only; no publisher/content trust claim.
    window_class: str
    root: int
    session: int
    desktop: str

    def __post_init__(self):
        if (any(type(x) is not int for x in
                (self.hwnd, self.pid, self.tid, self.creation_time, self.root, self.session))
                or any(type(x) is not str for x in
                       (self.executable, self.window_class, self.desktop))):
            raise TypeError("Immutable window identity fields required.")

    def valid(self, context):
        return (type(context) is DesktopContext and context.valid()
                and all(type(x) is int and x > 0 for x in
                        (self.hwnd, self.pid, self.tid, self.creation_time, self.root))
                and self.root == self.hwnd and type(self.session) is int
                and self.session == context.session and self.desktop == context.input_desktop
                and type(self.executable) is str and bool(self.executable.strip())
                and type(self.window_class) is str and bool(self.window_class.strip()))


@dataclass(frozen=True, slots=True, repr=False)
class WindowState(_Redacted):
    visible: bool | None = None
    iconic: bool | None = None
    maximized: bool | None = None
    window_rect: tuple[int, int, int, int] | None = None
    client_rect: tuple[int, int, int, int] | None = None
    client_origin: tuple[int, int] | None = None
    monitor: int | None = None  # Association identifier, not an owned handle.
    dpi: int | None = None
    window_awareness: int | None = None
    observer_awareness: int | None = None

    def __post_init__(self):
        for value in (self.visible, self.iconic, self.maximized):
            if value is not None and type(value) is not bool:
                raise TypeError("Typed window state required.")
        for value, length in ((self.window_rect, 4), (self.client_rect, 4), (self.client_origin, 2)):
            if value is not None and (type(value) is not tuple or len(value) != length
                                      or any(type(x) is not int for x in value)):
                raise TypeError("Immutable geometry required.")
        for value in (self.monitor, self.dpi, self.window_awareness, self.observer_awareness):
            if value is not None and type(value) is not int:
                raise TypeError("Typed optional state required.")


@dataclass(frozen=True, slots=True, repr=False)
class ForegroundEvidence(_Redacted):
    early: WindowIdentity
    late: WindowIdentity
    context: DesktopContext
    late_context: DesktopContext
    state: WindowState
    started_ns: int
    ended_ns: int

    def __post_init__(self):
        if (type(self.early) is not WindowIdentity or type(self.late) is not WindowIdentity
                or type(self.context) is not DesktopContext or type(self.late_context) is not DesktopContext
                or type(self.state) is not WindowState
                or type(self.started_ns) is not int or type(self.ended_ns) is not int):
            raise TypeError("Immutable typed snapshot evidence required.")

    def complete(self):
        return (type(self.early) is WindowIdentity and type(self.late) is WindowIdentity
                and self.early.valid(self.context) and self.late.valid(self.late_context)
                and type(self.started_ns) is int and type(self.ended_ns) is int
                and 0 <= self.started_ns <= self.ended_ns)

    def consistent(self):
        return (self.complete() and self.early == self.late
                and self.context == self.late_context)


@dataclass(frozen=True, slots=True)
class ForegroundObservation:
    state: ForegroundState
    reason: ObservationReason
    _evidence: ForegroundEvidence | None = field(default=None, repr=False)

    def __post_init__(self):
        if not isinstance(self.state, ForegroundState) or not isinstance(self.reason, ObservationReason):
            raise TypeError("Typed observation state and reason required.")
        if self._evidence is not None and type(self._evidence) is not ForegroundEvidence:
            raise TypeError("Typed private observation evidence required.")


class ComputerControlService:
    """Trusted observation only. Construction and validation perform no native reads."""
    def __init__(self, *, adapter=None):
        if adapter is None:
            from nayeon.services.windows_desktop import WindowsDesktopAdapter
            adapter = WindowsDesktopAdapter()
        self._adapter = adapter

    def observe_foreground_window(self) -> ForegroundObservation:
        try:
            result = self._adapter.observe_foreground_window()
            if type(result) is ForegroundObservation:
                return result
        except Exception:
            pass  # Native/adapter error detail must not cross the public boundary.
        return ForegroundObservation(ForegroundState.UNAVAILABLE, ObservationReason.CONTEXT)
