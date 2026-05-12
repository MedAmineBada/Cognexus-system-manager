from fastapi import APIRouter

from api.v1.services import get_flags, toggle_flag, toggle_service

router = APIRouter(prefix="/flags")


@router.get("")
async def get():
    return await get_flags()


@router.post("/{flag_name}/toggle")
async def toggle(flag_name: str):
    return await toggle_flag(flag_name)


@router.post("/service/{service_name}/toggle")
async def toggle_service_endpoint(service_name: str):
    """Toggle entire service - disable all if any enabled, enable all if all disabled"""
    return await toggle_service(service_name)
