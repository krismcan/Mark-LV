"""Process-local ownership of one non-secret connection; no runtime wiring."""

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore


class ProviderConnectionService:
    """Cache one immutable document and persist each replacement before swapping.

    Initialization is lazy and retryable after failure. Callers serialize lifecycle
    operations. Future trusted composition independently verifies provider-to-
    credential identity; this metadata service grants no credential authority.
    """

    __slots__ = ("_store", "_current")

    def __init__(self, store: ProviderConnectionFileStore) -> None:
        if type(store) is not ProviderConnectionFileStore:
            raise TypeError("Store must be an exact ProviderConnectionFileStore")
        self._store = store
        self._current: ProviderConnectionDocumentV1 | None = None

    @property
    def is_initialized(self) -> bool:
        return self._current is not None

    @property
    def current(self) -> ProviderConnectionDocumentV1:
        if self._current is None:
            raise RuntimeError("Provider connection service is not initialized")
        return self._current

    def initialize(self) -> ProviderConnectionDocumentV1:
        if self._current is None:
            document = self._store.load()
            if document is None:
                document = ProviderConnectionDocumentV1(connection=None)
            self._current = document
        return self._current

    def replace(self, configuration: ProviderConnectionConfiguration) -> ProviderConnectionDocumentV1:
        if self._current is None:
            raise RuntimeError("Provider connection service is not initialized")
        if type(configuration) is not ProviderConnectionConfiguration:
            raise TypeError("Configuration must be an exact ProviderConnectionConfiguration")
        document = ProviderConnectionDocumentV1(connection=configuration)
        self._store.save(document)
        self._current = document
        return document

    def clear(self) -> ProviderConnectionDocumentV1:
        if self._current is None:
            raise RuntimeError("Provider connection service is not initialized")
        document = ProviderConnectionDocumentV1(connection=None)
        self._store.save(document)
        self._current = document
        return document
