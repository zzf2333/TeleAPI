from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from teleapi.auth import verify_api_key
from teleapi.database import get_session
from teleapi.models.webhook_delivery import WebhookDelivery

router = APIRouter(prefix="/api", tags=["webhooks"], dependencies=[Depends(verify_api_key)])


@router.get("/webhook-deliveries")
async def list_webhook_deliveries(
    webhook_name: str | None = None,
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(WebhookDelivery)
    if webhook_name:
        stmt = stmt.where(WebhookDelivery.webhook_name == webhook_name)
    if status:
        stmt = stmt.where(WebhookDelivery.status == status)
    stmt = stmt.order_by(WebhookDelivery.created_at.desc()).limit(limit)

    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": d.id,
            "webhook_name": d.webhook_name,
            "event": d.event,
            "message_id": d.message_id,
            "status": d.status,
            "attempts": d.attempts,
            "response_status": d.response_status,
            "response_body": d.response_body,
            "error": d.error,
            "created_at": d.created_at.isoformat(),
        }
        for d in results
    ]
