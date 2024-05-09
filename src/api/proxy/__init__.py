from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from . import views

if TYPE_CHECKING:
    from fastapi import FastAPI

    from src.config import ServiceConfig


def setup(app: FastAPI, services: list[ServiceConfig]) -> None:
    for service in services:
        service_router = APIRouter(tags=[service.name])
        service_router.add_api_route("/{path:path}", views.proxy)
        app.include_router(service_router, prefix=f"/{service.name}")
