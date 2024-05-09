from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import FastAPI


class TestClient(AsyncClient):
    def __init__(self, *, app: FastAPI, **kwargs):
        self.app = app
        transport = ASGITransport(app)  # type: ignore[arg-type]
        super().__init__(transport=transport, **kwargs)


@pytest.fixture(scope="session")
async def app() -> FastAPI:
    """Application fixture."""
    return create_app()


@pytest.fixture
async def client(app) -> AsyncIterator[TestClient]:
    """Test client fixture to make requests against app endpoints."""
    async with TestClient(app=app, base_url="http://test") as cli:
        yield cli


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
