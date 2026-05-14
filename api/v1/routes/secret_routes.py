from fastapi import APIRouter

from api.v1.services import rotate_secret

router = APIRouter(prefix="/secret")


@router.get("/rotate")
async def rotate():
    return await rotate_secret()
