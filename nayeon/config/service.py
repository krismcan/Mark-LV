"""Process-local ownership of presentation configuration; no runtime wiring."""

from __future__ import annotations

from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.config.persistence import PresentationConfigurationFileStore


class PresentationConfigurationService:
    """Own one immutable document through an explicit sealed file store.

    Initialization is lazy and retryable after failure. Successful initialization
    is cached for this instance; replacement persists before changing ownership.
    Callers serialize lifecycle operations; no concurrent-operation API is offered.
    """

    __slots__ = ("_store", "_current")

    def __init__(self, store: PresentationConfigurationFileStore) -> None:
        if type(store) is not PresentationConfigurationFileStore:
            raise TypeError("Store must be an exact presentation configuration file store")
        self._store = store
        self._current: PresentationConfigurationDocumentV1 | None = None

    @property
    def is_initialized(self) -> bool:
        return self._current is not None

    @property
    def current(self) -> PresentationConfigurationDocumentV1:
        if self._current is None:
            raise RuntimeError("Presentation configuration service is not initialized")
        return self._current

    def initialize(self) -> PresentationConfigurationDocumentV1:
        if self._current is None:
            document = self._store.load()
            if document is None:
                document = PresentationConfigurationDocumentV1()
            self._current = document
        return self._current

    def replace(self, document: PresentationConfigurationDocumentV1) -> PresentationConfigurationDocumentV1:
        if self._current is None:
            raise RuntimeError("Presentation configuration service is not initialized")
        if type(document) is not PresentationConfigurationDocumentV1:
            raise TypeError("Document must be an exact presentation configuration document")
        self._store.save(document)
        self._current = document
        return document
