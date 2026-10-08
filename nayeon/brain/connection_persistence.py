"""Bounded persistence of non-secret connection documents; no composition."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from nayeon.brain.connection_document import (
    ProviderConnectionDocumentV1,
    parse_provider_connection_document,
    provider_connection_document_to_mapping,
)


MAX_PROVIDER_CONNECTION_FILE_BYTES = 16384


class ProviderConnectionPersistenceError(Exception):
    """Fixed safe file/content errors without path or connection metadata."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("Non-standard JSON constant")


class ProviderConnectionFileStore:
    """Use an explicit native Path; caller owns path and filesystem permissions.

    Saves use same-directory atomic replace after temporary file fsync and close.
    No locking is provided; concurrent saves are last-writer-wins. No power-loss
    directory fsync durability is claimed. Parents must already exist; no
    directory creation, migration or permission mutation is performed.
    """

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        # Path constructs the native concrete WindowsPath or PosixPath type.
        if type(path) is not type(Path()):
            raise TypeError("Path must be an exact native pathlib.Path")
        self._path = path

    def load(self) -> ProviderConnectionDocumentV1 | None:
        try:
            stream = self._path.open("rb")
        except FileNotFoundError:
            return None
        except OSError:
            raise ProviderConnectionPersistenceError("Cannot read provider connection configuration") from None
        try:
            with stream:
                content = stream.read(MAX_PROVIDER_CONNECTION_FILE_BYTES + 1)
            if len(content) > MAX_PROVIDER_CONNECTION_FILE_BYTES:
                raise ValueError("Provider connection configuration exceeds size limit")
            data = json.loads(
                content.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
            return parse_provider_connection_document(data)
        except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
            raise ProviderConnectionPersistenceError("Invalid or unreadable provider connection configuration") from None

    def save(self, document: ProviderConnectionDocumentV1) -> None:
        # Programmer misuse is rejected before any filesystem I/O.
        if type(document) is not ProviderConnectionDocumentV1:
            raise TypeError("Document must be an exact ProviderConnectionDocumentV1")
        temporary_path = None
        try:
            data = provider_connection_document_to_mapping(document)
            content = json.dumps(
                data, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
            if len(content) > MAX_PROVIDER_CONNECTION_FILE_BYTES:
                raise ValueError("Provider connection configuration exceeds size limit")
            with tempfile.NamedTemporaryFile(mode="wb", dir=self._path.parent, delete=False) as stream:
                temporary_path = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self._path)
        except (OSError, UnicodeError, ValueError, TypeError):
            raise ProviderConnectionPersistenceError("Cannot save provider connection configuration") from None
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    # Best effort; neither mask a failure nor undo successful replace.
                    pass
