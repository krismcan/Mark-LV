"""Private approved text/target binding; no retained target or owning resource."""
from dataclasses import dataclass, field
from enum import Enum

from nayeon.services.computer_control import _Redacted
from nayeon.services.window_focus import WindowFocusService, _FocusBinding, _valid_focus_binding

MAX_TEXT_SCALARS = 256


def validate_text(text):
    # Python str counts scalar values once lone surrogates are rejected.
    if type(text) is not str:
        raise TypeError("Exactly one plain text string is required.")
    if not 1 <= len(text) <= MAX_TEXT_SCALARS or not text.isprintable():
        raise ValueError("Text must contain 1 to 256 printable Unicode scalar characters.")
    return text  # No trimming, case folding, escape interpretation or NFC conversion.


@dataclass(frozen=True, slots=True, repr=False)
class _TextBinding(_Redacted):
    target: _FocusBinding
    text: str


def _valid_text_binding(binding):
    if type(binding) is not _TextBinding or not _valid_focus_binding(binding.target):
        return False
    try:
        validate_text(binding.text)
        return True
    except (TypeError, ValueError):
        return False


class TextInputState(str, Enum):
    TYPED = "typed"
    PARTIAL = "partial"
    NOT_TYPED = "not_typed"
    TARGET_CHANGED = "target_changed"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class KeyboardTextResult:
    state: TextInputState
    _binding: _TextBinding = field(repr=False)

    def __post_init__(self):
        if not isinstance(self.state, TextInputState) or not _valid_text_binding(self._binding):
            raise TypeError("Typed bounded keyboard result required.")


class KeyboardTextService:
    def __init__(self, *, adapter=None):
        if adapter is None:
            from nayeon.services.windows_keyboard import WindowsKeyboardAdapter
            adapter = WindowsKeyboardAdapter()
        self._adapter = adapter

    def prepare_text(self, text):
        validate_text(text)
        target = WindowFocusService(adapter=self._adapter).prepare_focus()
        return _TextBinding(target, text)

    def type_text(self, binding):
        if not _valid_text_binding(binding):
            raise ValueError("Invalid saved text action.")
        try:
            state = self._adapter.type_text(binding)
            if isinstance(state, TextInputState):
                return KeyboardTextResult(state, binding)
        except Exception:
            pass
        return KeyboardTextResult(TextInputState.INCONCLUSIVE, binding)

    def observe_target(self, binding):
        if not _valid_text_binding(binding):
            return TextInputState.INCONCLUSIVE
        try:
            state = self._adapter.observe_target(binding)
            if isinstance(state, TextInputState):
                return state
        except Exception:
            pass
        return TextInputState.INCONCLUSIVE
