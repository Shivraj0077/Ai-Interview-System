import pytest

from demo.seed import build_samples
from errors import ConflictError, RateLimitedError, UpstreamError, ValidationError
from interview.difficulty import update_difficulty
from interview.evaluator import apply_evidence_cap, verify_grounding


def test_update_difficulty_matches_original_rules():
    assert update_difficulty("L1", 8) == "L2"
    assert update_difficulty("L2", 9) == "L3"
    assert update_difficulty("L3", 10) == "L3"
    assert update_difficulty("L2", 4) == "L1"
    assert update_difficulty("L1", 0) == "L1"
    assert update_difficulty("L2", 6) == "L2"


def test_grounding_removes_invented_signals_and_derives_missed():
    result = verify_grounding(
        {"core_coverage": ["a", "made up"], "advanced_coverage": ["x"], "missed_core_signals": ["b", "nope"],
         "misconceptions_detected": ["m", "fake"]},
        ["a", "b", "c"], ["y"], ["m"],
    )
    assert result["core_coverage"] == ["a"]
    assert result["advanced_coverage"] == []
    assert result["missed_core_signals"] == ["b", "c"]
    assert result["misconceptions_detected"] == ["m"]
    assert set(result["ungrounded_removed"]) == {"made up", "x", "nope", "fake"}


def test_clean_question_strips_wrappers():
    from interview.question import clean_question
    assert clean_question('Here is a question:\n"What does `next()` do in **middleware**?"') == "What does next() do in middleware?"


def test_evidence_cap_limits_unsupported_scores():
    result = apply_evidence_cap(
        {"score": 10, "verdict": "strong", "core_coverage": [], "advanced_coverage": []}, ["a", "b", "c", "d"]
    )
    assert result["score"] == 2 and result["score_capped_from"] == 10 and result["verdict"] == "weak"


def test_full_adaptive_interview(engine, llm, config):
    llm.scores = [9, 8, 3, 6]
    interview = engine.create(config, candidate_name="Test", role="Backend Engineer")
    interview = engine.start(interview["id"])
    assert interview["status"] == "in_progress"

    for _ in range(4):
        turn = interview["state"]["turns"][-1]
        assert turn["domain"] in config["focus_areas"]
        assert turn["difficulty"] == turn["target_difficulty"]
        interview = engine.submit_answer(interview["id"], turn["index"], "My answer about this concept.")

    assert interview["status"] == "completed"
    turns = interview["state"]["turns"]
    assert [t["difficulty"] for t in turns] == ["L1", "L2", "L3", "L2"]
    assert len({t["concept_id"] for t in turns}) == 4
    # hallucinated signal from the fake model was stripped by grounding verification
    assert all("An invented signal" not in t["evaluation"]["core_coverage"] for t in turns)
    assert all(t["evaluation"]["ungrounded_removed"] == ["An invented signal"] for t in turns)

    report = interview["report"]
    assert report["difficulty_progression"] == ["L1", "L2", "L3", "L2"]
    assert report["peak_difficulty"] == "L3"
    assert 0 <= report["overall"] <= 100
    assert report["grounding"]["ungrounded_claims_removed"] == 4
    assert report["grounding"]["catalog_fallbacks"] == 4
    # exactly one question-generation and one evaluation call per question
    assert sum(1 for c in llm.calls if not c["json"]) == 4
    assert sum(1 for c in llm.calls if c["json"]) == 4


def test_previous_evaluation_feeds_next_question(engine, llm, config):
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    engine.submit_answer(interview["id"], 0, "answer")
    last_question_prompt = [c for c in llm.calls if not c["json"]][-1]["prompt"]
    assert "Previous Evaluation:" in last_question_prompt
    assert "Role being interviewed for: R" in last_question_prompt


def test_fixed_difficulty_does_not_adapt(engine, llm, config):
    config = {**config, "difficulty_mode": "fixed", "start_difficulty": "L2", "focus_areas": []}
    llm.scores = [10, 10]
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    interview = engine.submit_answer(interview["id"], 0, "a")
    interview = engine.submit_answer(interview["id"], 1, "a")
    assert [t["difficulty"] for t in interview["state"]["turns"]] == ["L2", "L2", "L2"]


def test_evaluation_failure_saves_nothing_and_allows_retry(engine, llm, config):
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    llm.fail_next = RateLimitedError("slow down")
    with pytest.raises(RateLimitedError):
        engine.submit_answer(interview["id"], 0, "answer")
    stored = engine.get(interview["id"])
    assert stored["state"]["turns"][0]["answered_at"] is None
    interview = engine.submit_answer(interview["id"], 0, "answer")
    assert len(interview["state"]["turns"]) == 2


def test_invalid_json_is_retried_then_reported(engine, llm, config):
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    llm.raw_eval = "not json at all"
    with pytest.raises(UpstreamError) as exc:
        engine.submit_answer(interview["id"], 0, "answer")
    assert exc.value.code == "invalid_model_output"


def test_next_question_failure_keeps_answer_and_can_be_retried(engine, llm, config):
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    original_generate = engine.questions.generate

    def failing(*a, **k):
        raise UpstreamError("down")

    engine.questions.generate = failing
    interview = engine.submit_answer(interview["id"], 0, "answer")
    assert interview["_question_error"]["message"] == "down"
    assert engine.get(interview["id"])["state"]["turns"][0]["answered_at"]

    engine.questions.generate = original_generate
    interview = engine.ensure_question(interview["id"])
    assert len(interview["state"]["turns"]) == 2


def test_stale_and_empty_answers_are_rejected(engine, config):
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    with pytest.raises(ValidationError):
        engine.submit_answer(interview["id"], 0, "   ")
    engine.submit_answer(interview["id"], 0, "a")
    with pytest.raises(ConflictError):
        engine.submit_answer(interview["id"], 0, "a again")


def test_skip_and_early_finish(engine, config):
    interview = engine.start(engine.create(config, candidate_name="T", role="R")["id"])
    interview = engine.skip(interview["id"], 0)
    assert interview["state"]["turns"][0]["skipped"]
    interview = engine.finish(interview["id"])
    assert interview["status"] == "completed"
    # the pending, unanswered question is dropped
    assert len(interview["state"]["turns"]) == 1
    assert interview["report"]["questions_skipped"] == 1


def test_samples_are_consistent_and_read_only(engine):
    samples = build_samples(engine.retriever.catalog, engine.engine_info)
    for s in samples:
        for t in s["state"]["turns"]:
            assert t["difficulty"] == t["target_difficulty"], (s["role"], t["concept_id"])
            if t["evaluation"]:
                assert "score_capped_from" not in t["evaluation"], (s["role"], t["concept_id"])
        engine.repo.save(s)
    with pytest.raises(ConflictError):
        engine.start(samples[-1]["id"])
