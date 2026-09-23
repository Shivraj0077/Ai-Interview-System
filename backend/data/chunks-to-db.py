# Superseded by load_knowledge_base.py (single step, signal lists taken from Rag-db.json).
# Kept for reference; running it is not needed.

import json
import os
import re
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ==========================
# CONFIG
# ==========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
INPUT_FILE = "final-chunks.json"

# ==========================
# INIT
# ==========================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

# ==========================
# Helper: extract signals from text
# ==========================
def extract_section(text, section_name):
    pattern = rf"{section_name}:\n(.*?)(\n\n|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        return [x.strip() for x in content.split(",") if x.strip()]
    return []

# ==========================
# INSERT
# ==========================
batch = []

for chunk in chunks:

    text = chunk["text"]

    core_signals = extract_section(text, "Core signals")
    advanced_signals = extract_section(text, "Advanced signals")
    misconceptions = extract_section(text, "Common misconceptions")

    batch.append({
        "id": chunk["id"],
        "text": text,
        "domain": chunk["metadata"]["domain"],
        "subdomain": chunk["metadata"]["subdomain"],
        "difficulty": chunk["metadata"]["difficulty"],
        "core_signals": core_signals,
        "advanced_signals": advanced_signals,
        "misconceptions": misconceptions
    })

# Insert in batches
for i in range(0, len(batch), 100):
    supabase.table("rag_concepts").upsert(batch[i:i+100]).execute()
    print(f"Inserted batch {i//100 + 1}")

print("All concepts inserted successfully.")
