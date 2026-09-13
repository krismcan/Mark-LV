"""Nayeon secrets service.

Secrets are deliberately kept separate from normal configuration.

For the first Nayeon foundation, secrets are read from environment
variables only. They are never written to the repository or config files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class SecretNotFoundError(RuntimeError):
    """Raised when a required secret is not available."""


@dataclass(frozen=True)
class SecretReference:
    """Description of an environment-backed secret."""

    name: str
    environment_variable: str


class SecretStore:
    """Read secrets from the process environment."""

    def __init__(
        self,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._environment = (
            os.environ if environment is None else environment
        )

    def get(
        self,
        name: str,
        *,
        required: bool = False,
    ) -> str | None:
        """Return a secret from an environment variable."""

        value = self._environment.get(name)

        if value is None or not value.strip():
            if required:
                raise SecretNotFoundError(
                    f"Required secret is not configured: {name}"
                )

            return None

        return value

    def require(self, name: str) -> str:
        """Return a required secret or raise an error."""

        value = self.get(name, required=True)

        if value is None:
            raise SecretNotFoundError(
                f"Required secret is not configured: {name}"
            )

        return value

    def is_available(self, name: str) -> bool:
        """Return whether a non-empty secret is available."""

        value = self.get(name)
        return value is not None