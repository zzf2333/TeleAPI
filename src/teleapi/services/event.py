from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Coroutine, Any

logger = logging.getLogger("teleapi.services.event")


class EventDispatcher:

    def __init__(self):
        self._handlers: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[..., Coroutine[Any, Any, None]]):
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler %s to event %s", handler.__name__, event_type)

    async def dispatch(self, event_type: str, payload: dict):
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                logger.error("Event handler %s failed for %s: %s", handler.__name__, event_type, e)
