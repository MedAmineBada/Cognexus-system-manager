from typing import Dict, Any

from api.v1.utils.exceptions import FlagNotFoundException, ServiceNotFoundException
from api.v1.utils.flag_utils import publish_flag_changes, find_dependent_flags
from config import get_redis, get_service_config


async def get_flags() -> Dict[str, Any]:
    """Get all flags with their current status, grouped by service"""
    redis = get_redis()
    config = get_service_config()

    current_flags = await redis.hgetall("feature_flags")

    services = {}

    for service_name, service_data in config["services"].items():
        services[service_name] = {
            "description": service_data.get("description", ""),
            "endpoints": {},
        }

        for endpoint_name, endpoint_data in service_data["endpoints"].items():
            flag_name = f"{service_name}.{endpoint_name}"

            services[service_name]["endpoints"][endpoint_name] = {
                "flag_name": flag_name,
                "description": endpoint_data.get("description", ""),
                "enabled": current_flags.get(flag_name, "1") == "1",
                "depends_on": endpoint_data.get("depends_on", []),
            }

    return {
        "services": services,
        "total_flags": len(current_flags),
        "enabled_count": sum(1 for v in current_flags.values() if v == "1"),
        "disabled_count": sum(1 for v in current_flags.values() if v == "0"),
    }


async def toggle_flag(flag_name: str) -> Dict[str, Any]:
    """Toggle a flag and handle cascading disable logic"""
    redis = get_redis()
    config = get_service_config()

    # Check if flag exists
    current_value = await redis.hget("feature_flags", flag_name)
    if current_value is None:
        raise FlagNotFoundException(f"Flag '{flag_name}' does not exist")

    # Calculate new value
    new_value = "0" if current_value == "1" else "1"
    is_disabling = new_value == "0"

    # Update the primary flag
    await redis.hset("feature_flags", flag_name, new_value)

    changes = [{"flag": flag_name, "enabled": new_value == "1", "reason": "manual"}]

    # Handle cascading disable only (not re-enable)
    if is_disabling:
        dependent_flags = find_dependent_flags(flag_name, config)
        for dependent_flag in dependent_flags:
            # Check if dependent is currently enabled
            dep_current = await redis.hget("feature_flags", dependent_flag)
            if dep_current == "1":
                await redis.hset("feature_flags", dependent_flag, "0")
                changes.append(
                    {
                        "flag": dependent_flag,
                        "enabled": False,
                        "reason": f"auto-disabled due to {flag_name}",
                    }
                )

    # Publish changes to Redis Pub/Sub
    await publish_flag_changes(changes)

    return {
        "primary_flag": flag_name,
        "new_value": new_value == "1",
        "changes": changes,
        "total_changes": len(changes),
    }


async def toggle_service(service_name: str) -> Dict[str, Any]:
    """Toggle entire service - if all endpoints enabled, disable all. If any disabled, enable all."""
    redis = get_redis()
    config = get_service_config()

    if service_name not in config["services"]:
        raise ServiceNotFoundException(f"Service '{service_name}' does not exist")

    service_data = config["services"][service_name]

    enabled_count = 0
    total_endpoints = 0

    for endpoint_name in service_data["endpoints"]:
        flag_name = f"{service_name}.{endpoint_name}"
        current_value = await redis.hget("feature_flags", flag_name)
        total_endpoints += 1
        if current_value == "1":
            enabled_count += 1

    # If ALL are enabled → disable all. If ANY are disabled → enable all.
    should_disable = enabled_count == total_endpoints
    action = "disabled" if should_disable else "enabled"
    target_value = "0" if should_disable else "1"

    changes = []

    for endpoint_name in service_data["endpoints"]:
        flag_name = f"{service_name}.{endpoint_name}"
        await redis.hset("feature_flags", flag_name, target_value)
        changes.append(
            {
                "flag": flag_name,
                "enabled": target_value == "1",
                "reason": f"service-level toggle of {service_name}",
            }
        )

        if should_disable:
            dependent_flags = find_dependent_flags(flag_name, config)
            for dependent_flag in dependent_flags:
                dep_current = await redis.hget("feature_flags", dependent_flag)
                if dep_current == "1":
                    await redis.hset("feature_flags", dependent_flag, "0")
                    changes.append(
                        {
                            "flag": dependent_flag,
                            "enabled": False,
                            "reason": f"auto-disabled due to {flag_name}",
                        }
                    )

    await publish_flag_changes(changes)

    return {
        "service": service_name,
        "action": action,
        "changes": changes,
        "total_changes": len(changes),
    }
