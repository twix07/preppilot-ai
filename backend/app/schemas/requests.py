"""Request DTOs (Pydantic v2). Responses are assembled by services as documented dicts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=10)


class DevLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(default="Demo Student", max_length=200)


class ResumeTextRequest(BaseModel):
    raw_text: str = Field(min_length=20, max_length=20000)
    source: Literal["paste"] = "paste"


class JDRequest(BaseModel):
    raw_text: str = Field(min_length=20, max_length=20000)
    company_notes: str | None = Field(default=None, max_length=8000)


class InterviewStartRequest(BaseModel):
    track: Literal["behavioral", "pm"]
    resume_id: str | None = None
    jd_id: str | None = None


class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    text: str = Field(min_length=1, max_length=1800)


class ResumeAnalyzeRequest(BaseModel):
    resume_id: str
    jd_id: str | None = None


class JDAnalyzeRequest(BaseModel):
    jd_id: str
    resume_id: str | None = None


class FeedbackThumbsRequest(BaseModel):
    session_id: str
    question_id: str | None = None
    helpful: bool
