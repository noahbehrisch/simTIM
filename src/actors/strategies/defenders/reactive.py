from typing import Any

from src.actors.strategies.base import DefenderStrategy


class ReactiveDefenderStrategy(DefenderStrategy):
    def __init__(self):
        super().__init__("reactive", detection_window_hours=4.0)

    def get_priority(
        self, action: Any, node: Any, detected_nodes: set[str] | None = None, network: Any = None
    ) -> float:
        node_id = getattr(node, "id", str(node))
        tactic = self.get_d3fend_tactic(action)
        priority = 1.0

        has_detection = detected_nodes and node_id in detected_nodes
        is_compromised = node.compromised

        if has_detection:
            priority += 100
            tactic_boost = {
                "Evict": 200,
                "Isolate": 150,
                "Restore": 100,
                "Detect": 50,
                "Harden": 30,
                "Model": 20,
                "Deceive": 20,
            }
            priority += tactic_boost.get(tactic, 0)

        if is_compromised:
            tactic_boost = {
                "Evict": 300,
                "Restore": 200,
                "Isolate": 150,
                "Harden": 50,
                "Detect": 30,
                "Model": 20,
                "Deceive": 20,
            }
            priority += tactic_boost.get(tactic, 20)

        priority += len(node.assets) * 3

        return priority
