from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.core.access_utils import get_node_access

from .actor import Actor
from .strategies import get_defender_strategy

if TYPE_CHECKING:
    from src.actions.action import Action
    from src.core.network import Link, Node

logger = logging.getLogger(__name__)


class Defender(Actor):
    def __init__(
        self,
        id: str,
        strategy: str = "reactive",
        capacity: int = 2,
        budget: float = float("inf"),
    ):
        super().__init__(id, "defender", capacity=capacity, strategy=strategy, budget=budget)
        self.is_defender: bool = True
        self.is_attacker: bool = False
        self.visible_nodes: set[Node] = set()
        self.compromised_nodes: set[str] = set()
        self.visible_links: set[Link] = set()
        self.compromised_links: set[Link] = set()
        self.available_actions: list[Action] = []
        self.system_damage_prevented: float = 0.0
        self.detected_attacks: list[dict[str, Any]] = []
        self._strategy_component = get_defender_strategy(strategy)

    def make_decision(self, network_state):
        if not self.can_schedule_action():
            logger.debug(
                f"Defender {self.id} cannot schedule (capacity={self.capacity}, ongoing={len(self.ongoing_actions)}, pending={self.pending_action_count})"
            )
            return False
        decision = self.choose_best_action(network_state)
        if decision:
            action, target = decision
            if hasattr(action, "is_link_action") and action.is_link_action():
                actor_access = get_node_access(target.node1, self.id)
            else:
                actor_access = get_node_access(target, self.id)
            logger.info(
                f"Defender {self.id} scheduling {action.name} on {getattr(target, 'id', str(target))}"
            )
            if action.precondition(target, actor_access, self.id):
                self.pending_action_count += 1
                self._pending_pairs.add((action.name, getattr(target, "id", str(target))))
                self.simulator.schedule_event(
                    self.simulator.current_time,
                    "start_action",
                    {
                        "actor": self,
                        "action": action,
                        "target": target,
                        "actor_access": actor_access,
                    },
                )
                return True
            else:
                self._pending_pairs.add((action.name, getattr(target, "id", str(target))))
                logger.warning(
                    f"Defender {self.id}: Precondition failed for {action.name} on {target.id}"
                )
        return False

    def choose_best_action(self, network_state) -> tuple[Any, Any] | None:
        return self._strategy_component.choose_action(self, network_state)

    def change_strategy(self, new_strategy: str):
        self.strategy = new_strategy
        self._strategy_component = get_defender_strategy(new_strategy)

    def on_action_finished(self, action, status, target=None):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        if self.running and self.simulator:
            self._last_run_time = -1.0
            self.simulator.schedule_event(
                self.simulator.current_time,
                "actor_run",
                {"actor": self},
            )

    def on_attack_detected(self, detection_data):
        detected_action = detection_data.get("detected_action")
        detected_target = detection_data.get("detected_target")
        detected_actor = detection_data.get("detected_actor")
        if not all([detected_action, detected_target, detected_actor]):
            logger.warning(f"Defender {self.id}: Invalid detection data received")
            return
        timestamp = getattr(self.simulator, "current_time", 0.0)
        logger.info(
            f"Defender {self.id}: Detected {detected_action.name} by {detected_actor.id} on {getattr(detected_target, 'id', str(detected_target))}"
        )
        self.detected_attacks.append(
            {
                "timestamp": timestamp,
                "detected_action": detected_action.name,
                "detected_actor": detected_actor.id,
                "detected_target": getattr(detected_target, "id", str(detected_target)),
                "detection_method": detection_data.get("detection_method", "unknown"),
            }
        )
        if self.can_schedule_action() and self.simulator:
            self.simulator.schedule_event(
                self.simulator.current_time,
                "actor_run",
                {"actor": self},
            )

    def record_detection_economics(self, attack_source, damage_prevented=0.0, detection_cost=0.0):
        timestamp = getattr(self.simulator, "current_time", 0.0)
        if detection_cost > 0:
            self.incurred_cost += detection_cost
            self.record_economic_event(
                timestamp,
                "cost",
                detection_cost,
                {"attacker": attack_source, "type": "detection_cost"},
            )
        if damage_prevented > 0:
            self.record_economic_event(
                timestamp,
                "damage_prevented",
                -damage_prevented,
                {"attacker": attack_source, "type": "mitigation"},
            )

    def _execute_defensive_action(self, action, target):
        if self.simulator and self.can_schedule_action():
            actor_access = get_node_access(target, self.id)
            if action.precondition(target, actor_access, self.id):
                self.pending_action_count += 1
                self.simulator.schedule_event(
                    self.simulator.current_time,
                    "start_action",
                    {
                        "actor": self,
                        "action": action,
                        "target": target,
                        "actor_access": actor_access,
                    },
                )

    def _calculate_total_system_damage(self, time_interval=None):
        if hasattr(self.simulator, "get_total_system_damage"):
            return self.simulator.get_total_system_damage(time_interval)
        estimated_damage = 0.0
        for detection in self.detected_attacks:
            if (
                time_interval is None
                or time_interval[0] <= detection.get("timestamp", 0) <= time_interval[1]
            ):
                estimated_damage += 5000.0
        if hasattr(self.simulator, "network") and self.simulator.network:
            nodes = self.simulator.network.nodes_list
            for node in nodes:
                if getattr(node, "compromised", False):
                    assets = getattr(node, "assets", [])
                    damage_rate = len(assets) * 100.0
                    if time_interval:
                        duration = time_interval[1] - time_interval[0]
                        estimated_damage += damage_rate * duration
                    else:
                        estimated_damage += damage_rate * getattr(
                            self.simulator, "current_time", 1.0
                        )
        return estimated_damage

    def record_system_damage(self, damage_amount, timestamp=None, metadata=None):
        if timestamp is None:
            timestamp = getattr(self.simulator, "current_time", 0.0)
        self.record_economic_event(
            timestamp, "damage", damage_amount, metadata or {"type": "system_damage"}
        )
