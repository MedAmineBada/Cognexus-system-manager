from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import SuperAdmin, Email, Status
from api.v1.utils import NotFoundException, ForbiddenException, ConflictException
from api.v1.utils.email_utils import push_email


async def activate_account(admin_id: str, acc_id: str, session: AsyncSession):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")

    account = await session.get(SuperAdmin, acc_id)

    if not account:
        raise NotFoundException("Account not found")
    if account.status == Status.active:
        raise ConflictException("Account already activated")

    account.status = Status.active
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
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")

    account = await session.get(SuperAdmin, acc_id)

    if not account:
        raise NotFoundException("Account not found")
    if account.status != Status.active:
        raise ConflictException("Account already deactivated")

    result = await session.execute(
        select(SuperAdmin).where(SuperAdmin.status == Status.active)
    )
    active_users = result.scalars().all()

    if len(active_users) == 1 and active_users[0].id == acc_id:
        raise ConflictException(
            "Cannot deactivate the last active account. At least one active account must exist."
        )

    account.status = Status.inactive
    await session.commit()

    email = Email(
        title="Account Deactivated",
        content=f"Your account has been deactivated by {admin.username}\n({admin.username}'s email: {admin.email}).",
        email=account.email,
    )
    await push_email(email)

    return {"success": "account deactivated"}


async def get_all_users(
    admin_id: str,
    session: AsyncSession,
    user_id: str = None,
):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")

    if user_id:
        user = await session.get(SuperAdmin, user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "status": user.status.value,
            },
        }

    result = await session.execute(select(SuperAdmin))
    users = result.scalars().all()

    status_order = {Status.active: 0, Status.pending: 1, Status.inactive: 2}

    sorted_users = sorted(
        users, key=lambda u: (status_order.get(u.status, 999), u.username.lower())
    )

    return {
        "admin_id": admin_id,
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "status": user.status.value,
            }
            for user in sorted_users
        ],
    }
