"""Append-only analytics/observability event logging."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalyticsEvent


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, user_id: str | None, type_: str, payload: dict | None = None) -> None:
        self.db.add(AnalyticsEvent(user_id=user_id, type=type_, payload=payload or {}))

    async def counts_by_type(self) -> dict[str, int]:
        res = await self.db.execute(
            select(AnalyticsEvent.type, func.count()).group_by(AnalyticsEvent.type)
        )
        return {row[0]: int(row[1]) for row in res.all()}

    async def feedback_trust(self) -> dict:
        res = await self.db.execute(
            select(AnalyticsEvent.payload).where(AnalyticsEvent.type == "feedback_thumbs")
        )
        up = down = 0
        for row in res.all():
            payload = row[0] or {}
            if payload.get("helpful"):
                up += 1
            else:
                down += 1
        total = up + down
        return {"up": up, "down": down, "rate": round(up / total, 3) if total else None}

    async def llm_events(self, limit: int = 500) -> list[dict]:
        res = await self.db.execute(
            select(AnalyticsEvent.payload)
            .where(AnalyticsEvent.type == "llm_call")
            .order_by(AnalyticsEvent.created_at.desc())
            .limit(limit)
        )
        return [row[0] or {} for row in res.all()]
