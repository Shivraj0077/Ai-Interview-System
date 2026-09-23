"""Builds the engine and its dependencies from settings (one place for wiring)."""

import logging
from functools import lru_cache

from ai.groq_provider import GroqProvider
from config import settings
from interview.engine import InterviewEngine
from interview.evaluator import AnswerEvaluator
from interview.question import QuestionGenerator
from rag.embeddings import GeminiEmbedder
from rag.retrieval import ConceptRetriever
from storage.repository import LocalInterviewRepository, SupabaseInterviewRepository

log = logging.getLogger(__name__)


@lru_cache
def supabase_client():
    if not (settings.supabase_url and settings.supabase_key):
        return None
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_key)


@lru_cache
def get_engine() -> InterviewEngine:
    llm = GroqProvider(settings.groq_api_key, settings.llm_model)
    client = supabase_client()

    embedder = None
    if settings.gemini_api_key:
        embedder = GeminiEmbedder(settings.gemini_api_key, settings.embed_model, settings.embed_dimensions)
    else:
        log.warning("GEMINI_API_KEY not set: concept retrieval will not be semantic")

    if settings.interview_store == "local" or client is None:
        if client is None:
            log.warning("Supabase not configured: storing interviews in %s", settings.local_store_path)
        repo = LocalInterviewRepository(settings.local_store_path)
    else:
        repo = SupabaseInterviewRepository(client)

    return InterviewEngine(
        repo=repo,
        retriever=ConceptRetriever(client, embedder, settings.data_dir),
        questions=QuestionGenerator(llm),
        evaluator=AnswerEvaluator(llm),
        engine_info={
            "provider": llm.name,
            "model": llm.model,
            "embeddings": f"Gemini {settings.embed_model}" if embedder else None,
            "vector_store": "Supabase pgvector" if client else None,
        },
    )
