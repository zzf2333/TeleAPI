from __future__ import annotations

import pytest


pytestmark = pytest.mark.api


class TestChannelsAPI:
    async def test_list_empty(self, client):
        resp = await client.get("/api/channels")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_data(self, client, seed_channel):
        resp = await client.get("/api/channels")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["username"] == "testchannel"
        assert "message_count" in data[0]

    async def test_get_by_id(self, client, seed_channel):
        resp = await client.get(f"/api/channels/{seed_channel.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["telegram_id"] == seed_channel.telegram_id

    async def test_get_by_username(self, client, seed_channel):
        resp = await client.get(f"/api/channels/{seed_channel.username}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testchannel"

    async def test_get_not_found(self, client):
        resp = await client.get("/api/channels/nonexistent")
        assert resp.status_code == 404
