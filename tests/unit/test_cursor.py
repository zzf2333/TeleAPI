from __future__ import annotations

import pytest
from datetime import datetime, timezone

from teleapi.api.messages import _encode_cursor, _decode_cursor


pytestmark = pytest.mark.unit


class TestCursorCodec:
    def test_roundtrip(self):
        dt = datetime(2025, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        uid = "abc123def456"
        cursor = _encode_cursor(dt, uid)
        decoded_dt, decoded_id = _decode_cursor(cursor)
        assert decoded_dt == dt
        assert decoded_id == uid

    def test_invalid_base64(self):
        with pytest.raises(Exception):
            _decode_cursor("not!valid!base64!!!")

    def test_utc_datetime_stable(self):
        dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        c1 = _encode_cursor(dt, "id1")
        c2 = _encode_cursor(dt, "id1")
        assert c1 == c2
