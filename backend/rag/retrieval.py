import logging
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from errors import UpstreamError
from rag.knowledge_base import build_concepts

log = logging.getLogger(__name__)

LEVELS = ["L1", "L2", "L3"]

# Knowledge-base domains (see data/add-levels.py) with recruiter-facing labels.
DOMAINS: dict[str, str] = {
    "backend": "Backend & APIs",
    "database": "Databases",
    "distributed_systems": "Distributed Systems",
    "system_design": "System Design",
    "data_structures": "Data Structures & Complexity",
    "programming_fundamentals": "Programming Fundamentals",
    "security": "Security",
    "devops": "DevOps & Cloud",
    "observability": "Observability",
    "software_engineering": "Engineering Practices",
    "code_quality": "Code Quality",
    "soft_skills": "Collaboration",
}


class Embedder(Protocol):
    def embed(self, text: str) -> tuple[float, ...]: ...


@dataclass
class Retrieval:
    concept: dict
    mode: str  # "semantic" | "catalog"
    relaxed: str | None = None  # why the pick deviates from the requested difficulty/focus


def concept_name(concept: dict) -> str:
    if concept.get("concept"):
        return concept["concept"]
    match = re.match(r"Concept:\s*(.+)", concept.get("text", ""))
    return match.group(1).strip() if match else concept["id"]


def load_local_catalog(data_dir: Path) -> dict[str, dict]:
    return {c["id"]: c for c in build_concepts(data_dir)}


class ConceptRetriever:
    """
    Picks the next interview concept.

    Ranking is semantic (pgvector similarity between the interview context and
    each concept's embedding). Focus areas and difficulty are hard filters.
    If the vector search is unavailable the retriever degrades to a filtered
    random pick from the concept catalog and records that it did so.
    """

    def __init__(self, supabase, embedder: Embedder | None, data_dir: Path):
        self.supabase = supabase
        self.embedder = embedder
        self.data_dir = data_dir
        self._catalog: dict[str, dict] | None = None

    @property
    def catalog(self) -> dict[str, dict]:
        if self._catalog is None:
            self._catalog = self._load_catalog()
        return self._catalog

    def _load_catalog(self) -> dict[str, dict]:
        if self.supabase is not None:
            try:
                rows = (
                    self.supabase.table("rag_concepts")
                    .select("id,concept,text,domain,subdomain,difficulty,core_signals,advanced_signals,misconceptions")
                    .execute()
                    .data
                )
                if rows:
                    return {r["id"]: r for r in rows}
            except Exception:
                log.exception("Could not load rag_concepts from Supabase; using local knowledge base file")
        return load_local_catalog(self.data_dir)

    def _semantic_rank(self, query_text: str, difficulty: str, exclude_ids: list[str], domains: list[str]) -> list[str]:
        if self.supabase is None or self.embedder is None:
            raise UpstreamError("Semantic retrieval is not configured.")
        embedding = list(self.embedder.embed(query_text))
        try:
            rows = self.supabase.rpc(
                "match_concepts_filtered",
                {
                    "query_embedding": embedding,
                    "match_difficulty": difficulty,
                    "match_domains": domains or None,
                    "exclude_ids": exclude_ids,
                    "match_count": 5,
                },
            ).execute().data
        except Exception:
            # Older databases only have the original match_concepts RPC; over-fetch and filter here.
            log.info("match_concepts_filtered unavailable, falling back to match_concepts")
            try:
                rows = self.supabase.rpc(
                    "match_concepts",
                    {
                        "query_embedding": embedding,
                        "match_difficulty": difficulty,
                        "exclude_ids": exclude_ids,
                        "match_count": 40,
                    },
                ).execute().data
            except Exception as e:
                log.exception("Vector search failed")
                raise UpstreamError("Semantic retrieval is temporarily unavailable.") from e
        ids = [r["id"] for r in rows or [] if r.get("id") in self.catalog]
        if domains:
            ids = [i for i in ids if self.catalog[i]["domain"] in domains]
        return ids

    def select(self, *, difficulty: str, domains: list[str], exclude_ids: list[str], query_text: str) -> Retrieval:
        # Try the requested difficulty first; if the focus areas have nothing
        # left there, widen the domain (keeps the difficulty the candidate
        # earned), then step to the nearest other difficulty.
        idx = LEVELS.index(difficulty) if difficulty in LEVELS else 0
        nearby = sorted((l for l in LEVELS if l != difficulty), key=lambda l: (abs(LEVELS.index(l) - idx), l))
        attempts = [(difficulty, domains, None)]
        if domains:
            attempts.append((difficulty, [], "No remaining focus-area concepts at this level; widened topic scope."))
        attempts += [(lvl, domains, f"No remaining {difficulty} concepts; used nearest level {lvl}.") for lvl in nearby]
        attempts += [(lvl, [], f"No remaining {difficulty} concepts; used nearest level {lvl}.") for lvl in nearby]

        semantic_ok = True
        for level, doms, relaxed in attempts:
            pool = [
                c for c in self.catalog.values()
                if c["difficulty"] == level and c["id"] not in exclude_ids and (not doms or c["domain"] in doms)
            ]
            if not pool:
                continue
            if semantic_ok:
                try:
                    ranked = self._semantic_rank(query_text, level, exclude_ids, doms)
                    if ranked:
                        # Random among the top-k semantic matches: topical, but not identical every run.
                        return Retrieval(self.catalog[random.choice(ranked[:5])], "semantic", relaxed)
                except UpstreamError:
                    semantic_ok = False
            return Retrieval(random.choice(pool), "catalog", relaxed)

        raise UpstreamError("The knowledge base has no unused concepts left for this interview.", retryable=False)
