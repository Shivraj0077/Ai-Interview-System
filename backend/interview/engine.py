"""
Interview orchestration.

The original CLI kept `difficulty`, `used_concepts`, `history` and
`previous_eval` in local variables for a single terminal session. Here that
state lives on the interview record, so a web interview can be resumed,
retried after a provider failure, and reported on afterwards.
"""

import logging
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from errors import ConflictError, UpstreamError, ValidationError
from interview.difficulty import update_difficulty
from interview.evaluator import AnswerEvaluator
from interview.question import QuestionGenerator
from interview.report import build_report
from rag.retrieval import ConceptRetriever, concept_name
from storage.repository import InterviewRepository

log = logging.getLogger(__name__)

MAX_ANSWER_CHARS = 4000


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InterviewEngine:
    def __init__(
        self,
        repo: InterviewRepository,
        retriever: ConceptRetriever,
        questions: QuestionGenerator,
        evaluator: AnswerEvaluator,
        engine_info: dict,
    ):
        self.repo = repo
        self.retriever = retriever
        self.questions = questions
        self.evaluator = evaluator
        self.engine_info = engine_info
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

    # ---------- lifecycle ----------

    def create(self, config: dict, *, candidate_name: str, role: str, is_sample: bool = False) -> dict:
        start = config.get("start_difficulty", "L1")
        interview = {
            "id": uuid.uuid4().hex[:12],
            "created_at": now(),
            "updated_at": now(),
            "status": "created",
            "is_sample": is_sample,
            "candidate_name": candidate_name,
            "role": role,
            "config": config,
            "state": {
                "current_difficulty": start,
                "used_concepts": [],
                "turns": [],
                "started_at": None,
                "finished_at": None,
                "engine": self.engine_info,
            },
            "report": None,
        }
        self._save(interview)
        return interview

    def start(self, interview_id: str) -> dict:
        with self._locks[interview_id]:
            interview = self._get_mutable(interview_id)
            if interview["status"] == "completed":
                raise ConflictError("This interview has already finished.")
            if interview["status"] == "created":
                interview["status"] = "in_progress"
                interview["state"]["started_at"] = now()
                self._save(interview)
            return self._ensure_question(interview)

    def ensure_question(self, interview_id: str) -> dict:
        """Prepare the next question if none is pending (used to retry after a provider failure)."""
        with self._locks[interview_id]:
            interview = self._get_mutable(interview_id)
            if interview["status"] != "in_progress":
                raise ConflictError("This interview is not in progress.")
            return self._ensure_question(interview)

    def submit_answer(self, interview_id: str, question_index: int, answer: str) -> dict:
        answer = (answer or "").strip()
        if not answer:
            raise ValidationError("Write an answer before submitting, or skip the question.")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ValidationError(f"Answers are limited to {MAX_ANSWER_CHARS} characters.")

        with self._locks[interview_id]:
            interview = self._get_mutable(interview_id)
            turn = self._pending_turn(interview, question_index)
            concept = self.retriever.catalog.get(turn["concept_id"])
            if concept is None:
                raise UpstreamError("This question's concept is no longer in the knowledge base.", retryable=False)

            # If evaluation fails nothing is saved, so the same answer can simply be resubmitted.
            evaluation = self.evaluator.evaluate(concept, answer)

            turn.update(answer=answer, evaluation=evaluation, answered_at=now(), skipped=False)
            state = interview["state"]
            if interview["config"].get("difficulty_mode", "adaptive") == "adaptive":
                state["current_difficulty"] = update_difficulty(state["current_difficulty"], evaluation["score"])
            return self._advance(interview)

    def skip(self, interview_id: str, question_index: int) -> dict:
        with self._locks[interview_id]:
            interview = self._get_mutable(interview_id)
            turn = self._pending_turn(interview, question_index)
            turn.update(answer=None, evaluation=None, answered_at=now(), skipped=True)
            return self._advance(interview)

    def finish(self, interview_id: str) -> dict:
        with self._locks[interview_id]:
            interview = self._get_mutable(interview_id)
            if interview["status"] == "completed":
                return interview
            if interview["status"] == "created":
                raise ConflictError("This interview has not started yet.")
            # An unanswered pending question is dropped rather than scored as zero.
            interview["state"]["turns"] = [t for t in interview["state"]["turns"] if t.get("answered_at")]
            return self._complete(interview)

    def get(self, interview_id: str) -> dict:
        return self.repo.get(interview_id)

    # ---------- internals ----------

    def _get_mutable(self, interview_id: str) -> dict:
        interview = self.repo.get(interview_id)
        if interview.get("is_sample"):
            raise ConflictError("Sample interviews are read-only. Start the demo interview to try the live engine.")
        return interview

    def _save(self, interview: dict) -> None:
        interview["updated_at"] = now()
        self.repo.save(interview)

    def _pending_turn(self, interview: dict, question_index: int) -> dict:
        if interview["status"] != "in_progress":
            raise ConflictError("This interview is not in progress.")
        turns = interview["state"]["turns"]
        if not turns or turns[-1].get("answered_at"):
            raise ConflictError("There is no open question right now. Refresh to continue.")
        if turns[-1]["index"] != question_index:
            raise ConflictError("That question was already answered. Refresh to continue.")
        return turns[-1]

    def _advance(self, interview: dict) -> dict:
        answered = sum(1 for t in interview["state"]["turns"] if t.get("answered_at"))
        if answered >= interview["config"]["num_questions"]:
            return self._complete(interview)
        self._save(interview)
        try:
            return self._ensure_question(interview)
        except UpstreamError as e:
            # The answer is already saved; the client can retry just the next question.
            log.warning("Next question generation failed for %s: %s", interview["id"], e.message)
            interview["_question_error"] = {"message": e.message, "code": e.code}
            return interview

    def _complete(self, interview: dict) -> dict:
        interview["status"] = "completed"
        interview["state"]["finished_at"] = now()
        interview["report"] = build_report(interview)
        self._save(interview)
        return interview

    def _ensure_question(self, interview: dict) -> dict:
        state = interview["state"]
        turns = state["turns"]
        if turns and not turns[-1].get("answered_at"):
            return interview

        config = interview["config"]
        answered = [t for t in turns if t.get("answer")]
        history = [{"question": t["question"], "answer": t["answer"]} for t in answered]
        previous_eval = answered[-1]["evaluation"] if answered and turns[-1].get("answer") else None

        retrieval = self.retriever.select(
            difficulty=state["current_difficulty"],
            domains=config.get("focus_areas") or [],
            exclude_ids=state["used_concepts"],
            query_text=self._retrieval_query(interview, history),
        )
        concept = retrieval.concept
        question = self.questions.generate(concept, history=history, previous_eval=previous_eval, role=interview["role"])

        state["used_concepts"].append(concept["id"])
        turns.append({
            "index": len(turns),
            "concept_id": concept["id"],
            "concept_name": concept_name(concept),
            "domain": concept["domain"],
            "subdomain": concept.get("subdomain"),
            "difficulty": concept["difficulty"],
            "target_difficulty": state["current_difficulty"],
            "advanced_signal_count": len(concept.get("advanced_signals") or []),
            "question": question,
            "answer": None,
            "evaluation": None,
            "skipped": False,
            "retrieval_mode": retrieval.mode,
            "retrieval_note": retrieval.relaxed,
            "asked_at": now(),
            "answered_at": None,
        })
        self._save(interview)
        return interview

    @staticmethod
    def _retrieval_query(interview: dict, history: list[dict]) -> str:
        """
        The text embedded for semantic retrieval. Once the candidate has
        answered, retrieval follows what they have actually been discussing
        (as in the original engine); the first question is steered by the
        role, job description and resume instead of a generic seed.
        """
        if history:
            return " ".join(h["answer"] for h in history[-2:])
        config = interview["config"]
        parts = [f"{interview['role']} technical interview"]
        if config.get("job_description"):
            parts.append(config["job_description"][:800])
        if config.get("resume_text"):
            parts.append(config["resume_text"][:600])
        if len(parts) == 1:
            parts.append(f"introductory {interview['state']['current_difficulty']} backend and AI engineering concept")
        return "\n".join(parts)
