from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from teleapi.database import init_engine, init_db, get_session, close_db
import teleapi.database as _db


pytestmark = pytest.mark.db


class TestDatabaseLifecycle:
    async def test_init_engine_creates_engine(self):
        init_engine("sqlite+aiosqlite://")
        assert _db._engine is not None
        assert _db._async_session_factory is not None
        await _db._engine.dispose()

    async def test_init_db_creates_tables(self):
        init_engine("sqlite+aiosqlite://")
        await init_db()
        async with _db._engine.begin() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = {r[0] for r in result.fetchall()}
        assert "channels" in tables
        assert "messages" in tables
        await _db._engine.dispose()

    async def test_get_session_returns_async_session(self):
        init_engine("sqlite+aiosqlite://")
        await init_db()
        gen = get_session()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass
        await _db._engine.dispose()

    async def test_wal_mode_enabled(self):
        init_engine("sqlite+aiosqlite://")
        await init_db()
        async with _db._engine.begin() as conn:
            result = await conn.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
        assert mode in ("wal", "memory")
        await _db._engine.dispose()

    async def test_close_db_disposes_engine(self):
        init_engine("sqlite+aiosqlite://")
        await init_db()
        await close_db()
        assert _db._engine is not None
