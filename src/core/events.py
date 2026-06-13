import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from weakref import ReferenceType, WeakMethod, ref

logger = logging.getLogger(__name__)


class EventType(Enum):
    ACTION_STARTED = auto()
    ACTION_FINISHED = auto()
    ACTION_SUCCEEDED = auto()
    ACTION_FAILED = auto()
    ACTION_ABORTED = auto()
    ACTION_INTERRUPTED = auto()
    ACTION_CAPACITY_EXCEEDED = auto()
    ACTION_ERROR = auto()
    ATTACK_DETECTED = auto()
    ACTOR_RUN = auto()
    STATE_CHANGED = auto()
    ACCESS_CHANGED = auto()
    PROPERTY_CHANGED = auto()
    SIMULATION_STARTED = auto()
    SIMULATION_ENDED = auto()
    TIME_ACCUMULATED = auto()
    CUSTOM = auto()


@dataclass
class SimulationEvent:
    event_type: EventType
    time: float
    data: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    propagate: bool = True

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def stop_propagation(self) -> None:
        self.propagate = False

    def with_data(self, **kwargs) -> "SimulationEvent":
        new_data = {**self.data, **kwargs}
        return SimulationEvent(
            event_type=self.event_type,
            time=self.time,
            data=new_data,
            source=self.source,
            propagate=self.propagate,
        )


EventCallback = Callable[[SimulationEvent], None]
EventFilter = Callable[[SimulationEvent], bool]
EventMiddleware = Callable[[SimulationEvent, Callable[[], None]], None]


@dataclass
class Subscription:
    callback: EventCallback
    priority: int = 0
    filter_fn: EventFilter | None = None
    once: bool = False
    weak: bool = False
    _weak_ref: "WeakMethod[EventCallback] | ReferenceType[EventCallback] | None" = field(
        default=None, repr=False
    )

    def matches(self, event: SimulationEvent) -> bool:
        if self.filter_fn is None:
            return True
        try:
            return self.filter_fn(event)
        except Exception:
            return False

    def invoke(self, event: SimulationEvent) -> bool:
        if self.weak and self._weak_ref is not None:
            callback = self._weak_ref()
            if callback is None:
                return False
            callback(event)
        else:
            self.callback(event)
        return True


