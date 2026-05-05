from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import init_db, init_redis, close_redis
from config.broker_config import load_service_config, sync_flags


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    load_service_config()
    await sync_flags()
    yield
    await close_redis()
    print("Application shutdown")


app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10100,
    )
