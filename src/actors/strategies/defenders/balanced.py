from typing import Any

from src.actors.strategies.base import DefenderStrategy


class BalancedDefenderStrategy(DefenderStrategy):
    def __init__(self):
        super().__init__("balanced", detection_window_hours=3.0)

    def get_priority(
        self, action: Any, node: Any, detected_nodes: set[str] | None = None, network: Any = None
    ) -> float:
        node_id = getattr(node, "id", str(node))
        tactic = self.get_d3fend_tactic(action)
        priority = 1.0

        if detected_nodes and node_id in detected_nodes:
            priority += 100
            tactic_boost = {
                "Evict": 80,
                "Isolate": 60,
                "Restore": 40,
                "Detect": 30,
                "Harden": 20,
                "Model": 15,
                "Deceive": 15,
            }
            priority += tactic_boost.get(tactic, 0)

        if node.compromised:
            tactic_boost = {
                "Evict": 120,
                "Restore": 80,
                "Isolate": 60,
                "Harden": 30,
                "Detect": 25,
                "Model": 15,
                "Deceive": 15,
            }
            priority += tactic_boost.get(tactic, 15)

        if not node.compromised and len(node.vulnerabilities) > 0:
            if tactic == "Harden":
                priority += 80 + len(node.vulnerabilities) * 12
            elif tactic == "Model":
                priority += 50 + len(node.vulnerabilities) * 8

        baseline = {
            "Detect": 50,
            "Harden": 45,
            "Model": 40,
            "Isolate": 35,
            "Deceive": 30,
            "Evict": 25,
            "Restore": 20,
        }
        priority += baseline.get(tactic, 10)

        priority += len(node.assets) * 6

        return priority

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        """Balanced strategy applies moderate selectivity, weighing
        both proactive and reactive value for concurrent actions."""
        return 40.0 * ongoing_count
