from __future__ import annotations

from src.api.exceptions import APIError


class TestAPIErrorRepresentation:
    def test(self):
        # GIVEN
        error = APIError()
        expected = "APIError(description='Something has gone wrong on the server')"
        # WHEN
        result = repr(error)
        # THEN
        assert result == expected
