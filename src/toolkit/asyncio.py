from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable

T = TypeVar("T")


class ConcurrencyLimiter:
    def __init__(self, max_concurrency: int):
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def __call__(self, coro: Awaitable[T]) -> T:
        async with self._semaphore:
            return await coro
