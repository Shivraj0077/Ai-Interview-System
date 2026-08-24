import os
import random
import json
from dotenv import load_dotenv
from supabase import create_client
from groq import Groq
import google.genai as genai

# ==========================
# CONFIG
# ==========================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

EMBED_MODEL = "models/text-embedding-004"


# ==========================
# EMBEDDING HELPER
# ==========================
def embed_text(text):
    """Embed text using the same model used at ingestion time (embed.py)."""
    response = genai.embed_content(model=EMBED_MODEL, content=text)
    return response["embedding"]


# ==========================
# SEMANTIC RETRIEVAL (pgvector)
# ==========================
def fetch_concept(difficulty="L1", exclude_ids=None, history=None):
    """
    Retrieve a concept using pgvector semantic search instead of random selection.

    Query vector = embedding of the candidate's recent answers (or a generic
    'next topic' seed if no history yet), so retrieval is grounded in what the
    candidate has actually been discussing rather than picked at random.
    """
    exclude_ids = exclude_ids or []

    if history:
        # Ground retrieval in the candidate's own recent answers
        query_text = " ".join(h["answer"] for h in history[-2:])
    else:
        query_text = f"introductory {difficulty} backend and AI engineering concept"

    query_embedding = embed_text(query_text)

    response = supabase.rpc(
        "match_concepts",
        {
            "query_embedding": query_embedding,
            "match_difficulty": difficulty,
            "exclude_ids": exclude_ids,
            "match_count": 5,
        },
    ).execute()

    candidates = response.data
    if not candidates:
        raise Exception(f"No concepts found for difficulty {difficulty}")

    # Pick randomly among the top-k semantically relevant candidates
    # (keeps some variety while staying topically grounded)
    return random.choice(candidates)


def update_difficulty(current_level, score):
    """L1 -> L2 if score >= 8. L1/L2 -> L1 if score <= 4."""
    levels = ["L1", "L2", "L3"]
    idx = levels.index(current_level) if current_level in levels else 0

    if score >= 8 and idx < len(levels) - 1:
        idx += 1
    elif score <= 4 and idx > 0:
        idx -= 1

    return levels[idx]


# ==========================
# GENERATE QUESTION
# ==========================
def generate_question(concept, history=None, previous_eval=None):
    history_text = ""
    if history:
        recent = history[-2:]
        hist_fmt = "\n".join([f"Q: {h['question']}\nA: {h['answer']}" for h in recent])
        history_text += f"\nRecent Interview History:\n{hist_fmt}\n"

    eval_text = ""
    if previous_eval:
        eval_text += f"""
Previous Evaluation:
Score: {previous_eval.get('score')}
Misconceptions: {', '.join(previous_eval.get('misconceptions_detected', [])) or 'None'}
Missed Core: {', '.join(previous_eval.get('missed_core_signals', [])) or 'None'}

Instruction: Tailor the new question to implicitly address or probe the candidate's
previous misconceptions or missed concepts if relevant, while staying within the new
Concept context below. Do not introduce facts not present in the Knowledge Context.
"""

    prompt = f"""
Generate exactly ONE conceptual interview question.

Concept: {concept['id']}
Difficulty: {concept['difficulty']}

Knowledge Context (ground the question strictly in this):
{concept.get('text', '')}
{history_text}{eval_text}
Rules:
- Ask only ONE question.
- The question must be answerable using only the Knowledge Context above.
- No explanation. No answer.
- Make it conversational and natural for an interview.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert AI interviewer generating questions adaptively. Never ask about facts outside the given context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=150,
    )

    return response.choices[0].message.content.strip()


# ==========================
# EVALUATE ANSWER (hallucination-reduced)
# ==========================
def evaluate_answer(concept, user_answer):
    """
    Evaluate the candidate's answer with hallucination-reduction techniques:

    1. Retrieval grounding: the evaluator only sees the retrieved concept's
       core/advanced signals + misconceptions — not open-domain knowledge.
    2. Forced citation: every score claim must reference a specific signal
       string from the provided list, not a paraphrase or invented fact.
    3. Low temperature (0) for deterministic, less creative scoring.
    4. A second grounding-verification pass that checks every cited signal
       actually exists in the source concept, rejecting/flagging any that don't.
    """
    core_signals = concept.get("core_signals", [])
    advanced_signals = concept.get("advanced_signals", [])
    misconceptions = concept.get("misconceptions", [])

    prompt = f"""
