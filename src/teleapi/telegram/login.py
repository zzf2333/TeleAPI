from __future__ import annotations

import asyncio
import io
import base64
import logging
from dataclasses import dataclass, field
from enum import Enum

import qrcode
from telethon.errors import SessionPasswordNeededError

from teleapi.telegram.client import TelegramClientManager

logger = logging.getLogger("teleapi.telegram.login")


class LoginStatus(str, Enum):
    IDLE = "idle"
    WAITING = "waiting"
    TWO_FA_REQUIRED = "2fa_required"
    SUCCESS = "success"
    EXPIRED = "expired"
    ERROR = "error"


@dataclass
class LoginState:
    status: LoginStatus = LoginStatus.IDLE
    qr_image_base64: str = ""
    error: str = ""
    _task: asyncio.Task | None = field(default=None, repr=False)
    _qr_login: object | None = field(default=None, repr=False)


class QRLoginService:

    def __init__(self, client_manager: TelegramClientManager):
        self._cm = client_manager
        self._state = LoginState()

    @property
    def state(self) -> LoginState:
        return self._state

    def _generate_qr_base64(self, url: str) -> str:
        img = qrcode.make(url, box_size=8, border=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    async def start(self) -> LoginState:
        if self._state._task and not self._state._task.done():
            return self._state

        client = self._cm.client
        qr_login = await client.qr_login()
        self._state._qr_login = qr_login

        qr_b64 = self._generate_qr_base64(qr_login.url)
        self._state.status = LoginStatus.WAITING
        self._state.qr_image_base64 = qr_b64
        self._state.error = ""

        self._state._task = asyncio.create_task(self._wait_for_scan(qr_login))
        return self._state

    async def _wait_for_scan(self, qr_login):
        try:
            await qr_login.wait(timeout=120)
            self._cm.save_session()
            self._state.status = LoginStatus.SUCCESS
            me = await self._cm.get_me()
            logger.info("QR login success: %s", me)
        except SessionPasswordNeededError:
            self._state.status = LoginStatus.TWO_FA_REQUIRED
            logger.info("QR login: 2FA password required")
        except asyncio.TimeoutError:
            self._state.status = LoginStatus.EXPIRED
            logger.info("QR login expired")
        except Exception as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = str(e)
            logger.error("QR login error: %s", e)

    async def submit_2fa(self, password: str) -> LoginState:
        try:
            await self._cm.client.sign_in(password=password)
            self._cm.save_session()
            self._state.status = LoginStatus.SUCCESS
            logger.info("2FA login success")
        except Exception as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = str(e)
            logger.error("2FA login error: %s", e)
        return self._state

    async def refresh_qr(self) -> LoginState:
        if self._state._qr_login is None:
            return await self.start()
        try:
            await self._state._qr_login.recreate()
            qr_b64 = self._generate_qr_base64(self._state._qr_login.url)
            self._state.status = LoginStatus.WAITING
            self._state.qr_image_base64 = qr_b64
            self._state.error = ""

            if self._state._task and not self._state._task.done():
                self._state._task.cancel()
            self._state._task = asyncio.create_task(self._wait_for_scan(self._state._qr_login))
        except Exception as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = str(e)
        return self._state

    def reset(self):
        if self._state._task and not self._state._task.done():
            self._state._task.cancel()
        self._state = LoginState()
