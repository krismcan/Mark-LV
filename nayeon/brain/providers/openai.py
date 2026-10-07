"""OpenAI provider for Nayeon's AI service."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from nayeon.brain.service import AIMessage, AIResponse
from nayeon.secrets.contracts import SecretIdentifier
from nayeon.secrets.resolver import BoundSecretResolver


class OpenAIProviderInitializationError(RuntimeError):
    """Client construction failed without disclosing credential details."""


class OpenAIProvider:
    """OpenAI-backed provider for Nayeon's reasoning model."""

    name = "openai"

    def __init__(
        self,
        api_key: BoundSecretResolver,
        *,
        model: str = "gpt-5.6",
    ) -> None:
        if type(api_key) is not BoundSecretResolver:
            raise TypeError("API key must be an exact BoundSecretResolver")
        if api_key.identifier != SecretIdentifier("openai.api_key"):
            raise ValueError("API key resolver has an invalid identifier")
        self._api_key: BoundSecretResolver | None = api_key
        self._model = model
        self._client: OpenAI | None = None

    @property
    def model(self) -> str:
        """Return the configured OpenAI model."""

        return self._model

    def _get_client(self) -> OpenAI:
        """Create the OpenAI client when it is first needed."""

        if self._client is None:
            secret = self._api_key.resolve()
            try:
                client = OpenAI(api_key=secret.reveal())
            except Exception:
                raise OpenAIProviderInitializationError(
                    "OpenAI provider initialization failed"
                ) from None
            self._client = client
            self._api_key = None

        return self._client

    def generate(
        self,
        messages: list[AIMessage],
        *,
        system_prompt: str | None = None,
    ) -> AIResponse:
        """Generate a response using the OpenAI Responses API."""

        if not messages:
            raise ValueError("At least one message is required.")

        input_messages: list[dict[str, Any]] = []

        for message in messages:
            input_messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        request_args: dict[str, Any] = {
            "model": self._model,
            "input": input_messages,
        }

        if system_prompt:
            request_args["instructions"] = system_prompt

        response = self._get_client().responses.create(
            **request_args,
        )

        usage: dict[str, object] = {}

        if response.usage is not None:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return AIResponse(
            text=response.output_text,
            provider=self.name,
            model=self._model,
            usage=usage,
        )
