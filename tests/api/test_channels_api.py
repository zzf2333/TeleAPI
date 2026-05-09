from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.models.sync_job import SyncJob


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


class TestAddChannel:
    async def test_add_success(self, client, test_app):
        entity = MagicMock()
        entity.id = 9999999
        entity.title = "New Channel"
        test_app.state.channel_manager._client.get_entity = AsyncMock(return_value=entity)
        test_app.state.telegram_client.is_authorized = AsyncMock(return_value=True)

        resp = await client.post("/api/channels", json={"username": "newchannel"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newchannel"
        assert data["title"] == "New Channel"
        assert data["enabled"] is True

    async def test_add_strips_at_sign(self, client, test_app):
        entity = MagicMock()
        entity.id = 8888888
        entity.title = "At Channel"
        test_app.state.channel_manager._client.get_entity = AsyncMock(return_value=entity)
        test_app.state.telegram_client.is_authorized = AsyncMock(return_value=True)

        resp = await client.post("/api/channels", json={"username": "@atchannel"})
        assert resp.status_code == 201
        assert resp.json()["username"] == "atchannel"

    async def test_add_empty_username(self, client, test_app):
        test_app.state.telegram_client.is_authorized = AsyncMock(return_value=True)
        resp = await client.post("/api/channels", json={"username": "  "})
        assert resp.status_code == 400

    async def test_add_not_found_on_telegram(self, client, test_app):
        test_app.state.channel_manager._client.get_entity = AsyncMock(
            side_effect=Exception("No user has 'badname' as username")
        )
        test_app.state.telegram_client.is_authorized = AsyncMock(return_value=True)

        resp = await client.post("/api/channels", json={"username": "badname"})
        assert resp.status_code == 400
        assert "badname" in resp.json()["error"]

    async def test_add_duplicate(self, client, test_app, seed_channel):
        test_app.state.telegram_client.is_authorized = AsyncMock(return_value=True)

        resp = await client.post("/api/channels", json={"username": "testchannel"})
        assert resp.status_code == 409

    async def test_add_not_authorized(self, client, test_app):
        test_app.state.telegram_client.is_authorized = AsyncMock(return_value=False)

        resp = await client.post("/api/channels", json={"username": "anychannel"})
        assert resp.status_code == 503


class TestUpdateChannel:
    async def test_toggle_disable(self, client, test_app, seed_channel):
        resp = await client.put(
            f"/api/channels/{seed_channel.id}",
            json={"enabled": False},
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    async def test_toggle_enable(self, client, test_app, seed_channel, db_session):
        seed_channel.enabled = False
        await db_session.commit()

        entity = MagicMock()
        entity.id = seed_channel.telegram_id
        entity.title = seed_channel.title
        test_app.state.channel_manager._client.get_entity = AsyncMock(return_value=entity)

        resp = await client.put(
            f"/api/channels/{seed_channel.id}",
            json={"enabled": True},
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    async def test_toggle_not_found(self, client):
        resp = await client.put("/api/channels/nonexistent", json={"enabled": False})
        assert resp.status_code == 404


class TestDeleteChannel:
    async def test_delete_success(self, client, seed_channel):
        resp = await client.delete(f"/api/channels/{seed_channel.id}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        resp2 = await client.get(f"/api/channels/{seed_channel.id}")
        assert resp2.status_code == 404

    async def test_delete_with_messages(self, client, seed_channel, seed_messages):
        resp = await client.delete(f"/api/channels/{seed_channel.id}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_delete_not_found(self, client):
        resp = await client.delete("/api/channels/nonexistent")
        assert resp.status_code == 404
