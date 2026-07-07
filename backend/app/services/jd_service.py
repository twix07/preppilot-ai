"""Job Description ingestion (direct context). Untrusted text; treated as data only."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, PayloadTooLargeError, ValidationAppError
from app.models import JobDescription
from app.repositories.repositories import JDRepository

MAX_TEXT_CHARS = 20000


class JDService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JDRepository(db)

    async def create(self, user_id: str, raw_text: str, company_notes: str | None) -> JobDescription:
        text = (raw_text or "").strip()
        if len(text) < 20:
            raise ValidationAppError("Job description is too short.")
        if len(text) > MAX_TEXT_CHARS:
            raise PayloadTooLargeError("Job description is too long. Please trim it.")
        jd = JobDescription(
            user_id=user_id, raw_text=text, company_notes=(company_notes or "").strip() or None
        )
        await self.repo.add(jd)
        await self.db.commit()
        return jd

    async def get_owned_text(self, user_id: str, jd_id: str | None) -> tuple[str | None, str]:
        if not jd_id:
            return None, ""
        jd = await self.repo.get(jd_id)
        if jd is None:
            return None, ""
        if jd.user_id != user_id:
            raise ForbiddenError("You do not have access to that job description.")
        return jd.id, jd.raw_text
