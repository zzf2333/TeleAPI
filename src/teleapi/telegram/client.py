from __future__ import annotations

import logging
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger("teleapi.telegram")

SESSION_FILE = Path("data/session.key")


class TelegramClientManager:

    def __init__(self, api_id: int, api_hash: str, session_name: str = "teleapi"):
        self._api_id = api_id
        self._api_hash = api_hash
        self._session_name = session_name
        self._client: TelegramClient | None = None

    @property
    def client(self) -> TelegramClient:
        if self._client is None:
            raise RuntimeError("Telegram client not connected")
        return self._client

    async def connect(self):
        session_string = ""
        if SESSION_FILE.exists():
            session_string = SESSION_FILE.read_text().strip()
            logger.info("Loaded existing session from %s", SESSION_FILE)

        self._client = TelegramClient(
            StringSession(session_string),
            self._api_id,
            self._api_hash,
        )
        await self._client.connect()

        if await self._client.is_user_authorized():
            me = await self._client.get_me()
            logger.info("Telegram session restored: %s (id=%s)", me.first_name, me.id)
        else:
            logger.info("Telegram session not authorized, QR login required")

    async def is_authorized(self) -> bool:
        if self._client is None:
            return False
        return await self._client.is_user_authorized()

    async def get_me(self) -> dict | None:
        if not await self.is_authorized():
            return None
        me = await self._client.get_me()
        return {
            "id": me.id,
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "username": me.username or "",
            "phone": me.phone or "",
        }

    def save_session(self):
        session_string = self._client.session.save()
        tmp = SESSION_FILE.with_suffix(".tmp")
        tmp.write_text(session_string)
        tmp.rename(SESSION_FILE)
        logger.info("Session saved to %s", SESSION_FILE)

    async def disconnect(self):
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            logger.info("Telegram client disconnected")

    async def logout(self):
        if self._client:
            await self._client.log_out()
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        logger.info("Telegram session cleared")
