import json
import secrets
import string

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from config import get_redis

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)

    except VerifyMismatchError:
        return False


def generate_secure_alphanumeric(length=6):
    # Generates letters (upper/lower) and digits
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


async def get_code():
    redis = get_redis()

    raw_code = await redis.hget("secrets", "admin_join_code")

    return json.loads(raw_code)["val"]
