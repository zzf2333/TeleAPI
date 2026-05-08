from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time

import httpx

from teleapi.config import WebhookConfig
from teleapi.models.webhook_delivery import WebhookDelivery
from teleapi.services.filter import FilterEngine

logger = logging.getLogger("teleapi.services.webhook")


class WebhookDispatcher:

    def __init__(
        self,
        webhooks: list[WebhookConfig],
        filter_engine: FilterEngine,
        session_factory,
    ):
        self._webhooks = webhooks
        self._filter = filter_engine
        self._session_factory = session_factory
        self._http = httpx.AsyncClient(timeout=10)

    async def on_message_created(self, payload: dict):
        for webhook in self._webhooks:
            if not webhook.enabled:
                continue
            if "message.created" not in webhook.events:
                continue
            if webhook.channels and payload.get("channel_username") not in webhook.channels:
                continue
            if webhook.filters and not self._filter.apply_filters(payload, webhook.filters):
                continue

            asyncio.create_task(self._deliver_with_retry(webhook, payload))

    async def _deliver_with_retry(self, webhook: WebhookConfig, payload: dict):
        body = json.dumps(
            {
                "event": "message.created",
                "channel": {
                    "id": payload.get("channel_id", ""),
                    "username": payload.get("channel_username", ""),
                    "title": payload.get("channel_title", ""),
                },
                "message": {
                    "id": payload.get("message_id", ""),
                    "telegram_message_id": payload.get("telegram_message_id"),
                    "text": payload.get("text", ""),
                    "type": payload.get("type", "text"),
                    "date": payload.get("date"),
                    "url": payload.get("url", ""),
                },
            },
            ensure_ascii=False,
        )

        timestamp = str(int(time.time()))
        headers = {"Content-Type": "application/json"}

        if webhook.secret:
            sig_payload = f"{timestamp}.{body}"
            signature = hmac.new(webhook.secret.encode(), sig_payload.encode(), hashlib.sha256).hexdigest()
            headers["X-TeleAPI-Signature"] = f"sha256={signature}"
            headers["X-TeleAPI-Timestamp"] = timestamp

        max_attempts = webhook.retry.max_attempts
        backoffs = webhook.retry.backoff_seconds

        delivery = WebhookDelivery(
            webhook_name=webhook.name,
            event="message.created",
            message_id=payload.get("message_id", ""),
            status="pending",
        )

        for attempt in range(max_attempts):
            delivery.attempts = attempt + 1
            try:
                resp = await self._http.post(webhook.url, content=body, headers=headers)
                delivery.response_status = resp.status_code

                if 200 <= resp.status_code < 300:
                    delivery.status = "success"
                    delivery.response_body = resp.text[:1000]
                    logger.info("Webhook %s delivered to %s (HTTP %d)", webhook.name, webhook.url, resp.status_code)
                    break
                else:
                    delivery.response_body = resp.text[:1000]
                    delivery.error = f"HTTP {resp.status_code}"
                    logger.warning(
                        "Webhook %s delivery failed: HTTP %d (attempt %d/%d)",
                        webhook.name, resp.status_code, attempt + 1, max_attempts,
                    )

            except Exception as e:
                delivery.error = str(e)[:500]
                logger.warning(
                    "Webhook %s delivery error: %s (attempt %d/%d)",
                    webhook.name, e, attempt + 1, max_attempts,
                )

            if attempt < max_attempts - 1:
                backoff = backoffs[attempt] if attempt < len(backoffs) else backoffs[-1]
                await asyncio.sleep(backoff)
        else:
            delivery.status = "failed"

        async with self._session_factory() as session:
            session.add(delivery)
            await session.commit()

    async def close(self):
        await self._http.aclose()
