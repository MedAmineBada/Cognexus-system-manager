import json
from datetime import datetime, timedelta

from api.v1.utils import generate_secret
from api.v1.utils.scheduler import schedule_secret_rotation
from config import get_redis


async def rotate_secret():
    redis = get_redis()

    now = datetime.now()

    iat = now.replace(second=0, microsecond=0)

    exp = (iat + timedelta(days=7)).replace(
        hour=23,
        minute=59,
        second=0,
        microsecond=0,
    )

    data = {
        "val": generate_secret(),
        "iat": iat.isoformat(),
        "exp": exp.isoformat(),
    }

    await redis.hset(
        "secrets",
        "cognexus_secret",
        json.dumps(data),
    )

    await redis.publish(
        "system:secret:rotated",
        json.dumps(
            {
                "key": "cognexus_secret",
                "iat": data["iat"],
                "exp": data["exp"],
            }
        ),
    )

    await schedule_secret_rotation(exp)

    raw = await redis.hget("secrets", "cognexus_secret")
    res = json.loads(raw)

    return {
        "iat": res["iat"],
        "exp": res["exp"],
    }
