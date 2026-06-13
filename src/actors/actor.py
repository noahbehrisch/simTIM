from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.actions.action import Action
    from src.core.network import Network
    from src.core.simulator import Simulator


class Actor:
    def __init__(
        self,
        id: str,
        role: str,
        capacity: int | float | None = None,
        strategy: str = "None",
        budget: float = float("inf"),
    ):
        self.id = id
        self.role = role
        self.capacity: int | float = capacity if capacity is not None else 1
        self.strategy = strategy
        self.budget = budget
        self.incurred_cost: float = 0.0
        self.ongoing_actions: set[Action] = set()
        self.pending_action_count: int = 0
        self.simulator: Simulator | None = None
        self.running: bool = False
        self.decision_interval: float = 1.0
        self.total_gain: float = 0.0
        self.action_history: list[dict[str, Any]] = []
        self.economic_events: list[dict[str, Any]] = []
        self._pending_pairs: set[tuple[str, str]] = set()
        self._last_run_time: float = -1.0

    def run(self):
        if not self.running:
            return
        current_time = self.simulator.current_time if self.simulator else 0.0
        if current_time == self._last_run_time:
            return
        self._last_run_time = current_time
        self._pending_pairs.clear()
        max_decisions = min(self.capacity, 10) if self.capacity != float("inf") else 10
        decisions_made = 0
        while self.can_schedule_action() and decisions_made < max_decisions:
            if not self.make_decision(self.simulator.network if self.simulator else None):
                break
            decisions_made += 1
        self._pending_pairs.clear()
        if self.running and self.simulator:
            self.simulator.schedule_event(
                self.simulator.current_time + self.decision_interval,
                "actor_run",
                {"actor": self},
            )

    def __repr__(self) -> str:
        return f"Actor(id={self.id}, capacity={self.capacity}, budget={self.budget}, incurred_cost={self.incurred_cost}, strategy={self.strategy})"

    def can_schedule_action(self) -> bool:
        total_ongoing = len(self.ongoing_actions) + self.pending_action_count
        capacity_ok = self.capacity == float("inf") or total_ongoing < self.capacity
        budget_ok = self.budget == float("inf") or self.incurred_cost < self.budget
        return capacity_ok and budget_ok

    def schedule_action(self, action: Action) -> None:
        if action not in self.ongoing_actions and self.can_schedule_action():
            self.ongoing_actions.add(action)

    def notify_action_finished(self, action: Action, status: str) -> None:
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        self.on_action_finished(action, status)

    def on_action_finished(self, action: Action, status: str, target: Any = None) -> None:
        pass

    def make_decision(self, network_state: Network | None) -> bool:
        raise NotImplementedError

    def record_action_cost(self, action: Action, timestamp: float) -> None:
        cost = action.cost
        self.incurred_cost += cost
        self.action_history.append(
            {
                "timestamp": timestamp,
                "action": action.name,
                "cost": cost,
                "type": "cost",
            }
        )

    def get_concurrent_actions_count(self):
        return len(self.ongoing_actions)

    def record_economic_event(self, timestamp, event_type, value, details=None):
        self.economic_events.append(
            {
                "timestamp": timestamp,
                "type": event_type,
                "value": value,
                "details": details or {},
            }
        )
