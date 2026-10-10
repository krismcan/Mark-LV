"""Phase 8.21: explicitly refreshed first-run read-only status controller.

One user-driven refresh makes exactly one injected observation call. A previous
result is never authorization or proof that the underlying secret still exists.
No callbacks to launch, validate, mutate or persist are exposed.
"""
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection_reconciliation import ConnectionObservation
from nayeon.brain.first_run_summary import FirstRunSummary, summarize_first_run


class FirstRunRefreshStatus(str, Enum):
    OBSERVED = "observed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True, repr=False)
class FirstRunRefresh:
    status: FirstRunRefreshStatus
    summary: FirstRunSummary | None = None
    requires_reobservation: bool = True

    def __post_init__(self) -> None:
        if type(self.status) is not FirstRunRefreshStatus:
            raise TypeError("Exact refresh status required")
        if self.status is FirstRunRefreshStatus.OBSERVED:
            if type(self.summary) is not FirstRunSummary:
                raise TypeError("A successful refresh requires a typed summary")
        elif self.summary is not None:
            raise TypeError("Unavailable observations cannot carry stale data")
        if self.requires_reobservation is not True:
            raise ValueError("A refresh does not grant continued authority")


class FirstRunReadOnlyController:
    """Use only from an explicitly invoked trusted host / UI callback."""

    __slots__ = ("_observe", "_refreshing")

    def __init__(self, *, observe: Callable[[], ConnectionObservation]) -> None:
        if not callable(observe):
            raise TypeError("An injected read-only observation callback is required")
        self._observe = observe
        self._refreshing = False

    def refresh(self) -> FirstRunRefresh:
        if self._refreshing:
            return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
        self._refreshing = True
        try:
            observation = self._observe()
            if type(observation) is not ConnectionObservation:
                return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
            summary = summarize_first_run(observation)
            return FirstRunRefresh(FirstRunRefreshStatus.OBSERVED, summary)
        except Exception:
            return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
        finally:
            self._refreshing = False
