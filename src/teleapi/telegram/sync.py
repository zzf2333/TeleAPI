from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import select
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError

from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.models.sync_job import SyncJob
from teleapi.telegram.normalizer import normalize_message

logger = logging.getLogger("teleapi.telegram.sync")

BATCH_SIZE = 100


class HistorySyncService:

    def __init__(self, client: TelegramClient, session_factory):
        self._client = client
        self._session_factory = session_factory

    async def sync_channel(self, channel_id: str, entity, job_id: str, limit: int = 1000, force: bool = False):
        async with self._session_factory() as session:
            job = (await session.execute(select(SyncJob).where(SyncJob.id == job_id))).scalar_one()
            job.status = "running"
            job.total = limit
            job.started_at = datetime.now(timezone.utc)
            await session.commit()

            channel = (await session.execute(select(Channel).where(Channel.id == channel_id))).scalar_one()

        try:
            offset_id = 0
            if not force and channel.last_message_id:
                offset_id = channel.last_message_id

            synced = 0
            async for msg in self._client.iter_messages(
                entity,
                limit=limit,
                offset_id=offset_id,
                reverse=True if offset_id else False,
            ):
                if msg.action:
                    continue

                data = normalize_message(msg, channel.username, channel.title)
                data["channel_id"] = channel_id

                async with self._session_factory() as session:
                    existing = (
                        await session.execute(
                            select(Message.id).where(
                                Message.channel_id == channel_id,
                                Message.telegram_message_id == data["telegram_message_id"],
                            )
                        )
                    ).scalar_one_or_none()

                    if not existing:
                        session.add(Message(**data))
                        await session.commit()

                synced += 1

                if synced % BATCH_SIZE == 0:
                    async with self._session_factory() as session:
                        job = (await session.execute(select(SyncJob).where(SyncJob.id == job_id))).scalar_one()
                        job.synced = synced
                        await session.commit()
                    await asyncio.sleep(1)

            async with self._session_factory() as session:
                job = (await session.execute(select(SyncJob).where(SyncJob.id == job_id))).scalar_one()
                job.status = "success"
                job.synced = synced
                job.finished_at = datetime.now(timezone.utc)
                await session.commit()

                channel = (await session.execute(select(Channel).where(Channel.id == channel_id))).scalar_one()
                last_msg = (
                    await session.execute(
                        select(Message.telegram_message_id)
                        .where(Message.channel_id == channel_id)
                        .order_by(Message.telegram_message_id.desc())
                        .limit(1)
                    )
                ).scalar()
                if last_msg:
                    channel.last_message_id = last_msg
                    channel.updated_at = datetime.now(timezone.utc)
                    await session.commit()

            logger.info("Sync complete for channel %s: %d messages", channel.username, synced)

        except FloodWaitError as e:
            logger.warning("FloodWait: sleeping %d seconds", e.seconds)
            await asyncio.sleep(e.seconds + 1)
            await self.sync_channel(channel_id, entity, job_id, limit, force)

        except ChannelPrivateError:
            async with self._session_factory() as session:
                job = (await session.execute(select(SyncJob).where(SyncJob.id == job_id))).scalar_one()
                job.status = "failed"
                job.error = "Channel is private or not accessible"
                job.finished_at = datetime.now(timezone.utc)
                await session.commit()
            logger.error("Channel %s is private or not accessible", channel.username)

        except Exception as e:
            async with self._session_factory() as session:
                job = (await session.execute(select(SyncJob).where(SyncJob.id == job_id))).scalar_one()
                job.status = "failed"
                job.error = str(e)[:500]
                job.finished_at = datetime.now(timezone.utc)
                await session.commit()
            logger.error("Sync failed for channel %s: %s", channel.username, e)
