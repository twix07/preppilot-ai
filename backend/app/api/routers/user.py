from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.services.user_service import UserService

router = APIRouter()


@router.delete("/data", status_code=204)
async def delete_my_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Irreversibly delete all of the current user's data."""
    await UserService(db).delete_all_data(user.id)
    return Response(status_code=204)
