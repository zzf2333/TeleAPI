from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from teleapi.telegram.normalizer import (
    _detect_type,
    _extract_entities,
    _extract_media,
    _serialize_safe,
    normalize_message,
)


pytestmark = pytest.mark.unit


def _make_msg(**kwargs):
    msg = MagicMock()
    msg.id = kwargs.get("id", 100)
    msg.message = kwargs.get("message", "hello")
    msg.media = kwargs.get("media", None)
    msg.entities = kwargs.get("entities", None)
    msg.date = kwargs.get("date", datetime(2025, 1, 1, tzinfo=timezone.utc))
    msg.edit_date = kwargs.get("edit_date", None)
    msg.views = kwargs.get("views", 10)
    msg.forwards = kwargs.get("forwards", 1)
    msg.replies = kwargs.get("replies", None)
    msg.action = kwargs.get("action", None)
    msg.to_dict.return_value = {"_": "Message", "id": msg.id}
    return msg


class TestDetectType:
    def test_text_no_media(self):
        msg = _make_msg()
        assert _detect_type(msg) == "text"

    def test_photo(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaPhoto"
        msg = _make_msg(media=media)
        assert _detect_type(msg) == "photo"

    def test_document(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaDocument"
        msg = _make_msg(media=media)
        assert _detect_type(msg) == "document"

    def test_link(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaWebPage"
        msg = _make_msg(media=media)
        assert _detect_type(msg) == "link"

    def test_geo(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaGeo"
        msg = _make_msg(media=media)
        assert _detect_type(msg) == "geo"

    def test_poll(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaPoll"
        msg = _make_msg(media=media)
        assert _detect_type(msg) == "poll"

    def test_unknown_media(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaUnknown"
        msg = _make_msg(media=media)
        assert _detect_type(msg) == "other"


class TestExtractMedia:
    def test_no_media(self):
        msg = _make_msg()
        assert _extract_media(msg) == []

    def test_photo_media(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaPhoto"
        media.photo.id = 12345
        media.document = None
        media.webpage = None
        msg = _make_msg(media=media)
        result = _extract_media(msg)
        assert len(result) == 1
        assert result[0]["photo_id"] == 12345

    def test_document_media(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaDocument"
        media.photo = None
        media.document.id = 99
        media.document.mime_type = "application/pdf"
        media.document.size = 1024
        del media.webpage
        msg = _make_msg(media=media)
        result = _extract_media(msg)
        assert result[0]["document_id"] == 99
        assert result[0]["mime_type"] == "application/pdf"

    def test_webpage_media(self):
        media = MagicMock()
        type(media).__name__ = "MessageMediaWebPage"
        media.photo = None
        media.document = None
        media.webpage.url = "https://example.com"
        media.webpage.title = "Example"
        msg = _make_msg(media=media)
        result = _extract_media(msg)
        assert result[0]["url"] == "https://example.com"


class TestExtractEntities:
    def test_no_entities(self):
        msg = _make_msg(entities=None)
        assert _extract_entities(msg) == []

    def test_entities(self):
        e = MagicMock()
        type(e).__name__ = "MessageEntityBold"
        e.offset = 0
        e.length = 5
        del e.url
        msg = _make_msg(entities=[e])
        result = _extract_entities(msg)
        assert result[0]["type"] == "bold"
        assert result[0]["offset"] == 0

    def test_entity_with_url(self):
        e = MagicMock()
        type(e).__name__ = "MessageEntityTextUrl"
        e.offset = 0
        e.length = 10
        e.url = "https://example.com"
        msg = _make_msg(entities=[e])
        result = _extract_entities(msg)
        assert result[0]["url"] == "https://example.com"


class TestNormalizeMessage:
    def test_basic(self):
        msg = _make_msg()
        result = normalize_message(msg, "testch", "Test Ch")
        assert result["telegram_message_id"] == 100
        assert result["channel_username"] == "testch"
        assert result["type"] == "text"
        assert result["text"] == "hello"
        assert result["url"] == "https://t.me/testch/100"

    def test_empty_text(self):
        msg = _make_msg(message=None)
        result = normalize_message(msg, "ch", "Ch")
        assert result["text"] == ""

    def test_naive_datetime_gets_utc(self):
        naive = datetime(2025, 6, 1, 12, 0, 0)
        msg = _make_msg(date=naive)
        result = normalize_message(msg, "ch", "Ch")
        assert result["date"].tzinfo == timezone.utc

    def test_edit_date_gets_utc(self):
        naive = datetime(2025, 6, 1, 13, 0, 0)
        msg = _make_msg(edit_date=naive)
        result = normalize_message(msg, "ch", "Ch")
        assert result["edit_date"].tzinfo == timezone.utc

    def test_replies_count(self):
        replies = MagicMock()
        replies.replies = 42
        msg = _make_msg(replies=replies)
        result = normalize_message(msg, "ch", "Ch")
        assert result["replies"] == 42

    def test_media_serialized_as_json(self):
        msg = _make_msg()
        result = normalize_message(msg, "ch", "Ch")
        parsed = json.loads(result["media"])
        assert isinstance(parsed, list)

    def test_raw_field(self):
        msg = _make_msg()
        result = normalize_message(msg, "ch", "Ch")
        parsed = json.loads(result["raw"])
        assert parsed["_"] == "Message"


class TestSerializeSafe:
    def test_bytes_to_hex(self):
        result = json.loads(_serialize_safe({"data": b"\xde\xad"}))
        assert result["data"] == "dead"

    def test_datetime_to_iso(self):
        dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        result = json.loads(_serialize_safe({"ts": dt}))
        assert "2025-01-01" in result["ts"]
