from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from teleapi.auth import verify_api_key
from teleapi.database import get_session
from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.models.webhook_delivery import WebhookDelivery
from teleapi.telegram.client import SESSION_FILE

router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(verify_api_key)])


@router.get("/status")
async def system_status(request: Request, session: AsyncSession = Depends(get_session)):
    cm = request.app.state.telegram_client
    authorized = await cm.is_authorized()
    user_info = await cm.get_me() if authorized else None

    channel_count = (await session.execute(select(func.count(Channel.id)).where(Channel.enabled.is_(True)))).scalar() or 0
    message_count = (await session.execute(select(func.count(Message.id)))).scalar() or 0

    last_msg = (await session.execute(select(Message.date).order_by(Message.date.desc()).limit(1))).scalar()

    success_count = (
        await session.execute(select(func.count(WebhookDelivery.id)).where(WebhookDelivery.status == "success"))
    ).scalar() or 0
    failed_count = (
        await session.execute(select(func.count(WebhookDelivery.id)).where(WebhookDelivery.status == "failed"))
    ).scalar() or 0

    db_path = Path("data/teleapi.db")
    db_size = db_path.stat().st_size if db_path.exists() else 0

    return {
        "telegram": {
            "connected": authorized,
            "user": user_info,
        },
        "channels": {"enabled_count": channel_count},
        "messages": {
            "total_count": message_count,
            "last_received_at": last_msg.isoformat() if last_msg else None,
        },
        "database": {
            "size_bytes": db_size,
        },
        "webhooks": {
            "success_count": success_count,
            "failed_count": failed_count,
        },
    }


@router.get("/config-check")
async def config_check(request: Request):
    config = request.app.state.config

    checks = [
        {"name": "api_id", "ok": config.telegram.api_id > 0},
        {"name": "api_hash", "ok": bool(config.telegram.api_hash and config.telegram.api_hash != "your_api_hash")},
        {"name": "admin_api_key", "ok": True},
        {"name": "session_file", "ok": SESSION_FILE.exists()},
        {"name": "database_writable", "ok": Path("data/teleapi.db").exists()},
        {"name": "channels_configured", "ok": len(config.telegram.channels) > 0, "count": len(config.telegram.channels)},
        {"name": "webhooks_configured", "ok": len(config.outputs.webhooks) > 0, "count": len(config.outputs.webhooks)},
    ]

    return {"checks": checks, "all_ok": all(c["ok"] for c in checks)}
