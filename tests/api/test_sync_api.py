from __future__ import annotations

import pytest



pytestmark = pytest.mark.api


class TestTriggerSync:
    async def test_trigger(self, client, seed_channel, test_app):
        test_app.state.channel_manager._entities[seed_channel.username] = None
        resp = await client.post(f"/api/channels/{seed_channel.id}/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    async def test_channel_not_found(self, client):
        resp = await client.post("/api/channels/nonexistent/sync")
        assert resp.status_code == 404

    async def test_conflict(self, client, seed_channel, seed_sync_job, test_app):
        test_app.state.channel_manager._entities[seed_channel.username] = None
        resp = await client.post(f"/api/channels/{seed_channel.id}/sync")
        assert resp.status_code == 409

    async def test_custom_params(self, client, seed_channel, test_app):
        test_app.state.channel_manager._entities[seed_channel.username] = None
        resp = await client.post(
            f"/api/channels/{seed_channel.id}/sync",
            json={"limit": 500, "force": True},
        )
        assert resp.status_code == 200

    async def test_entity_none_still_creates_job(self, client, seed_channel, test_app):
        resp = await client.post(f"/api/channels/{seed_channel.id}/sync")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"


class TestSyncJobsAPI:
    async def test_list(self, client, seed_sync_job):
        resp = await client.get("/api/sync-jobs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_filter_by_channel(self, client, seed_sync_job, seed_channel):
        resp = await client.get(f"/api/sync-jobs?channel_id={seed_channel.id}")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_filter_by_status(self, client, seed_sync_job):
        resp = await client.get("/api/sync-jobs?status=pending")
        assert resp.status_code == 200
        assert all(j["status"] == "pending" for j in resp.json())

    async def test_get_single(self, client, seed_sync_job):
        resp = await client.get(f"/api/sync-jobs/{seed_sync_job.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == seed_sync_job.id

    async def test_get_not_found(self, client):
        resp = await client.get("/api/sync-jobs/nonexistent")
        assert resp.status_code == 404
