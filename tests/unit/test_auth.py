from __future__ import annotations

import pytest

from tests.conftest import TEST_API_KEY


pytestmark = pytest.mark.unit


class TestAuthVerification:
    async def test_bearer_valid(self, client):
        resp = await client.get("/api/channels")
        assert resp.status_code == 200

    async def test_bearer_invalid(self, test_app):
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"Authorization": "Bearer wrong_key"},
        ) as c:
            resp = await c.get("/api/channels")
        assert resp.status_code == 403

    async def test_x_teleapi_key_valid(self, test_app):
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"X-TeleAPI-Key": TEST_API_KEY},
        ) as c:
            resp = await c.get("/api/channels")
        assert resp.status_code == 200

    async def test_x_teleapi_key_invalid(self, test_app):
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"X-TeleAPI-Key": "wrong"},
        ) as c:
            resp = await c.get("/api/channels")
        assert resp.status_code == 403

    async def test_no_header_401(self, unauthed_client):
        resp = await unauthed_client.get("/api/channels")
        assert resp.status_code == 401

    async def test_empty_bearer_falls_back_to_x_key(self, test_app):
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"Authorization": "Bearer ", "X-TeleAPI-Key": TEST_API_KEY},
        ) as c:
            resp = await c.get("/api/channels")
        assert resp.status_code == 200

    async def test_bearer_takes_priority(self, test_app):
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {TEST_API_KEY}", "X-TeleAPI-Key": "wrong"},
        ) as c:
            resp = await c.get("/api/channels")
        assert resp.status_code == 200
