from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from teleapi.auth import verify_api_key
from teleapi.database import get_session
from teleapi.models.channel import Channel
from teleapi.models.message import Message

router = APIRouter(prefix="/api", tags=["channels"], dependencies=[Depends(verify_api_key)])


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
    return [
        {
            "id": ch.id,
            "telegram_id": ch.telegram_id,
            "username": ch.username,
            "title": ch.title,
            "enabled": ch.enabled,
            "last_message_id": ch.last_message_id,
            "message_count": count,
            "created_at": ch.created_at.isoformat(),
            "updated_at": ch.updated_at.isoformat(),
        }
        for ch, count in results
    ]


@router.get("/channels/{channel_id}")
async def get_channel(channel_id: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Channel).where((Channel.id == channel_id) | (Channel.username == channel_id))
    channel = (await session.execute(stmt)).scalar_one_or_none()
    if not channel:
        return JSONResponse({"error": "Channel not found"}, status_code=404)

    count_stmt = select(func.count(Message.id)).where(Message.channel_id == channel.id)
    message_count = (await session.execute(count_stmt)).scalar() or 0

    return {
        "id": channel.id,
        "telegram_id": channel.telegram_id,
        "username": channel.username,
        "title": channel.title,
        "enabled": channel.enabled,
        "last_message_id": channel.last_message_id,
        "message_count": message_count,
        "created_at": channel.created_at.isoformat(),
        "updated_at": channel.updated_at.isoformat(),
    }
