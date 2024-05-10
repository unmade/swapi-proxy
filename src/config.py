from __future__ import annotations

from pydantic import AnyHttpUrl, AnyUrl, BaseModel
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict


class CORSConfig(BaseModel):
    allowed_origins: list[str] = []
    allowed_methods: list[str] = ["*"]
    allowed_headers: list[str] = ["*"]


class RateLimiterConfig(BaseModel):
    backend_dsn: AnyUrl = AnyUrl("mem://")


class ServiceConfig(BaseModel):
    name: str
    host: AnyHttpUrl
    timeout: float = 5.0
    rate_limit: int = 100
    rate_limit_period: int = 3600
    max_concurrent_requests: int = 10


class AppConfig(BaseSettings):
    app_name: str = "SWAPI Proxy"
    app_version: str = "dev"
    app_debug: bool = False

    cors: CORSConfig = CORSConfig()
    services: list[ServiceConfig] = [
        ServiceConfig(
            name="swapi",
            host=Url("https://swapi.dev/api"),
        )
    ]
    limiter: RateLimiterConfig = RateLimiterConfig()

    _service_map: dict[str, ServiceConfig]

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod", ".env.local"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    def __init__(self, **data):
        super().__init__(**data)
        self._service_map = {service.name: service for service in self.services}

    def get_service(self, name: str) -> ServiceConfig | None:
        return self._service_map.get(name)


config = AppConfig()
