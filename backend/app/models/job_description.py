from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey
from app.models.types import JSONType


class JobDescription(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "job_descriptions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)  # untrusted input (data, not commands)
    company_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # optional, user-pasted (E2)
    required_skills: Mapped[list | None] = mapped_column(JSONType, nullable=True)  # extracted (E2)
