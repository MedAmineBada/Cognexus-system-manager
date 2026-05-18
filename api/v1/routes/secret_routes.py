from fastapi import APIRouter, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import SuperAdmin, Status
from api.v1.services import rotate_secrets, get_secrets
from api.v1.utils import (
    verify_access_token,
    get_user_id_from_payload,
    NotFoundException,
    ForbiddenException,
)
from config import get_db

router = APIRouter(prefix="/secrets")


@router.post("/rotate")
async def rotate(
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

    return await rotate_secrets()


@router.get("")
async def get(
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

    return await get_secrets()
