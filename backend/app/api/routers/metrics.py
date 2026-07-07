from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.observability.metrics import METRICS
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/metrics")
async def internal_metrics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Internal system observability view (auth-gated)."""
    analytics = AnalyticsService(db)
    llm = await analytics.llm_events()
    tokens = sum(int(e.get("input_tokens", 0)) + int(e.get("output_tokens", 0)) for e in llm)
    cost = round(sum(float(e.get("cost_usd", 0)) for e in llm), 4)
    ai_lat = [float(e.get("latency_ms", 0)) for e in llm if e.get("latency_ms") is not None]
    counts = await analytics.counts_by_type()
    trust = await analytics.feedback_trust()
    return {
        "api": METRICS.snapshot(),
        "ai": {
            "llm_calls": len(llm),
            "tokens_total": tokens,
            "est_cost_usd": cost,
            "ai_latency_ms_avg": round(sum(ai_lat) / len(ai_lat), 1) if ai_lat else 0.0,
        },
        "product": {
            "interviews_started": counts.get("interview_started", 0),
            "interviews_completed": counts.get("interview_completed", 0),
            "feedback_trust": trust,
        },
    }
