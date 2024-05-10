from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from . import views

if TYPE_CHECKING:
    from fastapi import FastAPI

    from src.config import ServiceConfig

_METHODS = ["DELETE", "HEAD", "GET", "OPTIONS", "POST", "PATCH", "PUT", "TRACE"]


def setup(app: FastAPI, services: list[ServiceConfig]) -> None:
    for service in services:
        service_router = APIRouter(tags=[service.name])
        service_router.add_api_route(
            f"/proxy/{service.name}/{{path:path}}",
            views.proxy,
            methods=_METHODS,
        )
        service_router.add_api_route(
            f"/proxy_batch/{service.name}",
            views.proxy_batch,
            methods=["POST"],
        )
    app.include_router(service_router)
