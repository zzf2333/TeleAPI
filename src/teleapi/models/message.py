from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Column, Field, SQLModel, String, Text, UniqueConstraint


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("channel_id", "telegram_message_id", name="uq_channel_message"),
    )

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    telegram_message_id: int = Field(index=True)
    channel_id: str = Field(foreign_key="channels.id", index=True)
    channel_username: str = ""
    channel_title: str = ""
    type: str = "text"
    text: Optional[str] = Field(default=None, sa_column=Column(Text))
    date: datetime = Field(index=True)
    edit_date: Optional[datetime] = None
    views: Optional[int] = None
    forwards: Optional[int] = None
    replies: Optional[int] = None
    url: str = ""
    media: str = Field(default="[]", sa_column=Column(Text))
    entities: str = Field(default="[]", sa_column=Column(Text))
    raw: str = Field(default="{}", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
