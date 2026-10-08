"""Explicit-path, metadata-only startup without provider activation."""

from dataclasses import dataclass
from pathlib import Path

from nayeon.brain.connection_bootstrap import bootstrap_provider_connection
from nayeon.brain.connection_readiness import (
    ProviderConnectionReadiness,
    assess_provider_connection_readiness,
)
from nayeon.brain.connection_service import ProviderConnectionService


@dataclass(frozen=True, slots=True, repr=False)
class ProviderConnectionStartupResult:
    owner: ProviderConnectionService
    readiness: ProviderConnectionReadiness

    def __post_init__(self) -> None:
        if type(self.owner) is not ProviderConnectionService:
            raise TypeError("Owner must be an exact provider connection service")
        if type(self.readiness) is not ProviderConnectionReadiness:
            raise TypeError("Readiness must be an exact provider connection readiness")


def startup_provider_connection(path: Path) -> ProviderConnectionStartupResult:
    """Bootstrap one owner, assess cached metadata and return without activation."""
    owner = bootstrap_provider_connection(path)
    readiness = assess_provider_connection_readiness(owner)
    return ProviderConnectionStartupResult(owner=owner, readiness=readiness)
