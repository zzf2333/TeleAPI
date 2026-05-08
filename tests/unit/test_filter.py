from __future__ import annotations

import pytest

from teleapi.config import FilterConfig
from teleapi.services.filter import FilterEngine


pytestmark = pytest.mark.unit


def _msg(text="hello world", channel="testch", type_="text"):
    return {"text": text, "channel_username": channel, "type": type_}


class TestFilterMatches:
    def test_unknown_filter_passes(self):
        engine = FilterEngine([])
        assert engine.matches(_msg(), "nonexistent") is True

    def test_keyword_match(self):
        f = FilterConfig(name="f1", include_keywords=["hello"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_keyword_no_match(self):
        f = FilterConfig(name="f1", include_keywords=["bye"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is False

    def test_keyword_case_insensitive(self):
        f = FilterConfig(name="f1", include_keywords=["HELLO"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_regex_match(self):
        f = FilterConfig(name="f1", regex=[r"hel+o"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_regex_case_insensitive(self):
        f = FilterConfig(name="f1", regex=[r"HELLO"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_keyword_or_regex(self):
        f = FilterConfig(name="f1", include_keywords=["bye"], regex=[r"hel+o"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_keyword_and_regex_both_miss(self):
        f = FilterConfig(name="f1", include_keywords=["bye"], regex=[r"xyz"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is False

    def test_exclude_keywords(self):
        f = FilterConfig(name="f1", include_keywords=["hello"], exclude_keywords=["world"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is False

    def test_channel_filter_match(self):
        f = FilterConfig(name="f1", channels=["testch"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_channel_filter_no_match(self):
        f = FilterConfig(name="f1", channels=["otherch"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is False

    def test_type_filter_match(self):
        f = FilterConfig(name="f1", message_types=["text"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True

    def test_type_filter_no_match(self):
        f = FilterConfig(name="f1", message_types=["photo"])
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is False

    def test_empty_filter_passes(self):
        f = FilterConfig(name="f1")
        engine = FilterEngine([f])
        assert engine.matches(_msg(), "f1") is True


class TestApplyFilters:
    def test_any_match(self):
        f1 = FilterConfig(name="f1", include_keywords=["bye"])
        f2 = FilterConfig(name="f2", include_keywords=["hello"])
        engine = FilterEngine([f1, f2])
        assert engine.apply_filters(_msg(), ["f1", "f2"]) is True

    def test_none_match(self):
        f1 = FilterConfig(name="f1", include_keywords=["bye"])
        f2 = FilterConfig(name="f2", include_keywords=["nope"])
        engine = FilterEngine([f1, f2])
        assert engine.apply_filters(_msg(), ["f1", "f2"]) is False

    def test_empty_list_passes(self):
        engine = FilterEngine([])
        assert engine.apply_filters(_msg(), []) is True
