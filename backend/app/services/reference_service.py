"""Seed reference data (competencies) from the rubric config."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rubrics import COMPETENCIES
from app.models import Competency
from app.repositories.repositories import CompetencyRepository


async def ensure_competencies_seeded(db: AsyncSession) -> None:
    repo = CompetencyRepository(db)
    existing = {c.key for c in await repo.all()}
    for c in COMPETENCIES:
        if c["key"] not in existing:
            db.add(
                Competency(
                    id=c["id"], key=c["key"], name=c["name"], description=c["description"]
                )
            )
