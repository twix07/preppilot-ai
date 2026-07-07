"""Account/privacy: delete-my-data and retention purge."""
from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import (
    AnalyticsEvent,
    Answer,
    AnswerScore,
    InterviewSession,
    JobDescription,
    Question,
    ReadinessScore,
    Resume,
    UsageCounter,
    User,
)
from app.repositories.repositories import ResumeRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_all_data(self, user_id: str) -> None:
        """Irreversibly purge all of a user's data. Cascades would cover most of this,
        but we delete explicitly so behavior is identical on SQLite (no FK cascade)."""
        # Order matters where cascades aren't enforced.
        session_ids = [
            r[0] for r in (
                await self.db.execute(
                    InterviewSession.__table__.select().with_only_columns(InterviewSession.id)
                    .where(InterviewSession.user_id == user_id)
                )
            ).all()
        ]
        if session_ids:
            answer_ids = [
                r[0] for r in (
                    await self.db.execute(
                        Answer.__table__.select().with_only_columns(Answer.id)
                        .where(Answer.session_id.in_(session_ids))
                    )
                ).all()
            ]
            if answer_ids:
                await self.db.execute(
                    delete(AnswerScore).where(AnswerScore.answer_id.in_(answer_ids))
                )
            await self.db.execute(delete(Answer).where(Answer.session_id.in_(session_ids)))
            await self.db.execute(delete(Question).where(Question.session_id.in_(session_ids)))
            await self.db.execute(
                delete(ReadinessScore).where(ReadinessScore.session_id.in_(session_ids))
            )
        await self.db.execute(delete(InterviewSession).where(InterviewSession.user_id == user_id))
        await self.db.execute(delete(Resume).where(Resume.user_id == user_id))
        await self.db.execute(delete(JobDescription).where(JobDescription.user_id == user_id))
        await self.db.execute(delete(UsageCounter).where(UsageCounter.user_id == user_id))
        await self.db.execute(delete(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id))
        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()

    async def purge_inactive_resumes(self) -> int:
        count = await ResumeRepository(self.db).purge_inactive(settings.resume_retention_days)
        await self.db.commit()
        return count
