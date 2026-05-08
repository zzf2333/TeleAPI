from __future__ import annotations

from datetime import datetime, timezone

import pytest

from teleapi.models.message import Message
from teleapi.models.webhook_delivery import WebhookDelivery


pytestmark = pytest.mark.api


class TestWebhookDeliveriesAPI:
    async def test_list_empty(self, client):
        resp = await client.get("/api/webhook-deliveries")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_data(self, client, db_session, seed_channel):
        m = Message(
            telegram_message_id=777,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)

        d = WebhookDelivery(
            webhook_name="wh1",
            event="message.created",
            message_id=m.id,
            status="success",
            attempts=1,
            response_status=200,
        )
        db_session.add(d)
        await db_session.commit()

        resp = await client.get("/api/webhook-deliveries")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["webhook_name"] == "wh1"

    async def test_filter_by_name(self, client, db_session, seed_channel):
        m = Message(
            telegram_message_id=778,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)

        for name in ["wh_a", "wh_b"]:
            d = WebhookDelivery(webhook_name=name, message_id=m.id, status="success")
            db_session.add(d)
        await db_session.commit()

        resp = await client.get("/api/webhook-deliveries?webhook_name=wh_a")
        data = resp.json()
        assert all(d["webhook_name"] == "wh_a" for d in data)

    async def test_filter_by_status(self, client, db_session, seed_channel):
        m = Message(
            telegram_message_id=779,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)

        d1 = WebhookDelivery(webhook_name="wh1", message_id=m.id, status="success")
        d2 = WebhookDelivery(webhook_name="wh2", message_id=m.id, status="failed")
        db_session.add_all([d1, d2])
        await db_session.commit()

        resp = await client.get("/api/webhook-deliveries?status=failed")
        data = resp.json()
        assert all(d["status"] == "failed" for d in data)

    async def test_limit(self, client, db_session, seed_channel):
        m = Message(
            telegram_message_id=780,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)

        for i in range(5):
            d = WebhookDelivery(webhook_name=f"wh{i}", message_id=m.id)
            db_session.add(d)
        await db_session.commit()

        resp = await client.get("/api/webhook-deliveries?limit=3")
        assert len(resp.json()) == 3
