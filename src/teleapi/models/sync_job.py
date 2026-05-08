from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class SyncJob(SQLModel, table=True):
    __tablename__ = "sync_jobs"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    channel_id: str = Field(foreign_key="channels.id", index=True)
    status: str = Field(default="pending", index=True)
    total: Optional[int] = None
    synced: int = 0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
