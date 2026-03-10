"""Tests for EventBus, SimulationEvent, and observers."""

import pytest

from src.core.events import (
    DefenderAlertObserver,
    EventBus,
    EventType,
    HistoryRecorder,
    SimulationEvent,
)


@pytest.fixture
def bus():
    return EventBus()


def _event(etype=EventType.ACTION_STARTED, time=0.0, **data):
    return SimulationEvent(event_type=etype, time=time, data=data, source="test")


# ── SimulationEvent ──────────────────────────────────────────────


class TestSimulationEvent:
    def test_get_data(self):
        e = _event(node_id="web")
        assert e.get("node_id") == "web"
        assert e.get("missing", 42) == 42

    def test_stop_propagation(self):
        e = _event()
        assert e.propagate is True
        e.stop_propagation()
        assert e.propagate is False

    def test_with_data_returns_new_event(self):
        e = _event(foo="bar")
        e2 = e.with_data(baz="qux")
        assert e2.get("foo") == "bar"
        assert e2.get("baz") == "qux"
        assert e.get("baz") is None  # original untouched


# ── Subscribe / Publish ──────────────────────────────────────────


class TestSubscribePublish:
    def test_basic_subscribe_publish(self, bus):
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(e))
        bus.publish(_event())
        assert len(received) == 1

    def test_different_event_type_not_received(self, bus):
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(e))
        bus.publish(_event(etype=EventType.ACTION_FAILED))
        assert len(received) == 0

    def test_unsubscribe(self, bus):
        received = []
        unsub = bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(e))
        unsub()
        bus.publish(_event())
        assert len(received) == 0

    def test_subscribe_once(self, bus):
        received = []
        bus.subscribe_once(EventType.ACTION_STARTED, lambda e: received.append(e))
        bus.publish(_event())
        bus.publish(_event())
        assert len(received) == 1

    def test_priority_ordering(self, bus):
        order = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: order.append("low"), priority=0)
        bus.subscribe(EventType.ACTION_STARTED, lambda e: order.append("high"), priority=10)
        bus.publish(_event())
        assert order == ["high", "low"]

    def test_filter_fn(self, bus):
        received = []
        bus.subscribe(
            EventType.ACTION_STARTED,
            lambda e: received.append(e),
            filter_fn=lambda e: e.get("important") is True,
        )
        bus.publish(_event(important=False))
        bus.publish(_event(important=True))
        assert len(received) == 1


class TestSubscribeAll:
    def test_receives_any_event_type(self, bus):
        received = []
        bus.subscribe_all(lambda e: received.append(e.event_type))
        bus.publish(_event(etype=EventType.ACTION_STARTED))
        bus.publish(_event(etype=EventType.ACTION_FAILED))
        assert received == [EventType.ACTION_STARTED, EventType.ACTION_FAILED]

    def test_unsubscribe_all(self, bus):
        received = []
        unsub = bus.subscribe_all(lambda e: received.append(1))
        unsub()
        bus.publish(_event())
        assert len(received) == 0


# ── Stop propagation ─────────────────────────────────────────────


class TestStopPropagation:
    def test_stops_later_handlers(self, bus):
        order = []

        def stopper(e):
            order.append("first")
            e.stop_propagation()

        bus.subscribe(EventType.ACTION_STARTED, stopper, priority=10)
        bus.subscribe(EventType.ACTION_STARTED, lambda e: order.append("second"), priority=0)
        bus.publish(_event())
        assert order == ["first"]


# ── Pause / Resume ───────────────────────────────────────────────


class TestPauseResume:
    def test_paused_events_queued(self, bus):
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(1))
        bus.pause()
        bus.publish(_event())
        assert len(received) == 0
        bus.resume()
        assert len(received) == 1

    def test_resume_clears_queue(self, bus):
        bus.pause()
        bus.publish(_event())
        bus.resume()
        # second resume should not re-deliver
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(1))
        bus.resume()
        assert len(received) == 0


# ── History ──────────────────────────────────────────────────────


class TestHistory:
    def test_history_disabled_by_default(self, bus):
        bus.publish(_event())
        assert bus.get_history() == []

    def test_enable_records(self, bus):
        bus.enable_history()
        bus.publish(_event(time=1.0))
        bus.publish(_event(time=2.0))
        assert len(bus.get_history()) == 2

    def test_filter_by_type(self, bus):
        bus.enable_history()
        bus.publish(_event(etype=EventType.ACTION_STARTED, time=1.0))
        bus.publish(_event(etype=EventType.ACTION_FAILED, time=2.0))
        assert len(bus.get_history(event_type=EventType.ACTION_STARTED)) == 1

    def test_filter_by_time(self, bus):
        bus.enable_history()
        bus.publish(_event(time=1.0))
        bus.publish(_event(time=5.0))
        assert len(bus.get_history(since_time=3.0)) == 1

    def test_history_max_size(self, bus):
        bus.enable_history(max_size=2)
        for t in range(5):
            bus.publish(_event(time=float(t)))
        assert len(bus.get_history()) == 2

    def test_clear_history(self, bus):
        bus.enable_history()
        bus.publish(_event())
        bus.clear_history()
        assert bus.get_history() == []

    def test_disable_stops_recording(self, bus):
        bus.enable_history()
        bus.publish(_event(time=1.0))
        bus.disable_history()
        bus.publish(_event(time=2.0))
        assert len(bus.get_history()) == 1


