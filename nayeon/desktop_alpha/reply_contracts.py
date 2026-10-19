"""Phase 8.34 A: bounded fake-only data; no UI or execution authority.

Opaque identities must be plain object tokens, never widgets. These records
are not a sandbox against arbitrary Python memory mutation. Human admission
and fresh UI binding are obligations of the later trusted bridge.
"""

from dataclasses import dataclass
from enum import Enum
import unicodedata


MAX_PROMPT_CODEPOINTS = 512
MAX_PROMPT_UTF8_BYTES = 2048
MAX_REPLY_CODEPOINTS = 512
MAX_REPLY_UTF8_BYTES = 2048
MAX_REQUEST_NUMBER = 65535
MAX_CLOCK_MS = (1 << 63) - 1
DEADLINE_MS = 30000
SIMULATED_TEXT = "SIMULATED REPLY / NO AI REQUEST: This is a constant local preview. No action occurred."
ERROR_TEXT = "SIMULATED REPLY / NO AI REQUEST: Local preview unavailable. No action occurred."


class ReplyState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    DRAINING = "draining"
    CLOSING = "closing"
    RETIRED = "retired"
    DESTROYED = "destroyed"


class ReplyKind(Enum):
    SIMULATED = "simulated"
    ERROR = "error"


class RefusalCode(Enum):
    AUTHORITY = "REPLY_AUTHORITY"
    BUSY = "REPLY_BUSY"
    INPUT = "REPLY_INPUT"
    CLOCK = "REPLY_CLOCK"
    CLOSED = "REPLY_CLOSED"
    POISONED = "REPLY_POISONED"
    UNAVAILABLE = "REPLY_UNAVAILABLE"


class ReplyRefused(RuntimeError):
    def __init__(self, code: RefusalCode):
        self.code = code
        super().__init__(code.value)


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ReplyContext:
    root_identity: object
    view_identity: object
    generation: int
    session_identity: object
    epoch: int


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ReplyTicket:
    """Only exact identity in the owner's active slot grants authority."""


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ReplyRequest:
    number: int
    prompt: str


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class ReplyResult:
    request: ReplyRequest
    kind: ReplyKind
    text: str


def valid_prompt(value):
    if type(value) is not str or not 1 <= len(value) <= MAX_PROMPT_CODEPOINTS:
        return False
    if any(unicodedata.category(c) in {"Cc", "Cf", "Cs"}
           or c in {"\u2028", "\u2029"} for c in value):
        return False
    if not value.strip() or unicodedata.normalize("NFC", value) != value:
        return False
    return len(value.encode("utf-8", errors="strict")) <= MAX_PROMPT_UTF8_BYTES


def valid_request(value):
    return (type(value) is ReplyRequest and type(value.number) is int
            and 1 <= value.number <= MAX_REQUEST_NUMBER and valid_prompt(value.prompt))


def valid_context(value):
    return (type(value) is ReplyContext
            and type(value.root_identity) is object
            and type(value.view_identity) is object
            and type(value.session_identity) is object
            and type(value.generation) is int and 0 <= value.generation <= MAX_CLOCK_MS
            and type(value.epoch) is int and 0 <= value.epoch <= MAX_CLOCK_MS)


def valid_result(value, request):
    if (type(value) is not ReplyResult or value.request is not request
            or not valid_request(request) or type(value.text) is not str
            or type(value.kind) is not ReplyKind):
        return False
    expected = SIMULATED_TEXT if value.kind is ReplyKind.SIMULATED else ERROR_TEXT
    return (value.text == expected and len(value.text) <= MAX_REPLY_CODEPOINTS
            and len(value.text.encode("utf-8", errors="strict")) <= MAX_REPLY_UTF8_BYTES)
