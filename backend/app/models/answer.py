from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey
from app.models.types import JSONType


class Answer(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "answers"

    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    # {improvements: [...], recommendations: [...]} — improvements must quote the student.
    feedback: Mapped[dict | None] = mapped_column(JSONType, nullable=True)


class AnswerScore(Base, UUIDPrimaryKey, TimestampMixin):
    """One row per rubric dimension (competency) per scored answer.

    This is the source of truth: ReadinessScores are fully recomputable from here.
    """

    __tablename__ = "answer_scores"

    answer_id: Mapped[str] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), index=True
    )
    competency_id: Mapped[int] = mapped_column(
        ForeignKey("competencies.id", ondelete="RESTRICT"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1..5 (validated in service)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
