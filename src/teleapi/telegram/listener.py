from __future__ import annotations

import logging

from telethon import TelegramClient, events
from sqlmodel import select

from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.services.event import EventDispatcher
from teleapi.telegram.normalizer import normalize_message

logger = logging.getLogger("teleapi.telegram.listener")


class RealtimeListener:

    def __init__(
        self,
        client: TelegramClient,
        session_factory,
        event_dispatcher: EventDispatcher,
    ):
        self._client = client
        self._session_factory = session_factory
        self._dispatcher = event_dispatcher
        self._handler = None

    async def start(self, channel_entities: list):
        if not channel_entities:
            logger.info("No channels to listen to")
            return

        entity_ids = [e.id for e in channel_entities]

        @self._client.on(events.NewMessage(chats=entity_ids))
        async def on_new_message(event):
            await self._handle_new_message(event)

        self._handler = on_new_message
        logger.info("Realtime listener started for %d channels", len(entity_ids))

    async def _handle_new_message(self, event):
        msg = event.message
        if msg.action:
            return

        try:
            chat = await event.get_chat()
            username = getattr(chat, "username", "") or ""
            title = getattr(chat, "title", "") or ""

            async with self._session_factory() as session:
                channel = (
                    await session.execute(select(Channel).where(Channel.telegram_id == chat.id))
                ).scalar_one_or_none()

                if not channel:
                    logger.warning("Received message from unknown channel: %s", username)
                    return

                existing = (
                    await session.execute(
                        select(Message.id).where(
                            Message.channel_id == channel.id,
                            Message.telegram_message_id == msg.id,
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    return

                data = normalize_message(msg, username, title)
                data["channel_id"] = channel.id
                message = Message(**data)
                session.add(message)
                await session.commit()
                await session.refresh(message)

                logger.info("New message from %s: %s", username, (msg.message or "")[:80])

                await self._dispatcher.dispatch("message.created", {
                    "message_id": message.id,
                    "channel_id": channel.id,
                    "channel_username": username,
                    "channel_title": title,
                    "telegram_message_id": msg.id,
                    "type": data["type"],
                    "text": data["text"],
                    "date": data["date"].isoformat() if data["date"] else None,
                    "url": data["url"],
                })

        except Exception as e:
            logger.error("Error handling new message: %s", e)

    async def stop(self):
        if self._handler:
            self._client.remove_event_handler(self._handler)
            self._handler = None
            logger.info("Realtime listener stopped")
