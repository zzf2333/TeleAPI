from __future__ import annotations

import asyncio
import io
import base64
import logging
from dataclasses import dataclass, field
from enum import Enum

import qrcode
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    FloodWaitError,
)

from teleapi.telegram.client import TelegramClientManager

logger = logging.getLogger("teleapi.telegram.login")


class LoginStatus(str, Enum):
    IDLE = "idle"
    WAITING = "waiting"
    CODE_SENT = "code_sent"
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


@dataclass
class PhoneLoginState:
    status: LoginStatus = LoginStatus.IDLE
    phone: str = ""
    phone_code_hash: str = ""
    error: str = ""


class PhoneLoginService:

    def __init__(self, client_manager: TelegramClientManager):
        self._cm = client_manager
        self._state = PhoneLoginState()

    @property
    def state(self) -> PhoneLoginState:
        return self._state

    async def send_code(self, phone: str) -> PhoneLoginState:
        try:
            result = await self._cm.client.send_code_request(phone)
            self._state.phone = phone
            self._state.phone_code_hash = result.phone_code_hash
            self._state.status = LoginStatus.CODE_SENT
            self._state.error = ""
            logger.info("Verification code sent to %s", phone)
        except PhoneNumberInvalidError:
            self._state.status = LoginStatus.ERROR
            self._state.error = "手机号格式无效，请使用国际格式（如 +86...）"
        except FloodWaitError as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = f"请求过于频繁，请在 {e.seconds} 秒后重试"
        except Exception as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = str(e)
            logger.error("Send code error: %s", e)
        return self._state

    async def verify_code(self, code: str) -> PhoneLoginState:
        try:
            await self._cm.client.sign_in(
                phone=self._state.phone,
                code=code,
                phone_code_hash=self._state.phone_code_hash,
            )
            self._cm.save_session()
            self._state.status = LoginStatus.SUCCESS
            logger.info("Phone login success")
        except PhoneCodeInvalidError:
            self._state.status = LoginStatus.ERROR
            self._state.error = "验证码错误"
        except PhoneCodeExpiredError:
            self._state.status = LoginStatus.EXPIRED
            self._state.error = "验证码已过期，请重新发送"
        except SessionPasswordNeededError:
            self._state.status = LoginStatus.TWO_FA_REQUIRED
            logger.info("Phone login: 2FA password required")
        except FloodWaitError as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = f"请求过于频繁，请在 {e.seconds} 秒后重试"
        except Exception as e:
            self._state.status = LoginStatus.ERROR
            self._state.error = str(e)
            logger.error("Phone login error: %s", e)
        return self._state

    async def submit_2fa(self, password: str) -> PhoneLoginState:
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

    def reset(self):
        self._state = PhoneLoginState()
