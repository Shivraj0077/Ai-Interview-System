"""
Load the curated knowledge base into Supabase (rag_concepts) with embeddings.

    cd backend && python data/load_knowledge_base.py          # embed + upsert everything
    cd backend && python data/load_knowledge_base.py --check  # just report what's in the table

Run db/schema.sql first. Replaces the older embed.py + chunks-to-db.py two-step,
and takes signal lists from Rag-db.json directly (see rag/knowledge_base.py).
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings  # noqa: E402
from rag.embeddings import GeminiEmbedder  # noqa: E402
from rag.knowledge_base import build_concepts  # noqa: E402
from services import supabase_client  # noqa: E402

BATCH = 25


def check(client) -> None:
    res = client.table("rag_concepts").select("id,difficulty,embedding", count="exact").execute()
    embedded = sum(1 for r in res.data if r.get("embedding"))
    levels = {lvl: sum(1 for r in res.data if r["difficulty"] == lvl) for lvl in ("L1", "L2", "L3")}
    print(f"rag_concepts: {res.count} rows, {embedded} embedded, by level {levels}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="only report table contents")
    args = parser.parse_args()

    client = supabase_client()
    if client is None:
        sys.exit("Set SUPABASE_URL and SUPABASE_KEY in backend/.env")
    if args.check:
        check(client)
        return
    if not settings.gemini_api_key:
        sys.exit("Set GEMINI_API_KEY in backend/.env")

    embedder = GeminiEmbedder(settings.gemini_api_key, settings.embed_model, settings.embed_dimensions)
    concepts = build_concepts(settings.data_dir)
    print(f"Embedding {len(concepts)} concepts with {settings.embed_model} ({settings.embed_dimensions} dims)")

    for start in range(0, len(concepts), BATCH):
        batch = concepts[start : start + BATCH]
        for attempt in range(4):
            try:
                vectors = embedder.embed_documents([c["text"] for c in batch])
                break
            except Exception as e:  # free-tier rate limits: back off and retry
                if attempt == 3:
                    raise
                wait = 15 * (attempt + 1)
                print(f"  embedding failed ({type(e).__name__}), retrying in {wait}s")
                time.sleep(wait)
        rows = [{**c, "embedding": v} for c, v in zip(batch, vectors)]
        client.table("rag_concepts").upsert(rows).execute()
        print(f"  upserted {start + len(batch)}/{len(concepts)}")

    check(client)


if __name__ == "__main__":
    main()
