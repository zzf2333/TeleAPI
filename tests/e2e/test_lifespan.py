from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import TEST_API_KEY


pytestmark = pytest.mark.e2e


class TestLifespan:
    async def test_startup_shutdown(self, test_app):
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        ) as c:
            resp = await c.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

    async def test_authorized_auto_setup(self, test_app):
        assert test_app.state.telegram_client is not None
        assert test_app.state.login_service is not None
        assert test_app.state.phone_login_service is not None
        assert test_app.state.channel_manager is not None
        assert test_app.state.sync_service is not None

    async def test_not_authorized_no_crash(self, test_app):
        test_app.state.telegram_client._client.is_user_authorized = AsyncMock(return_value=False)
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        ) as c:
            resp = await c.get("/health")
            assert resp.status_code == 200
