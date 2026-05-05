import asyncio
from pathlib import Path
from typing import Dict, Any

import redis.asyncio as redis
import yaml

from .env_config import env

redis_client: redis.Redis | None = None
_service_config: Dict[str, Any] | None = None


async def init_redis() -> None:
    global redis_client

    max_time = 30
    interval = 2
    elapsed = 0

    while elapsed < max_time:
        try:
            redis_client = await redis.from_url(
                env.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await redis_client.ping()
            print("Redis connected")
            return
        except Exception as e:
            print(f"Redis connection failed. Retrying in {interval}s...")
            await asyncio.sleep(interval)
            elapsed += interval

    raise RuntimeError("Could not connect to Redis after 30 seconds")


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        print("Redis connection closed")


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis not initialized")
    return redis_client


def load_service_config() -> Dict[str, Any]:
    global _service_config

    if _service_config is None:
        config_path = Path("config/service_dependencies.yaml")

        if not config_path.exists():
            raise FileNotFoundError(
                f"service_dependencies.yaml not found at {config_path.absolute()}"
            )

        with open(config_path, "r") as f:
            _service_config = yaml.safe_load(f)

        print("Service config loaded")

    return _service_config


def get_service_config() -> Dict[str, Any]:
    if _service_config is None:
        raise RuntimeError("Service config not loaded")
    return _service_config


async def sync_flags() -> None:
    r = get_redis()
    config = get_service_config()  # load config from file

    existing_flags = await r.hgetall("feature_flags")  # load old conf from redis

    expected_flags: Dict[str, str] = {}

    for service_name, service_data in config["services"].items():
        for endpoint_name, endpoint_data in service_data["endpoints"].items():
            # construct flag name, check if enabled or not, and add to dict
            flag_name = f"{service_name}.{endpoint_name}"
            default = "1" if endpoint_data.get("default_enabled", True) else "0"
            expected_flags[flag_name] = default

    new_flags: Dict[str, str] = {}
    # check if flag exists in old flags or is it new, if so add to new flags
    for flag_name, default_value in expected_flags.items():
        if flag_name not in existing_flags:
            new_flags[flag_name] = default_value

    if new_flags:
        await r.hset("feature_flags", mapping=new_flags)
        print(f"Added {len(new_flags)} new flags.")
    else:
        print("All flags up to date, nothing to add")

    deprecated = [f for f in existing_flags if f not in expected_flags]
    if deprecated:
        await r.hdel("feature_flags", *deprecated)
        print(f"Removed {len(deprecated)} deprecated flags.")

    print(f"Flags synced: {len(expected_flags)} total, {len(new_flags)} added")
