import json
from abc import ABC, abstractmethod
from typing import Any

from errors import UpstreamError


class LLMProvider(ABC):
    """
    The only surface the interview engine uses to talk to a language model.

    Swapping Groq/Llama for another provider means implementing `generate`;
    question generation and evaluation logic stay untouched.
    """

    name: str = "unknown"
    model: str = "unknown"

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 300,
        json_mode: bool = False,
    ) -> str:
        """Return the model's text response. Raise UpstreamError/RateLimitedError on failure."""

    def generate_json(self, messages: list[dict[str, str]], **kwargs: Any) -> dict:
        """Generate and parse a JSON object, retrying once if the model returns malformed JSON."""
        raw = self.generate(messages, json_mode=True, **kwargs)
        try:
            return parse_json_object(raw)
        except ValueError:
            retry = messages + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": "That was not valid JSON. Return ONLY the JSON object, nothing else."},
            ]
            raw = self.generate(retry, json_mode=True, **kwargs)
            try:
                return parse_json_object(raw)
            except ValueError as e:
                raise UpstreamError(
                    "The AI returned an unreadable evaluation. Please try submitting again.",
                    code="invalid_model_output",
                ) from e


def parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    if not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object in model output")
        text = text[start : end + 1]
    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(str(e)) from e
    if not isinstance(result, dict):
        raise ValueError("model output is not a JSON object")
    return result
