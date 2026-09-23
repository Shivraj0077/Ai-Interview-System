from typing import Literal

from pydantic import BaseModel, Field, field_validator

from rag.retrieval import DOMAINS

Level = Literal["L1", "L2", "L3"]


class CreateInterviewRequest(BaseModel):
    candidate_name: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=80)
    interview_type: Literal["technical"] = "technical"
    difficulty_mode: Literal["adaptive", "fixed"] = "adaptive"
    start_difficulty: Level = "L1"
    num_questions: int = Field(default=6, ge=3, le=10)
    focus_areas: list[str] = Field(default_factory=list, max_length=len(DOMAINS))
    job_description: str = Field(default="", max_length=6000)
    resume_text: str = Field(default="", max_length=8000)
    resume_filename: str | None = Field(default=None, max_length=200)

    @field_validator("candidate_name", "role", "job_description", "resume_text")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("focus_areas")
    @classmethod
    def known_domains(cls, v: list[str]) -> list[str]:
        unknown = [d for d in v if d not in DOMAINS]
        if unknown:
            raise ValueError(f"Unknown focus areas: {', '.join(unknown)}")
        return list(dict.fromkeys(v))


class AnswerRequest(BaseModel):
    question_index: int = Field(ge=0)
    answer: str = Field(max_length=4000)


class SkipRequest(BaseModel):
    question_index: int = Field(ge=0)
