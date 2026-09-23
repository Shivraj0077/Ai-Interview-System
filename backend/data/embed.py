# Superseded by load_knowledge_base.py (single step, signal lists taken from Rag-db.json).
# Kept for reference; running it is not needed.

import json
from google import genai
from google.genai import types
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# CONFIG
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Keep in sync with the backend (EMBED_MODEL / EMBED_DIMENSIONS): query and stored vectors must share a space.
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-004")
EMBED_DIMENSIONS = int(os.getenv("EMBED_DIMENSIONS", "768"))

genai_client = genai.Client(api_key=GEMINI_API_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

INPUT_FILE = "prepared_chunks.json"

# Load chunks
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

def embed_text(text):
    response = genai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBED_DIMENSIONS),
    )
    return response.embeddings[0].values

for chunk in chunks:
    print(f"Embedding: {chunk['id']}")

    embedding = embed_text(chunk["text"])

    data = {
        "id": chunk["id"],
        "text": chunk["text"],
        "domain": chunk["metadata"]["domain"],
        "subdomain": chunk["metadata"]["subdomain"],
        "difficulty": chunk["metadata"]["difficulty"],
        "embedding": embedding
    }

    supabase.table("rag_concepts").upsert(data).execute()

print("All chunks embedded and uploaded successfully.")