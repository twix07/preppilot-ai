"""FastAPI application factory — modular monolith entrypoint."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import api_router
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, unhandled_error_handler
from app.core.logging import configure_logging, get_logger
from app.db.session import init_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.observability.metrics import MetricsMiddleware

logger = get_logger("main")


def _configure_langsmith() -> None:
    if settings.langsmith_api_key and settings.langchain_tracing_v2:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
        logger.info("LangSmith tracing enabled (project=%s).", settings.langsmith_project)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    _configure_langsmith()
    await init_db()
    mode = "MOCK" if settings.llm_mock_mode else "LIVE"
    logger.info("PrepPilot API up. LLM=%s model=%s db=%s",
                mode, settings.llm_model, settings.database_url.split("://")[0])
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="PrepPilot AI API",
        version="0.1.0",
        description="AI Career Intelligence Platform — core interview→evaluation→readiness loop.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MetricsMiddleware)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        return {"status": "ok", "llm_mode": "mock" if settings.llm_mock_mode else "live"}

    app.include_router(api_router)
    return app


app = create_app()
