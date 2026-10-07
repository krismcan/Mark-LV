"""Canonical, dedicated OpenAI API-key client construction.

Plaintext is local to construction; the SDK necessarily retains auth material.
This boundary does not provide cryptographic memory isolation or erasure.
"""

from math import isfinite

from nayeon.secrets.contracts import SecretValue


OPENAI_API_BASE_URL = "https://api.openai.com/v1"
OPENAI_AUTHORIZATION_HEADER = "Authorization"


class OpenAIClientConstructionError(RuntimeError):
    """A construction failure with a fixed, credential-free message."""


def _load_openai_sdk():
    """Load only the pinned SDK's public constructors, when needed."""
    from openai import OpenAI, DefaultHttpxClient

    return OpenAI, DefaultHttpxClient


def create_openai_client(
    api_key: SecretValue,
    *,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
) -> object:
    """Construct a client with bounded routing and explicit authorization."""
    if type(api_key) is not SecretValue:
        raise TypeError("API key must be an exact SecretValue")
    if timeout_seconds is not None:
        if type(timeout_seconds) not in (int, float):
            raise TypeError("Timeout must be an exact int or float")
        # Positive integers are always finite; avoid float overflow on large ints.
        if timeout_seconds <= 0 or (
            type(timeout_seconds) is float and not isfinite(timeout_seconds)
        ):
            raise ValueError("Timeout must be finite and positive")
    if max_retries is not None:
        if type(max_retries) is not int:
            raise TypeError("Retries must be an exact int")
        if max_retries < 0:
            raise ValueError("Retries must be nonnegative")

    try:
        plaintext = api_key.reveal()
        OpenAI, DefaultHttpxClient = _load_openai_sdk()
        http_client = DefaultHttpxClient(trust_env=False, follow_redirects=False)
        kwargs = {
            "api_key": plaintext,
            "base_url": OPENAI_API_BASE_URL,
            "default_headers": {OPENAI_AUTHORIZATION_HEADER: f"Bearer {plaintext}"},
            "http_client": http_client,
        }
        if timeout_seconds is not None:
            kwargs["timeout"] = timeout_seconds
        if max_retries is not None:
            kwargs["max_retries"] = max_retries
        constructed = False
        try:
            client = OpenAI(**kwargs)
            constructed = True
            return client
        finally:
            if not constructed:
                try:
                    http_client.close()
                except Exception:
                    pass
    except Exception:
        raise OpenAIClientConstructionError("OpenAI client construction failed") from None
