from typing import Any, Set
from src.actors.strategies.base import DefenderStrategy


class MonitoringDefenderStrategy(DefenderStrategy):
    """
    Monitoring: Strongly prioritizes deploying monitoring/detection capabilities.
    Will still take other actions, but with lower priority.
    """

    def __init__(self):
        super().__init__("monitoring", detection_window_hours=0.0)

    def get_priority(self, action: Any, node: Any, detected_nodes: Set[str]) -> float:
        priority = 1

        if (
            "Monitoring" in action.name
            or "Detection" in action.name
            or "Log" in action.name
        ):
            priority += 100
            priority += len(node.assets) * 10
            priority += len(node.links) * 8

        if node.compromised:
            priority += 30

        return priority
