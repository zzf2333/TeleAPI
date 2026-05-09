from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, func, select

from teleapi.auth import verify_api_key
from teleapi.database import get_session
from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.models.sync_job import SyncJob

logger = logging.getLogger("teleapi.api.channels")

router = APIRouter(prefix="/api", tags=["channels"], dependencies=[Depends(verify_api_key)])


class AddChannelRequest(BaseModel):
    username: str
    sync_history: bool = False
    history_limit: int = 100


class UpdateChannelRequest(BaseModel):
    enabled: bool


def _channel_dict(ch: Channel, message_count: int = 0) -> dict:
    return {
        "id": ch.id,
        "telegram_id": ch.telegram_id,
        "username": ch.username,
        "title": ch.title,
        "enabled": ch.enabled,
        "last_message_id": ch.last_message_id,
        "message_count": message_count,
        "created_at": ch.created_at.isoformat(),
        "updated_at": ch.updated_at.isoformat(),
    }


async def _reload_listener(request: Request, session: AsyncSession):
    channel_manager = request.app.state.channel_manager
    listener = request.app.state.listener

    stmt = select(Channel).where(Channel.enabled.is_(True))
    enabled_channels = (await session.execute(stmt)).scalars().all()

    entities = []
    for ch in enabled_channels:
        entity = channel_manager.get_entity(ch.username)
        if entity:
            entities.append(entity)

    await listener.restart(entities)


@router.get("/channels")
async def list_channels(session: AsyncSession = Depends(get_session)):
    stmt = (
        select(
            Channel,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Channel.id == Message.channel_id)
        .group_by(Channel.id)
    )
    results = (await session.execute(stmt)).all()
    return [_channel_dict(ch, count) for ch, count in results]


@router.get("/channels/{channel_id}")
async def get_channel(channel_id: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Channel).where((Channel.id == channel_id) | (Channel.username == channel_id))
    channel = (await session.execute(stmt)).scalar_one_or_none()
    if not channel:
        return JSONResponse({"error": "Channel not found"}, status_code=404)

    count_stmt = select(func.count(Message.id)).where(Message.channel_id == channel.id)
    message_count = (await session.execute(count_stmt)).scalar() or 0

    return _channel_dict(channel, message_count)


@router.post("/channels", status_code=201)
async def add_channel(
    body: AddChannelRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    username = body.username.lstrip("@").strip()
    if not username:
        return JSONResponse({"error": "username 不能为空"}, status_code=400)

    telegram_client = request.app.state.telegram_client
    if not await telegram_client.is_authorized():
        return JSONResponse({"error": "Telegram 未登录，请先完成登录"}, status_code=503)

    existing = (
        await session.execute(select(Channel).where(Channel.username == username))
    ).scalar_one_or_none()
    if existing:
        return JSONResponse({"error": f"频道 @{username} 已存在"}, status_code=409)

    channel_manager = request.app.state.channel_manager

    try:
        channel = await channel_manager.resolve_single_channel(username, session)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    if body.sync_history:
        job = SyncJob(channel_id=channel.id, total=body.history_limit)
        session.add(job)
        await session.commit()
        await session.refresh(job)

        sync_service = request.app.state.sync_service
        entity = channel_manager.get_entity(username)
        if entity:
            asyncio.create_task(
                sync_service.sync_channel(channel.id, entity, job.id, body.history_limit)
            )

    await _reload_listener(request, session)

    count_stmt = select(func.count(Message.id)).where(Message.channel_id == channel.id)
    message_count = (await session.execute(count_stmt)).scalar() or 0

    return _channel_dict(channel, message_count)


@router.put("/channels/{channel_id}")
async def update_channel(
    channel_id: str,
    body: UpdateChannelRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    from datetime import datetime, timezone

    stmt = select(Channel).where((Channel.id == channel_id) | (Channel.username == channel_id))
    channel = (await session.execute(stmt)).scalar_one_or_none()
    if not channel:
        return JSONResponse({"error": "Channel not found"}, status_code=404)

    channel.enabled = body.enabled
    channel.updated_at = datetime.now(timezone.utc)

    channel_manager = request.app.state.channel_manager

    if body.enabled:
        if not channel_manager.get_entity(channel.username):
            try:
                await channel_manager.resolve_single_channel(channel.username, session)
            except ValueError:
                pass
    else:
        channel_manager.remove_entity(channel.username)

    await session.commit()
    await session.refresh(channel)

    await _reload_listener(request, session)

    count_stmt = select(func.count(Message.id)).where(Message.channel_id == channel.id)
    message_count = (await session.execute(count_stmt)).scalar() or 0

    return _channel_dict(channel, message_count)


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Channel).where((Channel.id == channel_id) | (Channel.username == channel_id))
    channel = (await session.execute(stmt)).scalar_one_or_none()
    if not channel:
        return JSONResponse({"error": "Channel not found"}, status_code=404)

    channel_manager = request.app.state.channel_manager
    channel_manager.remove_entity(channel.username)

    await session.execute(delete(Message).where(Message.channel_id == channel.id))
    await session.execute(delete(SyncJob).where(SyncJob.channel_id == channel.id))
    await session.delete(channel)
    await session.commit()

    await _reload_listener(request, session)

    return {"ok": True}
