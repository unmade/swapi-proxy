from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import FastAPI


class TestClient(AsyncClient):
    def __init__(self, *, app: FastAPI, **kwargs):
        transport = ASGITransport(app)  # type: ignore[arg-type]
        super().__init__(transport=transport, **kwargs)


@pytest.fixture(scope="session")
async def app():
    """Application fixture."""
    app = create_app()
    async with LifespanManager(app) as manager:
        yield manager.app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[TestClient]:
    """Test client fixture to make requests against app endpoints."""
    async with TestClient(app=app, base_url="http://test") as cli:
        yield cli
