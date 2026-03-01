import random
from datetime import datetime, timedelta, timezone

import pytest
from shift_manager_bot.database.models.invite_code import InviteCode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole


@pytest.fixture
async def owner(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4000000000, 4099999999),
        full_name="Test Owner",
        role=UserRole.OWNER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4100000000, 4199999999),
        full_name="Test Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_invite_code(db_session: AsyncSession, owner: User) -> None:
    code = InviteCode(
        code="ABC123",
        role=UserRole.MANAGER,
        created_by=owner.id,
    )
    db_session.add(code)
    await db_session.commit()
    await db_session.refresh(code)

    assert code.id is not None
    assert code.code == "ABC123"
    assert code.role == UserRole.MANAGER
    assert code.created_by == owner.id
    assert code.used_by is None
    assert code.manager_id is None
    assert code.expires_at is None
    assert code.created_at is not None


@pytest.mark.asyncio
async def test_create_employee_invite_code_with_manager(
    db_session: AsyncSession,
    owner: User,
    manager: User,
) -> None:
    code = InviteCode(
        code="EMP456",
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
        manager_id=manager.id,
    )
    db_session.add(code)
    await db_session.commit()
    await db_session.refresh(code)

    assert code.manager_id == manager.id
    assert code.role == UserRole.EMPLOYEE


@pytest.mark.asyncio
async def test_invite_code_is_unique(db_session: AsyncSession, owner: User) -> None:
    code1 = InviteCode(code="UNIQUE1", role=UserRole.EMPLOYEE, created_by=owner.id)
    code2 = InviteCode(code="UNIQUE1", role=UserRole.MANAGER, created_by=owner.id)
    db_session.add(code1)
    await db_session.commit()

    db_session.add(code2)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_invite_code_with_expiry(db_session: AsyncSession, owner: User) -> None:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    code = InviteCode(
        code="EXP789",
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
        expires_at=expires,
    )
    db_session.add(code)
    await db_session.commit()
    await db_session.refresh(code)

    assert code.expires_at is not None


@pytest.mark.asyncio
async def test_invite_code_can_be_marked_as_used(
    db_session: AsyncSession,
    owner: User,
    manager: User,
) -> None:
    code = InviteCode(
        code="USED123",
        role=UserRole.MANAGER,
        created_by=owner.id,
    )
    db_session.add(code)
    await db_session.commit()

    code.used_by = manager.id
    await db_session.commit()
    await db_session.refresh(code)

    assert code.used_by == manager.id


@pytest.mark.asyncio
async def test_get_invite_code_by_code(db_session: AsyncSession, owner: User) -> None:
    code = InviteCode(
        code="FIND123",
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
    )
    db_session.add(code)
    await db_session.commit()

    result = await db_session.execute(
        select(InviteCode).where(InviteCode.code == "FIND123")
    )
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.code == "FIND123"
