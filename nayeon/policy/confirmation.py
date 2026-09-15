"""One-time confirmation tokens for protected Nayeon actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets


@dataclass(frozen=True)
class ConfirmationRequest:
    token: str
    capability: str
    request: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class ConfirmationResult:
    approved: bool
    reason: str


class ConfirmationService:
    """Creates and validates short-lived, one-time action confirmations."""

    def __init__(self, *, ttl_seconds: int = 120) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero.")

        self._ttl = timedelta(seconds=ttl_seconds)
        self._pending: dict[str, ConfirmationRequest] = {}

    def create(
        self,
        capability: str,
        request: str,
    ) -> ConfirmationRequest:
        capability = capability.strip()
        request = request.strip()

        if not capability:
            raise ValueError("Capability name is required.")

        if not request:
            raise ValueError("Request is required.")

        now = datetime.now(timezone.utc)
        token = secrets.token_urlsafe(32)

        confirmation = ConfirmationRequest(
            token=token,
            capability=capability,
            request=request,
            created_at=now,
            expires_at=now + self._ttl,
        )

        self._pending[token] = confirmation
        return confirmation

    def approve(
        self,
        token: str,
        *,
        capability: str,
        request: str,
    ) -> ConfirmationResult:
        confirmation = self._pending.pop(token, None)

        if confirmation is None:
            return ConfirmationResult(
                approved=False,
                reason="Confirmation token is invalid or has already been used.",
            )

        now = datetime.now(timezone.utc)

        if now > confirmation.expires_at:
            return ConfirmationResult(
                approved=False,
                reason="Confirmation token has expired.",
            )

        if confirmation.capability != capability:
            return ConfirmationResult(
                approved=False,
                reason="Confirmation does not match the requested capability.",
            )

        if confirmation.request != request:
            return ConfirmationResult(
                approved=False,
                reason="Confirmation does not match the requested action.",
            )

        return ConfirmationResult(
            approved=True,
            reason="Action confirmed.",
        )

    def reject(self, token: str) -> ConfirmationResult:
        confirmation = self._pending.pop(token, None)

        if confirmation is None:
            return ConfirmationResult(
                approved=False,
                reason="Confirmation token is invalid or has already been used.",
            )

        return ConfirmationResult(
            approved=False,
            reason="Action rejected by user.",
        )