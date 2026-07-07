from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.requests import (
    FeedbackThumbsRequest,
    InterviewAnswerRequest,
    InterviewStartRequest,
)
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("/feedback/thumbs", status_code=202)
async def feedback_thumbs(
    body: FeedbackThumbsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record a 👍/👎 on a feedback card (product metric: feedback trust)."""
    await InterviewService(db).record_feedback_thumbs(
        user.id, body.session_id, body.question_id, body.helpful
    )
    return {"recorded": True}


@router.post("/start", status_code=201)
async def start_interview(
    body: InterviewStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await InterviewService(db).start(user.id, body.track, body.resume_id, body.jd_id)


@router.post("/answer")
async def submit_answer(
    body: InterviewAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await InterviewService(db).submit_answer(
        user.id, body.session_id, body.question_id, body.text
    )


@router.get("/{session_id}")
async def get_session_report(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await InterviewService(db).get_report(user.id, session_id)
