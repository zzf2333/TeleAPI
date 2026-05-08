from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


pytestmark = pytest.mark.api


class TestSystemStatusAPI:
    async def test_status_structure(self, client):
        with patch("teleapi.api.system.Path") as MockPath:
            MockPath.return_value.exists.return_value = False
            resp = await client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "telegram" in data
        assert "channels" in data
        assert "messages" in data
        assert "database" in data
        assert "webhooks" in data

    async def test_status_authorized(self, client):
        with patch("teleapi.api.system.Path") as MockPath:
            MockPath.return_value.exists.return_value = False
            resp = await client.get("/api/system/status")
        data = resp.json()
        assert data["telegram"]["connected"] is True
        assert data["telegram"]["user"] is not None

    async def test_status_not_authorized(self, client, test_app):
        test_app.state.telegram_client._client.is_user_authorized = AsyncMock(return_value=False)
        with patch("teleapi.api.system.Path") as MockPath:
            MockPath.return_value.exists.return_value = False
            resp = await client.get("/api/system/status")
        data = resp.json()
        assert data["telegram"]["connected"] is False


class TestConfigCheckAPI:
    async def test_structure(self, client):
        with patch("teleapi.api.system.SESSION_FILE") as mock_sf:
            mock_sf.exists.return_value = True
            with patch("teleapi.api.system.Path") as MockPath:
                MockPath.return_value.exists.return_value = True
                resp = await client.get("/api/system/config-check")
        assert resp.status_code == 200
        data = resp.json()
        assert "checks" in data
        assert "all_ok" in data
        assert isinstance(data["checks"], list)

    async def test_all_ok(self, client, test_app):
        test_app.state.config.telegram.channels = [
            type("Obj", (), {"username": "ch1", "enabled": True})()
        ]
        test_app.state.config.outputs.webhooks = [
            type("Obj", (), {"name": "wh1"})()
        ]
        with patch("teleapi.api.system.SESSION_FILE") as mock_sf:
            mock_sf.exists.return_value = True
            with patch("teleapi.api.system.Path") as MockPath:
                MockPath.return_value.exists.return_value = True
                resp = await client.get("/api/system/config-check")
        data = resp.json()
        assert data["all_ok"] is True
