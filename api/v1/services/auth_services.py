import uuid

from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import (
    LoginRequest,
    SuperAdmin,
    FirstRegisterRequest,
    RegisterRequest,
    Status,
)
from api.v1.utils import (
    NotFoundException,
    ConflictException,
    UnauthorizedException,
    generate_jwt_token,
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
        status=Status.active if active else Status.pending,
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

    if user.status != Status.active:
        raise UnauthorizedException("Account is not activated")

    access_token = await generate_jwt_token(user.id, "access")
    # 1440 mins = 1 day
    refresh_token = await generate_jwt_token(user.id, "refresh", 1440)

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
        status=Status.pending,
    )

    session.add(user)
    await session.commit()

    return {"success": "user created"}


async def refresh_access_token(
    request: Request,
    response: Response,
):
    # Read refresh token from HttpOnly cookie
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise UnauthorizedException("Missing refresh token")

    # Validate refresh token
    payload = await validate_jwt_token(
        token=refresh_token,
        verify_exp=True,
    )

    user_id = await get_user_id_from_payload(payload)

    token_type = await get_token_type_from_payload(payload)

    # Must be a refresh token
    if token_type != "refresh":
        raise UnauthorizedException("Invalid token type")

    # Generate new access token
    access_token = await generate_jwt_token(
        user_id=user_id,
        token_type="access",
    )

    # Generate new refresh token (rotation)
    new_refresh_token = await generate_jwt_token(
        user_id=user_id,
        token_type="refresh",
        expires_in_minutes=1440,  # 1 day
    )

    # Replace old refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # True in production HTTPS
        max_age=60 * 60 * 24,  # 1 day
    )

    # Return ONLY access token
    return {
        "access_token": access_token,
        "token_type": "Bearer",
    }


async def logout_user(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return {"success": "logged out"}
