from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Column, Field, SQLModel, Text


class WebhookDelivery(SQLModel, table=True):
    __tablename__ = "webhook_deliveries"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    webhook_name: str = Field(index=True)
    event: str = ""
    message_id: str = Field(foreign_key="messages.id")
    status: str = Field(default="pending", index=True)
    attempts: int = 0
    response_status: Optional[int] = None
    response_body: Optional[str] = Field(default=None, sa_column=Column(Text))
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
