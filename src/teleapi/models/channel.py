from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Channel(SQLModel, table=True):
    __tablename__ = "channels"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    username: str = Field(index=True)
    title: str = ""
    enabled: bool = True
    last_message_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
