"""Repository layer — the ONLY place that touches the database.

Grouped in one module for a small codebase; each class owns one aggregate and
contains no business rules (those live in services).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Answer,
    AnswerScore,
    Competency,
    InterviewSession,
    JobDescription,
    Question,
    ReadinessScore,
    Resume,
    UsageCounter,
    User,
)
from app.models.interview_session import SESSION_COMPLETED


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        res = await self.db.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def get_by_google_sub(self, sub: str) -> User | None:
        res = await self.db.execute(select(User).where(User.google_sub == sub))
        return res.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def touch_active(self, user: User) -> None:
        user.last_active_at = datetime.now(timezone.utc)


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, resume_id: str) -> Resume | None:
        return await self.db.get(Resume, resume_id)

    async def add(self, resume: Resume) -> Resume:
        self.db.add(resume)
        await self.db.flush()
        return resume

    async def latest_for_user(self, user_id: str) -> Resume | None:
        res = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        )
        return res.scalars().first()

    async def purge_inactive(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        res = await self.db.execute(delete(Resume).where(Resume.last_used_at < cutoff))
        return res.rowcount or 0


class JDRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, jd_id: str) -> JobDescription | None:
        return await self.db.get(JobDescription, jd_id)

    async def add(self, jd: JobDescription) -> JobDescription:
        self.db.add(jd)
        await self.db.flush()
        return jd

    async def latest_for_user(self, user_id: str) -> JobDescription | None:
        res = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .order_by(JobDescription.created_at.desc())
        )
        return res.scalars().first()


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, session_id: str) -> InterviewSession | None:
        return await self.db.get(InterviewSession, session_id)

    async def add(self, session: InterviewSession) -> InterviewSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def list_for_user(self, user_id: str) -> list[InterviewSession]:
        res = await self.db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list(res.scalars().all())

    async def completed_count(self, user_id: str) -> int:
        res = await self.db.execute(
            select(func.count())
            .select_from(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == SESSION_COMPLETED,
            )
        )
        return int(res.scalar_one())


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, question_id: str) -> Question | None:
        return await self.db.get(Question, question_id)

    async def add(self, question: Question) -> Question:
        self.db.add(question)
        await self.db.flush()
        return question

    async def list_for_session(self, session_id: str) -> list[Question]:
        res = await self.db.execute(
            select(Question)
            .where(Question.session_id == session_id)
            .order_by(Question.created_at.asc())
        )
        return list(res.scalars().all())


class AnswerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, answer: Answer) -> Answer:
        self.db.add(answer)
        await self.db.flush()
        return answer

    async def get_for_question(self, question_id: str) -> Answer | None:
        res = await self.db.execute(select(Answer).where(Answer.question_id == question_id))
        return res.scalars().first()

    async def list_for_session(self, session_id: str) -> list[Answer]:
        res = await self.db.execute(
            select(Answer).where(Answer.session_id == session_id).order_by(Answer.created_at.asc())
        )
        return list(res.scalars().all())

    async def add_score(self, score: AnswerScore) -> AnswerScore:
        self.db.add(score)
        await self.db.flush()
        return score

    async def recent_scores_for_user(self, user_id: str, track: str, limit: int = 60):
        """Per-dimension scores for a user+track, newest first — the readiness source data."""
        res = await self.db.execute(
            select(AnswerScore, Competency.key, Answer.created_at)
            .join(Answer, AnswerScore.answer_id == Answer.id)
            .join(InterviewSession, Answer.session_id == InterviewSession.id)
            .join(Competency, AnswerScore.competency_id == Competency.id)
            .where(InterviewSession.user_id == user_id, InterviewSession.track == track)
            .order_by(Answer.created_at.desc())
            .limit(limit)
        )
        return list(res.all())


class ReadinessRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, snapshot: ReadinessScore) -> ReadinessScore:
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def history_for_user(self, user_id: str) -> list[ReadinessScore]:
        res = await self.db.execute(
            select(ReadinessScore)
            .where(ReadinessScore.user_id == user_id)
            .order_by(ReadinessScore.created_at.asc())
        )
        return list(res.scalars().all())

    async def latest_for_user(self, user_id: str) -> ReadinessScore | None:
        res = await self.db.execute(
            select(ReadinessScore)
            .where(ReadinessScore.user_id == user_id)
            .order_by(ReadinessScore.created_at.desc())
        )
        return res.scalars().first()


class UsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_today(self, user_id: str) -> UsageCounter:
        today = date.today()
        counter = await self.db.get(UsageCounter, {"user_id": user_id, "day": today})
        if counter is None:
            counter = UsageCounter(user_id=user_id, day=today)
            self.db.add(counter)
            await self.db.flush()
        return counter


class CompetencyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def all(self) -> list[Competency]:
        res = await self.db.execute(select(Competency))
        return list(res.scalars().all())

    async def get_by_key(self, key: str) -> Competency | None:
        res = await self.db.execute(select(Competency).where(Competency.key == key))
        return res.scalar_one_or_none()
