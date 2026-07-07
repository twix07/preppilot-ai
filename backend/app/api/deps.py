"""Shared FastAPI dependencies: DB session + current authenticated user."""
from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models import User
from app.repositories.repositories import UserRepository


async def get_db() -> AsyncSession:  # thin passthrough for clarity in routers
    async for session in get_session():
        yield session


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token.")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    user = await UserRepository(db).get(user_id) if user_id else None
    if user is None:
        raise UnauthorizedError("User no longer exists.")
    return user
