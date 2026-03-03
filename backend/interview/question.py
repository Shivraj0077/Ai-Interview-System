import os
import random
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

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Groq(api_key=GROQ_API_KEY)

# ==========================
# FETCH RANDOM CONCEPT
# ==========================
def fetch_random_concept(difficulty="L1"):
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
You are a technical interviewer conducting a fresher SDE interview.

Generate exactly ONE conceptual interview question.

Concept: {concept['id']}
Domain: {concept['domain']}
Difficulty: {concept['difficulty']}

Knowledge Context:
{concept['text']}

Rules:
- Based on difficulty ask the question
- Ask only ONE question.
- No explanation.
- Do not provide the answer.
- Keep it concise.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a strict technical interviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    return response.choices[0].message.content.strip()

# ==========================
# RUN
# ==========================
if __name__ == "__main__":

    concept = fetch_random_concept("L1")

    print(f"\nSelected Concept: {concept['id']}")
    print(f"Domain: {concept['domain']} | Difficulty: {concept['difficulty']}")

    question = generate_question(concept)

    print("\nGenerated Question:\n")
    print(question)