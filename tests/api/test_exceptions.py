from __future__ import annotations

import json
from unittest import mock

import pytest
from fastapi import Request

from src.api.exceptions import APIError, RateLimit, rate_limit_error_handler
from src.toolkit.rate_limit.rate_limit import RateLimitError


class TestAPIErrorRepresentation:
    def test(self):
        # GIVEN
        error = APIError()
        expected = "APIError(description='Something has gone wrong on the server')"
        # WHEN
        result = repr(error)
        # THEN
        assert result == expected


@pytest.mark.anyio
class TestRateLimitErrorHandler:
    async def test(self):
        # GIVEN
        exc = RateLimitError()
        request = mock.MagicMock(Request)
        # WHEN
        result = await rate_limit_error_handler(request, exc)
        # THEN
        assert result.status_code == RateLimit.status_code
        assert json.loads(result.body) == RateLimit().as_dict()
