from __future__ import annotations

import abc
import contextlib
from typing import Protocol, Self, TypeAlias

from src.config import RateLimiterConfig

TTL: TypeAlias = int


class IBackend(Protocol):
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    @abc.abstractmethod
    async def incr(self, key: str, value: int, ttl: TTL | None = None) -> int:
        raise NotImplementedError()  # pragma: no cover


class RateLimitError(Exception):
    pass


class RateLimiter:
    def __init__(self, config: RateLimiterConfig):
        self._config = config
        self.backend = get_backend(str(config.backend_dsn))
        self._stack = contextlib.AsyncExitStack()

    async def __aenter__(self) -> Self:
        await self._stack.enter_async_context(self.backend)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._stack.aclose()

    async def limit(
        self,
        key: str,
        limit: int,
        limit_period: TTL,
        cost: int = 1,
    ) -> None:
        _key = f"limiter:{key}"
        requests_count = await self.backend.incr(_key, value=cost, ttl=limit_period)
        if requests_count and requests_count > limit:
            raise RateLimitError()


def get_backend(dsn: str) -> IBackend:
    if dsn.startswith("mem://"):
        from .backends.memory import InMemoryBackend

        return InMemoryBackend()
    if dsn.startswith("redis"):
        from .backends.redis import RedisBackend

        return RedisBackend(dsn)
    raise ValueError(f"Unsupported backend from DSN: `{dsn}`.")
