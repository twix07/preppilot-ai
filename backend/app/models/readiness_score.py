from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey
from app.models.types import JSONType

BAND_BUILDING_BASELINE = "building_baseline"
BAND_BUILDING = "building"
BAND_DEVELOPING = "developing"
BAND_NEARLY_READY = "nearly_ready"
BAND_INTERVIEW_READY = "interview_ready"


class ReadinessScore(Base, UUIDPrimaryKey, TimestampMixin):
    """A readiness snapshot taken after each completed session (powers the trend)."""

    __tablename__ = "readiness_scores"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE")
    )
    track: Mapped[str] = mapped_column(String(16))
    overall: Mapped[float] = mapped_column(Numeric(5, 2))
    competency_breakdown: Mapped[dict] = mapped_column(JSONType)  # {key: 0-100}
    band: Mapped[str] = mapped_column(String(24))
    session_count: Mapped[int] = mapped_column(Integer)
