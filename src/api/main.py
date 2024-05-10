from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, TypedDict

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exceptions import (
    APIError,
    api_error_exception_handler,
    rate_limit_error_handler,
)
from src.config import config
from src.toolkit.rate_limit import RateLimiter, RateLimitError

from . import proxy, router

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from httpx import AsyncClient


class State(TypedDict):
    http_client: AsyncClient
    limiter: RateLimiter


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    async with (
        httpx.AsyncClient() as http_client,
        RateLimiter(config.limiter) as limiter,
    ):
        yield {
            "http_client": http_client,
            "limiter": limiter,
        }


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        debug=config.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allowed_origins,
        allow_methods=config.cors.allowed_methods,
        allow_headers=config.cors.allowed_headers,
    )

    app.add_exception_handler(APIError, api_error_exception_handler)
    app.add_exception_handler(RateLimitError, rate_limit_error_handler)

    app.include_router(router)
    proxy.setup(app, config.services)

    return app


app = create_app()
