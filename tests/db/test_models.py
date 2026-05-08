from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.models.sync_job import SyncJob
from teleapi.models.webhook_delivery import WebhookDelivery


pytestmark = pytest.mark.db


class TestChannelModel:
    async def test_create(self, db_session):
        ch = Channel(telegram_id=111, username="ch1", title="Channel 1")
        db_session.add(ch)
        await db_session.commit()
        await db_session.refresh(ch)
        assert ch.id is not None
        assert len(ch.id) == 32

    async def test_uuid_generated(self, db_session):
        ch1 = Channel(telegram_id=111, username="ch1")
        ch2 = Channel(telegram_id=222, username="ch2")
        db_session.add_all([ch1, ch2])
        await db_session.commit()
        assert ch1.id != ch2.id

    async def test_telegram_id_unique(self, db_session):
        ch1 = Channel(telegram_id=111, username="ch1")
        ch2 = Channel(telegram_id=111, username="ch2")
        db_session.add(ch1)
        await db_session.commit()
        db_session.add(ch2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_defaults(self, db_session):
        ch = Channel(telegram_id=333, username="ch3")
        db_session.add(ch)
        await db_session.commit()
        await db_session.refresh(ch)
        assert ch.enabled is True
        assert ch.title == ""
        assert ch.last_message_id is None
        assert ch.created_at is not None


class TestMessageModel:
    async def test_create(self, db_session, seed_channel):
        m = Message(
            telegram_message_id=1,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)
        assert m.id is not None

    async def test_unique_constraint(self, db_session, seed_channel):
        m1 = Message(
            telegram_message_id=1,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        m2 = Message(
            telegram_message_id=1,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m1)
        await db_session.commit()
        db_session.add(m2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_null_text_allowed(self, db_session, seed_channel):
        m = Message(
            telegram_message_id=2,
            channel_id=seed_channel.id,
            text=None,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)
        assert m.text is None

    async def test_large_text(self, db_session, seed_channel):
        big_text = "x" * 50000
        m = Message(
            telegram_message_id=3,
            channel_id=seed_channel.id,
            text=big_text,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)
        assert len(m.text) == 50000


class TestSyncJobModel:
    async def test_create(self, db_session, seed_channel):
        job = SyncJob(channel_id=seed_channel.id)
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)
        assert job.id is not None

    async def test_default_pending(self, db_session, seed_channel):
        job = SyncJob(channel_id=seed_channel.id)
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)
        assert job.status == "pending"
        assert job.synced == 0

    async def test_status_transition(self, db_session, seed_channel):
        job = SyncJob(channel_id=seed_channel.id)
        db_session.add(job)
        await db_session.commit()
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(job)
        assert job.status == "running"
        job.status = "success"
        job.finished_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(job)
        assert job.status == "success"


class TestWebhookDeliveryModel:
    async def test_create(self, db_session, seed_channel):
        m = Message(
            telegram_message_id=999,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)

        d = WebhookDelivery(webhook_name="wh1", event="message.created", message_id=m.id)
        db_session.add(d)
        await db_session.commit()
        await db_session.refresh(d)
        assert d.id is not None

    async def test_defaults(self, db_session, seed_channel):
        m = Message(
            telegram_message_id=998,
            channel_id=seed_channel.id,
            date=datetime.now(timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(m)

        d = WebhookDelivery(webhook_name="wh2", message_id=m.id)
        db_session.add(d)
        await db_session.commit()
        await db_session.refresh(d)
        assert d.status == "pending"
        assert d.attempts == 0
        assert d.response_status is None
