import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .env_config import env

engine = create_async_engine(
    f"postgresql+asyncpg://{env.POSTGRES_USER}:{env.POSTGRES_PASSWORD}@{env.POSTGRES_HOST}:{env.POSTGRES_PORT}/{env.POSTGRES_DB}",
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"server_settings": {"search_path": "cog_sys_manager"}},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from api.v1.models import User

    _ = User

    max_time = 30
    interval = 2
    elapsed = 0

    while elapsed < max_time:
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS cog_sys_manager"))
                await conn.run_sync(Base.metadata.create_all)
            print("Database initialized")
            return
        except Exception as e:
            print(f"Database connection failed. Retrying in {interval}s...")
            await asyncio.sleep(interval)
            elapsed += interval

    raise RuntimeError("Could not connect to database after 30 seconds")
