"""Phase 8.21: explicitly refreshed first-run read-only status controller.

One user-driven refresh makes exactly one injected observation call. A previous
result is never authorization or proof that the underlying secret still exists.
No callbacks to launch, validate, mutate or persist are exposed.
P318 adds an explicit paired synthetic mode; it makes no live observation or
freshness guarantee and never falls back to the legacy callback.
"""
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from nayeon.brain.connection_reconciliation import ConnectionObservation
from nayeon.brain.first_run_summary import (
    FirstRunSummary, summarize_first_run, summarize_pending_custody_first_run,
)
from nayeon.brain.pending_custody_status_view import PendingCustodyStatusView


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

    __slots__ = ("_observe", "_observe_paired_synthetic", "_refreshing",
                 "_refresh_invalidated")

    def __init__(
        self, *, observe: Callable[[], ConnectionObservation] | None = None,
        observe_paired_synthetic: Callable[
            [], tuple[ConnectionObservation, PendingCustodyStatusView]
        ] | None = None,
    ) -> None:
        # A single callback supplies the whole pair. Two independent callbacks
        # would permit accidental mixing of different refresh observations.
        if (observe is None) == (observe_paired_synthetic is None):
            raise TypeError("Exactly one read-only observation mode is required")
        if not callable(observe if observe is not None else observe_paired_synthetic):
            raise TypeError("An injected read-only observation callback is required")
        self._observe = observe
        self._observe_paired_synthetic = observe_paired_synthetic
        self._refreshing = False
        self._refresh_invalidated = False

    @property
    def uses_paired_synthetic_observation(self) -> bool:
        """Presentation mode only; does not observe or grant authority."""
        return self._observe_paired_synthetic is not None

    def refresh(self) -> FirstRunRefresh:
        if self._refreshing:
            if self.uses_paired_synthetic_observation:
                self._refresh_invalidated = True
            return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
        self._refreshing = True
        self._refresh_invalidated = False
        try:
            if self.uses_paired_synthetic_observation:
                # Explicit synthetic seam only, with no host mounting, cached
                # observation, freshness claim, retry or legacy fallback.
                pair = self._observe_paired_synthetic()
                if type(pair) is not tuple or len(pair) != 2:
                    return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
                observation, custody = pair
                if (type(observation) is not ConnectionObservation or
                        type(custody) is not PendingCustodyStatusView):
                    return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
                # Recheck existing model invariants at this input boundary,
                # including exact instances forged around frozen constructors.
                ConnectionObservation.__post_init__(observation)
                PendingCustodyStatusView.__post_init__(custody)
                summary = summarize_pending_custody_first_run(observation, custody)
                if self._refresh_invalidated:
                    return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
            else:
                observation = self._observe()
                if type(observation) is not ConnectionObservation:
                    return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
                summary = summarize_first_run(observation)
            return FirstRunRefresh(FirstRunRefreshStatus.OBSERVED, summary)
        except Exception:
            return FirstRunRefresh(FirstRunRefreshStatus.UNAVAILABLE)
        finally:
            self._refreshing = False