class EventBus:
    def __init__(self, thread_safe: bool = False):
        self._subscribers: dict[EventType, list[Subscription]] = {}
        self._global_subscribers: list[Subscription] = []
        self._async_queue: list[SimulationEvent] = []
        self._processing = False
        self._middlewares: list[EventMiddleware] = []
        self._event_history: list[SimulationEvent] = []
        self._record_history = False
        self._history_max_size: int | None = None
        self._paused = False
        self._pending_while_paused: list[SimulationEvent] = []
        self._lock = threading.RLock() if thread_safe else None
        self._thread_safe = thread_safe

    def _acquire_lock(self):
        if self._lock:
            self._lock.acquire()

    def _release_lock(self):
        if self._lock:
            self._lock.release()

    def subscribe(
        self,
        event_type: EventType,
        callback: EventCallback,
        priority: int = 0,
        filter_fn: EventFilter | None = None,
        once: bool = False,
        weak: bool = False,
    ) -> Callable[[], None]:
        self._acquire_lock()
        try:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            weak_ref: WeakMethod[EventCallback] | ReferenceType[EventCallback] | None = None
            if weak:
                try:
                    weak_ref = WeakMethod(callback)
                except TypeError:
                    weak_ref = ref(callback)

            subscription = Subscription(
                callback=callback,
                priority=priority,
                filter_fn=filter_fn,
                once=once,
                weak=weak,
                _weak_ref=weak_ref,
            )

            self._subscribers[event_type].append(subscription)
            self._subscribers[event_type].sort(key=lambda s: -s.priority)

            def unsubscribe():
                self._acquire_lock()
                try:
                    if event_type in self._subscribers:
                        if subscription in self._subscribers[event_type]:
                            self._subscribers[event_type].remove(subscription)
                finally:
                    self._release_lock()

            return unsubscribe
        finally:
            self._release_lock()

    def subscribe_all(
        self,
        callback: EventCallback,
        priority: int = 0,
        filter_fn: EventFilter | None = None,
    ) -> Callable[[], None]:
        self._acquire_lock()
        try:
            subscription = Subscription(
                callback=callback,
                priority=priority,
                filter_fn=filter_fn,
            )
            self._global_subscribers.append(subscription)
            self._global_subscribers.sort(key=lambda s: -s.priority)

            def unsubscribe():
                self._acquire_lock()
                try:
                    if subscription in self._global_subscribers:
                        self._global_subscribers.remove(subscription)
                finally:
                    self._release_lock()

            return unsubscribe
        finally:
            self._release_lock()

    def subscribe_once(
        self,
        event_type: EventType,
        callback: EventCallback,
        priority: int = 0,
        filter_fn: EventFilter | None = None,
    ) -> Callable[[], None]:
        return self.subscribe(
            event_type=event_type,
            callback=callback,
            priority=priority,
            filter_fn=filter_fn,
            once=True,
        )

    def add_middleware(self, middleware: EventMiddleware) -> Callable[[], None]:
        self._middlewares.append(middleware)

        def remove():
            if middleware in self._middlewares:
                self._middlewares.remove(middleware)

        return remove

    def enable_history(self, max_size: int | None = None) -> None:
        self._record_history = True
        self._history_max_size = max_size

    def disable_history(self) -> None:
        self._record_history = False

    def get_history(
        self,
        event_type: EventType | None = None,
        since_time: float | None = None,
    ) -> list[SimulationEvent]:
        result = self._event_history
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if since_time is not None:
            result = [e for e in result if e.time >= since_time]
        return result

    def clear_history(self) -> None:
        self._event_history.clear()

    def replay_history(
        self,
        event_type: EventType | None = None,
        since_time: float | None = None,
    ) -> int:
        events = self.get_history(event_type, since_time)
        original_record_setting = self._record_history
        self._record_history = False
        try:
            for event in events:
                self.publish(event)
        finally:
            self._record_history = original_record_setting
        return len(events)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False
        for event in self._pending_while_paused:
            self.publish(event)
        self._pending_while_paused.clear()

    def publish(self, event: SimulationEvent) -> None:
        if self._paused:
            self._pending_while_paused.append(event)
            return

        self._acquire_lock()
        try:
            if self._record_history:
                if self._history_max_size and len(self._event_history) >= self._history_max_size:
                    self._event_history.pop(0)
                self._event_history.append(event)

            def dispatch():
                self._dispatch_event(event)

            if self._middlewares:
                self._run_middleware_chain(event, dispatch, 0)
            else:
                dispatch()
        finally:
            self._release_lock()

    def _run_middleware_chain(
        self,
        event: SimulationEvent,
        final_dispatch: Callable[[], None],
        index: int,
    ) -> None:
        if index >= len(self._middlewares):
            final_dispatch()
            return

        middleware = self._middlewares[index]

        def next_middleware():
            self._run_middleware_chain(event, final_dispatch, index + 1)

        try:
            middleware(event, next_middleware)
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            next_middleware()

    def _dispatch_event(self, event: SimulationEvent) -> None:
        to_remove_global = []
        for subscription in self._global_subscribers:
            if not event.propagate:
                break
            if subscription.matches(event):
                if not subscription.invoke(event):
                    to_remove_global.append(subscription)
                elif subscription.once:
                    to_remove_global.append(subscription)

        for sub in to_remove_global:
            if sub in self._global_subscribers:
                self._global_subscribers.remove(sub)

        if event.event_type in self._subscribers:
            to_remove = []
            for subscription in self._subscribers[event.event_type]:
                if not event.propagate:
                    break
                if subscription.matches(event):
                    if not subscription.invoke(event):
                        to_remove.append(subscription)
                    elif subscription.once:
                        to_remove.append(subscription)

            for sub in to_remove:
                if sub in self._subscribers[event.event_type]:
                    self._subscribers[event.event_type].remove(sub)

    def publish_async(self, event: SimulationEvent) -> None:
        self._async_queue.append(event)

    def process_async_queue(self) -> int:
        if self._processing:
            return 0

        self._processing = True
        processed = 0

        while self._async_queue:
            event = self._async_queue.pop(0)
            self.publish(event)
            processed += 1

        self._processing = False
        return processed

    def emit(
        self,
        event_type: EventType,
        time: float,
        source: str | None = None,
        **data,
    ) -> SimulationEvent:
        event = SimulationEvent(
            event_type=event_type,
            time=time,
            data=data,
            source=source,
        )
        self.publish(event)
        return event

    def clear(self) -> None:
        self._acquire_lock()
        try:
            self._subscribers.clear()
            self._global_subscribers.clear()
            self._async_queue.clear()
            self._middlewares.clear()
            self._event_history.clear()
            self._pending_while_paused.clear()
        finally:
            self._release_lock()

    def get_subscriber_count(self, event_type: EventType | None = None) -> int:
        if event_type is None:
            total = len(self._global_subscribers)
            for subscribers in self._subscribers.values():
                total += len(subscribers)
            return total
        return len(self._subscribers.get(event_type, []))


