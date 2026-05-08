from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from teleapi.telegram.login import QRLoginService, LoginStatus


pytestmark = pytest.mark.service


class TestQRLoginService:
    async def test_start_generates_qr(self, mock_client_manager):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock()
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        state = await svc.start()
        assert state.status == LoginStatus.WAITING
        assert state.qr_image_base64 != ""

    async def test_start_idempotent(self, mock_client_manager):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock(side_effect=asyncio.CancelledError)
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        await svc.start()
        state = await svc.start()
        assert state.status == LoginStatus.WAITING

    async def test_scan_success(self, mock_client_manager, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock(return_value=None)
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        await svc.start()
        await asyncio.sleep(0.1)
        assert svc.state.status == LoginStatus.SUCCESS

    async def test_scan_2fa_required(self, mock_client_manager):
        from telethon.errors import SessionPasswordNeededError
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock(side_effect=SessionPasswordNeededError(request=None))
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        await svc.start()
        await asyncio.sleep(0.1)
        assert svc.state.status == LoginStatus.TWO_FA_REQUIRED

    async def test_scan_timeout(self, mock_client_manager):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        await svc.start()
        await asyncio.sleep(0.1)
        assert svc.state.status == LoginStatus.EXPIRED

    async def test_scan_error(self, mock_client_manager):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock(side_effect=RuntimeError("network"))
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        await svc.start()
        await asyncio.sleep(0.1)
        assert svc.state.status == LoginStatus.ERROR
        assert "network" in svc.state.error

    async def test_submit_2fa_success(self, mock_client_manager, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        svc = QRLoginService(mock_client_manager)
        state = await svc.submit_2fa("password123")
        assert state.status == LoginStatus.SUCCESS

    async def test_submit_2fa_failure(self, mock_client_manager):
        mock_client_manager.client.sign_in = AsyncMock(side_effect=RuntimeError("bad pw"))
        svc = QRLoginService(mock_client_manager)
        state = await svc.submit_2fa("wrong")
        assert state.status == LoginStatus.ERROR

    async def test_refresh_qr(self, mock_client_manager):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock(side_effect=asyncio.CancelledError)
        qr_login.recreate = AsyncMock()
        mock_client_manager.client.qr_login = AsyncMock(return_value=qr_login)
        svc = QRLoginService(mock_client_manager)
        await svc.start()
        state = await svc.refresh_qr()
        assert state.status == LoginStatus.WAITING
        qr_login.recreate.assert_called_once()

    def test_reset(self, mock_client_manager):
        svc = QRLoginService(mock_client_manager)
        svc._state.status = LoginStatus.ERROR
        svc.reset()
        assert svc.state.status == LoginStatus.IDLE