Evaluate the candidate's answer STRICTLY using only the signals listed below.
Do not use outside knowledge. Do not invent signals that are not listed.

Concept: {concept['id']}

Core signals (candidate should mention these):
{core_signals}

Advanced signals (bonus if mentioned):
{advanced_signals}

Common misconceptions (flag if the candidate exhibits these):
{misconceptions}

Candidate Answer:
\"\"\"
{user_answer}
\"\"\"

Rules:
- Every item in "core_coverage" and "advanced_coverage" MUST be copied verbatim
  from the Core/Advanced signals lists above. Never write a signal that isn't
  in those lists.
- Every item in "missed_core_signals" MUST also come verbatim from the Core
  signals list.
- Every item in "misconceptions_detected" MUST come verbatim from the Common
  misconceptions list.
- If the candidate says something not covered by these signals, ignore it —
  do not score it positively or negatively.

Return ONLY valid JSON:
{{
  "score": 0-10,
  "core_coverage": [],
  "advanced_coverage": [],
  "missed_core_signals": [],
  "misconceptions_detected": [],
  "communication_score": 0-10,
  "verdict": "weak | average | strong"
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a strict technical evaluator. Return only JSON. Never cite a signal that was not provided to you."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=400,
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0].strip()
        result = json.loads(raw_output)
    except Exception:
        return {"error": "Invalid JSON returned", "raw": raw_output, "score": 0}

    return _verify_grounding(result, core_signals, advanced_signals, misconceptions)


def _verify_grounding(result, core_signals, advanced_signals, misconceptions):
    """
    Post-hoc grounding check: strip out any cited signal that the model
    hallucinated (i.e. wasn't actually in the source lists). This is the
    concrete mechanism behind the "reduced hallucinations" claim — it's not
    just a better prompt, it's a verification step that catches what the
    prompt constraint misses.
    """
    def clean(items, valid_set):
        removed = [i for i in items if i not in valid_set]
        if removed:
            result.setdefault("_ungrounded_removed", []).extend(removed)
        return [i for i in items if i in valid_set]

    core_set = set(core_signals)
    adv_set = set(advanced_signals)
    misc_set = set(misconceptions)

    result["core_coverage"] = clean(result.get("core_coverage", []), core_set)
    result["advanced_coverage"] = clean(result.get("advanced_coverage", []), adv_set)
    result["missed_core_signals"] = clean(result.get("missed_core_signals", []), core_set)
    result["misconceptions_detected"] = clean(result.get("misconceptions_detected", []), misc_set)

    return result


# ==========================
# INTERVIEW LOGIC
# ==========================
def run_interview(num_questions=3):
    difficulty = "L1"
    used_concepts = []
    history = []
    previous_eval = None

    print("\nStarting the Adaptive AI Interviewer...")
    print(f"Goal: {num_questions} questions | Initial Difficulty: {difficulty}")

    for i in range(num_questions):
        try:
            concept = fetch_concept(difficulty=difficulty, exclude_ids=used_concepts, history=history)
        except Exception as e:
            print(f"\nWarning: {e}")
            break

        used_concepts.append(concept["id"])
        print(f"\n--- Question {i+1} | Topic: {concept['id']} | Level: {difficulty} ---")

        question = generate_question(concept, history=history, previous_eval=previous_eval)
        print(f"\nQ: {question}")

        user_answer = input("\nYour Answer: ").strip()
        if not user_answer:
            print("Answer skipped.")
            continue

        print("\nEvaluating...")
        result = evaluate_answer(concept, user_answer)

        history.append({"question": question, "answer": user_answer})
        previous_eval = result

        score = result.get("score", 0)
        verdict = result.get("verdict", "N/A")

        print(f"Score: {score}/10 | Verdict: {verdict}")
        if result.get("misconceptions_detected"):
            print(f"Misconceptions: {', '.join(result['misconceptions_detected'])}")
        if result.get("_ungrounded_removed"):
            print(f"[grounding check] Removed hallucinated claims: {result['_ungrounded_removed']}")

        difficulty = update_difficulty(difficulty, score)
        print(f"Next Difficulty Target: {difficulty}")

    print("\n--- Interview Complete ---")
    print(f"Concepts covered: {', '.join(used_concepts)}")


if __name__ == "__main__":
    try:
        run_interview(num_questions=3)
    except KeyboardInterrupt:
        print("\n\nInterview terminated by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
