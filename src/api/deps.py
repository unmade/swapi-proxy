from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import Depends, Request
from httpx import AsyncClient

__all__ = [
    "HttpClientDeps",
]


async def http_client(request: Request):
    return request.state.http_client


HttpClientDeps: TypeAlias = Annotated[AsyncClient, Depends(http_client)]
