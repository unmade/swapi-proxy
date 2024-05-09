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


class ProxyBatchResponseItemResult(BaseModel):
    status_code: int
    content: dict[str, Any] | str | bytes


class ProxyBatchResponseItemError(BaseModel):
    code: str
    title: str
    description: str


class ProxyBatchResponseItem(BaseModel):
    path: str
    result: ProxyBatchResponseItemResult | None = None
    error: ProxyBatchResponseItemError | None = None

    @model_validator(mode="after")
    def validate_either_result_or_error_is_set(self) -> Self:
        assert (
            self.result and not self.error or not self.result and self.error
        ), "Can't have both `error` and `result`"
        return self


class ProxyBatchResponse(BaseModel):
    items: list[ProxyBatchResponseItem]
