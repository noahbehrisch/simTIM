from typing import Any

from src.actors.strategies.base import DefenderStrategy


class MonitoringDefenderStrategy(DefenderStrategy):
    def __init__(self):
        super().__init__("monitoring", detection_window_hours=0.0)

    def get_priority(
        self, action: Any, node: Any, detected_nodes: set[str] | None = None, network: Any = None
    ) -> float:
        tactic = self.get_d3fend_tactic(action)
        priority = 1.0

        tactic_priorities = {
            "Detect": 150,
            "Model": 100,
            "Deceive": 80,
            "Isolate": 40,
            "Harden": 30,
            "Evict": 20,
            "Restore": 20,
        }
        priority += tactic_priorities.get(tactic, 10)

        link_count = len(network.get_links_for_node(node.id)) if network else 0
        if tactic == "Detect":
            priority += len(node.assets) * 12
            priority += link_count * 10
        elif tactic == "Model":
            priority += len(node.assets) * 8
        elif tactic == "Deceive":
            priority += link_count * 5

        if node.compromised:
            if tactic == "Detect":
                priority += 50
            else:
                priority += 20

        return priority
