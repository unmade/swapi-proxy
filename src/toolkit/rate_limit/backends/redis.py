from __future__ import annotations

import contextlib
from typing import Self

import redis.asyncio as redis

from ..rate_limit import TTL, IBackend


class RedisBackend(IBackend):
    def __init__(self, dsn: str) -> None:
        pool = redis.ConnectionPool.from_url(dsn)
        self._client = redis.Redis.from_pool(pool)
        self._stack = contextlib.AsyncExitStack()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.aclose()

    async def incr(self, key: str, value: int, ttl: TTL | None = None) -> int:
        result: int = await self._client.incr(key, amount=value)
        if ttl:
            await self._client.expire(key, ttl)
        return result
