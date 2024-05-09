import os
from collections.abc import Mapping
from pathlib import Path
from typing import TypeAlias

from fastapi import APIRouter, Request, Response
from httpx import URL

from src.api.deps import HttpClientDeps
from src.config import config

router = APIRouter()

QueryParams: TypeAlias = Mapping[str, str]


def _resolve_url(path: str, query_params: QueryParams | None = None) -> URL:
    _, service_name, *parts = Path(path).parts
    service = config.get_service(service_name)
    assert service is not None, f"Unknown service: {service_name}"
    path = os.path.join(*parts or [""])
    url = URL(f"{service.host}/{path}")
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


async def proxy(request: Request, http_client: HttpClientDeps):
    """Proxies a request to a given service."""
    url = _resolve_url(request.url.path, query_params=request.query_params)

    response = await http_client.request(
        method=request.method,
        url=url,
        headers=_make_headers(request),
        content=await request.body(),
    )
    return Response(
        response.content,
        status_code=response.status_code,
        headers=response.headers,
        media_type=response.headers["Content-Type"],
    )
