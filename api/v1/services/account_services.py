from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import SuperAdmin, Email
from api.v1.utils import NotFoundException, ForbiddenException, ConflictException
from api.v1.utils.email_utils import push_email


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

    email = Email(
        title="Account Activated",
        content=f"Your account has been activated by {admin.username}\n({admin.username}'s email: {admin.email}).",
        email=account.email,
    )
    await push_email(email)

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

    email = Email(
        title="Account Deactivated",
        content=f"Your account has been deactivated by {admin.username}\n({admin.username}'s email: {admin.email}).",
        email=account.email,
    )
    await push_email(email)

    return {"success": "account deactivated"}
