import pytest
import fakeredis.aioredis
from app.core.exceptions import IdempotencyConflictError
from app.core.idempotency import IdempotencyManager


@pytest.mark.asyncio
async def test_idempotency_lock_and_conflict():
    """Verifies that duplicate concurrent requests trigger IdempotencyConflictError."""
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    mgr = IdempotencyManager()
    mgr._redis = fake_client

    key = "idem_key_12345"

    # 1. First lock acquisition succeeds
    acquired = await mgr.acquire_lock(key, lock_ttl_seconds=30)
    assert acquired is True

    # 2. Concurrent duplicate request while in flight raises conflict error
    with pytest.raises(IdempotencyConflictError):
        await mgr.acquire_lock(key, lock_ttl_seconds=30)

    # 3. Release lock allows re-acquisition
    await mgr.release_lock(key)
    reacquired = await mgr.acquire_lock(key, lock_ttl_seconds=30)
    assert reacquired is True

    await mgr.close()


@pytest.mark.asyncio
async def test_idempotency_response_caching():
    """Verifies that completed responses are cached and returned on retries."""
    fake_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    mgr = IdempotencyManager()
    mgr._redis = fake_client

    key = "idem_key_order_999"

    # Acquire lock
    await mgr.acquire_lock(key)

    # Save response
    body_data = {"transaction_id": "tx_abc", "status": "PROCESSING", "amount": 250000}
    await mgr.save_response(key, status_code=200, body=body_data, ttl_seconds=3600)

    # Lock should now be released
    cached = await mgr.get_cached_response(key)
    assert cached is not None
    assert cached["status_code"] == 200
    assert cached["body"]["transaction_id"] == "tx_abc"
    assert cached["body"]["amount"] == 250000

    await mgr.close()
