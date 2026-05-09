from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from telethon import TelegramClient

from teleapi.config import TelegramChannelConfig
from teleapi.models.channel import Channel

logger = logging.getLogger("teleapi.telegram.channel_manager")


class ChannelManager:

    def __init__(self, client: TelegramClient):
        self._client = client
        self._entities: dict[str, object] = {}

    async def resolve_channels(
        self,
        channel_configs: list[TelegramChannelConfig],
        session: AsyncSession,
    ) -> list[Channel]:
        resolved = []
        for cfg in channel_configs:
            if not cfg.enabled:
                continue
            try:
                entity = await self._client.get_entity(cfg.username)
                self._entities[cfg.username] = entity

                stmt = select(Channel).where(Channel.telegram_id == entity.id)
                channel = (await session.execute(stmt)).scalar_one_or_none()

                if channel:
                    channel.username = cfg.username
                    channel.title = getattr(entity, "title", cfg.username)
                    channel.enabled = cfg.enabled
                    channel.updated_at = datetime.now(timezone.utc)
                else:
                    channel = Channel(
                        telegram_id=entity.id,
                        username=cfg.username,
                        title=getattr(entity, "title", cfg.username),
                        enabled=cfg.enabled,
                    )
                    session.add(channel)

                await session.commit()
                await session.refresh(channel)
                resolved.append(channel)
                logger.info("Resolved channel: %s (id=%s)", cfg.username, entity.id)
            except Exception as e:
                logger.error("Failed to resolve channel %s: %s", cfg.username, e)

        return resolved

    async def resolve_single_channel(
        self,
        username: str,
        session: AsyncSession,
    ) -> Channel:
        try:
            entity = await self._client.get_entity(username)
        except Exception as e:
            raise ValueError(f"无法在 Telegram 上解析 '{username}': {e}")

        self._entities[username] = entity

        stmt = select(Channel).where(Channel.telegram_id == entity.id)
        channel = (await session.execute(stmt)).scalar_one_or_none()

        if channel:
            channel.username = username
            channel.title = getattr(entity, "title", username)
            channel.enabled = True
            channel.updated_at = datetime.now(timezone.utc)
        else:
            channel = Channel(
                telegram_id=entity.id,
                username=username,
                title=getattr(entity, "title", username),
                enabled=True,
            )
            session.add(channel)

        await session.commit()
        await session.refresh(channel)
        return channel

    def get_entity(self, username: str):
        return self._entities.get(username)

    def remove_entity(self, username: str):
        self._entities.pop(username, None)

    def get_all_entities(self) -> list:
        return list(self._entities.values())
