from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from teleapi.auth import verify_api_key
from teleapi.database import get_session
from teleapi.models.channel import Channel
from teleapi.models.sync_job import SyncJob


class SyncRequest(BaseModel):
    limit: int = 1000
    force: bool = False

router = APIRouter(prefix="/api", tags=["sync"], dependencies=[Depends(verify_api_key)])


@router.post("/channels/{channel_id}/sync")
async def trigger_sync(
    channel_id: str,
    request: Request,
    body: SyncRequest = SyncRequest(),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Channel).where((Channel.id == channel_id) | (Channel.username == channel_id))
    channel = (await session.execute(stmt)).scalar_one_or_none()
    if not channel:
        return JSONResponse({"error": "Channel not found"}, status_code=404)

    running = (
        await session.execute(
            select(SyncJob).where(SyncJob.channel_id == channel.id, SyncJob.status.in_(["pending", "running"]))
        )
    ).scalar_one_or_none()
    if running:
        return JSONResponse(
            {"error": "A sync job is already running for this channel", "job_id": running.id},
            status_code=409,
        )

    job = SyncJob(channel_id=channel.id, total=body.limit)
    session.add(job)
    await session.commit()
    await session.refresh(job)

    sync_service = request.app.state.sync_service
    channel_manager = request.app.state.channel_manager
    entity = channel_manager.get_entity(channel.username)
    if entity:
        asyncio.create_task(sync_service.sync_channel(channel.id, entity, job.id, body.limit, body.force))

    return {"job_id": job.id, "status": job.status}


@router.get("/sync-jobs")
async def list_sync_jobs(
    channel_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(SyncJob)
    if channel_id:
        stmt = stmt.where(SyncJob.channel_id == channel_id)
    if status:
        stmt = stmt.where(SyncJob.status == status)
    stmt = stmt.order_by(SyncJob.created_at.desc()).limit(limit)

    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": j.id,
            "channel_id": j.channel_id,
            "status": j.status,
            "total": j.total,
            "synced": j.synced,
            "error": j.error,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "created_at": j.created_at.isoformat(),
        }
        for j in results
    ]


@router.get("/sync-jobs/{job_id}")
async def get_sync_job(job_id: str, session: AsyncSession = Depends(get_session)):
    stmt = select(SyncJob).where(SyncJob.id == job_id)
    job = (await session.execute(stmt)).scalar_one_or_none()
    if not job:
        return JSONResponse({"error": "Sync job not found"}, status_code=404)

    return {
        "id": job.id,
        "channel_id": job.channel_id,
        "status": job.status,
        "total": job.total,
        "synced": job.synced,
        "error": job.error,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "created_at": job.created_at.isoformat(),
    }
