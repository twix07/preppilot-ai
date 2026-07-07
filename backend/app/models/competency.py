from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Competency(Base):
    """Reference table. Seeded from app.ai.rubrics at startup."""

    __tablename__ = "competencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # stable small ints
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
