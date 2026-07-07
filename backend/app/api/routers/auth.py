from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.requests import DevLoginRequest, GoogleLoginRequest
from app.services.auth_service import AuthService

router = APIRouter()


def _auth_response(user: User, token: str) -> dict:
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name},
    }


@router.post("/google")
async def google_login(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user, token = await AuthService(db).login_with_google(body.id_token)
    return _auth_response(user, token)


@router.post("/dev-login")
async def dev_login(body: DevLoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Dev/local only (disabled in production). Lets the app be demoed without Google."""
    user, token = await AuthService(db).dev_login(body.email, body.name)
    return _auth_response(user, token)


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}
