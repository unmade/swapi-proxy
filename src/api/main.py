from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import config

from . import proxy, router


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        debug=config.app_debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allowed_origins,
        allow_methods=config.cors.allowed_methods,
        allow_headers=config.cors.allowed_headers,
    )

    app.include_router(router)
    proxy.setup(app, config.services)

    return app


app = create_app()
