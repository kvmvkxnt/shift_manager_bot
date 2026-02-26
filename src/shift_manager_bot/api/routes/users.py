from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.api.dependencies import get_current_user, get_db, require_role
from shift_manager_bot.services.user_service import UserService


router = APIRouter()


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/team", response_model=list[UserResponse])
async def get_team(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.OWNER)),
) -> list[User]:
    service = UserService()
    return await service.get_all_active(session)
