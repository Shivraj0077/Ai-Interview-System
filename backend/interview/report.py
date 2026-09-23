"""
Builds the recruiter report from stored evaluations.

Deliberately deterministic (no LLM call): every number and bullet in the report
traces back to a verified signal or score from a specific question.
"""

from collections import defaultdict
from statistics import mean

from rag.retrieval import DOMAINS

WEIGHTS = {"technical_knowledge": 0.5, "conceptual_depth": 0.3, "communication": 0.2}


def _pct(values: list[float]) -> int | None:
    return round(mean(values)) if values else None


def _band(score: int | None) -> str:
    if score is None:
        return "Insufficient data"
    if score >= 75:
        return "Strong performance"
    if score >= 55:
        return "Solid, with gaps"
    return "Needs development"


def build_report(interview: dict) -> dict:
    turns = [t for t in interview["state"]["turns"] if t.get("answered_at")]
    evaluated = [t for t in turns if not t.get("skipped") and t.get("evaluation")]

    technical = _pct([(t["evaluation"]["score"] if t in evaluated else 0) * 10 for t in turns])
    communication = _pct([t["evaluation"]["communication_score"] * 10 for t in evaluated])

    depth_values = []
    for t in evaluated:
        ev = t["evaluation"]
        n_core = len(ev["core_coverage"]) + len(ev["missed_core_signals"])
        core_ratio = len(ev["core_coverage"]) / n_core if n_core else 0
        n_adv = t.get("advanced_signal_count") or 0
        adv_ratio = min(1, len(ev["advanced_coverage"]) / n_adv) if n_adv else 0
        depth_values.append((0.75 * core_ratio + 0.25 * adv_ratio) * 100)
    depth = _pct(depth_values)

    dims = {"technical_knowledge": technical, "conceptual_depth": depth, "communication": communication}
    overall = None
    if technical is not None:
        overall = round(sum((dims[k] or 0) * w for k, w in WEIGHTS.items()))

    strengths, improvements = [], []
    for t in evaluated:
        ev = t["evaluation"]
        if ev["score"] >= 7:
            covered = ev["core_coverage"] + ev["advanced_coverage"]
            strengths.append({
                "title": t["concept_name"],
                "detail": ("Covered " + ", ".join(covered[:3])) if covered else "Answered confidently",
            })
        if ev["score"] <= 5 or ev["misconceptions_detected"]:
            missed = ev["missed_core_signals"]
            improvements.append({
                "title": t["concept_name"],
                "detail": ("Missed " + ", ".join(missed[:3])) if missed else "Answer held a misconception",
            })
    for t in turns:
        if t.get("skipped"):
            improvements.append({"title": t["concept_name"], "detail": "Question skipped"})

    by_domain: dict[str, list[float]] = defaultdict(list)
    for t in turns:
        by_domain[t["domain"]].append((t["evaluation"]["score"] if t in evaluated else 0) * 10)
    coverage = sorted(
        (
            {"domain": d, "label": DOMAINS.get(d, d.replace("_", " ").title()), "score": round(mean(v)), "questions": len(v)}
            for d, v in by_domain.items()
        ),
        key=lambda c: -c["questions"],
    )

    misconceptions = sorted({m for t in evaluated for m in t["evaluation"]["misconceptions_detected"]})
    levels = [t["difficulty"] for t in turns]
    order = {"L1": 1, "L2": 2, "L3": 3}

    return {
        "overall": overall,
        "band": _band(overall),
        "dimensions": dims,
        "strengths": strengths,
        "improvements": improvements,
        "misconceptions": misconceptions,
        "coverage": coverage,
        "difficulty_progression": levels,
        "peak_difficulty": max(levels, key=lambda l: order.get(l, 0)) if levels else None,
        "questions_answered": len(evaluated),
        "questions_skipped": sum(1 for t in turns if t.get("skipped")),
        "questions_planned": interview["config"]["num_questions"],
        "grounding": {
            "ungrounded_claims_removed": sum(len(t["evaluation"].get("ungrounded_removed", [])) for t in evaluated),
            "scores_capped": sum(1 for t in evaluated if "score_capped_from" in t["evaluation"]),
            "semantic_retrievals": sum(1 for t in turns if t.get("retrieval_mode") == "semantic"),
            "catalog_fallbacks": sum(1 for t in turns if t.get("retrieval_mode") == "catalog"),
        },
    }
