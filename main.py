from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from api.v1.services import rotate_secrets
from api.v1.utils import (
    AppException,
    app_exception_manager,
    default_exception_manager,
    init_secret_rotation_scheduler,
    stop_secret_rotation_scheduler,
    sqlalchemy_exception_manager,
    sqlalchemy_integrity_exception_manager,
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
    existing_code = await redis.hget("secrets", "admin_join_code")

    if existing_secret and existing_code:
        print("[STARTUP] Existing secret and join code found in Redis")

    elif not existing_secret and not existing_code:
        print("[STARTUP] Secret and Code not found, generating initial secret")
        await rotate_secrets()

    elif not existing_secret:
        print("[STARTUP] No secret found, generating initial secret")
        await rotate_secrets()

    else:
        print("[STARTUP] No code found, generating initial secret")
        await rotate_secrets()

    await init_secret_rotation_scheduler()

    yield

    await stop_secret_rotation_scheduler()
    await close_redis()
    print("Application shutdown")


app = FastAPI(lifespan=lifespan)

app.include_router(v1_router)

app.add_exception_handler(AppException, app_exception_manager)
app.add_exception_handler(
    SQLAlchemyError,
    sqlalchemy_exception_manager,
)

app.add_exception_handler(
    IntegrityError,
    sqlalchemy_integrity_exception_manager,
)
app.add_exception_handler(Exception, default_exception_manager)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10100,
    )
