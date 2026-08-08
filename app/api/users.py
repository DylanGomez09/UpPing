from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.ping_test import PingTest
from app.models.user import User
from app.schemas.user import MeOut, UpdateProfileRequest, UserOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeOut:
    total_tests = await db.scalar(
        select(func.count()).select_from(PingTest).where(
            PingTest.user_id == user.id
        )
    )
    base = UserOut.model_validate(user)
    return MeOut(**base.model_dump(), total_tests=total_tests or 0)


@router.patch("", response_model=UserOut)
async def update_me(
    payload: UpdateProfileRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user.display_name = payload.display_name
    await db.commit()
    await db.refresh(user)
    return user
