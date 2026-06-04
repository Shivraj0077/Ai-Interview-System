import os
import random
import json
from dotenv import load_dotenv
from supabase import create_client
from groq import Groq

# ==========================
# CONFIG
# ==========================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Groq(api_key=GROQ_API_KEY)

# ==========================
# HELPERS
# ==========================
def fetch_concept(difficulty="L1", exclude_ids=None):
    """
    Fetch a concept from Supabase based on difficulty.
    """
    response = (
        supabase
        .table("rag_concepts")
        .select("*")
        .eq("difficulty", difficulty)
        .execute()
    )

    concepts = response.data
    if not concepts:
        raise Exception(f"No concepts found for difficulty {difficulty}")

    if exclude_ids:
        concepts = [c for c in concepts if c["id"] not in exclude_ids]
    
    if not concepts:
        raise Exception(f"No new concepts available for difficulty {difficulty}")

    return random.choice(concepts)

def update_difficulty(current_level, score):
    """
    Adjust the interview difficulty based on the score (0-10).
    L1 -> L2 if score >= 8
    L1/L2 -> L1 if score <= 4
    """
    levels = ["L1", "L2", "L3"]
    try:
        idx = levels.index(current_level)
    except ValueError:
        idx = 0

    if score >= 8 and idx < len(levels) - 1:
        idx += 1
    elif score <= 4 and idx > 0:
        idx -= 1

    return levels[idx]

# ==========================
# GENERATE QUESTION
# ==========================
def generate_question(concept, history=None, previous_eval=None):
    """
    Use Groq to generate a question for a given concept, adaptively based on past context.
    """
    history_text = ""
    if history:
        recent = history[-2:] # take last 2 for context
        hist_fmt = "\n".join([f"Q: {h['question']}\nA: {h['answer']}" for h in recent])
        history_text += f"\nRecent Interview History:\n{hist_fmt}\n"
    
    eval_text = ""
    if previous_eval:
        eval_text += f"""
Previous Evaluation:
Score: {previous_eval.get('score')}
Misconceptions: {', '.join(previous_eval.get('misconceptions_detected', [])) if previous_eval.get('misconceptions_detected') else 'None'}
Missed Core: {', '.join(previous_eval.get('missed_core_signals', [])) if previous_eval.get('missed_core_signals') else 'None'}

Instruction: Tailor the new question to implicitly address or probe the candidate's previous misconceptions or missed concepts if relevant, while remaining focused on the new Concept context.
"""

    prompt = f"""
Generate exactly ONE conceptual interview question.

Concept: {concept['id']}
Difficulty: {concept['difficulty']}

Knowledge Context:
{concept.get('text', '')}
{history_text}{eval_text}
Rules:
- Ask only ONE question.
- No explanation.
- No answer.
- Make it conversational and natural for an interview.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert AI interviewer generating questions adaptively."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )

    return response.choices[0].message.content.strip()

# ==========================
# EVALUATE ANSWER
# ==========================
def evaluate_answer(concept, user_answer):
    """
    Use Groq to evaluate the user's answer against core and advanced signals.
    """
    prompt = f"""
Evaluate the candidate answer strictly.

Concept: {concept['id']}

Core signals:
{concept.get('core_signals', [])}

Advanced signals:
{concept.get('advanced_signals', [])}

Common misconceptions:
{concept.get('common_misconceptions', [])}

Candidate Answer:
\"\"\"
{user_answer}
\"\"\"

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
            {"role": "system", "content": "You are a strict technical evaluator. Return only JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=400
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        # Some models use markdown blocks for JSON
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0].strip()
        
        return json.loads(raw_output)
    except:
        return {"error": "Invalid JSON returned", "raw": raw_output, "score": 0}

# ==========================
# INTERVIEW LOGIC
# ==========================
def run_interview(num_questions=3):
    """
    Conduct a multi-question interview with dynamic difficulty and adaptive questions.
    """
    difficulty = "L1"
    used_concepts = []
    history = []
    previous_eval = None

    print("\nStarting the Adaptive AI Interviewer...")
    print(f"Goal: {num_questions} questions | Initial Difficulty: {difficulty}")

    for i in range(num_questions):
        try:
            concept = fetch_concept(
                difficulty=difficulty,
                exclude_ids=used_concepts
            )
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
        
        # Save to history
        history.append({
            "question": question,
            "answer": user_answer
        })
        previous_eval = result

        score = result.get("score", 0)
        verdict = result.get("verdict", "N/A")

        print(f"Score: {score}/10 | Verdict: {verdict}")
        if result.get("misconceptions_detected"):
            print(f"Misconceptions: {', '.join(result['misconceptions_detected'])}")

        difficulty = update_difficulty(difficulty, score)
        print(f"Next Difficulty Target: {difficulty}")

    print("\n--- Interview Complete ---")
    print(f"Concepts covered: {', '.join(used_concepts)}")

# ==========================
# ENTRY POINT
# ==========================
if __name__ == "__main__":
    try:
        run_interview(num_questions=3)
    except KeyboardInterrupt:
        print("\n\nInterview terminated by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")