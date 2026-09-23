"""
Terminal interview, same experience as the original question.py script but
running on the shared engine (so it exercises exactly what the web app does).

    python cli.py --questions 3
"""

import argparse

from errors import ServiceError
from services import get_engine


def run_interview(num_questions: int = 3, role: str = "Software Engineer") -> None:
    engine = get_engine()
    interview = engine.create(
        {"num_questions": num_questions, "difficulty_mode": "adaptive", "start_difficulty": "L1", "focus_areas": []},
        candidate_name="CLI Candidate",
        role=role,
    )

    print("\nStarting the Adaptive AI Interviewer...")
    print(f"Goal: {num_questions} questions | Initial Difficulty: L1")

    interview = engine.start(interview["id"])
    while interview["status"] == "in_progress":
        turn = interview["state"]["turns"][-1]
        print(f"\n--- Question {turn['index'] + 1} | Topic: {turn['concept_name']} | Level: {turn['difficulty']} ---")
        print(f"\nQ: {turn['question']}")

        answer = input("\nYour Answer: ").strip()
        if not answer:
            print("Answer skipped.")
            interview = engine.skip(interview["id"], turn["index"])
        else:
            print("\nEvaluating...")
            interview = engine.submit_answer(interview["id"], turn["index"], answer)
            ev = next(t for t in interview["state"]["turns"] if t["index"] == turn["index"])["evaluation"]
            print(f"Score: {ev['score']}/10 | Verdict: {ev['verdict']}")
            if ev["misconceptions_detected"]:
                print(f"Misconceptions: {', '.join(ev['misconceptions_detected'])}")
            if ev["ungrounded_removed"]:
                print(f"[grounding check] Removed hallucinated claims: {ev['ungrounded_removed']}")
            print(f"Next Difficulty Target: {interview['state']['current_difficulty']}")

        if "_question_error" in interview:
            raise ServiceError(interview["_question_error"]["message"])

    report = interview["report"]
    print("\n--- Interview Complete ---")
    print(f"Overall: {report['overall']}/100 ({report['band']})")
    print(f"Difficulty progression: {' -> '.join(report['difficulty_progression'])}")
    print(f"Concepts covered: {', '.join(t['concept_name'] for t in interview['state']['turns'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive AI technical interview (terminal)")
    parser.add_argument("--questions", type=int, default=3)
    parser.add_argument("--role", default="Software Engineer")
    args = parser.parse_args()
    try:
        run_interview(args.questions, args.role)
    except KeyboardInterrupt:
        print("\n\nInterview terminated by user.")
    except ServiceError as e:
        print(f"\nError: {e.message}")
