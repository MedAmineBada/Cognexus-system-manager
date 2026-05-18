from fastapi import APIRouter
from fastapi.params import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import SuperAdmin, Status
from api.v1.services import get_flags, toggle_flag, toggle_service
from api.v1.utils import (
    verify_access_token,
    get_user_id_from_payload,
    NotFoundException,
    ForbiddenException,
)
from config import get_db

router = APIRouter(prefix="/flags")


@router.get("")
async def get(
    authorization: str = Header(...), session: AsyncSession = Depends(get_db)
):
    payload = await verify_access_token(authorization)
    admin_id = await get_user_id_from_payload(payload)

    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")
    return await get_flags()


@router.post("/{flag_name}/toggle")
async def toggle(
    flag_name: str,
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_db),
):
    payload = await verify_access_token(authorization)
    admin_id = await get_user_id_from_payload(payload)

    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")
    return await toggle_flag(flag_name)


@router.post("/service/{service_name}/toggle")
async def toggle_service_endpoint(
    service_name: str,
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_db),
):
    payload = await verify_access_token(authorization)
    admin_id = await get_user_id_from_payload(payload)

    admin = await session.get(SuperAdmin, admin_id)

    if not admin:
        raise NotFoundException("Admin not found")
    if admin.status != Status.active:
        raise ForbiddenException("Account not activated")
    return await toggle_service(service_name)
