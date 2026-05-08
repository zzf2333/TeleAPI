from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, text


_engine = None
_async_session_factory = None


def init_engine(database_url: str):
    global _engine, _async_session_factory
    _engine = create_async_engine(database_url, echo=False)
    _async_session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL"))


async def get_session() -> AsyncSession:
    async with _async_session_factory() as session:
        yield session


async def close_db():
    if _engine:
        await _engine.dispose()
