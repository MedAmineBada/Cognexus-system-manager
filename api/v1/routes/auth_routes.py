from fastapi import APIRouter, Header
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import LoginRequest, FirstRegisterRequest, RegisterRequest
from api.v1.services import (
    sign_in,
    first_user_check,
    create_user,
    sign_up,
    refresh_access_token,
)
from config import get_db

router = APIRouter(prefix="/auth")


@router.get("/check")
async def first_check(session: AsyncSession = Depends(get_db)):
    return await first_user_check(session)


@router.post("/init")
async def init(r: FirstRegisterRequest, session: AsyncSession = Depends(get_db)):
    return await create_user(r, session, True)


@router.post("/login")
async def login(r: LoginRequest, session: AsyncSession = Depends(get_db)):
    return await sign_in(r, session)


@router.post("/register")
async def register(r: RegisterRequest, session: AsyncSession = Depends(get_db)):
    return await sign_up(r, session)


@router.post("/refresh")
async def refresh(authorization: str = Header(...)):
    return await refresh_access_token(authorization)
