from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import Depends, Request
from httpx import AsyncClient

from src.toolkit.rate_limit.rate_limit import RateLimiter

__all__ = [
    "HttpClientDeps",
]


async def http_client(request: Request):
    return request.state.http_client


async def rate_limiter(request: Request):
    return request.state.limiter


HttpClientDeps: TypeAlias = Annotated[AsyncClient, Depends(http_client)]
LimiterDeps: TypeAlias = Annotated[RateLimiter, Depends(rate_limiter)]
