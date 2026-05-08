from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from telethon.errors import (
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    FloodWaitError,
)

from teleapi.telegram.login import PhoneLoginService, LoginStatus


pytestmark = pytest.mark.service


class TestPhoneLoginService:
    async def test_send_code_success(self, mock_client_manager):
        result = MagicMock()
        result.phone_code_hash = "hash123"
        mock_client_manager.client.send_code_request = AsyncMock(return_value=result)
        svc = PhoneLoginService(mock_client_manager)
        state = await svc.send_code("+8613800138000")
        assert state.status == LoginStatus.CODE_SENT
        assert state.phone_code_hash == "hash123"

    async def test_send_code_invalid_phone(self, mock_client_manager):
        mock_client_manager.client.send_code_request = AsyncMock(
            side_effect=PhoneNumberInvalidError(request=None)
        )
        svc = PhoneLoginService(mock_client_manager)
        state = await svc.send_code("badphone")
        assert state.status == LoginStatus.ERROR
        assert "手机号格式无效" in state.error

    async def test_send_code_flood(self, mock_client_manager):
        err = FloodWaitError(request=None, capture=0)
        err.seconds = 60
        mock_client_manager.client.send_code_request = AsyncMock(side_effect=err)
        svc = PhoneLoginService(mock_client_manager)
        state = await svc.send_code("+8613800138000")
        assert state.status == LoginStatus.ERROR
        assert "请求过于频繁" in state.error

    async def test_verify_code_success(self, mock_client_manager, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        svc = PhoneLoginService(mock_client_manager)
        svc._state.phone = "+8613800138000"
        svc._state.phone_code_hash = "hash123"
        state = await svc.verify_code("12345")
        assert state.status == LoginStatus.SUCCESS

    async def test_verify_code_invalid(self, mock_client_manager):
        mock_client_manager.client.sign_in = AsyncMock(
            side_effect=PhoneCodeInvalidError(request=None)
        )
        svc = PhoneLoginService(mock_client_manager)
        svc._state.phone = "+8613800138000"
        svc._state.phone_code_hash = "hash123"
        state = await svc.verify_code("wrong")
        assert state.status == LoginStatus.ERROR
        assert "验证码错误" in state.error

    async def test_verify_code_expired(self, mock_client_manager):
        mock_client_manager.client.sign_in = AsyncMock(
            side_effect=PhoneCodeExpiredError(request=None)
        )
        svc = PhoneLoginService(mock_client_manager)
        svc._state.phone = "+8613800138000"
        svc._state.phone_code_hash = "hash123"
        state = await svc.verify_code("12345")
        assert state.status == LoginStatus.EXPIRED
        assert "验证码已过期" in state.error

    async def test_verify_code_2fa_required(self, mock_client_manager):
        mock_client_manager.client.sign_in = AsyncMock(
            side_effect=SessionPasswordNeededError(request=None)
        )
        svc = PhoneLoginService(mock_client_manager)
        svc._state.phone = "+8613800138000"
        svc._state.phone_code_hash = "hash123"
        state = await svc.verify_code("12345")
        assert state.status == LoginStatus.TWO_FA_REQUIRED

    async def test_verify_code_flood(self, mock_client_manager):
        err = FloodWaitError(request=None, capture=0)
        err.seconds = 120
        mock_client_manager.client.sign_in = AsyncMock(side_effect=err)
        svc = PhoneLoginService(mock_client_manager)
        svc._state.phone = "+8613800138000"
        svc._state.phone_code_hash = "hash123"
        state = await svc.verify_code("12345")
        assert state.status == LoginStatus.ERROR
        assert "请求过于频繁" in state.error

    async def test_submit_2fa_success(self, mock_client_manager, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        svc = PhoneLoginService(mock_client_manager)
        state = await svc.submit_2fa("password123")
        assert state.status == LoginStatus.SUCCESS

    async def test_submit_2fa_failure(self, mock_client_manager):
        mock_client_manager.client.sign_in = AsyncMock(side_effect=RuntimeError("bad"))
        svc = PhoneLoginService(mock_client_manager)
        state = await svc.submit_2fa("wrong")
        assert state.status == LoginStatus.ERROR

    def test_reset(self, mock_client_manager):
        svc = PhoneLoginService(mock_client_manager)
        svc._state.status = LoginStatus.CODE_SENT
        svc._state.phone = "+86xxx"
        svc.reset()
        assert svc.state.status == LoginStatus.IDLE
        assert svc.state.phone == ""
