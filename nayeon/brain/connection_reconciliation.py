"""Explicit, read-only reconciliation of provider metadata and key availability.

Observations are neither atomic snapshots nor authorization to use credentials.
No credential plaintext, validator, provider SDK, mutation, or runtime wiring.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from nayeon.brain.connection_bootstrap import bootstrap_provider_connection
from nayeon.brain.connection_readiness import (
    ProviderConnectionReadinessStatus,
    assess_provider_connection_readiness,
)
from nayeon.secrets.contracts import SecretIdentifier


class CredentialAvailability(Protocol):
    """Least-authority read interface, narrower than SecretBackend."""

    def is_available(self, identifier: SecretIdentifier) -> bool: ...


class ConnectionObservationStatus(str, Enum):
    SETUP_REQUIRED = "setup_required"
    UNCONFIGURED_CREDENTIAL_PRESENT = "unconfigured_credential_present"
    CREDENTIAL_REQUIRED = "credential_required"
    VALIDATION_REQUIRED = "validation_required"
    UNSUPPORTED_CONFIGURATION = "unsupported_configuration"
    CHANGED_DURING_OBSERVATION = "changed_during_observation"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True, repr=False)
class ConnectionObservation:
    """Non-secret observation. A subsequent change can invalidate any result."""

    status: ConnectionObservationStatus

    def __post_init__(self) -> None:
        if type(self.status) is not ConnectionObservationStatus:
            raise TypeError("Observation must contain an exact status")


_IDENTIFIER = SecretIdentifier("openai.api_key")


def observe_connection(
    path: Path, availability: CredentialAvailability,
) -> ConnectionObservation:
    """Read metadata fresh, optionally check canonical key presence, re-read.

    The read/recheck only detects some changes; it is NOT a transaction,
    freshness guarantee, successful validation or a permission to act.
    """
    if type(path) is not type(Path()):
        raise TypeError("Path must be an exact native pathlib.Path")
    try:
        supported = callable(getattr(availability, "is_available", None))
    except Exception:
        raise TypeError("Availability source must provide is_available") from None
    if not supported:
        raise TypeError("Availability source must provide is_available")

    try:
        first = bootstrap_provider_connection(path)
        first_status = assess_provider_connection_readiness(first).status
        first_document = first.current
    except Exception:
        return ConnectionObservation(ConnectionObservationStatus.UNKNOWN)

    # Never look up a credential for a configuration selecting another
    # provider/identifier. Even this unsupported assessment is rechecked.
    if first_status is ProviderConnectionReadinessStatus.UNSUPPORTED:
        try:
            second = bootstrap_provider_connection(path)
            second_status = assess_provider_connection_readiness(second).status
            if second.current != first_document or second_status is not first_status:
                return ConnectionObservation(ConnectionObservationStatus.CHANGED_DURING_OBSERVATION)
        except Exception:
            return ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
        return ConnectionObservation(ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION)

    # No value, get, validation, SDK/client, deletion or storage mutation.
    try:
        present = availability.is_available(_IDENTIFIER)
        if type(present) is not bool:
            return ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
    except Exception:
        return ConnectionObservation(ConnectionObservationStatus.UNKNOWN)

    try:
        second = bootstrap_provider_connection(path)
        second_status = assess_provider_connection_readiness(second).status
        if second.current != first_document or second_status is not first_status:
            return ConnectionObservation(ConnectionObservationStatus.CHANGED_DURING_OBSERVATION)
    except Exception:
        return ConnectionObservation(ConnectionObservationStatus.UNKNOWN)

    if first_status is ProviderConnectionReadinessStatus.UNCONFIGURED:
        status = (
            ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT if present
            else ConnectionObservationStatus.SETUP_REQUIRED
        )
    elif first_status is ProviderConnectionReadinessStatus.READY_FOR_COMPOSITION:
        status = (
            ConnectionObservationStatus.VALIDATION_REQUIRED if present
            else ConnectionObservationStatus.CREDENTIAL_REQUIRED
        )
    else:
        return ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
    return ConnectionObservation(status)
