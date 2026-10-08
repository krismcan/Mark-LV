"""Versioned non-secret connection metadata and a pure, strict mapping codec."""

from dataclasses import dataclass

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.secrets.contracts import SecretIdentifier


PROVIDER_CONNECTION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True, repr=False)
class ProviderConnectionDocumentV1:
    """One optional connection; metadata grants no credential binding authority."""

    schema_version: int = PROVIDER_CONNECTION_SCHEMA_VERSION
    connection: ProviderConnectionConfiguration | None = None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise TypeError("Schema version must be an exact built-in int")
        if self.schema_version != PROVIDER_CONNECTION_SCHEMA_VERSION:
            raise ValueError("Unsupported provider connection schema version")
        if self.connection is not None and type(self.connection) is not ProviderConnectionConfiguration:
            raise TypeError("Connection must be an exact ProviderConnectionConfiguration or None")


def _validate_mapping(data: object, keys: tuple[str, ...]) -> None:
    if type(data) is not dict:
        raise TypeError("Provider connection section must be an exact built-in dict")
    if any(type(key) is not str for key in data):
        raise TypeError("Provider connection keys must be exact built-in str")
    if len(data) != len(keys) or any(key not in data for key in keys):
        raise ValueError("Provider connection section has missing or unknown keys")


def parse_provider_connection_document(data: object) -> ProviderConnectionDocumentV1:
    """Parse without coercion, normalization, migration or mutable input retention."""
    _validate_mapping(data, ("schema_version", "connection"))
    connection = data["connection"]
    if connection is not None:
        _validate_mapping(connection, ("provider", "model", "credential"))
        connection = ProviderConnectionConfiguration(
            provider=connection["provider"],
            model=connection["model"],
            credential=SecretIdentifier(connection["credential"]),
        )
    return ProviderConnectionDocumentV1(
        schema_version=data["schema_version"], connection=connection
    )


def provider_connection_document_to_mapping(
    document: ProviderConnectionDocumentV1,
) -> dict[str, object]:
    """Encode fresh canonical mappings containing only safe identifier metadata."""
    if type(document) is not ProviderConnectionDocumentV1:
        raise TypeError("Document must be an exact ProviderConnectionDocumentV1")
    connection = document.connection
    return {
        "schema_version": PROVIDER_CONNECTION_SCHEMA_VERSION,
        "connection": None if connection is None else {
            "provider": connection.provider,
            "model": connection.model,
            "credential": connection.credential.value,
        },
    }