class SimulationObserver:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._unsubscribers: list[Callable[[], None]] = []

    def on_action_started(self, event: SimulationEvent) -> None:
        pass

    def on_action_succeeded(self, event: SimulationEvent) -> None:
        pass

    def on_action_failed(self, event: SimulationEvent) -> None:
        pass

    def on_attack_detected(self, event: SimulationEvent) -> None:
        pass

    def on_state_changed(self, event: SimulationEvent) -> None:
        pass

    def register(self) -> None:
        self._unsubscribers.append(
            self._event_bus.subscribe(EventType.ACTION_STARTED, self.on_action_started)
        )
        self._unsubscribers.append(
            self._event_bus.subscribe(EventType.ACTION_SUCCEEDED, self.on_action_succeeded)
        )
        self._unsubscribers.append(
            self._event_bus.subscribe(EventType.ACTION_FAILED, self.on_action_failed)
        )
        self._unsubscribers.append(
            self._event_bus.subscribe(EventType.ATTACK_DETECTED, self.on_attack_detected)
        )
        self._unsubscribers.append(
            self._event_bus.subscribe(EventType.STATE_CHANGED, self.on_state_changed)
        )

    def unregister(self) -> None:
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()


class HistoryRecorder(SimulationObserver):
    def __init__(self, event_bus: EventBus, max_size: int | None = None):
        super().__init__(event_bus)
        self._history: list[tuple[float, str, dict[str, Any]]] = []
        self._max_size = max_size

    def _record(self, event: SimulationEvent) -> None:
        entry = (event.time, event.event_type.name.lower(), event.data)
        if self._max_size and len(self._history) >= self._max_size:
            self._history.pop(0)
        self._history.append(entry)

    def register(self) -> None:
        self._unsubscribers.append(self._event_bus.subscribe_all(self._record))

    @property
    def history(self) -> list[tuple[float, str, dict[str, Any]]]:
        return self._history

    def clear(self) -> None:
        self._history.clear()


class DefenderAlertObserver(SimulationObserver):
    def __init__(self, event_bus: EventBus, defenders: list):
        super().__init__(event_bus)
        self._defenders = defenders

    def on_attack_detected(self, event: SimulationEvent) -> None:
        for defender in self._defenders:
            if hasattr(defender, "on_attack_detected"):
                defender.on_attack_detected(event.data)
