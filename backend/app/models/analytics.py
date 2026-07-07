from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.types import JSONType

# BIGINT on Postgres; INTEGER (rowid, auto-increments) on SQLite for local/dev/test.
_BigIntPK = BigInteger().with_variant(Integer, "sqlite")


class AnalyticsEvent(Base, TimestampMixin):
    """Append-only product + system events (activation, completion, latency, cost)."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
