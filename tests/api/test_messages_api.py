from __future__ import annotations

import pytest


pytestmark = pytest.mark.api


class TestMessagesAPI:
    async def test_list_default(self, client, seed_channel, seed_messages):
        resp = await client.get(f"/api/channels/{seed_channel.id}/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 20

    async def test_list_with_limit(self, client, seed_channel, seed_messages):
        resp = await client.get(f"/api/channels/{seed_channel.id}/messages?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 5
        assert data["next_cursor"] is not None

    async def test_cursor_pagination(self, client, seed_channel, seed_messages):
        resp1 = await client.get(f"/api/channels/{seed_channel.id}/messages?limit=10")
        cursor = resp1.json()["next_cursor"]
        assert cursor is not None
        resp2 = await client.get(f"/api/channels/{seed_channel.id}/messages?limit=10&cursor={cursor}")
        data2 = resp2.json()
        assert len(data2["data"]) == 10
        ids1 = {m["id"] for m in resp1.json()["data"]}
        ids2 = {m["id"] for m in data2["data"]}
        assert ids1.isdisjoint(ids2)

    async def test_filter_keyword(self, client, seed_channel, seed_messages):
        resp = await client.get(f"/api/channels/{seed_channel.id}/messages?keyword=message 5")
        data = resp.json()
        assert all("message 5" in m["text"] for m in data["data"])

    async def test_filter_type(self, client, seed_channel, seed_messages):
        resp = await client.get(f"/api/channels/{seed_channel.id}/messages?type=photo")
        data = resp.json()
        assert all(m["type"] == "photo" for m in data["data"])

    async def test_filter_before(self, client, seed_channel, seed_messages):
        resp = await client.get(
            f"/api/channels/{seed_channel.id}/messages?before=2025-01-01T05:00:00%2B00:00"
        )
        data = resp.json()
        assert len(data["data"]) > 0
        assert len(data["data"]) < 25

    async def test_filter_after(self, client, seed_channel, seed_messages):
        resp = await client.get(
            f"/api/channels/{seed_channel.id}/messages?after=2025-01-01T20:00:00%2B00:00"
        )
        data = resp.json()
        assert len(data["data"]) > 0
        assert len(data["data"]) < 25

    async def test_empty_channel(self, client, seed_channel):
        resp = await client.get(f"/api/channels/{seed_channel.id}/messages")
        data = resp.json()
        assert data["data"] == []
        assert data["next_cursor"] is None

    async def test_by_username(self, client, seed_channel, seed_messages):
        resp = await client.get(f"/api/channels/{seed_channel.username}/messages?limit=5")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 5

    async def test_get_single_message(self, client, seed_channel, seed_messages):
        msg_id = seed_messages[0].id
        resp = await client.get(f"/api/messages/{msg_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == msg_id

    async def test_get_message_not_found(self, client):
        resp = await client.get("/api/messages/nonexistent")
        assert resp.status_code == 404

    async def test_combined_filters(self, client, seed_channel, seed_messages):
        resp = await client.get(
            f"/api/channels/{seed_channel.id}/messages?type=text&keyword=message&limit=5"
        )
        data = resp.json()
        for m in data["data"]:
            assert m["type"] == "text"
            assert "message" in m["text"]
