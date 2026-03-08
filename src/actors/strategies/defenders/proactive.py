from typing import Any

from src.actors.strategies.base import DefenderStrategy


class ProactiveDefenderStrategy(DefenderStrategy):
    def __init__(self):
        super().__init__("proactive", detection_window_hours=1.0)

    def get_priority(
        self, action: Any, node: Any, detected_nodes: set[str] | None = None, network: Any = None
    ) -> float:
        tactic = self.get_d3fend_tactic(action)
        priority = 1.0

        if not node.compromised and len(node.vulnerabilities) > 0:
            if tactic == "Harden":
                priority += 200 + len(node.vulnerabilities) * 25
            elif tactic == "Model":
                priority += 150 + len(node.vulnerabilities) * 15

        tactic_priorities = {
            "Harden": 120,
            "Model": 100,
            "Detect": 80,
            "Isolate": 70,
            "Deceive": 50,
            "Evict": 30,
            "Restore": 20,
        }
        priority += tactic_priorities.get(tactic, 10)

        priority += len(node.assets) * 12
        link_count = len(network.get_links_for_node(node.id)) if network else 0
        priority += link_count * 4

        if node.compromised:
            priority += 15

        return priority

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        return 40.0 * ongoing_count
