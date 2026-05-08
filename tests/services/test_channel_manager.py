from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from teleapi.config import TelegramChannelConfig
from teleapi.telegram.channel_manager import ChannelManager


pytestmark = pytest.mark.service


class TestChannelManager:
    async def test_resolve_single(self, mock_telegram_client, db_session):
        entity = MagicMock()
        entity.id = 1001
        entity.title = "Test Channel"
        mock_telegram_client.get_entity = AsyncMock(return_value=entity)
        cm = ChannelManager(mock_telegram_client)
        configs = [TelegramChannelConfig(username="testch")]
        result = await cm.resolve_channels(configs, db_session)
        assert len(result) == 1
        assert result[0].telegram_id == 1001

    async def test_skip_disabled(self, mock_telegram_client, db_session):
        cm = ChannelManager(mock_telegram_client)
        configs = [TelegramChannelConfig(username="testch", enabled=False)]
        result = await cm.resolve_channels(configs, db_session)
        assert len(result) == 0

    async def test_update_existing(self, mock_telegram_client, db_session, seed_channel):
        entity = MagicMock()
        entity.id = seed_channel.telegram_id
        entity.title = "Updated Title"
        mock_telegram_client.get_entity = AsyncMock(return_value=entity)
        cm = ChannelManager(mock_telegram_client)
        configs = [TelegramChannelConfig(username=seed_channel.username)]
        result = await cm.resolve_channels(configs, db_session)
        assert result[0].title == "Updated Title"

    async def test_create_new(self, mock_telegram_client, db_session):
        entity = MagicMock()
        entity.id = 9999
        entity.title = "New Channel"
        mock_telegram_client.get_entity = AsyncMock(return_value=entity)
        cm = ChannelManager(mock_telegram_client)
        configs = [TelegramChannelConfig(username="newch")]
        result = await cm.resolve_channels(configs, db_session)
        assert len(result) == 1
        assert result[0].telegram_id == 9999

    async def test_error_skipped(self, mock_telegram_client, db_session):
        mock_telegram_client.get_entity = AsyncMock(side_effect=RuntimeError("fail"))
        cm = ChannelManager(mock_telegram_client)
        configs = [TelegramChannelConfig(username="badch")]
        result = await cm.resolve_channels(configs, db_session)
        assert len(result) == 0

    def test_get_entity_cached(self, mock_telegram_client):
        cm = ChannelManager(mock_telegram_client)
        entity = MagicMock()
        cm._entities["testch"] = entity
        assert cm.get_entity("testch") is entity

    def test_get_entity_not_resolved(self, mock_telegram_client):
        cm = ChannelManager(mock_telegram_client)
        assert cm.get_entity("unknown") is None
