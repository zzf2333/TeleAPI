from __future__ import annotations

import base64
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from teleapi.auth import verify_api_key
from teleapi.database import get_session
from teleapi.models.message import Message

router = APIRouter(prefix="/api", tags=["messages"], dependencies=[Depends(verify_api_key)])


def _encode_cursor(date: datetime, id: str) -> str:
    return base64.urlsafe_b64encode(f"{date.isoformat()}|{id}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
    date_str, id_str = decoded.split("|", 1)
    return datetime.fromisoformat(date_str), id_str


@router.get("/channels/{channel_id}/messages")
async def list_channel_messages(
    channel_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    before: str | None = None,
    after: str | None = None,
    keyword: str | None = None,
    type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Message).where(
        (Message.channel_id == channel_id) | (Message.channel_username == channel_id)
    )

    if cursor:
        cursor_date, cursor_id = _decode_cursor(cursor)
        stmt = stmt.where(
            (Message.date < cursor_date) | ((Message.date == cursor_date) & (Message.id < cursor_id))
        )

    if before:
        stmt = stmt.where(Message.date < datetime.fromisoformat(before))
    if after:
        stmt = stmt.where(Message.date > datetime.fromisoformat(after))
    if keyword:
        stmt = stmt.where(Message.text.contains(keyword))
    if type:
        stmt = stmt.where(Message.type == type)

    stmt = stmt.order_by(Message.date.desc(), Message.id.desc()).limit(limit + 1)
    results = (await session.execute(stmt)).scalars().all()

    has_more = len(results) > limit
    messages = results[:limit]

    next_cursor = None
    if has_more and messages:
        last = messages[-1]
        next_cursor = _encode_cursor(last.date, last.id)

    return {
        "data": [
            {
                "id": m.id,
                "telegram_message_id": m.telegram_message_id,
                "channel_id": m.channel_id,
                "channel_username": m.channel_username,
                "channel_title": m.channel_title,
                "type": m.type,
                "text": m.text,
                "date": m.date.isoformat(),
                "edit_date": m.edit_date.isoformat() if m.edit_date else None,
                "views": m.views,
                "forwards": m.forwards,
                "replies": m.replies,
                "url": m.url,
                "media": json.loads(m.media),
                "entities": json.loads(m.entities),
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "next_cursor": next_cursor,
    }


@router.get("/messages/{message_id}")
async def get_message(message_id: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Message).where(Message.id == message_id)
    message = (await session.execute(stmt)).scalar_one_or_none()
    if not message:
        return JSONResponse({"error": "Message not found"}, status_code=404)

    return {
        "id": message.id,
        "telegram_message_id": message.telegram_message_id,
        "channel_id": message.channel_id,
        "channel_username": message.channel_username,
        "channel_title": message.channel_title,
        "type": message.type,
        "text": message.text,
        "date": message.date.isoformat(),
        "edit_date": message.edit_date.isoformat() if message.edit_date else None,
        "views": message.views,
        "forwards": message.forwards,
        "replies": message.replies,
        "url": message.url,
        "media": json.loads(message.media),
        "entities": json.loads(message.entities),
        "raw": json.loads(message.raw),
        "created_at": message.created_at.isoformat(),
    }
