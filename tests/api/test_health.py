from __future__ import annotations

import pytest

from teleapi import __version__


pytestmark = pytest.mark.api


class TestHealthEndpoint:
    async def test_health_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == __version__

    async def test_health_no_auth_required(self, unauthed_client):
        resp = await unauthed_client.get("/health")
        assert resp.status_code == 200
