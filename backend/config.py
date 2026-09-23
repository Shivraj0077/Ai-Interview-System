import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    llm_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    # Must match the model used at ingestion time (data/load_knowledge_base.py),
    # otherwise query vectors and stored vectors live in different spaces.
    embed_model: str = os.getenv("EMBED_MODEL", "gemini-embedding-001")
    embed_dimensions: int = int(os.getenv("EMBED_DIMENSIONS", "768"))

    # "supabase" (default) or "local" (JSON file, for offline development)
    interview_store: str = os.getenv("INTERVIEW_STORE", "supabase")
    local_store_path: Path = BACKEND_DIR / ".local-data" / "interviews.json"

    data_dir: Path = BACKEND_DIR / "data"
    cors_origins: list[str] = field(
        default_factory=lambda: _csv(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
    )


settings = Settings()
