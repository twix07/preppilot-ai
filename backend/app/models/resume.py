from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey, _now
from app.models.types import JSONType


class Resume(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Stored encrypted at rest (Fernet). Access via ResumeService which decrypts.
    raw_text_enc: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="paste")  # paste | pdf
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    # Extension (E1) fields — nullable so Core ships without them.
    extracted_skills: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
