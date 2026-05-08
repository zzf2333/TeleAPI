from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import select

from teleapi.models.message import Message
from teleapi.services.event import EventDispatcher
from teleapi.telegram.listener import RealtimeListener


pytestmark = pytest.mark.service


def _make_event(msg_id=1, text="hello", chat_id=1001234567, username="testchannel", action=None):
    event = MagicMock()
    msg = MagicMock()
    msg.id = msg_id
    msg.message = text
    msg.media = None
    msg.entities = None
    msg.date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    msg.edit_date = None
    msg.views = 10
    msg.forwards = 1
    msg.replies = None
    msg.action = action
    msg.to_dict.return_value = {}
    event.message = msg

    chat = MagicMock()
    chat.id = chat_id
    chat.username = username
    chat.title = "Test Channel"
    event.get_chat = AsyncMock(return_value=chat)
    return event


class TestRealtimeListener:
    async def test_start_registers_handler(self, mock_telegram_client, async_session_factory):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        entity = MagicMock()
        entity.id = 123
        await listener.start([entity])
        mock_telegram_client.on.assert_called_once()

    async def test_empty_entities_no_handler(self, mock_telegram_client, async_session_factory):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        await listener.start([])
        mock_telegram_client.on.assert_not_called()

    async def test_new_message_creates_record(self, mock_telegram_client, async_session_factory, seed_channel):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        event = _make_event(msg_id=5000, chat_id=seed_channel.telegram_id, username=seed_channel.username)
        await listener._handle_new_message(event)

        async with async_session_factory() as session:
            msgs = (await session.execute(
                select(Message).where(Message.channel_id == seed_channel.id)
            )).scalars().all()
        assert len(msgs) == 1
        assert msgs[0].telegram_message_id == 5000

    async def test_skip_action_message(self, mock_telegram_client, async_session_factory, seed_channel):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        event = _make_event(action=MagicMock())
        await listener._handle_new_message(event)

        async with async_session_factory() as session:
            msgs = (await session.execute(select(Message))).scalars().all()
        assert len(msgs) == 0

    async def test_unknown_channel_skipped(self, mock_telegram_client, async_session_factory):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        event = _make_event(chat_id=9999999)
        await listener._handle_new_message(event)

        async with async_session_factory() as session:
            msgs = (await session.execute(select(Message))).scalars().all()
        assert len(msgs) == 0

    async def test_dedup(self, mock_telegram_client, async_session_factory, seed_channel):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        event = _make_event(msg_id=6000, chat_id=seed_channel.telegram_id, username=seed_channel.username)
        await listener._handle_new_message(event)
        await listener._handle_new_message(event)

        async with async_session_factory() as session:
            msgs = (await session.execute(
                select(Message).where(Message.telegram_message_id == 6000)
            )).scalars().all()
        assert len(msgs) == 1

    async def test_dispatch_called(self, mock_telegram_client, async_session_factory, seed_channel):
        dispatcher = EventDispatcher()
        handler = AsyncMock()
        dispatcher.subscribe("message.created", handler)
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        event = _make_event(msg_id=7000, chat_id=seed_channel.telegram_id, username=seed_channel.username)
        await listener._handle_new_message(event)
        handler.assert_called_once()
        payload = handler.call_args[0][0]
        assert payload["telegram_message_id"] == 7000

    async def test_stop_removes_handler(self, mock_telegram_client, async_session_factory):
        dispatcher = EventDispatcher()
        listener = RealtimeListener(mock_telegram_client, async_session_factory, dispatcher)
        listener._handler = MagicMock()
        await listener.stop()
        mock_telegram_client.remove_event_handler.assert_called_once()
        assert listener._handler is None
