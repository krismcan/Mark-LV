"""Core task models for Nayeon's agent runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskKind(str, Enum):
    """High-level execution categories."""

    LOCAL = "local"
    LLM_ASSISTED = "llm_assisted"
    AGENTIC = "agentic"


@dataclass(frozen=True)
class TaskRequest:
    """A normalized task waiting to be executed."""

    request: str
    kind: TaskKind
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_llm(self) -> bool:
        """Return whether this task requires an LLM call."""

        return self.kind in {
            TaskKind.LLM_ASSISTED,
            TaskKind.AGENTIC,
        }

    @property
    def is_local(self) -> bool:
        """Return whether this task can be handled locally."""

        return self.kind == TaskKind.LOCAL