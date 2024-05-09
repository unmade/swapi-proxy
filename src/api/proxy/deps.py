import os
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, Request

from src.config import ServiceConfig, config

__all__ = [
    "ServiceConfigDeps",
]


def get_headers(request: Request) -> Mapping[str, str]:
    headers = request.headers.mutablecopy()
    headers["x-forwarded-host"] = headers["host"]
    del headers["host"]
    if request.client:
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


HeadersDeps = Annotated[Mapping[str, str], Depends(get_headers)]
ServiceConfigDeps = Annotated[ServiceConfig, Depends(get_service_config)]
ProxyPathDeps = Annotated[str, Depends(get_proxy_path)]
