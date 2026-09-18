"""Structured capability contracts for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class StructuredCapabilityRequest:
    """
    Structured input produced after intent resolution.

    Arguments are still untrusted at this stage. A capability must validate
    and normalize them before any side effect is allowed to occur.
    """

    original_request: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized_request = self.original_request.strip()

        if not normalized_request:
            raise ValueError("original_request must not be empty")

        object.__setattr__(
            self,
            "original_request",
            normalized_request,
        )

        object.__setattr__(
            self,
            "arguments",
            dict(self.arguments),
        )


@runtime_checkable
class StructuredCapability(Protocol):
    """
    Optional contract for capabilities that support structured execution.

    Validation and execution are deliberately separate so that validated
    arguments can later pass through policy and confirmation before any
    side effect occurs.
    """

    def validate_arguments(
        self,
        arguments: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Validate and normalize structured arguments.

        Must raise ValueError or TypeError when input is invalid.
        Must not perform the capability's side effect.
        """
        ...

    def execute_structured(
        self,
        arguments: Mapping[str, Any],
    ) -> object:
        """
        Execute using previously validated structured arguments.
        """
        ...