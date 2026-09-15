"""Central policy decisions for Nayeon capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from nayeon.policy.permissions import PermissionService
from nayeon.registry import Capability


class PolicyAction(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


@dataclass(frozen=True)
class PolicyDecision:
    action: PolicyAction
    reason: str

    @property
    def allowed(self) -> bool:
        return self.action is PolicyAction.ALLOW

    @property
    def requires_confirmation(self) -> bool:
        return self.action is PolicyAction.CONFIRM

    @property
    def denied(self) -> bool:
        return self.action is PolicyAction.DENY


class PolicyService:
    """Decides whether a capability may execute."""

    def __init__(
        self,
        permissions: PermissionService | None = None,
        blocked_capabilities: set[str] | None = None,
    ) -> None:
        self._permissions = permissions or PermissionService(default_allowed=True)
        self._blocked_capabilities = blocked_capabilities or set()

    def evaluate(self, capability: Capability) -> PolicyDecision:
        permission = self._permissions.check(capability.name)

        if not permission.allowed:
            return PolicyDecision(
                action=PolicyAction.DENY,
                reason=permission.reason,
            )

        if capability.name in self._blocked_capabilities:
            return PolicyDecision(
                action=PolicyAction.DENY,
                reason=f"Capability '{capability.name}' is blocked by policy.",
            )

        if capability.requires_confirmation:
            return PolicyDecision(
                action=PolicyAction.CONFIRM,
                reason=f"Capability '{capability.name}' requires user confirmation.",
            )

        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason=f"Capability '{capability.name}' is permitted.",
        )