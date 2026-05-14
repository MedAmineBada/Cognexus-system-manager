import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import (
    LoginRequest,
    SuperAdmin,
    FirstRegisterRequest,
    RegisterRequest,
)
from api.v1.utils import (
    NotFoundException,
    ConflictException,
    UnauthorizedException,
    generate_jwt_token,
    extract_bearer_token,
    validate_jwt_token,
    get_user_id_from_payload,
    get_token_type_from_payload,
)
from api.v1.utils.password_helpers import hash_password, verify_password, get_code


async def first_user_check(session: AsyncSession):
    result = await session.execute(select(SuperAdmin))

    user = result.scalars().first()

    if not user:
        raise NotFoundException("No users in db")

    return {"message": "Users found"}


async def create_user(
    r: FirstRegisterRequest,
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
        active=active,
    )

    session.add(user)
    await session.commit()

    return {"success": "user created"}


async def sign_in(r: LoginRequest, session: AsyncSession):
    result = await session.execute(
        select(SuperAdmin).where(SuperAdmin.email == r.email)
    )

    user = result.scalars().first()

    if not user:
        raise NotFoundException("No account with this email was found")

    if not verify_password(r.password, user.password):
        raise UnauthorizedException("Wrong password")

    if not user.active:
        raise UnauthorizedException("Account is not activated")

    access_token = await generate_jwt_token(user.id, "access")
    # 4320 mins = 3 days
    refresh_token = await generate_jwt_token(user.id, "refresh", 4320)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


async def sign_up(r: RegisterRequest, session: AsyncSession):
    code = await get_code()

    if r.code != code:
        raise UnauthorizedException("Invalid code")

    result = await session.execute(
        select(SuperAdmin).where(SuperAdmin.email == r.email)
    )

    user = result.scalars().first()

    if user:
        raise ConflictException("There's Already at a user with this email")

    user = SuperAdmin(
        id=str(uuid.uuid4()),
        email=r.email,
        password=hash_password(r.password),
        username=r.name,
        active=False,
    )

    session.add(user)
    await session.commit()

    return {"success": "user created"}


async def refresh_access_token(
    authorization: str,
):
    token = extract_bearer_token(authorization)

    payload = await validate_jwt_token(
        token=token,
        verify_exp=False,
    )

    user_id = await get_user_id_from_payload(payload)

    token_type = await get_token_type_from_payload(payload)

    if token_type != "access":
        raise UnauthorizedException("Invalid token type")

    access_token = await generate_jwt_token(
        user_id=user_id,
        token_type="access",
    )

    refresh_token = await generate_jwt_token(
        user_id=user_id,
        token_type="refresh",
        expires_in_minutes=4320,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }
