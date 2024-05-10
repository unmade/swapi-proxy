from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.toolkit.rate_limit.rate_limit import TTL, IBackend


@dataclass
class Value:
    key: str
    value: Any
    ttl: float | None
    timestamp: float = field(default_factory=time.monotonic)


class InMemoryStorage:
    def __init__(self):
        self._data: dict[str, Value] = {}

    def get(self, key: str) -> Value | None:
        value = self._data.get(key)
        if not value:
            return None

        if value.ttl and time.monotonic() - value.timestamp > value.ttl:
            del self._data[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: TTL | None = None) -> None:
        self._data[key] = Value(
            key=key,
            value=value,
            ttl=float(ttl) if ttl is not None else None,
        )


class InMemoryBackend(IBackend):
    def __init__(self) -> None:
        self._storage = InMemoryStorage()

    async def incr(self, key: str, value: int = 1, ttl: TTL | None = None) -> int:
        _key = f"limiter:{key}"
        result = self._storage.get(_key)
        incr_by: int = result.value + value if result else value
        self._storage.set(_key, incr_by, ttl)
        return incr_by
