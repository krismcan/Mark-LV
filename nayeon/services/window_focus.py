"""Private preparation-time window binding and bounded best-effort focus."""
from dataclasses import dataclass, field
from enum import Enum

from nayeon.services.computer_control import (
    ComputerControlService, DesktopContext, ForegroundState, WindowIdentity, _Redacted,
)


@dataclass(frozen=True, slots=True, repr=False)
class _FocusBinding(_Redacted):
    identity: WindowIdentity
    context: DesktopContext


def _valid_focus_binding(binding):
    return (type(binding) is _FocusBinding and type(binding.identity) is WindowIdentity
            and type(binding.context) is DesktopContext and binding.identity.valid(binding.context))


class FocusState(str, Enum):
    FOCUSED = "focused"
    NOT_FOCUSED = "not_focused"
    TARGET_CHANGED = "target_changed"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class WindowFocusResult:
    state: FocusState
    _binding: _FocusBinding = field(repr=False)

    def __post_init__(self):
        if not isinstance(self.state, FocusState) or not _valid_focus_binding(self._binding):
            raise TypeError("Typed bounded focus result required.")


class WindowFocusService:
    """No retained target or owning resource; executor owns pending bindings."""
    def __init__(self, *, adapter=None):
        if adapter is None:
            from nayeon.services.windows_focus import WindowsFocusAdapter
            adapter = WindowsFocusAdapter()
        self._adapter = adapter

    def prepare_focus(self):
        observation = ComputerControlService(adapter=self._adapter).observe_foreground_window()
        evidence = observation._evidence
        if (observation.state is not ForegroundState.OBSERVED or evidence is None
                or not evidence.consistent()):
            raise ValueError("Focus target preparation could not be established.")
        return _FocusBinding(evidence.early, evidence.context)

    def focus_window(self, binding):
        if not _valid_focus_binding(binding):
            raise ValueError("Invalid focus binding.")
        try:
            state = self._adapter.focus_window(binding)
            if isinstance(state, FocusState):
                return WindowFocusResult(state, binding)
        except Exception:
            pass
        return WindowFocusResult(FocusState.INCONCLUSIVE, binding)

    def observe_focus(self, binding):
        if not _valid_focus_binding(binding):
            return FocusState.INCONCLUSIVE
        try:
            state = self._adapter.observe_focus(binding)
            if isinstance(state, FocusState):
                return state
        except Exception:
            pass
        return FocusState.INCONCLUSIVE
