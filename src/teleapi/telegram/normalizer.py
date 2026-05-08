from __future__ import annotations

import json
from datetime import timezone


def _serialize_safe(obj) -> str:
    def _default(o):
        if isinstance(o, bytes):
            return o.hex()
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return str(o)

    return json.dumps(obj, default=_default, ensure_ascii=False)


def _detect_type(msg) -> str:
    if msg.media is None:
        return "text"
    type_name = type(msg.media).__name__
    mapping = {
        "MessageMediaPhoto": "photo",
        "MessageMediaDocument": "document",
        "MessageMediaWebPage": "link",
        "MessageMediaGeo": "geo",
        "MessageMediaContact": "contact",
        "MessageMediaPoll": "poll",
        "MessageMediaDice": "dice",
    }
    return mapping.get(type_name, "other")


def _extract_media(msg) -> list[dict]:
    if msg.media is None:
        return []
    media_type = _detect_type(msg)
    info = {"type": media_type}
    if hasattr(msg.media, "photo") and msg.media.photo:
        photo = msg.media.photo
        info["photo_id"] = photo.id
    if hasattr(msg.media, "document") and msg.media.document:
        doc = msg.media.document
        info["document_id"] = doc.id
        info["mime_type"] = doc.mime_type
        info["size"] = doc.size
    if hasattr(msg.media, "webpage") and msg.media.webpage:
        wp = msg.media.webpage
        info["url"] = getattr(wp, "url", "")
        info["title"] = getattr(wp, "title", "")
    return [info]


def _extract_entities(msg) -> list[dict]:
    if not msg.entities:
        return []
    results = []
    for e in msg.entities:
        ent = {
            "type": type(e).__name__.replace("MessageEntity", "").lower(),
            "offset": e.offset,
            "length": e.length,
        }
        if hasattr(e, "url") and e.url:
            ent["url"] = e.url
        results.append(ent)
    return results


def normalize_message(msg, channel_username: str, channel_title: str) -> dict:
    date = msg.date
    if date and date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    edit_date = msg.edit_date
    if edit_date and edit_date.tzinfo is None:
        edit_date = edit_date.replace(tzinfo=timezone.utc)

    replies_count = None
    if msg.replies:
        replies_count = msg.replies.replies

    return {
        "telegram_message_id": msg.id,
        "channel_username": channel_username,
        "channel_title": channel_title,
        "type": _detect_type(msg),
        "text": msg.message or "",
        "date": date,
        "edit_date": edit_date,
        "views": msg.views,
        "forwards": msg.forwards,
        "replies": replies_count,
        "url": f"https://t.me/{channel_username}/{msg.id}",
        "media": _serialize_safe(_extract_media(msg)),
        "entities": _serialize_safe(_extract_entities(msg)),
        "raw": _serialize_safe(msg.to_dict() if hasattr(msg, "to_dict") else {}),
    }
