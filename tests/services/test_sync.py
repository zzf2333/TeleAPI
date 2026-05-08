from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlmodel import select

from teleapi.models.message import Message
from teleapi.models.sync_job import SyncJob
from teleapi.telegram.sync import HistorySyncService


pytestmark = pytest.mark.service


def _make_tg_message(id_, text="hello", action=None):
    msg = MagicMock()
    msg.id = id_
    msg.message = text
    msg.media = None
    msg.entities = None
    msg.date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    msg.edit_date = None
    msg.views = 10
    msg.forwards = 1
    msg.replies = None
    msg.action = action
    msg.to_dict.return_value = {"_": "Message", "id": id_}
    return msg


class TestHistorySyncService:
    async def test_basic_sync(self, mock_telegram_client, async_session_factory, seed_channel, seed_sync_job):
        msgs = [_make_tg_message(i) for i in range(3)]

        async def mock_iter(*args, **kwargs):
            for m in msgs:
                yield m

        mock_telegram_client.iter_messages = MagicMock(return_value=mock_iter())
        svc = HistorySyncService(mock_telegram_client, async_session_factory)
        entity = MagicMock()

        await svc.sync_channel(seed_channel.id, entity, seed_sync_job.id, limit=100)

        async with async_session_factory() as session:
            job = (await session.execute(select(SyncJob).where(SyncJob.id == seed_sync_job.id))).scalar_one()
            assert job.status == "success"
            assert job.synced == 3

    async def test_skip_action_messages(self, mock_telegram_client, async_session_factory, seed_channel, seed_sync_job):
        msgs = [
            _make_tg_message(1),
            _make_tg_message(2, action=MagicMock()),
            _make_tg_message(3),
        ]

        async def mock_iter(*args, **kwargs):
            for m in msgs:
                yield m

        mock_telegram_client.iter_messages = MagicMock(return_value=mock_iter())
        svc = HistorySyncService(mock_telegram_client, async_session_factory)
        await svc.sync_channel(seed_channel.id, MagicMock(), seed_sync_job.id, limit=100)

        async with async_session_factory() as session:
            count = len((await session.execute(select(Message).where(Message.channel_id == seed_channel.id))).scalars().all())
        assert count == 2

    async def test_dedup_existing(self, mock_telegram_client, async_session_factory, seed_channel, seed_sync_job, db_session):
        m = Message(
            telegram_message_id=1,
            channel_id=seed_channel.id,
            channel_username=seed_channel.username,
            date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        db_session.add(m)
        await db_session.commit()

        async def mock_iter(*args, **kwargs):
            yield _make_tg_message(1)
            yield _make_tg_message(2)

        mock_telegram_client.iter_messages = MagicMock(return_value=mock_iter())
        svc = HistorySyncService(mock_telegram_client, async_session_factory)
        await svc.sync_channel(seed_channel.id, MagicMock(), seed_sync_job.id, limit=100)

        async with async_session_factory() as session:
            all_msgs = (await session.execute(
                select(Message).where(Message.channel_id == seed_channel.id)
            )).scalars().all()
        assert len(all_msgs) == 2

    async def test_zero_messages(self, mock_telegram_client, async_session_factory, seed_channel, seed_sync_job):
        async def mock_iter(*args, **kwargs):
            return
            yield

        mock_telegram_client.iter_messages = MagicMock(return_value=mock_iter())
        svc = HistorySyncService(mock_telegram_client, async_session_factory)
        await svc.sync_channel(seed_channel.id, MagicMock(), seed_sync_job.id, limit=100)

        async with async_session_factory() as session:
            job = (await session.execute(select(SyncJob).where(SyncJob.id == seed_sync_job.id))).scalar_one()
            assert job.status == "success"
            assert job.synced == 0

    async def test_channel_private_error(self, mock_telegram_client, async_session_factory, seed_channel, seed_sync_job):
        from telethon.errors import ChannelPrivateError

        async def mock_iter(*args, **kwargs):
            raise ChannelPrivateError(request=None)
            yield

        mock_telegram_client.iter_messages = MagicMock(return_value=mock_iter())
        svc = HistorySyncService(mock_telegram_client, async_session_factory)
        await svc.sync_channel(seed_channel.id, MagicMock(), seed_sync_job.id, limit=100)

        async with async_session_factory() as session:
            job = (await session.execute(select(SyncJob).where(SyncJob.id == seed_sync_job.id))).scalar_one()
            assert job.status == "failed"
            assert "private" in job.error.lower()

    async def test_generic_exception(self, mock_telegram_client, async_session_factory, seed_channel, seed_sync_job):
        async def mock_iter(*args, **kwargs):
            raise RuntimeError("unexpected")
            yield

        mock_telegram_client.iter_messages = MagicMock(return_value=mock_iter())
        svc = HistorySyncService(mock_telegram_client, async_session_factory)
        await svc.sync_channel(seed_channel.id, MagicMock(), seed_sync_job.id, limit=100)

        async with async_session_factory() as session:
            job = (await session.execute(select(SyncJob).where(SyncJob.id == seed_sync_job.id))).scalar_one()
            assert job.status == "failed"
            assert "unexpected" in job.error
