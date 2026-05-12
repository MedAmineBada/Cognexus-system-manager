import json
import time
from typing import Dict, List, Any

from config import get_redis
from api.v1.utils.exceptions import BadGatewayException


def find_dependent_flags(disabled_flag: str, config: Dict[str, Any]) -> List[str]:
    """Find all flags that depend on the given disabled flag"""
    dependents = []

    for service_name, service_data in config["services"].items():
        for endpoint_name, endpoint_data in service_data["endpoints"].items():
            flag_name = f"{service_name}.{endpoint_name}"
            depends_on = endpoint_data.get("depends_on", [])

            if disabled_flag in depends_on:
                dependents.append(flag_name)

    return dependents


async def publish_flag_changes(changes: List[Dict[str, Any]]) -> None:
    """Publish flag changes to Redis Pub/Sub channel"""
    redis = get_redis()

    for change in changes:
        message = {
            "flag": change["flag"],
            "enabled": change["enabled"],
            "reason": change["reason"],
            "timestamp": int(time.time()),
        }
        try:
            await redis.publish("system:flags:changed", json.dumps(message))
        except Exception as e:
            # Catching a broad exception here because redis.publish can raise various connection errors
            raise BadGatewayException(f"Failed to publish flag changes to Redis: {e}")
