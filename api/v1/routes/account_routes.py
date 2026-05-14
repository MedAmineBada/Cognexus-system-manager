from fastapi import APIRouter, Header
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.services import activate_account, deactivate_account
from api.v1.utils import verify_access_token, get_user_id_from_payload
from config import get_db

router = APIRouter(prefix="/accounts")


@router.post("/activate/{acc_id}")
async def activate(
    acc_id: str,
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_db),
):
    payload = await verify_access_token(authorization)
    admin_id = await get_user_id_from_payload(payload)

    return await activate_account(
        admin_id,
        acc_id,
        session,
    )


@router.post("/deactivate/{acc_id}")
async def activate(
    acc_id: str,
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_db),
):
    payload = await verify_access_token(authorization)
    admin_id = await get_user_id_from_payload(payload)

    return await deactivate_account(
        admin_id,
        acc_id,
        session,
    )
