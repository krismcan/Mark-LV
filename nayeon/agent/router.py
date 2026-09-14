"""Task routing policy for Nayeon's agent runtime."""

from __future__ import annotations

from dataclasses import dataclass

from nayeon.registry import CapabilityRegistry, Capability

from .task import TaskKind, TaskRequest


@dataclass(frozen=True)
class RoutingDecision:
    """Decision returned by the task router."""

    task: TaskRequest
    use_llm: bool
    reason: str
    capability: Capability | None = None


class TaskRouter:
    """Classify tasks and decide whether an LLM is required."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def route(self, request: str) -> RoutingDecision:
        """Return a routing decision for a user request."""

        normalized = request.strip().lower()

        if not normalized:
            raise ValueError("Task request cannot be empty.")

        capability = self._find_capability(normalized)

        if capability is not None:
            task = TaskRequest(
                request=request,
                kind=TaskKind(capability.execution_mode.value),
                metadata={
                    "capability": capability.name,
                    "service": capability.service,
                },
            )

            return RoutingDecision(
                task=task,
                use_llm=capability.requires_llm,
                reason=(
                    f"Matched capability '{capability.name}' "
                    f"for service '{capability.service}'."
                ),
                capability=capability,
            )

        kind = self._classify_fallback(normalized)

        task = TaskRequest(
            request=request,
            kind=kind,
        )

        if task.is_local:
            return RoutingDecision(
                task=task,
                use_llm=False,
                reason=(
                    "Task can be handled by a deterministic "
                    "local capability."
                ),
            )

        if kind == TaskKind.LLM_ASSISTED:
            return RoutingDecision(
                task=task,
                use_llm=True,
                reason=(
                    "No known local capability matched; "
                    "interpretation or summarisation may be required."
                ),
            )

        return RoutingDecision(
            task=task,
            use_llm=True,
            reason=(
                "No known capability matched; "
                "planning or multi-step reasoning may be required."
            ),
        )

    def _find_capability(
        self,
        request: str,
    ) -> Capability | None:
        """Return the first capability matching the request."""

        for capability in self._registry.all():
            for pattern in capability.intent_patterns:
                if request.startswith(pattern.lower()):
                    return capability

        return None

    def _classify_fallback(self, request: str) -> TaskKind:
        """Classify requests that do not match a known capability."""

        llm_assisted_phrases = (
            "summarise ",
            "summarize ",
            "explain ",
            "translate ",
            "rewrite ",
            "analyse ",
            "analyze ",
        )

        if request.startswith(llm_assisted_phrases):
            return TaskKind.LLM_ASSISTED

        agentic_phrases = (
            "research ",
            "find the best ",
            "compare ",
            "plan ",
            "figure out ",
            "fix ",
            "build ",
            "investigate ",
        )

        if request.startswith(agentic_phrases):
            return TaskKind.AGENTIC

        # Ambiguous requests are treated as LLM-assisted until
        # richer intent matching exists.
        return TaskKind.LLM_ASSISTED