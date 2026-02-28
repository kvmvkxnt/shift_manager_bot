from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_init_data import parse, validate
from telegram_init_data.exceptions import (
    AuthDateInvalidError,
    ExpiredError,
    SignatureInvalidError,
    SignatureMissingError,
)

from shift_manager_bot.config import settings
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.database.session import async_session_factory
from shift_manager_bot.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    authorization: str = Header(...), session: AsyncSession = Depends(get_db)
) -> User:
    if not authorization.startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    init_data_raw = authorization.removeprefix("tma ")

    try:
        validate(init_data_raw, settings.bot_token)
    except SignatureMissingError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature is missing from init data",
        )
    except AuthDateInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth date is invalid or missing",
        )
    except ExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Init data has expired"
        )
    except SignatureInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature verification failed",
        )

    init_data = parse(init_data_raw)
    tg_user = init_data.get("user")

    if not tg_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User data not found in init data",
        )

    user_service = UserService()

    # NOTE: Pyright errors are ignored because they are invalid
    user, _ = await user_service.get_or_create(
        session,
        telegram_id=tg_user["id"],  # pyright: ignore
        full_name=tg_user["first_name"],  # pyright: ignore
        username=tg_user.get("username"),
    )
    return user


def require_role(*roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action",
            )
        return current_user

    return role_checker
