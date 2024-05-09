from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.api.conftest import TestClient

pytestmark = [pytest.mark.anyio]


class TestProxy:
    async def test(self, client: TestClient):
        # WHEN
        response = await client.get("/swapi/")
        # THEN
        assert response.status_code == 200
        assert response.json() == "OK"
