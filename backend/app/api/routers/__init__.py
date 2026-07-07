"""Router registry."""
from fastapi import APIRouter

from app.api.routers import (
    analytics,
    auth,
    dashboard,
    interview,
    jd,
    metrics,
    resume,
    user,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(jd.router, prefix="/jd", tags=["job-description"])
api_router.include_router(interview.router, prefix="/interview", tags=["interview"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(metrics.router, tags=["observability"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
