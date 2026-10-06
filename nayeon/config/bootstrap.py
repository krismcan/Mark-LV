"""Compose the presentation owner from an explicit caller-selected path."""

from __future__ import annotations

from pathlib import Path

from nayeon.config.persistence import PresentationConfigurationFileStore
from nayeon.config.service import PresentationConfigurationService


def bootstrap_presentation_configuration(
    path: Path,
) -> PresentationConfigurationService:
    """Return one initialized service, propagating sealed initialization errors."""
    store = PresentationConfigurationFileStore(path)
    service = PresentationConfigurationService(store)
    service.initialize()
    return service
