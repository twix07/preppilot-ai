from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.requests import JDAnalyzeRequest, JDRequest
from app.services.jd_service import JDService
from app.services.job_intelligence_service import JobIntelligenceService

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_jd(
    body: JDRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    jd = await JDService(db).create(user.id, body.raw_text, body.company_notes)
    return {"id": jd.id, "created_at": jd.created_at.isoformat(),
            "required_skills": jd.required_skills or []}


@router.post("/analyze")
async def analyze_jd(
    body: JDAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """E2 — Job Intelligence: required skills, resume comparison, company prep tips."""
    return await JobIntelligenceService(db).analyze(user.id, body.jd_id, body.resume_id)
