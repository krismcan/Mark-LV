"""Structured audit logging for Nayeon."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import uuid
from typing import Any


class AuditEventType(str, Enum):
    POLICY_DECISION = "policy_decision"
    CONFIRMATION_CREATED = "confirmation_created"
    CONFIRMATION_APPROVED = "confirmation_approved"
    CONFIRMATION_REJECTED = "confirmation_rejected"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_SUCCEEDED = "execution_succeeded"
    EXECUTION_FAILED = "execution_failed"
    UNDO_REGISTERED = "undo_registered"
    UNDO_REGISTRATION_FAILED = "undo_registration_failed"

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    capability: str
    outcome: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class AuditService:
    """Records structured audit events, optionally persisting them as JSONL."""

    def __init__(self, log_path: Path | None = None) -> None:
        self._log_path = log_path
        self._events: list[AuditEvent] = []

    def record(
        self,
        event_type: AuditEventType,
        *,
        capability: str,
        outcome: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            capability=capability.strip(),
            outcome=outcome.strip(),
            message=message.strip(),
            details=dict(details or {}),
        )

        self._events.append(event)

        if self._log_path is not None:
            self._write_event(event)

        return event

    def all(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def _write_event(self, event: AuditEvent) -> None:
        assert self._log_path is not None

        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        payload = asdict(event)
        payload["event_type"] = event.event_type.value
        payload["timestamp"] = event.timestamp.isoformat()

        with self._log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")