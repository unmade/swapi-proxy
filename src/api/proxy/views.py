import asyncio
import os
from collections.abc import Awaitable, Mapping
from pathlib import Path
from typing import TypeAlias, TypeVar

import httpx
from fastapi import APIRouter, Request, Response
from httpx import Response as HTTPXResponse

from src.api import exceptions
from src.api.deps import HttpClientDeps
from src.config import config

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


def _resolve_url(path: str, query_params: QueryParams | None = None) -> httpx.URL:
    _, _, service_name, *parts = Path(path).parts
    service = config.get_service(service_name)
    assert service is not None, f"Unknown service: {service_name}"
    path = os.path.join(*parts or [""])
    url = httpx.URL(f"{service.host}/{path}")
    if query_params:
        return url.copy_merge_params(query_params)
    return url


def _make_headers(request: Request) -> Mapping[str, str]:
    headers = request.headers.mutablecopy()
    headers["x-forwarded-host"] = headers["host"]
    del headers["host"]
    if request.client:
        headers["x-forwarded-for"] = request.client.host
    return headers


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


async def proxy(request: Request, http_client: HttpClientDeps):
    """Proxies a request to a given service."""
    url = _resolve_url(request.url.path, query_params=request.query_params)
    headers = _make_headers(request)

    response = await _reraise_httpx_errors(
        http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body(),
            # TODO: timeout
        )
    )

    return Response(
        response.content,
        status_code=response.status_code,
        headers=response.headers,
        media_type=response.headers["Content-Type"],
    )


async def proxy_batch(
    request: Request,
    payload: ProxyBatchRequest,
    http_client: HttpClientDeps,
):
    """Aggregates multiple calls to the proxy API in a single call."""
    _, _, service_name, *_ = Path(request.url.path).parts
    service = config.get_service(service_name)
    assert service is not None, f"Unknown service: {service_name}"
    headers = _make_headers(request)

    tasks = {}
    async with asyncio.TaskGroup() as tg:
        for item in payload.items:
            tasks[item.path] = tg.create_task(
                _return_exceptions(
                    http_client.request(
                        method=str(item.method),
                        url=httpx.URL(f"{service.host}{item.path}"),
                        headers=headers,
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
