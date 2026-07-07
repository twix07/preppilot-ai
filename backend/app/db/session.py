"""Async engine + session factory + init helpers."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base

engine = create_async_engine(settings.async_database_url, echo=False, future=True, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables and seed reference data. Used at startup for a zero-config run.

    Production migrations are managed with Alembic (see alembic/); create_all is
    idempotent and safe as a bootstrap for fresh databases.
    """
    # Import models so they register on the metadata before create_all.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.services.reference_service import ensure_competencies_seeded

    async with SessionLocal() as session:
        await ensure_competencies_seeded(session)
        await session.commit()
