"""Dashboard + analytics assembly. Pure data — no LLM calls."""
from __future__ import annotations

from app.ai.rubrics import COMPETENCY_NAME_BY_KEY, TRACK_PM
from app.models.interview_session import SESSION_COMPLETED
from app.repositories.repositories import (
    ReadinessRepository,
    SessionRepository,
)
from app.services import roadmap_service
from app.services.scoring_service import compute_readiness


class DashboardService:
    def __init__(self, db):
        self.db = db
        self.readiness = ReadinessRepository(db)
        self.sessions = SessionRepository(db)

    async def _primary_track(self, user_id: str) -> str:
        latest = await self.readiness.latest_for_user(user_id)
        return latest.track if latest else TRACK_PM

    async def build_dashboard(self, user_id: str) -> dict:
        track = await self._primary_track(user_id)
        result = await compute_readiness(self.db, user_id, track)
        history = await self.readiness.history_for_user(user_id)
        sessions = await self.sessions.list_for_user(user_id)

        competencies = [
            {"key": k, "name": COMPETENCY_NAME_BY_KEY[k], "score": round(v, 1)}
            for k, v in result.competency_breakdown.items()
        ]
        trend = [
            {"date": s.created_at.date().isoformat(), "overall": float(s.overall),
             "band": s.band, "track": s.track}
            for s in history
        ]
        recent = [
            {"id": s.id, "track": s.track, "date": s.created_at.date().isoformat(),
             "status": s.status,
             "overall": (s.report or {}).get("readiness", {}).get("overall")}
            for s in sessions[:8]
        ]
        return {
            "readiness": {
                "overall": result.overall, "band": result.band,
                "session_count": result.session_count,
                "min_sessions": _min_sessions(),
            },
            "competencies": competencies,
            "trend": trend,
            "top_weaknesses": roadmap_service.top_weaknesses(result.competency_breakdown),
            "skill_gaps": roadmap_service.skill_gaps(result.competency_breakdown, None),
            "roadmap": roadmap_service.weekly_roadmap(result.competency_breakdown),
            "recent_sessions": recent,
        }

    async def build_analytics(self, user_id: str) -> dict:
        sessions = await self.sessions.list_for_user(user_id)
        completed = [s for s in sessions if s.status == SESSION_COMPLETED]
        history = await self.readiness.history_for_user(user_id)
        overalls = [float(s.overall) for s in history]
        change_30d = round(overalls[-1] - overalls[0], 1) if len(overalls) >= 2 else 0.0
        return {
            "sessions": [
                {"id": s.id, "track": s.track, "date": s.created_at.date().isoformat(),
                 "status": s.status,
                 "overall": (s.report or {}).get("readiness", {}).get("overall"),
                 "band": (s.report or {}).get("readiness", {}).get("band")}
                for s in sessions
            ],
            "totals": {
                "interviews_completed": len(completed),
                "avg_score": round(sum(overalls) / len(overalls), 1) if overalls else 0.0,
                "readiness_change_30d": change_30d,
            },
        }


def _min_sessions() -> int:
    from app.core.config import settings

    return settings.readiness_min_sessions
