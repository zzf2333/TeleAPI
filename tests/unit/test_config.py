from __future__ import annotations


import pytest
import yaml

from teleapi.config import TeleAPIConfig, load_config


pytestmark = pytest.mark.unit


class TestLoadConfig:
    def test_load_valid(self, tmp_path, minimal_config_dict):
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(minimal_config_dict))
        cfg = load_config(str(p))
        assert cfg.telegram.api_id == 123456

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "missing.yaml"))

    def test_empty_yaml(self, tmp_path):
        p = tmp_path / "config.yaml"
        p.write_text("")
        with pytest.raises(Exception):
            load_config(str(p))

    def test_missing_telegram_section(self, tmp_path):
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump({"security": {"admin_api_key": "x" * 20}}))
        with pytest.raises(Exception):
            load_config(str(p))


class TestEnvOverrides:
    def test_override_api_id(self, tmp_path, minimal_config_dict, monkeypatch):
        monkeypatch.setenv("TELEAPI_TELEGRAM_API_ID", "999999")
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(minimal_config_dict))
        cfg = load_config(str(p))
        assert cfg.telegram.api_id == 999999

    def test_override_api_hash(self, tmp_path, minimal_config_dict, monkeypatch):
        monkeypatch.setenv("TELEAPI_TELEGRAM_API_HASH", "overridden_hash")
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(minimal_config_dict))
        cfg = load_config(str(p))
        assert cfg.telegram.api_hash == "overridden_hash"

    def test_override_admin_api_key(self, tmp_path, minimal_config_dict, monkeypatch):
        new_key = "env_override_strong_key_123"
        monkeypatch.setenv("TELEAPI_SECURITY_ADMIN_API_KEY", new_key)
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(minimal_config_dict))
        cfg = load_config(str(p))
        assert cfg.security.admin_api_key == new_key

    def test_override_database_url(self, tmp_path, minimal_config_dict, monkeypatch):
        monkeypatch.setenv("TELEAPI_DATABASE_URL", "sqlite+aiosqlite:///test.db")
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(minimal_config_dict))
        cfg = load_config(str(p))
        assert cfg.database.url == "sqlite+aiosqlite:///test.db"


class TestWeakKeyRejection:
    def test_empty_key(self, minimal_config_dict):
        minimal_config_dict["security"]["admin_api_key"] = ""
        with pytest.raises(Exception):
            TeleAPIConfig(**minimal_config_dict)

    def test_changeme(self, minimal_config_dict):
        minimal_config_dict["security"]["admin_api_key"] = "changeme"
        with pytest.raises(Exception):
            TeleAPIConfig(**minimal_config_dict)

    def test_default_placeholder(self, minimal_config_dict):
        minimal_config_dict["security"]["admin_api_key"] = "your_admin_api_key"
        with pytest.raises(Exception):
            TeleAPIConfig(**minimal_config_dict)

    def test_short_key(self, minimal_config_dict):
        minimal_config_dict["security"]["admin_api_key"] = "short"
        with pytest.raises(Exception):
            TeleAPIConfig(**minimal_config_dict)

    def test_case_insensitive_forbidden(self, minimal_config_dict):
        minimal_config_dict["security"]["admin_api_key"] = "CHANGEME"
        with pytest.raises(Exception):
            TeleAPIConfig(**minimal_config_dict)

    def test_accept_strong_key(self, minimal_config_dict):
        minimal_config_dict["security"]["admin_api_key"] = "a_very_strong_secret_key_here"
        cfg = TeleAPIConfig(**minimal_config_dict)
        assert cfg.security.admin_api_key == "a_very_strong_secret_key_here"


class TestDefaults:
    def test_app_defaults(self, minimal_config_dict):
        cfg = TeleAPIConfig(**minimal_config_dict)
        assert cfg.app.name == "TeleAPI"
        assert cfg.app.port == 8080
        assert cfg.app.log_level == "info"

    def test_database_default_url(self, minimal_config_dict):
        cfg = TeleAPIConfig(**minimal_config_dict)
        assert "teleapi.db" in cfg.database.url

    def test_filter_default_empty(self, minimal_config_dict):
        cfg = TeleAPIConfig(**minimal_config_dict)
        assert cfg.filters == []

    def test_channel_config_defaults(self):
        from teleapi.config import TelegramChannelConfig
        ch = TelegramChannelConfig(username="test")
        assert ch.enabled is True
        assert ch.sync_history is False
        assert ch.history_limit == 1000

    def test_retry_config_defaults(self):
        from teleapi.config import RetryConfig
        rc = RetryConfig()
        assert rc.max_attempts == 3
        assert rc.backoff_seconds == [5, 30, 120]
