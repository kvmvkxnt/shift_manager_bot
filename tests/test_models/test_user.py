import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user = User(
        telegram_id=123456789,
        username="testuser",
        full_name="Test User",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.role == UserRole.EMPLOYEE
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_telegram_id_is_unique(db_session: AsyncSession):
    user1 = User(telegram_id=999999999, full_name="User One", role=UserRole.EMPLOYEE)
    user2 = User(telegram_id=999999999, full_name="User Two", role=UserRole.EMPLOYEE)

    db_session.add(user1)
    await db_session.commit()

    db_session.add(user2)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_username_is_optional(db_session: AsyncSession):
    user = User(telegram_id=111111111, full_name="No Username", role=UserRole.EMPLOYEE)

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.username is None


@pytest.mark.asyncio
async def test_get_user_by_telegram_id(db_session: AsyncSession):
    user = User(telegram_id=222222222, full_name="Findable User", role=UserRole.MANAGER)

    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.telegram_id == 222222222))
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.full_name == "Findable User"
