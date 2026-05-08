from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from teleapi.config import TeleAPIConfig
from teleapi.models.channel import Channel
from teleapi.models.message import Message
from teleapi.models.sync_job import SyncJob

TEST_API_KEY = "test_secure_key_for_testing_1234"


@pytest.fixture
def minimal_config_dict():
    return {
        "telegram": {"api_id": 123456, "api_hash": "abc123def456"},
        "security": {"admin_api_key": TEST_API_KEY},
    }


@pytest.fixture
def test_config(minimal_config_dict):
    minimal_config_dict["database"] = {"url": "sqlite+aiosqlite://"}
    return TeleAPIConfig(**minimal_config_dict)


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def async_session_factory(async_engine):
    return sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(async_session_factory):
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def seed_channel(db_session):
    ch = Channel(
        id=uuid4().hex,
        telegram_id=1001234567,
        username="testchannel",
        title="Test Channel",
        enabled=True,
    )
    db_session.add(ch)
    await db_session.commit()
    await db_session.refresh(ch)
    return ch


@pytest.fixture
async def seed_messages(db_session, seed_channel):
    base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    messages = []
    for i in range(25):
        m = Message(
            id=uuid4().hex,
            telegram_message_id=1000 + i,
            channel_id=seed_channel.id,
            channel_username=seed_channel.username,
            channel_title=seed_channel.title,
            type="text" if i % 3 != 0 else "photo",
            text=f"Test message {i}",
            date=base_date + timedelta(hours=i),
            url=f"https://t.me/{seed_channel.username}/{1000 + i}",
        )
        db_session.add(m)
        messages.append(m)
    await db_session.commit()
    for m in messages:
        await db_session.refresh(m)
    return messages


@pytest.fixture
async def seed_sync_job(db_session, seed_channel):
    job = SyncJob(channel_id=seed_channel.id, total=1000)
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
def mock_telegram_client():
    client = AsyncMock()
    client.is_connected = MagicMock(return_value=True)
    client.is_user_authorized = AsyncMock(return_value=True)
    me = MagicMock()
    me.id = 12345
    me.first_name = "Test"
    me.last_name = "User"
    me.username = "testuser"
    me.phone = "+1234567890"
    client.get_me = AsyncMock(return_value=me)
    client.qr_login = AsyncMock()
    client.send_code_request = AsyncMock()
    client.sign_in = AsyncMock()
    client.log_out = AsyncMock()
    client.disconnect = AsyncMock()
    client.connect = AsyncMock()
    client.get_entity = AsyncMock()
    client.iter_messages = MagicMock()
    client.on = MagicMock(side_effect=lambda event: lambda f: f)
    client.remove_event_handler = MagicMock()
    session = MagicMock()
    session.save.return_value = "session_string_data"
    client.session = session
    return client


@pytest.fixture
def mock_client_manager(mock_telegram_client):
    from teleapi.telegram.client import TelegramClientManager
    cm = TelegramClientManager(api_id=123456, api_hash="abc123def456")
    cm._client = mock_telegram_client
    return cm


@pytest.fixture
def test_app(test_config, async_session_factory, mock_client_manager):
    from teleapi.api.auth_routes import router as auth_router
    from teleapi.api.channels import router as channels_router
    from teleapi.api.messages import router as messages_router
    from teleapi.api.sync import router as sync_router
    from teleapi.api.webhooks import router as webhooks_router
    from teleapi.api.system import router as system_router
    from teleapi.database import get_session
    from teleapi.telegram.login import QRLoginService, PhoneLoginService
    from teleapi.telegram.channel_manager import ChannelManager
    from teleapi.telegram.sync import HistorySyncService
    from teleapi.telegram.listener import RealtimeListener
    from teleapi.services.event import EventDispatcher

    app = FastAPI()

    async def override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    app.include_router(auth_router)
    app.include_router(channels_router)
    app.include_router(messages_router)
    app.include_router(sync_router)
    app.include_router(webhooks_router)
    app.include_router(system_router)

    app.state.config = test_config
    app.state.telegram_client = mock_client_manager
    app.state.login_service = QRLoginService(mock_client_manager)
    app.state.phone_login_service = PhoneLoginService(mock_client_manager)
    app.state.channel_manager = ChannelManager(mock_client_manager.client)
    app.state.sync_service = HistorySyncService(mock_client_manager.client, async_session_factory)
    app.state.event_dispatcher = EventDispatcher()
    app.state.listener = RealtimeListener(mock_client_manager.client, async_session_factory, app.state.event_dispatcher)

    @app.get("/health")
    async def health():
        from teleapi import __version__
        return {"status": "ok", "version": __version__}

    return app


@pytest.fixture
async def client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as c:
        yield c


@pytest.fixture
async def unauthed_client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as c:
        yield c
