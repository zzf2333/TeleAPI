from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from teleapi.telegram.login import LoginStatus


pytestmark = pytest.mark.api


class TestQRLoginAPI:
    async def test_start(self, client, test_app):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock()
        test_app.state.telegram_client.client.qr_login = AsyncMock(return_value=qr_login)
        resp = await client.post("/api/auth/qr-login")
        assert resp.status_code == 200
        assert resp.json()["status"] == "waiting"

    async def test_status(self, client):
        resp = await client.get("/api/auth/qr-login/status")
        assert resp.status_code == 200
        assert "status" in resp.json()

    async def test_refresh(self, client, test_app):
        qr_login = MagicMock()
        qr_login.url = "tg://login?token=abc"
        qr_login.wait = AsyncMock()
        test_app.state.telegram_client.client.qr_login = AsyncMock(return_value=qr_login)
        resp = await client.post("/api/auth/qr-login/refresh")
        assert resp.status_code == 200


class TestPhoneLoginAPI:
    async def test_send_code(self, client, test_app):
        result = MagicMock()
        result.phone_code_hash = "hash123"
        test_app.state.telegram_client.client.send_code_request = AsyncMock(return_value=result)
        resp = await client.post("/api/auth/phone-login/send-code", json={"phone": "+8613800138000"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "code_sent"

    async def test_send_code_empty_phone(self, client):
        resp = await client.post("/api/auth/phone-login/send-code", json={"phone": ""})
        assert resp.status_code == 400

    async def test_verify_code(self, client, test_app, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        test_app.state.phone_login_service._state.phone = "+86xxx"
        test_app.state.phone_login_service._state.phone_code_hash = "hash"
        resp = await client.post("/api/auth/phone-login/verify-code", json={"code": "12345"})
        assert resp.status_code == 200

    async def test_verify_code_empty(self, client):
        resp = await client.post("/api/auth/phone-login/verify-code", json={"code": ""})
        assert resp.status_code == 400

    async def test_phone_status(self, client):
        resp = await client.get("/api/auth/phone-login/status")
        assert resp.status_code == 200
        assert "status" in resp.json()


class TestTwoFAAPI:
    async def test_submit_2fa(self, client, test_app, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        resp = await client.post("/api/auth/2fa", json={"password": "pass123"})
        assert resp.status_code == 200

    async def test_submit_2fa_empty_password(self, client):
        resp = await client.post("/api/auth/2fa", json={"password": ""})
        assert resp.status_code == 400

    async def test_2fa_routes_to_phone_svc(self, client, test_app, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        test_app.state.phone_login_service._state.status = LoginStatus.TWO_FA_REQUIRED
        resp = await client.post("/api/auth/2fa", json={"password": "pass123"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestAuthStatusAPI:
    async def test_authorized(self, client):
        resp = await client.get("/api/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authorized"] is True
        assert "user" in data

    async def test_not_authorized(self, client, test_app):
        test_app.state.telegram_client._client.is_user_authorized = AsyncMock(return_value=False)
        resp = await client.get("/api/auth/status")
        data = resp.json()
        assert data["authorized"] is False


class TestLogoutAPI:
    async def test_logout(self, client, test_app, tmp_path, monkeypatch):
        monkeypatch.setattr("teleapi.telegram.client.SESSION_FILE", tmp_path / "session.key")
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged_out"


class TestSessionLoginAPI:
    async def test_success(self, client, test_app):
        test_app.state.telegram_client.import_session = AsyncMock(
            return_value={"id": 123, "first_name": "Test", "last_name": "", "username": "test", "phone": "+1234567890"}
        )
        resp = await client.post("/api/auth/session-login", json={"session_string": "valid_session"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["user"]["id"] == 123

    async def test_empty_string(self, client):
        resp = await client.post("/api/auth/session-login", json={"session_string": ""})
        assert resp.status_code == 400

    async def test_invalid_session(self, client, test_app):
        test_app.state.telegram_client.import_session = AsyncMock(
            side_effect=ValueError("Session 已失效或未授权，请提供有效的 Session")
        )
        resp = await client.post("/api/auth/session-login", json={"session_string": "bad_session"})
        assert resp.status_code == 400
        assert "error" in resp.json()


class TestAuthRequired:
    async def test_all_routes_need_auth(self, unauthed_client):
        routes = [
            ("POST", "/api/auth/qr-login"),
            ("GET", "/api/auth/qr-login/status"),
            ("POST", "/api/auth/qr-login/refresh"),
            ("POST", "/api/auth/phone-login/send-code"),
            ("GET", "/api/auth/phone-login/status"),
            ("POST", "/api/auth/session-login"),
            ("GET", "/api/auth/status"),
            ("POST", "/api/auth/logout"),
        ]
        for method, path in routes:
            if method == "GET":
                resp = await unauthed_client.get(path)
            else:
                resp = await unauthed_client.post(path, json={})
            assert resp.status_code == 401, f"{method} {path} should require auth"
