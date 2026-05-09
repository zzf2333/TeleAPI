from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from teleapi import __version__
from teleapi.config import TeleAPIConfig, load_config
from teleapi.database import close_db, init_db, init_engine
from teleapi import database as _db
from teleapi.telegram.client import TelegramClientManager
from teleapi.telegram.login import QRLoginService, PhoneLoginService
from teleapi.models.channel import Channel
from teleapi.telegram.channel_manager import ChannelManager
from teleapi.telegram.sync import HistorySyncService
from teleapi.telegram.listener import RealtimeListener
from teleapi.services.event import EventDispatcher
from teleapi.services.filter import FilterEngine
from teleapi.services.webhook import WebhookDispatcher
from teleapi.api.auth_routes import router as auth_router
from teleapi.api.channels import router as channels_router
from teleapi.api.messages import router as messages_router
from teleapi.api.sync import router as sync_router
from teleapi.api.webhooks import router as webhooks_router
from teleapi.api.system import router as system_router
import teleapi.models  # noqa: F401 — register SQLModel tables

logger = logging.getLogger("teleapi")


def _setup_logging(level: str):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _load_app_config() -> TeleAPIConfig:
    config_path = os.environ.get("TELEAPI_CONFIG", "config.yaml")
    return load_config(config_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = _load_app_config()
    _setup_logging(config.app.log_level)

    Path("data").mkdir(exist_ok=True)
    init_engine(config.database.url)
    await init_db()

    telegram_client = TelegramClientManager(
        api_id=config.telegram.api_id,
        api_hash=config.telegram.api_hash,
        session_name=config.telegram.session_name,
    )
    await telegram_client.connect()

    channel_manager = ChannelManager(telegram_client.client)
    sync_service = HistorySyncService(telegram_client.client, _db._async_session_factory)
    event_dispatcher = EventDispatcher()
    filter_engine = FilterEngine(config.filters)
    webhook_dispatcher = WebhookDispatcher(config.outputs.webhooks, filter_engine, _db._async_session_factory)
    event_dispatcher.subscribe("message.created", webhook_dispatcher.on_message_created)
    listener = RealtimeListener(telegram_client.client, _db._async_session_factory, event_dispatcher)

    app.state.config = config
    app.state.telegram_client = telegram_client
    app.state.login_service = QRLoginService(telegram_client)
    app.state.phone_login_service = PhoneLoginService(telegram_client)
    app.state.channel_manager = channel_manager
    app.state.sync_service = sync_service
    app.state.event_dispatcher = event_dispatcher
    app.state.listener = listener
    logger.info("TeleAPI v%s started", __version__)

    if await telegram_client.is_authorized():
        import asyncio
        from sqlmodel import select
        from teleapi.models.sync_job import SyncJob

        if config.telegram.channels:
            async with _db._async_session_factory() as session:
                channels = await channel_manager.resolve_channels(config.telegram.channels, session)
            for ch, cfg in zip(channels, [c for c in config.telegram.channels if c.enabled]):
                if not cfg.sync_history:
                    continue
                async with _db._async_session_factory() as session:
                    recent_ok = (await session.execute(
                        select(SyncJob)
                        .where(SyncJob.channel_id == ch.id, SyncJob.status == "success")
                        .order_by(SyncJob.created_at.desc())
                        .limit(1)
                    )).scalar_one_or_none()
                    if recent_ok:
                        logger.info("Skipping auto-sync for %s: recent success exists", cfg.username)
                        continue

                    entity = channel_manager.get_entity(cfg.username)
                    if entity and ch.last_message_id:
                        has_new = False
                        async for _ in telegram_client.client.iter_messages(entity, limit=1, min_id=ch.last_message_id):
                            has_new = True
                        if not has_new:
                            logger.info("Skipping auto-sync for %s: no new messages", cfg.username)
                            continue

                    job = SyncJob(channel_id=ch.id, total=cfg.history_limit)
                    session.add(job)
                    await session.commit()
                    await session.refresh(job)
                if entity:
                    asyncio.create_task(sync_service.sync_channel(ch.id, entity, job.id, cfg.history_limit))
                    logger.info("Auto-sync started for %s (job=%s)", cfg.username, job.id)

        async with _db._async_session_factory() as session:
            all_enabled = (await session.execute(
                select(Channel).where(Channel.enabled.is_(True))
            )).scalars().all()

            for ch in all_enabled:
                if not channel_manager.get_entity(ch.username):
                    try:
                        entity = await telegram_client.client.get_entity(ch.username)
                        channel_manager._entities[ch.username] = entity
                        logger.info("Resolved DB channel: %s", ch.username)
                    except Exception as e:
                        logger.warning("Failed to resolve DB channel %s: %s", ch.username, e)

        entities = channel_manager.get_all_entities()
        if entities:
            await listener.start(entities)

    yield

    await listener.stop()
    await webhook_dispatcher.close()
    await telegram_client.disconnect()
    await close_db()
    logger.info("TeleAPI shutdown")


app = FastAPI(
    title="TeleAPI",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(channels_router)
app.include_router(messages_router)
app.include_router(sync_router)
app.include_router(webhooks_router)
app.include_router(system_router)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "version": __version__})


_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=_frontend_dir / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file = _frontend_dir / path
        if file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(_frontend_dir / "index.html")


def cli():
    import uvicorn

    config = _load_app_config()
    uvicorn.run(
        "teleapi.main:app",
        host=config.app.host,
        port=config.app.port,
        log_level=config.app.log_level,
    )
