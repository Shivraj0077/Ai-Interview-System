import json
import google.genai as genai
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# CONFIG
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

INPUT_FILE = "prepared_chunks.json"

# Load chunks
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

def embed_text(text):
    response = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return response["embedding"]

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

    supabase.table("rag_concepts").insert(data).execute()

print("All chunks embedded and uploaded successfully.")