import asyncio
import json
from datetime import datetime
from typing import Optional

from config import get_redis

_SECRET_HASH = "secrets"
_SECRET_FIELD = "cognexus_secret"
_JOIN_CODE_FIELD = "admin_join_code"

_rotation_task: Optional[asyncio.Task] = None
_rotation_lock = asyncio.Lock()


async def _sleep_until_and_rotate(exp: datetime):
    try:
        delay = (exp - datetime.now()).total_seconds()

        if delay > 0:
            await asyncio.sleep(delay)

        print("[SCHEDULER] Secret expired, rotating secret now")

        # Import here to avoid circular imports
        from api.v1.services.secret_services import rotate_secret

        await rotate_secret()

    except asyncio.CancelledError:
        print("[SCHEDULER] Existing rotation schedule cancelled")
        return


async def schedule_secret_rotation(exp: datetime):
    global _rotation_task

    async with _rotation_lock:
        current_task = asyncio.current_task()

        if (
            _rotation_task
            and not _rotation_task.done()
            and _rotation_task is not current_task
        ):
            print("[SCHEDULER] Deleting old rotation schedule")

            _rotation_task.cancel()

            try:
                await _rotation_task
            except asyncio.CancelledError:
                pass

        print(f"[SCHEDULER] Creating new rotation schedule for: {exp.isoformat()}")

        _rotation_task = asyncio.create_task(_sleep_until_and_rotate(exp))


async def init_secret_rotation_scheduler():
    redis = get_redis()

    raw = await redis.hget(_SECRET_HASH, _SECRET_FIELD)
    raw_code = await redis.hget(_SECRET_HASH, _JOIN_CODE_FIELD)
    if not raw or not raw_code:
        print(
            "[SCHEDULER] Secret or join code not found in Redis, skipping scheduler init"
        )
        return

    try:
        data = json.loads(raw)
        exp = datetime.fromisoformat(data["exp"])

        print(f"[SCHEDULER] Restoring scheduler from Redis exp: {exp.isoformat()}")

    except Exception as e:
        print(f"[SCHEDULER] Failed to restore scheduler: {e}")
        return

    await schedule_secret_rotation(exp)


async def stop_secret_rotation_scheduler():
    global _rotation_task

    async with _rotation_lock:
        if _rotation_task and not _rotation_task.done():
            print("[SCHEDULER] Stopping scheduler")

            _rotation_task.cancel()

            try:
                await _rotation_task
            except asyncio.CancelledError:
                pass

        _rotation_task = None
