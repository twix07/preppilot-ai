"""Authentication: Google OAuth -> app user -> JWT. Dev-login fallback for local runs."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.core.security import create_access_token, verify_google_id_token
from app.models import User
from app.repositories.repositories import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def _get_or_create(self, *, email: str, name: str, google_sub: str | None) -> User:
        user = None
        if google_sub:
            user = await self.users.get_by_google_sub(google_sub)
        if user is None:
            user = await self.users.get_by_email(email)
        if user is None:
            user = await self.users.add(User(email=email, name=name, google_sub=google_sub))
        else:
            if google_sub and not user.google_sub:
                user.google_sub = google_sub
            if name and not user.name:
                user.name = name
        await self.users.touch_active(user)
        return user

    async def login_with_google(self, id_token_str: str) -> tuple[User, str]:
        info = verify_google_id_token(id_token_str)
        user = await self._get_or_create(
            email=info["email"], name=info["name"], google_sub=info["sub"]
        )
        await self.db.commit()
        return user, create_access_token(user.id, user.email)

    async def dev_login(self, email: str, name: str) -> tuple[User, str]:
        if settings.is_production or not settings.allow_dev_login:
            raise ForbiddenError("Dev login is disabled.")
        user = await self._get_or_create(email=email, name=name or "Demo Student", google_sub=None)
        await self.db.commit()
        return user, create_access_token(user.id, user.email)
