from __future__ import annotations

import re
from teleapi.config import FilterConfig


class FilterEngine:

    def __init__(self, filters: list[FilterConfig]):
        self._filters: dict[str, FilterConfig] = {f.name: f for f in filters}
        self._compiled_regex: dict[str, list[re.Pattern]] = {}
        for f in filters:
            if f.regex:
                self._compiled_regex[f.name] = [re.compile(r, re.IGNORECASE) for r in f.regex]

    def matches(self, message: dict, filter_name: str) -> bool:
        cfg = self._filters.get(filter_name)
        if not cfg:
            return True

        if cfg.channels and message.get("channel_username", "") not in cfg.channels:
            return False

        if cfg.message_types and message.get("type", "text") not in cfg.message_types:
            return False

        text = (message.get("text") or "").lower()

        has_include = bool(cfg.include_keywords) or bool(cfg.regex)
        if has_include:
            keyword_hit = any(kw.lower() in text for kw in cfg.include_keywords) if cfg.include_keywords else False
            regex_patterns = self._compiled_regex.get(filter_name, [])
            regex_hit = any(p.search(message.get("text") or "") for p in regex_patterns) if regex_patterns else False
            if not keyword_hit and not regex_hit:
                return False

        if cfg.exclude_keywords:
            if any(kw.lower() in text for kw in cfg.exclude_keywords):
                return False

        return True

    def apply_filters(self, message: dict, filter_names: list[str]) -> bool:
        if not filter_names:
            return True
        return any(self.matches(message, name) for name in filter_names)
