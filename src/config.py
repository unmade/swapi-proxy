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
    timeout: float = 5.0


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
    _service_map: dict[str, ServiceConfig]

    def __init__(self, **data):
        super().__init__(**data)
        self._service_map = {service.name: service for service in self.services}

    def get_service(self, name: str) -> ServiceConfig | None:
        return self._service_map.get(name)


config = AppConfig()
