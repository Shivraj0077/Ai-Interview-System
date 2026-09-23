import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.provider import LLMProvider  # noqa: E402
from config import settings  # noqa: E402
from interview.engine import InterviewEngine  # noqa: E402
from interview.evaluator import AnswerEvaluator  # noqa: E402
from interview.question import QuestionGenerator  # noqa: E402
from rag.retrieval import ConceptRetriever  # noqa: E402
from storage.repository import LocalInterviewRepository  # noqa: E402


class FakeLLM(LLMProvider):
    """Returns a question for generation calls and a scripted evaluation for JSON calls."""

    name = "Fake"
    model = "fake-1"

    def __init__(self):
        self.scores: list[int] = []
        self.calls: list[dict] = []
        self.fail_next: Exception | None = None
        self.raw_eval: str | None = None

    def generate(self, messages, *, temperature=0.7, max_tokens=300, json_mode=False):
        self.calls.append({"json": json_mode, "prompt": messages[-1]["content"]})
        if self.fail_next:
            err, self.fail_next = self.fail_next, None
            raise err
        if not json_mode:
            return "Here is a question:\n\"How would you explain this concept to a teammate?\""
        if self.raw_eval is not None:
            return self.raw_eval
        prompt = messages[-1]["content"]
        core = ast.literal_eval(prompt.split("Core signals (candidate should mention these):")[1].split("Advanced signals")[0].strip())
        score = self.scores.pop(0) if self.scores else 6
        covered = core[: max(1, round(len(core) * score / 10))]
        return json.dumps({
            "score": score,
            "core_coverage": covered + ["An invented signal"],
            "advanced_coverage": [],
            "missed_core_signals": [],
            "misconceptions_detected": [],
            "communication_score": 7,
            "verdict": "strong" if score >= 8 else "average",
        })


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def engine(llm):
    retriever = ConceptRetriever(None, None, settings.data_dir)
    return InterviewEngine(
        repo=LocalInterviewRepository(None),
        retriever=retriever,
        questions=QuestionGenerator(llm),
        evaluator=AnswerEvaluator(llm),
        engine_info={"provider": "Fake", "model": "fake-1"},
    )


@pytest.fixture
def config():
    return {
        "interview_type": "technical",
        "difficulty_mode": "adaptive",
        "start_difficulty": "L1",
        "num_questions": 4,
        "focus_areas": ["backend", "database", "distributed_systems"],
        "job_description": "Build REST APIs",
        "resume_text": "",
        "resume_filename": None,
    }
