from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class AppConfig(BaseModel):
    name: str = "TeleAPI"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"


class TelegramChannelConfig(BaseModel):
    username: str
    enabled: bool = True
    sync_history: bool = False
    history_limit: int = 1000
    filters: list[str] = []


class TelegramConfig(BaseModel):
    api_id: int
    api_hash: str
    session_name: str = "teleapi"
    channels: list[TelegramChannelConfig] = []


class FilterConfig(BaseModel):
    name: str
    include_keywords: list[str] = []
    exclude_keywords: list[str] = []
    regex: list[str] = []
    message_types: list[str] = []
    channels: list[str] = []


class SecurityConfig(BaseModel):
    admin_api_key: str
    allow_health_without_auth: bool = True

    @field_validator("admin_api_key")
    @classmethod
    def reject_weak_key(cls, v: str) -> str:
        forbidden = {"", "changeme", "your_admin_api_key", "test", "admin"}
        if v.strip().lower() in forbidden:
            raise ValueError("admin_api_key must be set to a strong, unique value")
        if len(v) < 16:
            raise ValueError("admin_api_key must be at least 16 characters")
        return v


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff_seconds: list[int] = [5, 30, 120]


class WebhookConfig(BaseModel):
    name: str
    url: str
    secret: str = ""
    enabled: bool = True
    events: list[str] = ["message.created"]
    channels: list[str] = []
    filters: list[str] = []
    retry: RetryConfig = RetryConfig()


class APIOutputConfig(BaseModel):
    enabled: bool = True


class WebSocketOutputConfig(BaseModel):
    enabled: bool = True


class OutputsConfig(BaseModel):
    api: APIOutputConfig = APIOutputConfig()
    websocket: WebSocketOutputConfig = WebSocketOutputConfig()
    webhooks: list[WebhookConfig] = []


class DatabaseConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///./data/teleapi.db"


class TeleAPIConfig(BaseModel):
    app: AppConfig = AppConfig()
    telegram: TelegramConfig
    filters: list[FilterConfig] = []
    security: SecurityConfig
    outputs: OutputsConfig = OutputsConfig()
    database: DatabaseConfig = DatabaseConfig()


_ENV_OVERRIDES = {
    "TELEAPI_TELEGRAM_API_ID": ("telegram", "api_id"),
    "TELEAPI_TELEGRAM_API_HASH": ("telegram", "api_hash"),
    "TELEAPI_SECURITY_ADMIN_API_KEY": ("security", "admin_api_key"),
    "TELEAPI_DATABASE_URL": ("database", "url"),
}


def _apply_env_overrides(data: dict) -> dict:
    for env_key, path in _ENV_OVERRIDES.items():
        value = os.environ.get(env_key)
        if value is None:
            continue
        section, key = path
        if section not in data:
            data[section] = {}
        target = data[section]
        if key == "api_id":
            value = int(value)
        target[key] = value
    return data


def load_config(path: str | Path = "config.yaml") -> TeleAPIConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    data = _apply_env_overrides(data)
    return TeleAPIConfig(**data)
