"""Cost & abuse controls: per-user daily caps + spend tracking (Postgres, no Redis)."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import RateLimitedError
from app.repositories.repositories import UsageRepository


class UsageService:
    def __init__(self, db: AsyncSession):
        self.repo = UsageRepository(db)

    async def check_interview_cap(self, user_id: str) -> None:
        counter = await self.repo.get_or_create_today(user_id)
        if counter.interviews_started >= settings.daily_interview_cap:
            raise RateLimitedError(
                "You've reached today's practice limit. Come back tomorrow to keep going!"
            )

    async def check_llm_cap(self, user_id: str) -> None:
        counter = await self.repo.get_or_create_today(user_id)
        if counter.llm_calls >= settings.daily_llm_call_cap:
            raise RateLimitedError("You've reached today's AI usage limit. Please try again tomorrow.")

    async def record_interview_start(self, user_id: str) -> None:
        counter = await self.repo.get_or_create_today(user_id)
        counter.interviews_started += 1

    async def record_llm_call(self, user_id: str, cost_usd: float) -> None:
        counter = await self.repo.get_or_create_today(user_id)
        counter.llm_calls += 1
        counter.est_cost_usd = float(counter.est_cost_usd or 0) + float(cost_usd or 0)
