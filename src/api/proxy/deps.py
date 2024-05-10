from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, Request

from src.config import ServiceConfig, config
from src.toolkit.asyncio import ConcurrencyLimiter

__all__ = [
    "ConcurrencyLimiterDeps",
    "HeadersDeps",
    "RateLimiterKeyDeps",
    "ProxyPathDeps",
    "ServiceConfigDeps",
]

_concurrency_limiters: dict[str, ConcurrencyLimiter] = {}


async def get_concurrency_limiter(service: ServiceConfigDeps) -> ConcurrencyLimiter:
    if limiter := _concurrency_limiters.get(service.name):
        return limiter

    limiter = ConcurrencyLimiter(service.max_concurrent_requests)
    _concurrency_limiters[service.name] = limiter
    return limiter


def get_headers(request: Request) -> Mapping[str, str]:
    headers = request.headers.mutablecopy()
    headers["x-forwarded-host"] = headers["host"]
    assert request.client is not None
    headers["x-forwarded-for"] = request.client.host
    return headers


async def get_service_name_and_path(request: Request) -> tuple[str, str]:
    _, _, service_name, *parts = Path(request.url.path).parts
    path = os.path.join(*parts or [""])
    fullpath = httpx.URL(path).copy_merge_params(request.query_params)
    return service_name, str(fullpath)


async def get_service_config(
    service_name_and_path: tuple[str, str] = Depends(get_service_name_and_path),
) -> ServiceConfig:
    service_name, _ = service_name_and_path
    service = config.get_service(service_name)
    assert service is not None, f"Unknown service: {service_name}"
    return service


async def get_proxy_path(
    service_name_and_path: tuple[str, str] = Depends(get_service_name_and_path),
) -> str:
    _, path = service_name_and_path
    return path


async def get_limiter_key(request: Request, service: ServiceConfigDeps) -> str:
    assert request.client is not None, "Can't limit without client IP-address."
    return f"{service.name}:{request.client.host}"


ConcurrencyLimiterDeps = Annotated[ConcurrencyLimiter, Depends(get_concurrency_limiter)]
HeadersDeps = Annotated[Mapping[str, str], Depends(get_headers)]
RateLimiterKeyDeps = Annotated[str, Depends(get_limiter_key)]
ProxyPathDeps = Annotated[str, Depends(get_proxy_path)]
ServiceConfigDeps = Annotated[ServiceConfig, Depends(get_service_config)]
