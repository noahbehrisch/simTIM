"""Tests for src.utils.time_utils."""

from src.utils.time_utils import format_time, parse_event


class TestFormatTime:
    def test_whole_hour(self):
        assert format_time(5.0) == "05:00"

    def test_zero(self):
        assert format_time(0.0) == "00:00"

    def test_half_hour(self):
        assert format_time(1.5) == "01:30"

    def test_large(self):
        assert format_time(100.0) == "100:00"

    def test_quarter(self):
        assert format_time(2.25) == "02:15"


class TestParseEvent:
    def test_object_with_attrs(self):
        class Ev:
            time = 1.0
            event_type = "start_action"
            data = {"actor": "att1"}

        t, et, d = parse_event(Ev())
        assert t == 1.0
        assert et == "start_action"
        assert d == {"actor": "att1"}

    def test_tuple(self):
        t, et, d = parse_event((2.0, "end_action", {}))
        assert t == 2.0
        assert et == "end_action"

    def test_list(self):
        t, et, d = parse_event([3.0, "tick", None])
        assert t == 3.0

    def test_invalid(self):
        t, et, d = parse_event("not an event")
        assert t is None
        assert et is None
        assert d is None

    def test_short_tuple(self):
        t, et, d = parse_event((1.0,))
        assert t is None