# ── Replay ───────────────────────────────────────────────────────


class TestReplay:
    def test_replay_re_dispatches(self, bus):
        bus.enable_history()
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(e.time))
        bus.publish(_event(time=1.0))
        bus.publish(_event(time=2.0))
        received.clear()
        count = bus.replay_history()
        assert count == 2
        assert received == [1.0, 2.0]


# ── Middleware ───────────────────────────────────────────────────


class TestMiddleware:
    def test_middleware_intercepts(self, bus):
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(1))

        def blocker(event, next_fn):
            pass  # don't call next_fn

        bus.add_middleware(blocker)
        bus.publish(_event())
        assert len(received) == 0

    def test_middleware_passes_through(self, bus):
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(1))

        def passthrough(event, next_fn):
            next_fn()

        bus.add_middleware(passthrough)
        bus.publish(_event())
        assert len(received) == 1

    def test_remove_middleware(self, bus):
        def blocker(event, next_fn):
            pass

        remove = bus.add_middleware(blocker)
        remove()
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(1))
        bus.publish(_event())
        assert len(received) == 1


# ── Async queue ──────────────────────────────────────────────────


class TestAsyncQueue:
    def test_publish_async_defers(self, bus):
        received = []
        bus.subscribe(EventType.ACTION_STARTED, lambda e: received.append(1))
        bus.publish_async(_event())
        assert len(received) == 0
        count = bus.process_async_queue()
        assert count == 1
        assert len(received) == 1


# ── Emit shorthand ───────────────────────────────────────────────


class TestEmit:
    def test_emit_creates_and_publishes(self, bus):
        received = []
        bus.subscribe(EventType.STATE_CHANGED, lambda e: received.append(e))
        event = bus.emit(EventType.STATE_CHANGED, time=5.0, source="sim", node_id="web")
        assert len(received) == 1
        assert received[0].get("node_id") == "web"
        assert event.time == 5.0


# ── Subscriber count / clear ─────────────────────────────────────


class TestHousekeeping:
    def test_subscriber_count(self, bus):
        bus.subscribe(EventType.ACTION_STARTED, lambda e: None)
        bus.subscribe(EventType.ACTION_STARTED, lambda e: None)
        assert bus.get_subscriber_count(EventType.ACTION_STARTED) == 2
        assert bus.get_subscriber_count(EventType.ACTION_FAILED) == 0

    def test_total_subscriber_count(self, bus):
        bus.subscribe(EventType.ACTION_STARTED, lambda e: None)
        bus.subscribe_all(lambda e: None)
        assert bus.get_subscriber_count() == 2

    def test_clear(self, bus):
        bus.subscribe(EventType.ACTION_STARTED, lambda e: None)
        bus.enable_history()
        bus.publish(_event())
        bus.clear()
        assert bus.get_subscriber_count() == 0
        assert bus.get_history() == []


# ── HistoryRecorder observer ─────────────────────────────────────


class TestHistoryRecorder:
    def test_records_all_events(self, bus):
        recorder = HistoryRecorder(bus)
        recorder.register()
        bus.publish(_event(etype=EventType.ACTION_STARTED, time=1.0))
        bus.publish(_event(etype=EventType.ACTION_FAILED, time=2.0))
        assert len(recorder.history) == 2
        assert recorder.history[0][0] == 1.0

    def test_max_size(self, bus):
        recorder = HistoryRecorder(bus, max_size=2)
        recorder.register()
        for t in range(5):
            bus.publish(_event(time=float(t)))
        assert len(recorder.history) == 2

    def test_clear(self, bus):
        recorder = HistoryRecorder(bus)
        recorder.register()
        bus.publish(_event())
        recorder.clear()
        assert len(recorder.history) == 0

    def test_unregister_stops_recording(self, bus):
        recorder = HistoryRecorder(bus)
        recorder.register()
        bus.publish(_event(time=1.0))
        recorder.unregister()
        bus.publish(_event(time=2.0))
        assert len(recorder.history) == 1


# ── DefenderAlertObserver ────────────────────────────────────────


class TestDefenderAlertObserver:
    def test_forwards_detection_to_defenders(self, bus):
        alerts = []

        class FakeDefender:
            def on_attack_detected(self, data):
                alerts.append(data)

        observer = DefenderAlertObserver(bus, [FakeDefender()])
        observer.register()
        bus.publish(_event(etype=EventType.ATTACK_DETECTED, detected_action="exploit"))
        assert len(alerts) == 1
        assert alerts[0]["detected_action"] == "exploit"
