"""
Shapes returned to the frontend.

The candidate session view never includes scores or evaluations, so the
interview UI cannot leak them. The recruiter view includes per-question
evaluations but never prompts or raw model output (neither is stored).
"""

from rag.retrieval import DOMAINS


def _domain_label(domain: str) -> str:
    return DOMAINS.get(domain, domain.replace("_", " ").title())


def session_view(interview: dict) -> dict:
    state = interview["state"]
    turns = state["turns"]
    pending = turns[-1] if turns and not turns[-1].get("answered_at") else None
    return {
        "id": interview["id"],
        "status": interview["status"],
        "is_sample": interview.get("is_sample", False),
        "candidate_name": interview["candidate_name"],
        "role": interview["role"],
        "num_questions": interview["config"]["num_questions"],
        "answered": sum(1 for t in turns if t.get("answered_at")),
        "started_at": state.get("started_at"),
        "engine": state.get("engine"),
        "current_question": pending and {
            "index": pending["index"],
            "number": pending["index"] + 1,
            "text": pending["question"],
            "topic": pending["concept_name"],
            "domain": _domain_label(pending["domain"]),
            "difficulty": pending["difficulty"],
        },
        "question_error": interview.get("_question_error"),
    }


def _turn_view(turn: dict) -> dict:
    ev = turn.get("evaluation")
    return {
        "index": turn["index"],
        "number": turn["index"] + 1,
        "topic": turn["concept_name"],
        "domain": _domain_label(turn["domain"]),
        "difficulty": turn["difficulty"],
        "target_difficulty": turn.get("target_difficulty"),
        "question": turn["question"],
        "answer": turn.get("answer"),
        "skipped": turn.get("skipped", False),
        "answered": bool(turn.get("answered_at")),
        "retrieval_mode": turn.get("retrieval_mode"),
        "retrieval_note": turn.get("retrieval_note"),
        "evaluation": ev and {
            "score": ev["score"],
            "communication_score": ev["communication_score"],
            "verdict": ev["verdict"],
            "core_coverage": ev["core_coverage"],
            "advanced_coverage": ev["advanced_coverage"],
            "missed_core_signals": ev["missed_core_signals"],
            "misconceptions_detected": ev["misconceptions_detected"],
            "ungrounded_removed": ev.get("ungrounded_removed", []),
            "score_capped_from": ev.get("score_capped_from"),
        },
    }


def detail_view(interview: dict) -> dict:
    config = interview["config"]
    state = interview["state"]
    return {
        "id": interview["id"],
        "status": interview["status"],
        "is_sample": interview.get("is_sample", False),
        "created_at": interview["created_at"],
        "updated_at": interview["updated_at"],
        "candidate_name": interview["candidate_name"],
        "role": interview["role"],
        "config": {
            "interview_type": config.get("interview_type", "technical"),
            "difficulty_mode": config.get("difficulty_mode", "adaptive"),
            "start_difficulty": config.get("start_difficulty", "L1"),
            "num_questions": config["num_questions"],
            "focus_areas": [{"id": d, "label": _domain_label(d)} for d in config.get("focus_areas", [])],
            "has_job_description": bool(config.get("job_description")),
            "resume_filename": config.get("resume_filename"),
        },
        "started_at": state.get("started_at"),
        "finished_at": state.get("finished_at"),
        "engine": state.get("engine"),
        "turns": [_turn_view(t) for t in state["turns"]],
        "report": interview.get("report"),
    }
