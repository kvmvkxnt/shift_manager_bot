import random

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.user_service import UserService


@pytest.fixture
def service() -> UserService:
    return UserService()


@pytest.fixture
async def existing_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(800000000, 899999999),
        full_name="Existing User",
        username="existinguser",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_by_telegram_id(
    db_session: AsyncSession, service: UserService, existing_user: User
) -> None:
    user: User | None = await service.get_by_telegram_id(
        db_session, existing_user.telegram_id
    )

    assert user is not None
    assert user.telegram_id == existing_user.telegram_id
    assert user.full_name == existing_user.full_name


@pytest.mark.asyncio
async def test_get_by_telegram_id_not_found(
    db_session: AsyncSession, service: UserService
) -> None:
    user: User | None = await service.get_by_telegram_id(db_session, 9999999999999)

    assert user is None


@pytest.mark.asyncio
async def test_create_user_minimal(
    db_session: AsyncSession, service: UserService
) -> None:
    user: User = await service.create_user(
        db_session,
        telegram_id=random.randint(900000000, 999999999),
        full_name="Minimal User",
    )

    assert user.id is not None
    assert user.full_name == "Minimal User"
    assert user.username is None
    assert user.role == UserRole.PENDING
    assert user.is_active is True


@pytest.mark.asyncio
async def test_create_user_with_all_fields(
    db_session: AsyncSession, service: UserService
) -> None:
    user: User = await service.create_user(
        db_session,
        telegram_id=random.randint(1100000000, 1199999999),
        full_name="Full User",
        username="fulluser",
        role=UserRole.MANAGER,
    )

    assert user.username == "fulluser"
    assert user.role == UserRole.MANAGER


@pytest.mark.asyncio
async def test_get_or_create_creates_new(
    db_session: AsyncSession, service: UserService
) -> None:
    user: User
    created: bool
    telegram_id = random.randint(1200000000, 1299999999)
    user, created = await service.get_or_create(
        db_session,
        telegram_id=telegram_id,
        full_name="Brand New User",
    )

    assert created is True
    assert user.telegram_id == telegram_id
    assert user.role == UserRole.PENDING


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(
    db_session: AsyncSession, service: UserService, existing_user: User
) -> None:
    user: User
    created: bool
    user, created = await service.get_or_create(
        db_session,
        telegram_id=existing_user.telegram_id,
        full_name=existing_user.full_name,
    )

    assert created is False
    assert user.id == existing_user.id


@pytest.mark.asyncio
async def test_update_role(
    db_session: AsyncSession, service: UserService, existing_user: User
) -> None:
    updated: User = await service.update_role(
        db_session, existing_user, UserRole.MANAGER
    )

    assert updated.role == UserRole.MANAGER


@pytest.mark.asyncio
async def test_deactivate_user(
    db_session: AsyncSession, service: UserService, existing_user: User
) -> None:
    updated: User = await service.deactivate(db_session, existing_user)

    assert updated.is_active is False
