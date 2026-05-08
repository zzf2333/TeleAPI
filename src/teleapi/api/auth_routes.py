from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from teleapi.telegram.client import TelegramClientManager
from teleapi.telegram.login import LoginStatus, QRLoginService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_login_service(request: Request) -> QRLoginService:
    return request.app.state.login_service


def _get_client_manager(request: Request) -> TelegramClientManager:
    return request.app.state.telegram_client


@router.post("/qr-login")
async def start_qr_login(request: Request):
    svc = _get_login_service(request)
    state = await svc.start()
    return {
        "status": state.status.value,
        "qr_image": f"data:image/png;base64,{state.qr_image_base64}" if state.qr_image_base64 else "",
    }


@router.get("/qr-login/status")
async def qr_login_status(request: Request):
    svc = _get_login_service(request)
    state = svc.state
    resp = {"status": state.status.value}
    if state.error:
        resp["error"] = state.error
    return resp


@router.post("/qr-login/refresh")
async def refresh_qr(request: Request):
    svc = _get_login_service(request)
    state = await svc.refresh_qr()
    return {
        "status": state.status.value,
        "qr_image": f"data:image/png;base64,{state.qr_image_base64}" if state.qr_image_base64 else "",
    }


@router.post("/2fa")
async def submit_2fa(request: Request):
    body = await request.json()
    password = body.get("password", "")
    if not password:
        return JSONResponse({"error": "password is required"}, status_code=400)

    svc = _get_login_service(request)
    state = await svc.submit_2fa(password)
    resp = {"status": state.status.value}
    if state.error:
        resp["error"] = state.error
    return resp


@router.get("/status")
async def auth_status(request: Request):
    cm = _get_client_manager(request)
    authorized = await cm.is_authorized()
    data = {"authorized": authorized}
    if authorized:
        data["user"] = await cm.get_me()
    return data


@router.post("/logout")
async def logout(request: Request):
    cm = _get_client_manager(request)
    svc = _get_login_service(request)
    await cm.logout()
    svc.reset()
    return {"status": "logged_out"}
