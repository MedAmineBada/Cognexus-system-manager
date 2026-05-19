from fastapi import APIRouter, Request, Response
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import (
    LoginRequest,
    FirsRegisterRequest,
    RegisterRequest,
    OTPRequest,
    PasswordChangeRequest,
)
from api.v1.services import (
    sign_in,
    first_user_check,
    create_first_user,
    sign_up,
    refresh_access_token,
    logout_user,
    request_otp,
    change_password,
)
from config import get_db

router = APIRouter(prefix="/auth")


@router.get("/check")
async def first_check(session: AsyncSession = Depends(get_db)):
    return await first_user_check(session)


@router.post("/init")
async def init(r: FirsRegisterRequest, session: AsyncSession = Depends(get_db)):
    return await create_first_user(r, session, True)


@router.post("/login")
async def login(
    r: LoginRequest, response: Response, session: AsyncSession = Depends(get_db)
):
    data = await sign_in(r, session)

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=data["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=False,  # False only for local development
        max_age=60 * 60 * 24,  # 1 day
    )

    return {
        "user_id": data["id"],
        "access_token": data["access_token"],
        "token_type": data["token_type"],
    }


@router.post("/register")
async def register(r: RegisterRequest, session: AsyncSession = Depends(get_db)):
    return await sign_up(r, session)


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
):
    return await refresh_access_token(
        request,
        response,
    )


@router.post("/logout")
async def logout(response: Response):
    return await logout_user(response)


@router.post("/request-otp")
async def otp(r: OTPRequest, session: AsyncSession = Depends(get_db)):
    return await request_otp(r, session)


@router.post("/change-password")
async def change_pw(r: PasswordChangeRequest, session: AsyncSession = Depends(get_db)):
    return await change_password(r, session)
