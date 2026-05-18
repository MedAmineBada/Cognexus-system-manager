import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import (
    SuperAdmin,
    Email,
    Status,
    FirsRegisterRequest,
    AdminAdd,
    AdminUpdate,
)
from api.v1.utils import NotFoundException, ForbiddenException, ConflictException
from api.v1.utils.email_utils import push_email
from api.v1.utils.password_helpers import hash_password


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


async def create_first_user(
    r: FirsRegisterRequest,
    session: AsyncSession,
    active: bool = False,
):
    result = await session.execute(select(SuperAdmin))

    user = result.scalars().first()

    if user:
        raise ConflictException("There's Already at least one user")

    user = SuperAdmin(
        id=str(uuid.uuid4()),
        email=r.email,
        password=hash_password(r.password),
        username=r.name,
        status=Status.active if active else Status.pending,
    )

    session.add(user)
    await session.commit()

    return {"success": "user created"}


async def add_user(
    r: AdminAdd,
    admin_id: str,
    session: AsyncSession,
):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")

    result = await session.execute(
        select(SuperAdmin).where(SuperAdmin.email == r.email)
    )

    user = result.scalars().first()

    if user:
        raise ConflictException("There's Already a user with this email")

    user = SuperAdmin(
        id=str(uuid.uuid4()),
        email=r.email,
        password=hash_password(r.password),
        username=r.name,
        status=r.status,
    )

    session.add(user)
    await session.commit()

    return {"success": "user created"}


async def update_user(
    user_id: str,
    admin_id: str,
    update_data: AdminUpdate,
    session: AsyncSession,
):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")

    target_user = await session.get(SuperAdmin, user_id)

    if not target_user:
        raise NotFoundException("User not found")

    if update_data.email is not None:
        result = await session.execute(
            select(SuperAdmin).where(
                SuperAdmin.email == update_data.email,
                SuperAdmin.id != user_id,
            )
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise ConflictException("Email already in use by another user")
        target_user.email = update_data.email

    if update_data.name is not None:
        target_user.username = update_data.name

    if update_data.status is not None:
        if update_data.status == Status.active and target_user.status != Status.active:
            pass
        elif update_data.status == Status.inactive:
            result = await session.execute(
                select(SuperAdmin).where(SuperAdmin.status == Status.active)
            )
            active_users = result.scalars().all()
            if len(active_users) == 1 and active_users[0].id == user_id:
                raise ConflictException(
                    "Cannot deactivate the last active account. At least one active account must exist."
                )
        target_user.status = update_data.status

    await session.commit()

    return {
        "success": "user updated",
    }


async def delete_user(
    user_id: str,
    admin_id: str,
    session: AsyncSession,
):
    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")

    target_user = await session.get(SuperAdmin, user_id)

    if not target_user:
        raise NotFoundException("User not found")

    if target_user.status == Status.active:
        result = await session.execute(
            select(SuperAdmin).where(SuperAdmin.status == Status.active)
        )
        active_users = result.scalars().all()
        if len(active_users) == 1 and active_users[0].id == user_id:
            raise ConflictException(
                "Cannot delete the last active account. At least one active account must exist."
            )

    await session.delete(target_user)
    await session.commit()

    return {"success": "user deleted"}
