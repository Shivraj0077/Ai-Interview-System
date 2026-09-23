"""
The curated knowledge base, assembled from the files in backend/data:

- Rag-db.json        concept, explanation and the signal lists (source of truth)
- final-chunks.json  ids, domain/subdomain/level and the chunk text that gets embedded
                     (produced from Rag-db.json by data/add-levels.py, same order)

Signal lists are taken from Rag-db.json as real lists. Re-parsing them out of the
chunk text (as the original chunks-to-db.py did) splits signals that contain
commas, e.g. "HTTP Verbs (GET, POST, etc.)".
"""

import json
from pathlib import Path


def build_concepts(data_dir: Path) -> list[dict]:
    raw = json.loads((data_dir / "Rag-db.json").read_text(encoding="utf-8"))
    chunks = json.loads((data_dir / "final-chunks.json").read_text(encoding="utf-8"))
    if len(raw) != len(chunks):
        raise ValueError("Rag-db.json and final-chunks.json are out of sync; re-run data/add-levels.py")

    concepts = []
    for source, chunk in zip(raw, chunks):
        meta = chunk["metadata"]
        if meta["concept"] != source["concept"]:
            raise ValueError(f"Concept order mismatch at {chunk['id']}; re-run data/add-levels.py")
        concepts.append({
            "id": chunk["id"],
            "concept": source["concept"],
            "text": chunk["text"],
            "domain": meta["domain"],
            "subdomain": meta["subdomain"],
            "difficulty": meta["difficulty"],
            "core_signals": source.get("core_signals", []),
            "advanced_signals": source.get("advanced_signals", []),
            "misconceptions": source.get("common_misconceptions", []),
        })
    return concepts
