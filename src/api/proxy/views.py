import asyncio
from collections.abc import Awaitable, Mapping
from typing import TypeAlias, TypeVar

import httpx
from fastapi import APIRouter, Request, Response
from httpx import Response as HTTPXResponse

from src.api import exceptions
from src.api.deps import HttpClientDeps, RateLimiterDeps

from .deps import (
    ConcurrencyLimiterDeps,
    HeadersDeps,
    ProxyPathDeps,
    RateLimiterKeyDeps,
    ServiceConfigDeps,
)
from .schemas import (
    ProxyBatchRequest,
    ProxyBatchResponse,
    ProxyBatchResponseItem,
    ProxyBatchResponseItemError,
    ProxyBatchResponseItemResult,
)

router = APIRouter()

T = TypeVar("T")

QueryParams: TypeAlias = Mapping[str, str]


async def _reraise_httpx_errors(coro: Awaitable[T]) -> T:
    try:
        return await coro
    except httpx.TimeoutException as exc:
        raise exceptions.GatewayTimeout() from exc
    except httpx.NetworkError as exc:
        raise exceptions.BadGateway() from exc
    except httpx.HTTPError as exc:
        raise exceptions.APIError() from exc


async def _return_exceptions(coro: Awaitable[T]) -> T | exceptions.APIError:
    try:
        return await _reraise_httpx_errors(coro)
    except exceptions.APIError as exc:
        return exc


def _make_proxy_url(base_url: str, path: str) -> str:
    if not base_url.endswith("/") and not path.startswith("/"):
        return f"{base_url}/{path}"
    return f"{base_url}{path}"


async def proxy(
    request: Request,
    http_client: HttpClientDeps,
    limiter: RateLimiterDeps,
    limiter_key: RateLimiterKeyDeps,
    service: ServiceConfigDeps,
    headers: HeadersDeps,
    proxy_path: ProxyPathDeps,
):
    """Proxies a request to a given service."""
    url = _make_proxy_url(str(service.host), proxy_path)
    await limiter.limit(
        key=limiter_key,
        limit=service.rate_limit,
        limit_period=service.rate_limit_period,
    )

    response = await _reraise_httpx_errors(
        http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body(),
            timeout=service.timeout,
            follow_redirects=True,
        )
    )

    return Response(
        response.content,
        status_code=response.status_code,
        headers=response.headers,
        media_type=response.headers["Content-Type"],
    )


async def proxy_batch(
    payload: ProxyBatchRequest,
    http_client: HttpClientDeps,
    concurrency_limiter: ConcurrencyLimiterDeps,
    limiter: RateLimiterDeps,
    limiter_key: RateLimiterKeyDeps,
    service: ServiceConfigDeps,
    headers: HeadersDeps,
):
    """Aggregates multiple calls to the proxy API in a single call."""
    await limiter.limit(
        key=limiter_key,
        limit=service.rate_limit,
        limit_period=service.rate_limit_period,
        cost=len(payload.items),
    )

    tasks = {}
    async with asyncio.TaskGroup() as tg:
        for item in payload.items:
            tasks[item.path] = tg.create_task(
                concurrency_limiter(
                    _return_exceptions(
                        http_client.request(
                            method=str(item.method),
                            url=_make_proxy_url(str(service.host), item.path),
                            headers=headers,
                            timeout=service.timeout,
                        )
                    )
                )
            )

    items = []
    for path, task in tasks.items():
        response_or_exc: HTTPXResponse | exceptions.APIError = task.result()

        if isinstance(response_or_exc, HTTPXResponse):
            items.append(
                ProxyBatchResponseItem(
                    path=path,
                    result=ProxyBatchResponseItemResult(
                        status_code=response_or_exc.status_code,
                        content=response_or_exc.json(),
                    ),
                )
            )
        else:
            items.append(
                ProxyBatchResponseItem(
                    path=path,
                    error=ProxyBatchResponseItemError.model_validate(
                        response_or_exc.as_dict()
                    ),
                )
            )

    return ProxyBatchResponse(items=items)
