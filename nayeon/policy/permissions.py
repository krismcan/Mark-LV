"""Capability permission controls for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


class PermissionService:
    """Controls whether individual capabilities are permitted to operate."""

    def __init__(self, *, default_allowed: bool = True) -> None:
        self._default_allowed = default_allowed
        self._granted: set[str] = set()
        self._revoked: set[str] = set()

    def grant(self, capability: str) -> None:
        capability = self._normalize(capability)

        self._revoked.discard(capability)
        self._granted.add(capability)

    def revoke(self, capability: str) -> None:
        capability = self._normalize(capability)

        self._granted.discard(capability)
        self._revoked.add(capability)

    def check(self, capability: str) -> PermissionDecision:
        capability = self._normalize(capability)

        if capability in self._revoked:
            return PermissionDecision(
                allowed=False,
                reason=f"Capability '{capability}' is not permitted.",
            )

        if capability in self._granted:
            return PermissionDecision(
                allowed=True,
                reason=f"Capability '{capability}' is explicitly permitted.",
            )

        if self._default_allowed:
            return PermissionDecision(
                allowed=True,
                reason=f"Capability '{capability}' is permitted by default.",
            )

        return PermissionDecision(
            allowed=False,
            reason=f"Capability '{capability}' has not been granted permission.",
        )

    @staticmethod
    def _normalize(capability: str) -> str:
        capability = capability.strip()

        if not capability:
            raise ValueError("Capability name is required.")

        return capability