"""Bounded file persistence for the sealed presentation document; no runtime wiring."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from nayeon.config.document import (
    PresentationConfigurationDocumentV1,
    parse_presentation_configuration_document,
    presentation_configuration_document_to_mapping,
)


MAX_PRESENTATION_CONFIGURATION_FILE_BYTES = 65536


class PresentationConfigurationPersistenceError(Exception):
    """File access or invalid persisted content, with no personal data in messages."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("Non-standard JSON constant")


class PresentationConfigurationFileStore:
    """Use only an explicit native Path; parent directories must already exist.

    Saves replace the destination atomically after syncing and closing a temporary
    file in the same directory. No directory creation, migration, locking or
    power-loss directory durability is provided. Concurrent saves are last-writer
    wins. Callers own the destination path and its filesystem access permissions.
    """

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        # Path constructs the native concrete type (WindowsPath or PosixPath).
        # Reject subclasses as well as coercible strings/path-like objects.
        if type(path) is not type(Path()):
            raise TypeError("Path must be an exact native pathlib.Path")
        self._path = path

    def load(self) -> PresentationConfigurationDocumentV1 | None:
        try:
            stream = self._path.open("rb")
        except FileNotFoundError:
            return None
        except OSError:
            raise PresentationConfigurationPersistenceError("Cannot read presentation configuration") from None
        try:
            with stream:
                content = stream.read(MAX_PRESENTATION_CONFIGURATION_FILE_BYTES + 1)
            if len(content) > MAX_PRESENTATION_CONFIGURATION_FILE_BYTES:
                raise ValueError("Presentation configuration exceeds size limit")
            data = json.loads(
                content.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
            return parse_presentation_configuration_document(data)
        except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
            raise PresentationConfigurationPersistenceError("Invalid or unreadable presentation configuration") from None

    def save(self, document: PresentationConfigurationDocumentV1) -> None:
        # Keep programmer misuse distinct, and reject before any filesystem I/O.
        if type(document) is not PresentationConfigurationDocumentV1:
            raise TypeError("Document must be an exact presentation configuration document")
        temporary_path = None
        try:
            data = presentation_configuration_document_to_mapping(document)
            content = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
            if len(content) > MAX_PRESENTATION_CONFIGURATION_FILE_BYTES:
                raise ValueError("Presentation configuration exceeds size limit")
            with tempfile.NamedTemporaryFile(mode="wb", dir=self._path.parent, delete=False) as stream:
                temporary_path = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self._path)
        except (OSError, UnicodeError, ValueError, TypeError):
            raise PresentationConfigurationPersistenceError("Cannot save presentation configuration") from None
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    # Best effort; do not hide the original error or undo a replace.
                    pass
