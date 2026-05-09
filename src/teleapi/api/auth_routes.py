from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from teleapi.auth import verify_api_key
from teleapi.telegram.client import TelegramClientManager
from teleapi.telegram.login import LoginStatus, QRLoginService, PhoneLoginService

router = APIRouter(prefix="/api/auth", tags=["auth"], dependencies=[Depends(verify_api_key)])


def _get_login_service(request: Request) -> QRLoginService:
    return request.app.state.login_service


def _get_phone_login_service(request: Request) -> PhoneLoginService:
    return request.app.state.phone_login_service


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


@router.post("/phone-login/send-code")
async def phone_send_code(request: Request):
    body = await request.json()
    phone = body.get("phone", "").strip()
    if not phone:
        return JSONResponse({"error": "phone is required"}, status_code=400)

    svc = _get_phone_login_service(request)
    state = await svc.send_code(phone)
    resp = {"status": state.status.value}
    if state.error:
        resp["error"] = state.error
    return resp


@router.post("/phone-login/verify-code")
async def phone_verify_code(request: Request):
    body = await request.json()
    code = body.get("code", "").strip()
    if not code:
        return JSONResponse({"error": "code is required"}, status_code=400)

    svc = _get_phone_login_service(request)
    state = await svc.verify_code(code)
    resp = {"status": state.status.value}
    if state.error:
        resp["error"] = state.error
    return resp


@router.get("/phone-login/status")
async def phone_login_status(request: Request):
    svc = _get_phone_login_service(request)
    state = svc.state
    resp = {"status": state.status.value}
    if state.error:
        resp["error"] = state.error
    return resp


@router.post("/2fa")
async def submit_2fa(request: Request):
    body = await request.json()
    password = body.get("password", "")
    if not password:
        return JSONResponse({"error": "password is required"}, status_code=400)

    phone_svc = _get_phone_login_service(request)
    if phone_svc.state.status == LoginStatus.TWO_FA_REQUIRED:
        state = await phone_svc.submit_2fa(password)
    else:
        svc = _get_login_service(request)
        state = await svc.submit_2fa(password)

    resp = {"status": state.status.value}
    if state.error:
        resp["error"] = state.error
    return resp


@router.post("/session-login")
async def session_login(request: Request):
    body = await request.json()
    session_string = body.get("session_string", "").strip()
    if not session_string:
        return JSONResponse({"error": "session_string is required"}, status_code=400)
    cm = _get_client_manager(request)
    try:
        user_info = await cm.import_session(session_string)
        return {"status": "success", "user": user_info}
    except ValueError as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=400)


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
    qr_svc = _get_login_service(request)
    phone_svc = _get_phone_login_service(request)
    await cm.logout()
    qr_svc.reset()
    phone_svc.reset()
    return {"status": "logged_out"}
