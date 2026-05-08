from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import select

from teleapi.config import FilterConfig, RetryConfig, WebhookConfig
from teleapi.models.webhook_delivery import WebhookDelivery
from teleapi.services.filter import FilterEngine
from teleapi.services.webhook import WebhookDispatcher


pytestmark = pytest.mark.service


def _payload():
    return {
        "message_id": "msg1",
        "channel_id": "ch1",
        "channel_username": "testch",
        "channel_title": "Test",
        "telegram_message_id": 100,
        "type": "text",
        "text": "hello",
        "date": "2025-01-01T00:00:00+00:00",
        "url": "https://t.me/testch/100",
    }


def _webhook(**kwargs):
    defaults = {
        "name": "wh1",
        "url": "https://example.com/hook",
        "enabled": True,
        "events": ["message.created"],
        "channels": [],
        "filters": [],
        "secret": "",
        "retry": RetryConfig(max_attempts=1, backoff_seconds=[0]),
    }
    defaults.update(kwargs)
    return WebhookConfig(**defaults)


class TestWebhookFiltering:
    async def test_disabled_webhook_skipped(self, async_session_factory):
        wh = _webhook(enabled=False)
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)
        dispatcher._deliver_with_retry = AsyncMock()
        await dispatcher.on_message_created(_payload())
        dispatcher._deliver_with_retry.assert_not_called()
        await dispatcher.close()

    async def test_wrong_event_skipped(self, async_session_factory):
        wh = _webhook(events=["message.updated"])
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)
        dispatcher._deliver_with_retry = AsyncMock()
        await dispatcher.on_message_created(_payload())
        dispatcher._deliver_with_retry.assert_not_called()
        await dispatcher.close()

    async def test_wrong_channel_skipped(self, async_session_factory):
        wh = _webhook(channels=["otherch"])
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)
        dispatcher._deliver_with_retry = AsyncMock()
        await dispatcher.on_message_created(_payload())
        dispatcher._deliver_with_retry.assert_not_called()
        await dispatcher.close()

    async def test_filter_no_match_skipped(self, async_session_factory):
        f = FilterConfig(name="f1", include_keywords=["bye"])
        wh = _webhook(filters=["f1"])
        dispatcher = WebhookDispatcher([wh], FilterEngine([f]), async_session_factory)
        dispatcher._deliver_with_retry = AsyncMock()
        await dispatcher.on_message_created(_payload())
        dispatcher._deliver_with_retry.assert_not_called()
        await dispatcher.close()


class TestWebhookDelivery:
    async def test_success_200(self, async_session_factory):
        wh = _webhook()
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(return_value=mock_resp)
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        async with async_session_factory() as session:
            deliveries = (await session.execute(select(WebhookDelivery))).scalars().all()
        assert len(deliveries) == 1
        assert deliveries[0].status == "success"
        await dispatcher.close()

    async def test_retry_then_success(self, async_session_factory):
        wh = _webhook(retry=RetryConfig(max_attempts=2, backoff_seconds=[0]))
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.text = "error"
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.text = "ok"

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(side_effect=[fail_resp, ok_resp])
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        async with async_session_factory() as session:
            d = (await session.execute(select(WebhookDelivery))).scalar_one()
        assert d.status == "success"
        assert d.attempts == 2
        await dispatcher.close()

    async def test_retry_exhausted_failed(self, async_session_factory):
        wh = _webhook(retry=RetryConfig(max_attempts=2, backoff_seconds=[0]))
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.text = "error"

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(return_value=fail_resp)
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        async with async_session_factory() as session:
            d = (await session.execute(select(WebhookDelivery))).scalar_one()
        assert d.status == "failed"
        await dispatcher.close()

    async def test_network_error_retry(self, async_session_factory):
        wh = _webhook(retry=RetryConfig(max_attempts=2, backoff_seconds=[0]))
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.text = "ok"

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(side_effect=[ConnectionError("fail"), ok_resp])
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        async with async_session_factory() as session:
            d = (await session.execute(select(WebhookDelivery))).scalar_one()
        assert d.status == "success"
        await dispatcher.close()


class TestWebhookHMAC:
    async def test_with_secret(self, async_session_factory):
        wh = _webhook(secret="mysecret")
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        captured_headers = {}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"

        async def capture_post(url, content, headers):
            captured_headers.update(headers)
            return mock_resp

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(side_effect=capture_post)
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        assert "X-TeleAPI-Signature" in captured_headers
        assert captured_headers["X-TeleAPI-Signature"].startswith("sha256=")
        assert "X-TeleAPI-Timestamp" in captured_headers
        await dispatcher.close()

    async def test_without_secret(self, async_session_factory):
        wh = _webhook(secret="")
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        captured_headers = {}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"

        async def capture_post(url, content, headers):
            captured_headers.update(headers)
            return mock_resp

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(side_effect=capture_post)
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        assert "X-TeleAPI-Signature" not in captured_headers
        await dispatcher.close()


class TestWebhookPersistence:
    async def test_response_body_truncated(self, async_session_factory):
        wh = _webhook()
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "x" * 2000

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(return_value=mock_resp)
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        async with async_session_factory() as session:
            d = (await session.execute(select(WebhookDelivery))).scalar_one()
        assert len(d.response_body) == 1000
        await dispatcher.close()

    async def test_error_truncated(self, async_session_factory):
        wh = _webhook(retry=RetryConfig(max_attempts=1, backoff_seconds=[0]))
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)

        dispatcher._http = AsyncMock()
        dispatcher._http.post = AsyncMock(side_effect=RuntimeError("e" * 1000))
        dispatcher._http.aclose = AsyncMock()
        await dispatcher._deliver_with_retry(wh, _payload())

        async with async_session_factory() as session:
            d = (await session.execute(select(WebhookDelivery))).scalar_one()
        assert len(d.error) <= 500
        await dispatcher.close()

    async def test_close_releases_http(self, async_session_factory):
        wh = _webhook()
        dispatcher = WebhookDispatcher([wh], FilterEngine([]), async_session_factory)
        await dispatcher.close()
