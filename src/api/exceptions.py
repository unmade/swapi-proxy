from typing import cast

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.toolkit.rate_limit import RateLimitError


async def api_error_exception_handler(_: Request, exc: Exception) -> Response:
    exc = cast(APIError, exc)
    return JSONResponse(exc.as_dict(), status_code=exc.status_code)


async def rate_limit_error_handler(_: Request, exc: Exception) -> Response:
    exc = cast(RateLimitError, exc)
    rate_limit_error = RateLimit()
    return JSONResponse(
        rate_limit_error.as_dict(), status_code=rate_limit_error.status_code
    )


class APIError(Exception):
    status_code = 500
    code = "SERVER_ERROR"
    title = "A server error occurred"
    default_description = "Something has gone wrong on the server"

    def __init__(self, description: str | None = None):
        self.description = description or self.default_description

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(description={self.description!r})"

    def as_dict(self):
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
        }


class RateLimit(APIError):
    status_code = 429
    code = "RATE_LIMIT"
    title = "Rate limit"
    default_description = "Too many requests."


class BadGateway(APIError):
    status_code = 502
    code = "BAD_GATEWAY"
    title = "Bad gateway"
    default_description = "Invalid response from the upstream server."


class GatewayTimeout(APIError):
    status_code = 504
    code = "GATEWAY_TIMEOUT"
    title = "Gateway timeout"
    default_description = "Server does not receive a timely response from an upstream."
