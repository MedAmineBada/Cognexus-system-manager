import json
import secrets
from datetime import datetime, timezone, timedelta

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from api.v1.utils import AppException, UnauthorizedException
from config import get_redis


def generate_secret() -> str:
    secret = secrets.token_urlsafe(64)
    return secret


async def generate_jwt_token(
    user_id: str,
    token_type: str,
    expires_in_minutes: int = 60,
) -> str:
    if not token_type in ["access", "refresh"]:
        raise AppException
    now = datetime.now(timezone.utc)

    payload = {
        "user_id": user_id,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
    }

    redis = get_redis()

    secret = await redis.hget("secrets", "cognexus_secret")

    secret_val = json.loads(secret)

    secret_key = secret_val["val"]

    if not secret_key:
        raise AppException("Could not create token")

    token = jwt.encode(payload, secret_key, algorithm="HS256")

    return token


async def get_secret():
    redis = get_redis()

    raw_code = await redis.hget("secrets", "cognexus_secret")

    return json.loads(raw_code)["val"]


def extract_bearer_token(
    authorization: str,
) -> str:
    return authorization.replace("Bearer ", "").strip()


async def decode_jwt_token(
    token: str,
    verify_exp: bool = True,
) -> dict:
    return jwt.decode(
        token,
        await get_secret(),
        algorithms="HS256",
        options={"verify_exp": verify_exp},
    )


async def validate_jwt_token(
    token: str,
    verify_exp: bool = True,
) -> dict:
    try:
        payload = await decode_jwt_token(
            token=token,
            verify_exp=verify_exp,
        )

        return payload

    except ExpiredSignatureError:
        raise UnauthorizedException("Token expired")

    except InvalidTokenError:
        raise UnauthorizedException("Invalid token")


async def get_user_id_from_payload(
    payload: dict,
) -> str:
    user_id = payload.get("user_id")

    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    return user_id


async def get_token_type_from_payload(
    payload: dict,
) -> str:
    token_type = payload.get("type")

    if not token_type:
        raise UnauthorizedException("Missing token type")

    return token_type
