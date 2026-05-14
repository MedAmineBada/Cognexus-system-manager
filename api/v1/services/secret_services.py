import json
from datetime import datetime, timedelta

from api.v1.utils import generate_secret
from api.v1.utils.password_helpers import generate_secure_alphanumeric
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

    data_secret = {
        "val": generate_secret(),
        "iat": iat.isoformat(),
        "exp": exp.isoformat(),
    }

    data_code = {
        "val": generate_secure_alphanumeric(),
        "iat": iat.isoformat(),
        "exp": exp.isoformat(),
    }

    await redis.hset(
        "secrets",
        "cognexus_secret",
        json.dumps(data_secret),
    )

    await redis.hset(
        "secrets",
        "admin_join_code",
        json.dumps(data_code),
    )

    await redis.publish(
        "system:secret:rotated",
        json.dumps(
            {
                "key": "cognexus_secret",
                "iat": data_secret["iat"],
                "exp": data_secret["exp"],
            }
        ),
    )

    await schedule_secret_rotation(exp)

    raw_secret = await redis.hget("secrets", "cognexus_secret")
    raw_code = await redis.hget("secrets", "admin_join_code")

    res = json.loads(raw_secret)

    return {
        "iat": res["iat"],
        "exp": res["exp"],
        "admin_code": json.loads(raw_code)["val"],
    }
