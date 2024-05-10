from __future__ import annotations

import pytest

from src.toolkit.rate_limit.backends.redis import RedisBackend
from src.toolkit.rate_limit.rate_limit import TTL

pytestmark = [pytest.mark.anyio, pytest.mark.redis]


@pytest.fixture
def redis_dsn() -> str:
    return "redis://localhost:6379/10"


@pytest.fixture
async def redis_backend(redis_dsn: str):
    async with RedisBackend(redis_dsn) as backend:
        yield backend
        await backend._client.flushdb()


class TestIncr:
    @pytest.mark.parametrize("ttl", [None, 1])
    async def test(self, redis_backend: RedisBackend, ttl: TTL | None):
        # WHEN
        result = await redis_backend.incr("test:incr", value=1, ttl=ttl)
        # THEN
        assert result == 1
