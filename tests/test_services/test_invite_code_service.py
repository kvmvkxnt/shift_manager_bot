import random
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.invite_code import InviteCode
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.invite_code_service import InviteCodeService


@pytest.fixture
async def owner(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4200000000, 4299999999),
        full_name="Service Owner",
        role=UserRole.OWNER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4300000000, 4399999999),
        full_name="Service Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4400000000, 4499999999),
        full_name="Service Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def service() -> InviteCodeService:
    return InviteCodeService()


@pytest.mark.asyncio
async def test_generate_code(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
) -> None:
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.MANAGER,
        created_by=owner.id,
    )

    assert code.id is not None
    assert len(code.code) > 0
    assert code.role == UserRole.MANAGER
    assert code.created_by == owner.id
    assert code.used_by is None
    assert code.expires_at is None


@pytest.mark.asyncio
async def test_generate_code_with_expiry(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
) -> None:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
        expires_at=expires,
    )

    assert code.expires_at is not None


@pytest.mark.asyncio
async def test_generate_employee_code_with_manager(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
    manager: User,
) -> None:
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
        manager_id=manager.id,
    )

    assert code.manager_id == manager.id


@pytest.mark.asyncio
async def test_get_by_code(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
) -> None:
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.MANAGER,
        created_by=owner.id,
    )

    found: InviteCode | None = await service.get_by_code(db_session, code.code)

    assert found is not None
    assert found.id == code.id


@pytest.mark.asyncio
async def test_get_by_code_not_found(
    db_session: AsyncSession,
    service: InviteCodeService,
) -> None:
    found: InviteCode | None = await service.get_by_code(db_session, "NOTEXIST")

    assert found is None


@pytest.mark.asyncio
async def test_validate_valid_code(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
) -> None:
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.MANAGER,
        created_by=owner.id,
    )

    is_valid, error = await service.validate(db_session, code.code)

    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_nonexistent_code(
    db_session: AsyncSession,
    service: InviteCodeService,
) -> None:
    is_valid, error = await service.validate(db_session, "BADCODE")

    assert is_valid is False
    assert error is not None


@pytest.mark.asyncio
async def test_validate_already_used_code(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
    employee: User,
) -> None:
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
    )
    code.used_by = employee.id
    await db_session.commit()

    is_valid, error = await service.validate(db_session, code.code)

    assert is_valid is False
    assert error is not None


@pytest.mark.asyncio
async def test_validate_expired_code(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
) -> None:
    expired = datetime.now(timezone.utc) - timedelta(days=1)
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
        expires_at=expired,
    )

    is_valid, error = await service.validate(db_session, code.code)

    assert is_valid is False
    assert error is not None


@pytest.mark.asyncio
async def test_redeem_code(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
    employee: User,
) -> None:
    code: InviteCode = await service.generate(
        db_session,
        role=UserRole.MANAGER,
        created_by=owner.id,
    )

    redeemed: InviteCode = await service.redeem(db_session, code, employee.id)

    assert redeemed.used_by == employee.id


@pytest.mark.asyncio
async def test_codes_are_unique(
    db_session: AsyncSession,
    service: InviteCodeService,
    owner: User,
) -> None:
    code1: InviteCode = await service.generate(
        db_session,
        role=UserRole.MANAGER,
        created_by=owner.id,
    )
    code2: InviteCode = await service.generate(
        db_session,
        role=UserRole.MANAGER,
        created_by=owner.id,
    )

    assert code1.code != code2.code
