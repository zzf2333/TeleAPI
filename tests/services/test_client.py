from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from teleapi.telegram.client import TelegramClientManager, SESSION_FILE


pytestmark = pytest.mark.service


class TestTelegramClientManager:
    async def test_connect_no_session(self, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        cm = TelegramClientManager(api_id=123, api_hash="abc")
        with patch("teleapi.telegram.client.TelegramClient") as MockClient:
            mock = AsyncMock()
            mock.is_user_authorized = AsyncMock(return_value=False)
            MockClient.return_value = mock
            await cm.connect()
        assert cm._client is not None

    async def test_connect_with_session(self, tmp_path, monkeypatch):
        session_file = tmp_path / "session.key"
        session_file.write_text("existing_session")
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", session_file)
        cm = TelegramClientManager(api_id=123, api_hash="abc")
        with patch("teleapi.telegram.client.TelegramClient") as MockClient, \
             patch("teleapi.telegram.client.StringSession") as MockSession:
            mock = AsyncMock()
            mock.is_user_authorized = AsyncMock(return_value=False)
            MockClient.return_value = mock
            await cm.connect()
        assert cm._client is not None
        MockSession.assert_called_once_with("existing_session")

    def test_client_property_before_connect(self):
        cm = TelegramClientManager(api_id=123, api_hash="abc")
        with pytest.raises(RuntimeError, match="not connected"):
            _ = cm.client

    async def test_is_authorized_true(self, mock_client_manager):
        result = await mock_client_manager.is_authorized()
        assert result is True

    async def test_is_authorized_false(self):
        cm = TelegramClientManager(api_id=123, api_hash="abc")
        cm._client = AsyncMock()
        cm._client.is_user_authorized = AsyncMock(return_value=False)
        assert await cm.is_authorized() is False

    async def test_is_authorized_no_client(self):
        cm = TelegramClientManager(api_id=123, api_hash="abc")
        assert await cm.is_authorized() is False

    async def test_get_me_authorized(self, mock_client_manager):
        result = await mock_client_manager.get_me()
        assert result["first_name"] == "Test"
        assert result["username"] == "testuser"

    async def test_get_me_not_authorized(self):
        cm = TelegramClientManager(api_id=123, api_hash="abc")
        cm._client = AsyncMock()
        cm._client.is_user_authorized = AsyncMock(return_value=False)
        assert await cm.get_me() is None

    def test_save_session(self, tmp_path, mock_client_manager, monkeypatch):
        session_file = tmp_path / "session.key"
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", session_file)
        mock_client_manager._client.session.save.return_value = "saved_data"
        mock_client_manager.save_session()
        assert session_file.read_text() == "saved_data"

    async def test_disconnect(self, mock_client_manager):
        await mock_client_manager.disconnect()
        mock_client_manager._client.disconnect.assert_called_once()

    async def test_logout(self, tmp_path, mock_client_manager, monkeypatch):
        session_file = tmp_path / "session.key"
        session_file.write_text("data")
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", session_file)
        await mock_client_manager.logout()
        mock_client_manager._client.log_out.assert_called_once()
        assert not session_file.exists()

    async def test_logout_no_session_file(self, tmp_path, mock_client_manager, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "missing.key")
        await mock_client_manager.logout()
        mock_client_manager._client.log_out.assert_called_once()
