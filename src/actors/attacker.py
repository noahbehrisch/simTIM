import logging
from typing import Any

from src.core.access_levels import NodeAccessLevel
from src.core.access_utils import get_node_access, set_node_access
from src.core.economic_model import calculate_action_gain
from src.core.network import Node

from .actor import Actor
from .strategies import get_attacker_strategy

logger = logging.getLogger(__name__)


class Attacker(Actor):
    def __init__(
        self,
        id: str,
        strategy: str = "random",
        capacity: float = float("inf"),
        budget: float = float("inf"),
    ):
        super().__init__(id, "attacker", capacity=capacity, strategy=strategy, budget=budget)
        self.is_attacker = True
        self.visible_nodes: set[Any] = set()
        self.compromised_nodes: set[Any] = set()
        self.visible_links: set[Any] = set()
        self.compromised_links: set[Any] = set()
        self.available_actions: list[Any] = []
        self.time_proportional_gain_rate = 0.0
        self._strategy_component = get_attacker_strategy(strategy)

    def make_decision(self, network_state):
        if not self.can_schedule_action():
            logger.debug(
                f"{self.id} cannot schedule action (capacity: {len(self.ongoing_actions)}/{self.capacity})"
            )
            return False
        logger.debug(
            f"{self.id} making decision at t={(self.simulator.current_time if self.simulator else '?')}"
        )
        logger.debug(
            f"  Visible nodes: {[n.id if hasattr(n, 'id') else str(n) for n in self.visible_nodes]}"
        )
        logger.debug(f"  Available actions: {len(self.available_actions)}")
        decision = self.choose_action(network_state)
        if decision:
            action, target = decision
            actor_access = get_node_access(target, self.id)
            logger.debug(
                f"  Chose: {action.name} on {getattr(target, 'id', str(target))} (access: {actor_access})"
            )
            if action.precondition(target, actor_access, self.id):
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
            logger.debug("  No valid action found!")
        return False

    def choose_action(self, network_state):
        return self._strategy_component.choose_action(self, network_state)

    def change_strategy(self, new_strategy: str):
        self.strategy = new_strategy
        self._strategy_component = get_attacker_strategy(new_strategy)

    def on_action_finished(self, action, status, target=None):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        if status == "success" and target is not None:
            if hasattr(target, "access") and hasattr(target, "id"):
                access_level = get_node_access(target, self.id)
                if access_level >= NodeAccessLevel.USER:
                    self.compromised_nodes.add(target.id)
                    self._discover_links_from_node(target)
            if hasattr(self, "simulator") and self.simulator:
                self.on_successful_attack(action, target, self.simulator.current_time)

    def _discover_links_from_node(self, node: Node):
        if not hasattr(self, "simulator") or not self.simulator or not self.simulator.network:
            return
        links = self.simulator.network.get_links_for_node(node.id)
        for link in links:
            if link not in self.visible_links:
                self.visible_links.add(link)
            connected_node = link.node1 if link.node2.id == node.id else link.node2
            if connected_node not in self.visible_nodes:
                self.visible_nodes.add(connected_node)
                current_access = get_node_access(connected_node, self.id)
                if current_access == NodeAccessLevel.NONE:
                    set_node_access(connected_node, self.id, NodeAccessLevel.VISIBLE)

    def on_successful_attack(self, action, target, timestamp):
        get_node_access(target, self.id)
        one_off_gain = calculate_action_gain(action.name, target)
        self.total_gain += one_off_gain
        self.record_economic_event(
            timestamp,
            "gain",
            one_off_gain,
            {
                "action": action.name,
                "target": getattr(target, "id", str(target)),
                "type": "one_off_gain",
            },
        )
