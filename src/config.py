from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel
from pydantic_core import Url
from pydantic_settings import BaseSettings


class CORSConfig(BaseModel):
    allowed_origins: list[str] = []
    allowed_methods: list[str] = ["*"]
    allowed_headers: list[str] = ["*"]


class ServiceConfig(BaseModel):
    name: str
    host: AnyHttpUrl


class AppConfig(BaseSettings):
    app_name: str = "SWAPI Proxy"
    app_version: str = "dev"
    app_debug: bool = False

    cors: CORSConfig = CORSConfig()
    services: list[ServiceConfig] = [
        ServiceConfig(
            name="swapi",
            host=Url("https://swapi.dev/api/"),
        )
    ]


config = AppConfig()
