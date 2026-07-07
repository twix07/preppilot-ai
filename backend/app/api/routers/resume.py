from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.requests import ResumeAnalyzeRequest, ResumeTextRequest
from app.services.resume_intelligence_service import ResumeIntelligenceService
from app.services.resume_service import ResumeService

router = APIRouter()


def _dto(resume) -> dict:
    return {"id": resume.id, "source": resume.source, "char_count": resume.char_count,
            "created_at": resume.created_at.isoformat()}


@router.post("/upload", status_code=201)
async def upload_resume_text(
    body: ResumeTextRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    resume = await ResumeService(db).create_from_text(user.id, body.raw_text)
    return _dto(resume)


@router.post("/upload-pdf", status_code=201)
async def upload_resume_pdf(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    data = await file.read()
    resume = await ResumeService(db).create_from_pdf(user.id, file.filename or "resume.pdf", data)
    return _dto(resume)


@router.post("/analyze")
async def analyze_resume(
    body: ResumeAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """E1 — Resume Intelligence: skills, summary, JD match %, improvement suggestions."""
    return await ResumeIntelligenceService(db).analyze(user.id, body.resume_id, body.jd_id)
