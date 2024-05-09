from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock

    from tests.api.conftest import TestClient

pytestmark = [pytest.mark.anyio]


class TestProxy:
    async def test_proxy_to_root(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url = "https://swapi.dev/api/"
        expected_response = {"films": "https://swapi.dev/api/films/"}
        httpx_mock.add_response(url=proxy_url, json=expected_response, match_headers={})
        # WHEN
        response = await client.get("/swapi/")
        # THEN
        assert response.status_code == 200
        assert response.json() == expected_response

    async def test_proxy_to_non_root(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url = "https://swapi.dev/api/films/1"
        expected_response = {"release_date": "1977-05-25"}
        httpx_mock.add_response(url=proxy_url, json=expected_response, match_headers={})
        # WHEN
        response = await client.get("/swapi/films/1")
        # THEN
        assert response.status_code == 200
        assert response.json() == expected_response

    async def test_proxy_query_params(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url = "https://swapi.dev/api/people?search=r2"
        expected_response = {"count": 1, "next": None}
        httpx_mock.add_response(url=proxy_url, json=expected_response, match_headers={})
        # WHEN
        response = await client.get("/swapi/people/?search=r2")
        # THEN
        assert response.status_code == 200
        assert response.json() == expected_response
