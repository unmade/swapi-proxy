from __future__ import annotations

from typing import AsyncIterator
from unittest import mock

import pytest

from src.config import config
from src.toolkit.rate_limit.backends.memory import InMemoryBackend
from src.toolkit.rate_limit.backends.redis import RedisBackend
from src.toolkit.rate_limit.rate_limit import (
    IBackend,
    RateLimiter,
    RateLimitError,
    get_backend,
)

pytestmark = [pytest.mark.anyio]


@pytest.fixture
def backend() -> mock.MagicMock:
    return mock.MagicMock(IBackend)


@pytest.fixture
async def limiter(backend: mock.MagicMock) -> AsyncIterator[RateLimiter]:
    async with RateLimiter(config.limiter) as limiter:
        limiter.backend = backend
        yield limiter


class TestLimit:
    async def test(self, limiter: RateLimiter, backend: mock.MagicMock):
        # GIVEN
        key, limit, period = "test_limit", 10, 5
        backend.incr.return_value = 0
        # WHEN
        await limiter.limit(key=key, limit=limit, limit_period=period)
        # THEN
        backend.incr.assert_awaited_once_with(f"limiter:{key}", value=1, ttl=period)

    async def test_with_cost(self, limiter: RateLimiter, backend: mock.MagicMock):
        # GIVEN
        key, limit, period = "test_limit", 10, 5
        backend.incr.return_value = 0
        # WHEN
        await limiter.limit(key=key, limit=limit, limit_period=period, cost=2)
        # THEN
        backend.incr.assert_awaited_once_with(f"limiter:{key}", value=2, ttl=period)

    async def test_exceeding_the_limit(
        self, limiter: RateLimiter, backend: mock.MagicMock
    ):
        # GIVEN
        key, limit, period = "test_limit", 10, 5
        backend.incr.return_value = limit + 1
        # WHEN
        with pytest.raises(RateLimitError):
            await limiter.limit(key=key, limit=limit, limit_period=period, cost=2)
        # THEN
        backend.incr.assert_awaited_once_with(f"limiter:{key}", value=2, ttl=period)


class TestGetBackend:
    @pytest.mark.parametrize(
        ["dsn", "backend_cls"],
        [
            ("mem://", InMemoryBackend),
            ("redis://localhost:6379", RedisBackend),
        ],
    )
    async def test(self, dsn: str, backend_cls: type[IBackend]):
        # WHEN
        backend = get_backend(dsn)
        # THEN
        assert isinstance(backend, backend_cls)

    async def test_when_invalid_dsn(self):
        # GIVEN
        dsn = "memcache://"
        # WHEN
        with pytest.raises(ValueError) as excinfo:
            get_backend(dsn)
        # THEN
        assert str(excinfo.value) == f"Unsupported backend from DSN: `{dsn}`."
