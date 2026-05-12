from fastapi import APIRouter

from api.v1.routes import flag_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(flag_router)
