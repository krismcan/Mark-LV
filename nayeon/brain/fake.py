"""Fake AI provider used for local architecture tests."""

from __future__ import annotations

from nayeon.brain.service import AIMessage, AIResponse


class FakeAIProvider:
    """Simple deterministic provider for local testing."""

    name = "fake"
    model = "test-model"

    def generate(
        self,
        messages: list[AIMessage],
        *,
        system_prompt: str | None = None,
    ) -> AIResponse:
        """Return a deterministic response."""

        last_message = messages[-1]

        return AIResponse(
            text=f"FAKE RESPONSE: {last_message.content}",
            provider=self.name,
            model=self.model,
            usage={"input_messages": len(messages)},
        )