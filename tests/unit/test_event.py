from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from teleapi.services.event import EventDispatcher


pytestmark = pytest.mark.unit


class TestEventDispatcher:
    async def test_subscribe_and_dispatch(self):
        d = EventDispatcher()
        handler = AsyncMock()
        d.subscribe("test.event", handler)
        await d.dispatch("test.event", {"key": "value"})
        handler.assert_called_once_with({"key": "value"})

    async def test_multiple_handlers(self):
        d = EventDispatcher()
        h1 = AsyncMock()
        h2 = AsyncMock()
        d.subscribe("test.event", h1)
        d.subscribe("test.event", h2)
        await d.dispatch("test.event", {})
        h1.assert_called_once()
        h2.assert_called_once()

    async def test_no_handler_silent(self):
        d = EventDispatcher()
        await d.dispatch("no.handlers", {})

    async def test_handler_error_isolated(self):
        d = EventDispatcher()
        bad = AsyncMock(side_effect=RuntimeError("boom"))
        good = AsyncMock()
        d.subscribe("test.event", bad)
        d.subscribe("test.event", good)
        await d.dispatch("test.event", {})
        good.assert_called_once()

    async def test_payload_passthrough(self):
        d = EventDispatcher()
        handler = AsyncMock()
        d.subscribe("e", handler)
        payload = {"a": 1, "b": [2, 3]}
        await d.dispatch("e", payload)
        handler.assert_called_once_with(payload)

    async def test_same_handler_subscribed_twice(self):
        d = EventDispatcher()
        handler = AsyncMock()
        d.subscribe("e", handler)
        d.subscribe("e", handler)
        await d.dispatch("e", {})
        assert handler.call_count == 2

    async def test_different_events_isolated(self):
        d = EventDispatcher()
        h1 = AsyncMock()
        h2 = AsyncMock()
        d.subscribe("event.a", h1)
        d.subscribe("event.b", h2)
        await d.dispatch("event.a", {})
        h1.assert_called_once()
        h2.assert_not_called()
