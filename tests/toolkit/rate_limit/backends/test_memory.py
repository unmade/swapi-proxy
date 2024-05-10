from __future__ import annotations

import anyio
import pytest

from src.toolkit.rate_limit.backends.memory import InMemoryBackend, InMemoryStorage

pytestmark = [pytest.mark.anyio]


@pytest.fixture
def memory_backend():
    return InMemoryBackend()


class TestInMemoryStorage:
    async def test_get_set(self) -> None:
        # GIVEN
        key = "my_key"
        value = "Hello, World!"
        storage = InMemoryStorage()

        # WHEN: no value has been set
        result = storage.get(key)
        # THEN
        assert result is None

        # WHEN: settings the value and getting it again
        storage.set(key, value)
        result = storage.get(key)
        # THEN
        assert result is not None
        assert result.key == key
        assert result.value == value
        assert result.ttl is None

    async def test_getting_expired_value(self) -> None:
        # GIVEN
        key = "my_key"
        value = "Hello, World!"
        ttl = 0.25
        storage = InMemoryStorage()
        # WHEN: no value has been set
        storage.set(
            key,
            value=value,
            ttl=ttl,  # type: ignore[arg-type]
        )
        result = storage.get(key)
        assert result is not None
        # wait for expiration
        await anyio.sleep(ttl)
        result = storage.get(key)
        assert result is None


class TestIncr:
    async def test(self, memory_backend: InMemoryBackend):
        # WHEN
        result = await memory_backend.incr("test:incr", value=1)
        # THEN
        assert result == 1

        # WHEN
        result = await memory_backend.incr("test:incr", value=5)
        # THEN
        assert result == 6
