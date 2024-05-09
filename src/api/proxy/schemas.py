from __future__ import annotations

from http import HTTPMethod
from typing import Annotated, Any, Literal, Self

from pydantic import AfterValidator, BaseModel, model_validator


def _normalize_path(value: str) -> str:
    value = value.strip()
    if not value.startswith("/"):
        raise ValueError("Path must start with `/`")
    return value.lower()


class ProxyBatchItemSchema(BaseModel):
    method: Literal[HTTPMethod.GET] = HTTPMethod.GET
    path: Annotated[str, AfterValidator(_normalize_path)]


class ProxyBatchRequest(BaseModel):
    items: list[ProxyBatchItemSchema]

    @model_validator(mode="after")
    def validate_path_are_unique(self) -> Self:
        seen_paths = set()
        for item in self.items:
            if item.path in seen_paths:
                raise ValueError(f"Found non-unique path: `{item.path}`")
            seen_paths.add(item.path)
        return self


class ProxyBatchResponseItem(BaseModel):
    path: str
    status_code: int
    result: dict[str, Any] | str | bytes


class ProxyBatchResponse(BaseModel):
    items: list[ProxyBatchResponseItem]
