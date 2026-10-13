import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.exceptions import IdempotencyConflictError
from app.core.logging import logger


class IdempotencyManager:
    """
    Distributed Idempotency Engine backed by Redis with atomic locking and response caching.
    Prevents duplicate operations (e.g. double-charging) during client retries or network timeouts.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[aioredis.Redis] = None

    async def get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _lock_key(self, idempotency_key: str) -> str:
        return f"idempotency:lock:{idempotency_key}"

    def _response_key(self, idempotency_key: str) -> str:
        return f"idempotency:response:{idempotency_key}"

    async def acquire_lock(self, idempotency_key: str, lock_ttl_seconds: int = 30) -> bool:
        """
        Attempts to acquire an exclusive lock for this idempotency key.
        Raises IdempotencyConflictError if lock is already held by another in-flight request.
        """
        client = await self.get_redis()
        lock_key = self._lock_key(idempotency_key)

        # SETNX with expiration
        acquired = await client.set(lock_key, "IN_FLIGHT", nx=True, ex=lock_ttl_seconds)
        if not acquired:
            logger.warning(
                f"Idempotent request conflict detected for key '{idempotency_key}'",
                extra={"idempotency_key": idempotency_key},
            )
            raise IdempotencyConflictError(idempotency_key)

        return True

    async def get_cached_response(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        """Retrieves previously cached response if request was already processed."""
        client = await self.get_redis()
        response_key = self._response_key(idempotency_key)
        raw_data = await client.get(response_key)

        if raw_data:
            logger.info(
                f"Serving cached idempotent response for key '{idempotency_key}'",
                extra={"idempotency_key": idempotency_key},
            )
            return json.loads(raw_data)
        return None

    async def save_response(
        self,
        idempotency_key: str,
        status_code: int,
        body: dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> None:
        """Atomically saves processed response and releases the lock."""
        client = await self.get_redis()
        response_key = self._response_key(idempotency_key)
        lock_key = self._lock_key(idempotency_key)

        payload = {
            "status_code": status_code,
            "body": body,
        }

        async with client.pipeline(transaction=True) as pipe:
            pipe.set(response_key, json.dumps(payload), ex=ttl_seconds)
            pipe.delete(lock_key)
            await pipe.execute()

    async def release_lock(self, idempotency_key: str) -> None:
        """Releases the lock on failure so the client can retry."""
        client = await self.get_redis()
        await client.delete(self._lock_key(idempotency_key))

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


idempotency_manager = IdempotencyManager()
