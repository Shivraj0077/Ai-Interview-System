import io
import logging
from collections import Counter

from fastapi import APIRouter, File, UploadFile
from pypdf import PdfReader

from api.schemas import AnswerRequest, CreateInterviewRequest, SkipRequest
from api.views import detail_view, session_view
from config import settings
from demo.seed import ensure_samples
from errors import ValidationError
from rag.retrieval import DOMAINS
from services import get_engine

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

DEMO_PRESET = {
    "candidate_name": "Demo Candidate",
    "role": "Backend Engineer",
    "interview_type": "technical",
    "difficulty_mode": "adaptive",
    "start_difficulty": "L1",
    "num_questions": 5,
    "focus_areas": ["backend", "database", "distributed_systems"],
    "job_description": (
        "We're hiring an entry-level Backend Engineer to build and operate REST APIs for our payments "
        "platform. You'll design endpoints, model data in PostgreSQL, tune queries, and help make "
        "event-driven services reliable (retries, idempotency, message queues)."
    ),
}

_samples_ready = False


def _ensure_samples(engine) -> None:
    global _samples_ready
    if _samples_ready:
        return
    try:
        ensure_samples(engine)
        _samples_ready = True
    except Exception:
        # A missing table shouldn't break the dashboard; the list call will surface real DB errors.
        log.exception("Could not insert sample interviews")


@router.get("/health")
def health():
    return {
        "status": "ok",
        "configured": {
            "llm": bool(settings.groq_api_key),
            "embeddings": bool(settings.gemini_api_key),
            "database": bool(settings.supabase_url and settings.supabase_key),
        },
        "interview_store": settings.interview_store,
    }


@router.get("/meta")
def meta():
    engine = get_engine()
    counts: dict[str, Counter] = {d: Counter() for d in DOMAINS}
    for c in engine.retriever.catalog.values():
        if c["domain"] in counts:
            counts[c["domain"]][c["difficulty"]] += 1
    return {
        "focus_areas": [
            {"id": d, "label": label, "concepts": {lvl: counts[d].get(lvl, 0) for lvl in ("L1", "L2", "L3")}}
            for d, label in DOMAINS.items()
        ],
        "total_concepts": len(engine.retriever.catalog),
        "engine": engine.engine_info,
        "demo": DEMO_PRESET,
    }


@router.get("/interviews")
def list_interviews():
    engine = get_engine()
    _ensure_samples(engine)
    return {"interviews": engine.repo.list()}


@router.post("/interviews", status_code=201)
def create_interview(body: CreateInterviewRequest):
    config = body.model_dump(exclude={"candidate_name", "role"})
    interview = get_engine().create(config, candidate_name=body.candidate_name, role=body.role)
    return detail_view(interview)


@router.post("/interviews/demo", status_code=201)
def create_demo_interview():
    body = CreateInterviewRequest(**DEMO_PRESET)
    return create_interview(body)


@router.get("/interviews/{interview_id}")
def get_interview(interview_id: str):
    return detail_view(get_engine().get(interview_id))


@router.get("/interviews/{interview_id}/session")
def get_session(interview_id: str):
    return session_view(get_engine().get(interview_id))


@router.post("/interviews/{interview_id}/start")
def start_interview(interview_id: str):
    return session_view(get_engine().start(interview_id))


@router.post("/interviews/{interview_id}/question")
def prepare_question(interview_id: str):
    """Retry generating the next question after a provider failure."""
    return session_view(get_engine().ensure_question(interview_id))


@router.post("/interviews/{interview_id}/answer")
def submit_answer(interview_id: str, body: AnswerRequest):
    return session_view(get_engine().submit_answer(interview_id, body.question_index, body.answer))


@router.post("/interviews/{interview_id}/skip")
def skip_question(interview_id: str, body: SkipRequest):
    return session_view(get_engine().skip(interview_id, body.question_index))


@router.post("/interviews/{interview_id}/finish")
def finish_interview(interview_id: str):
    return session_view(get_engine().finish(interview_id))


@router.get("/interviews/{interview_id}/report")
def get_report(interview_id: str):
    interview = get_engine().get(interview_id)
    if interview["status"] != "completed":
        raise ValidationError("The report is available once the interview is finished.", code="not_ready")
    return detail_view(interview)


MAX_RESUME_BYTES = 2 * 1024 * 1024


@router.post("/resume")
async def parse_resume(file: UploadFile = File(...)):
    """Extract plain text from a PDF resume. Text only: no layout, OCR or field parsing."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise ValidationError("Upload the resume as a PDF file.")
    data = await file.read(MAX_RESUME_BYTES + 1)
    if len(data) > MAX_RESUME_BYTES:
        raise ValidationError("Resume PDFs are limited to 2 MB.")
    try:
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:5])
    except Exception:
        log.info("Could not parse uploaded PDF", exc_info=True)
        raise ValidationError("That PDF couldn't be read. Try exporting it again, or paste the text instead.")
    text = " ".join(text.split())
    if len(text) < 50:
        raise ValidationError("No text found in that PDF (scanned resumes aren't supported). Paste the text instead.")
    return {"filename": file.filename, "text": text[:8000], "truncated": len(text) > 8000}
