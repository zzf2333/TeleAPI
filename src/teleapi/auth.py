from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.exceptions import HTTPException


async def verify_api_key(request: Request):
    config = request.app.state.config
    expected_key = config.security.admin_api_key

    api_key = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        api_key = auth_header[7:]
    if not api_key:
        api_key = request.headers.get("X-TeleAPI-Key")

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
