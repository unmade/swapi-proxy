from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from src.api.exceptions import APIError, BadGateway, GatewayTimeout

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock

    from tests.api.conftest import TestClient

pytestmark = [pytest.mark.anyio]


class TestProxy:
    async def test_proxy_to_root(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url = "https://swapi.dev/api/"
        expected_response = {"films": "https://swapi.dev/api/films/"}
        httpx_mock.add_response(url=proxy_url, json=expected_response)
        # WHEN
        response = await client.get("/proxy/swapi/")
        # THEN
        # assert response.status_code == 200
        assert response.json() == expected_response

    async def test_proxy_to_non_root(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url = "https://swapi.dev/api/films/1"
        expected_response = {"release_date": "1977-05-25"}
        httpx_mock.add_response(url=proxy_url, json=expected_response)
        # WHEN
        response = await client.get("/proxy/swapi/films/1")
        # THEN
        assert response.status_code == 200
        assert response.json() == expected_response

    async def test_proxy_query_params(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url = "https://swapi.dev/api/people?search=r2"
        expected_response = {"count": 1, "next": None}
        httpx_mock.add_response(url=proxy_url, json=expected_response)
        # WHEN
        response = await client.get("/proxy/swapi/people/?search=r2")
        # THEN
        assert response.status_code == 200
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        ["error", "expected_error"],
        [
            (httpx.ReadTimeout("timeout"), GatewayTimeout()),
            (httpx.NetworkError("network error"), BadGateway()),
            (httpx.HTTPError("http error"), APIError()),
        ],
    )
    async def test_reraising_errors(
        self,
        client: TestClient,
        httpx_mock: HTTPXMock,
        error: httpx.HTTPError,
        expected_error: APIError,
    ):
        # GIVEN
        proxy_url = "https://swapi.dev/api/people?search=r2"
        httpx_mock.add_exception(error, url=proxy_url)
        # WHEN
        response = await client.get("/proxy/swapi/people/?search=r2")
        # THEN
        assert response.status_code == expected_error.status_code
        assert response.json() == expected_error.as_dict()


class TestProxyBatch:
    url = "/proxy_batch/swapi"

    async def test(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url_1 = "https://swapi.dev/api/films/1"
        expected_response_1 = {"release_date": "1977-05-25"}

        proxy_url_2 = "https://swapi.dev/api/films/2"
        expected_response_2 = {"release_date": "1980-05-17"}

        httpx_mock.add_response(url=proxy_url_1, json=expected_response_1)
        httpx_mock.add_response(url=proxy_url_2, json=expected_response_2)

        payload = {"items": [{"path": "/films/1"}, {"path": "/films/2"}]}

        # WHEN
        response = await client.post(self.url, json=payload)

        # THEN
        assert response.status_code == 200
        assert response.json() == {
            "items": [
                {
                    "path": "/films/1",
                    "result": {
                        "status_code": 200,
                        "content": expected_response_1,
                    },
                    "error": None,
                },
                {
                    "path": "/films/2",
                    "result": {
                        "status_code": 200,
                        "content": expected_response_2,
                    },
                    "error": None,
                },
            ]
        }

    async def test_error_handling(self, client: TestClient, httpx_mock: HTTPXMock):
        # GIVEN
        proxy_url_1 = "https://swapi.dev/api/films/1"
        expected_response_1 = {"release_date": "1977-05-25"}

        proxy_url_2 = "https://swapi.dev/api/films/2"

        proxy_url_3 = "https://swapi.dev/api/films/3"
        expected_response_3 = {"release_date": "1983-05-25"}

        httpx_mock.add_response(url=proxy_url_1, json=expected_response_1)
        httpx_mock.add_exception(httpx.ReadTimeout("timeout"), url=proxy_url_2)
        httpx_mock.add_response(url=proxy_url_3, json=expected_response_3)

        payload = {
            "items": [{"path": "/films/1"}, {"path": "/films/2"}, {"path": "/films/3"}]
        }

        # WHEN
        response = await client.post(self.url, json=payload)

        # THEN
        assert response.status_code == 200
        assert response.json() == {
            "items": [
                {
                    "path": "/films/1",
                    "result": {
                        "status_code": 200,
                        "content": expected_response_1,
                    },
                    "error": None,
                },
                {
                    "path": "/films/2",
                    "result": None,
                    "error": {
                        "code": "GATEWAY_TIMEOUT",
                        "title": "Gateway timeout",
                        "description": (
                            "Server does not receive a timely response from an "
                            "upstream."
                        ),
                    },
                },
                {
                    "path": "/films/3",
                    "result": {
                        "status_code": 200,
                        "content": expected_response_3,
                    },
                    "error": None,
                },
            ]
        }

    @pytest.mark.usefixtures("httpx_mock")
    async def test_when_path_does_not_start_with_slash(self, client: TestClient):
        # GIVEN
        payload = {"items": [{"path": ""}]}
        # WHEN
        response = await client.post(self.url, json=payload)
        # THEN
        assert response.status_code == 422
        error_msg = response.json()["detail"][0]["msg"]
        assert "Path must start with `/`" in error_msg

    @pytest.mark.usefixtures("httpx_mock")
    async def test_when_path_non_unique(self, client: TestClient):
        # GIVEN
        payload = {"items": [{"path": "/films/1"}, {"path": "/films/1"}]}
        # WHEN
        response = await client.post(self.url, json=payload)
        # THEN
        assert response.status_code == 422
        error_msg = response.json()["detail"][0]["msg"]
        assert "Found non-unique path: `/films/1`" in error_msg
