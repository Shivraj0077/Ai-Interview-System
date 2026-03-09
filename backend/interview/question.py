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
# FETCH CONCEPT
# ==========================
def fetch_concept(difficulty="L1"):
    response = (
        supabase
        .table("rag_concepts")
        .select("*")
        .eq("difficulty", difficulty)
        .execute()
    )

    concepts = response.data
    if not concepts:
        raise Exception("No concepts found")

    return random.choice(concepts)

# ==========================
# GENERATE QUESTION
# ==========================
def generate_question(concept):

    prompt = f"""
Generate exactly ONE conceptual interview question.

Concept: {concept['id']}
Difficulty: {concept['difficulty']}

Knowledge Context:
{concept['text']}

Rules:
- Ask only ONE question.
- No explanation.
- No answer.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You generate only interview questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=150
    )

    return response.choices[0].message.content.strip()

# ==========================
# EVALUATE ANSWER
# ==========================
def evaluate_answer(concept, user_answer):

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
        return json.loads(raw_output)
    except:
        return {"error": "Invalid JSON returned", "raw": raw_output}

# ==========================
# RUN INTERVIEW ROUND
# ==========================
if __name__ == "__main__":

    difficulty = "L1"

    concept = fetch_concept(difficulty)

    print("\n--- Interview Question ---\n")
    question = generate_question(concept)
    print(question)

    user_answer = input("\nYour Answer:\n")

    print("\n--- Evaluation ---\n")
    result = evaluate_answer(concept, user_answer)

    print(json.dumps(result, indent=2))