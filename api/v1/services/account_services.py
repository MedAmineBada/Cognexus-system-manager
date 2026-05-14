from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import SuperAdmin
from api.v1.utils import NotFoundException, ForbiddenException, ConflictException


async def activate_account(admin_id: str, acc_id: str, session: AsyncSession):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if not admin.active:
        raise ForbiddenException("Account not activated")

    account = await session.get(SuperAdmin, acc_id)

    if not account:
        raise NotFoundException("Account not found")
    if account.active:
        raise ConflictException("Account already activated")

    account.active = True
    await session.commit()

    return {"success": "account activated"}


async def deactivate_account(admin_id: str, acc_id: str, session: AsyncSession):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if not admin.active:
        raise ForbiddenException("Account not activated")

    account = await session.get(SuperAdmin, acc_id)

    if not account:
        raise NotFoundException("Account not found")
    if not account.active:
        raise ConflictException("Account already deactivated")

    account.active = False
    await session.commit()

    return {"success": "account deactivated"}
