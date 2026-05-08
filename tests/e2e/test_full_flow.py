from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import TEST_API_KEY


pytestmark = pytest.mark.e2e


class TestFullFlow:
    async def test_health_auth_channels(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

        resp = await client.get("/api/auth/status")
        assert resp.status_code == 200
        assert resp.json()["authorized"] is True

        resp = await client.get("/api/channels")
        assert resp.status_code == 200

    async def test_pagination_full_traverse(self, client, seed_channel, seed_messages):
        all_ids = set()
        cursor = None
        for _ in range(10):
            url = f"/api/channels/{seed_channel.id}/messages?limit=5"
            if cursor:
                url += f"&cursor={cursor}"
            resp = await client.get(url)
            data = resp.json()
            for m in data["data"]:
                all_ids.add(m["id"])
            cursor = data["next_cursor"]
            if not cursor:
                break
        assert len(all_ids) == 25

    async def test_sync_job_lifecycle(self, client, seed_channel, test_app):
        resp = await client.post(f"/api/channels/{seed_channel.id}/sync")
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        resp = await client.get(f"/api/sync-jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

        resp = await client.get("/api/sync-jobs")
        assert resp.status_code == 200
        ids = [j["id"] for j in resp.json()]
        assert job_id in ids

    async def test_phone_login_flow(self, client, test_app, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")

        result = MagicMock()
        result.phone_code_hash = "hash123"
        test_app.state.telegram_client.client.send_code_request = AsyncMock(return_value=result)

        resp = await client.post("/api/auth/phone-login/send-code", json={"phone": "+8613800138000"})
        assert resp.json()["status"] == "code_sent"

        resp = await client.post("/api/auth/phone-login/verify-code", json={"code": "12345"})
        assert resp.json()["status"] == "success"

        resp = await client.get("/api/auth/status")
        assert resp.json()["authorized"] is True
