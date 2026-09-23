import logging

import groq

from ai.provider import LLMProvider
from errors import RateLimitedError, UpstreamError

log = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Default provider: open-weight models on Groq (fast, free-tier friendly inference)."""

    name = "Groq"

    # Reasoning models spend tokens thinking before they answer; give them headroom
    # and keep the effort low (these prompts are short, structured tasks).
    REASONING_PREFIXES = ("openai/gpt-oss", "qwen/")
    REASONING_TOKEN_BUDGET = 1024

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        if not api_key:
            raise UpstreamError("The AI provider is not configured (missing GROQ_API_KEY).", retryable=False)
        self.client = groq.Groq(api_key=api_key, max_retries=2, timeout=30)
        self.model = model

    def generate(self, messages, *, temperature=0.7, max_tokens=300, json_mode=False) -> str:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self.model.startswith(self.REASONING_PREFIXES):
            kwargs["reasoning_effort"] = "low"
            kwargs["include_reasoning"] = False
            max_tokens += self.REASONING_TOKEN_BUDGET
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except groq.RateLimitError as e:
            log.warning("Groq rate limit: %s", e)
            raise RateLimitedError(
                "The AI interviewer is receiving too many requests right now (free-tier rate limit). "
                "Wait a few seconds and try again."
            ) from e
        except groq.APIError as e:
            log.exception("Groq request failed")
            raise UpstreamError("The AI interviewer is temporarily unavailable. Please try again.") from e

        content = response.choices[0].message.content or ""
        if not content.strip():
            raise UpstreamError("The AI interviewer returned an empty response. Please try again.")
        return content.strip()
