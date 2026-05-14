from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.v1.services import rotate_secret
from api.v1.utils import (
    AppException,
    app_exception_manager,
    default_exception_manager,
    init_secret_rotation_scheduler,
    stop_secret_rotation_scheduler,
)
from api.v1.v1_router import v1_router
from config import init_db, init_redis, close_redis
from config.broker_config import load_service_config, sync_flags, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    load_service_config()
    await sync_flags()

    redis = get_redis()
    existing_secret = await redis.hget("secrets", "cognexus_secret")

    if existing_secret:
        print("[SECRET] Existing secret found in Redis")
    else:
        print("[SECRET] No secret found, generating initial secret")
        await rotate_secret()

    await init_secret_rotation_scheduler()

    yield

    await stop_secret_rotation_scheduler()
    await close_redis()
    print("Application shutdown")


app = FastAPI(lifespan=lifespan)

app.include_router(v1_router)

app.add_exception_handler(AppException, app_exception_manager)
app.add_exception_handler(Exception, default_exception_manager)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10100,
    )
