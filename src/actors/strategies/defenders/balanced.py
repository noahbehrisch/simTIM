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
        return 40.0 * ongoing_count
