"""Task routing policy for Nayeon's agent runtime."""

from __future__ import annotations

from dataclasses import dataclass

from .task import TaskKind, TaskRequest


@dataclass(frozen=True)
class RoutingDecision:
    """Decision returned by the task router."""

    task: TaskRequest
    use_llm: bool
    reason: str


class TaskRouter:
    """Classify tasks and decide whether an LLM is required."""

    def route(self, request: str) -> RoutingDecision:
        """Return a routing decision for a user request."""

        normalized = request.strip().lower()

        if not normalized:
            raise ValueError("Task request cannot be empty.")

        kind = self._classify(normalized)

        task = TaskRequest(
            request=request,
            kind=kind,
        )

        if task.is_local:
            return RoutingDecision(
                task=task,
                use_llm=False,
                reason="Task can be handled by a deterministic local capability.",
            )

        if kind == TaskKind.LLM_ASSISTED:
            return RoutingDecision(
                task=task,
                use_llm=True,
                reason="Task requires interpretation or summarisation.",
            )

        return RoutingDecision(
            task=task,
            use_llm=True,
            reason="Task requires planning or multi-step reasoning.",
        )

    def _classify(self, request: str) -> TaskKind:
        """Classify obvious deterministic tasks without calling an LLM."""

        local_prefixes = (
            "open ",
            "launch ",
            "start ",
            "close ",
            "rename ",
            "move ",
            "copy ",
            "delete ",
            "create ",
            "turn the volume",
            "increase the volume",
            "decrease the volume",
            "turn on ",
            "turn off ",
        )

        if request.startswith(local_prefixes):
            return TaskKind.LOCAL

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

        # Until richer intent detection exists, ambiguous requests are
        # treated as LLM-assisted rather than pretending we know their intent.
        return TaskKind.LLM_ASSISTED