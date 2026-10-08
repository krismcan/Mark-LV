"""Initialize provider connection metadata from an explicitly supplied path."""

from pathlib import Path

from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_service import ProviderConnectionService


def bootstrap_provider_connection(path: Path) -> ProviderConnectionService:
    """Load connection metadata without activating a provider."""
    store = ProviderConnectionFileStore(path)
    service = ProviderConnectionService(store)
    service.initialize()
    return service
