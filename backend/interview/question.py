from ai.provider import LLMProvider
from errors import UpstreamError


class QuestionGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate(self, concept: dict, history=None, previous_eval=None, role: str | None = None) -> str:
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

        role_text = f"\nRole being interviewed for: {role}\n" if role else ""

        prompt = f"""
Generate exactly ONE conceptual interview question.

Concept: {concept['id']}
Difficulty: {concept['difficulty']}
{role_text}
Knowledge Context (ground the question strictly in this):
{concept.get('text', '')}
{history_text}{eval_text}
Rules:
- Ask only ONE question.
- The question must be answerable using only the Knowledge Context above.
- No explanation. No answer.
- Make it conversational and natural for an interview.
- Where it fits naturally, frame it around work the role above would do.
- Output only the question text.
"""

        raw = self.llm.generate(
            [
                {"role": "system", "content": "You are an expert AI interviewer generating questions adaptively. Never ask about facts outside the given context."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=150,
        )
        question = clean_question(raw)
        if len(question) < 10:
            raise UpstreamError("The AI interviewer produced an unusable question. Please try again.")
        return question


_PREAMBLES = ("here is", "here's", "question:", "sure", "okay", "ok,")


def clean_question(raw: str) -> str:
    """Strip the chatty wrappers small models like to add around the question."""
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    while len(lines) > 1 and lines[0].lower().startswith(_PREAMBLES) and lines[0].endswith(":"):
        lines.pop(0)
    text = " ".join(lines)
    if text.lower().startswith("question:"):
        text = text[len("question:"):].strip()
    # Questions render as plain text, so drop markdown emphasis/code markers.
    text = text.replace("`", "").replace("**", "")
    return text.strip().strip('"').strip("“”").strip()
