import logging
from functools import lru_cache

from google import genai
from google.genai import types

from errors import UpstreamError

log = logging.getLogger(__name__)


class GeminiEmbedder:
    """
    Gemini embeddings for both sides of retrieval. Documents (concepts) and
    queries (interview context) use their matching task types, and must use
    the same model and dimensions.
    """

    def __init__(self, api_key: str, model: str, dimensions: int):
        if not api_key:
            raise UpstreamError("Embeddings are not configured (missing GEMINI_API_KEY).", retryable=False)
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.dimensions = dimensions
        self.embed = lru_cache(maxsize=256)(self._embed_query)

    def _call(self, contents: list[str], task_type: str) -> list[list[float]]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=contents,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.dimensions),
        )
        return [e.values for e in response.embeddings]

    def _embed_query(self, text: str) -> tuple[float, ...]:
        try:
            return tuple(self._call([text], "RETRIEVAL_QUERY")[0])
        except Exception as e:
            log.exception("Gemini embedding failed")
            raise UpstreamError("Semantic retrieval is temporarily unavailable.") from e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Used at ingestion time (data/load_knowledge_base.py). Errors propagate."""
        return self._call(texts, "RETRIEVAL_DOCUMENT")
